# -*- coding: utf-8 -*-
# codesaver/core/lsp_provider.py
import re
import ast
import html
from PySide6.QtCore import QObject, Qt, QTimer, QEvent, QStringListModel
from PySide6.QtWidgets import QCompleter, QTextEdit, QToolTip
from PySide6.QtGui import QColor, QTextCursor, QTextFormat, QHelpEvent

try:
    import jedi
except ImportError:
    jedi = None


class PythonLSP(QObject):
    """Smart local Language Server Provider (LSP) using Jedi"""
    def __init__(self, editor: QTextEdit, file_path: str):
        super().__init__(editor)
        self.editor = editor
        self.file_path = file_path
        
        self._is_inserting = False
        
        self.completer = QCompleter(self)
        self.completer.setWidget(self.editor)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setMaxVisibleItems(10) 
        self.completer.activated.connect(self._insert_completion)
        
        self.completer.popup().setStyleSheet("""
            QListView { 
                background-color: #1e1e2e; 
                color: #cdd6f4; 
                border: 1px solid #45475a; 
                border-radius: 6px; 
                font-family: Consolas, monospace; 
                font-size: 13px; 
                outline: none;
            }
            QListView::item { 
                padding: 8px 5px; 
                border-bottom: 1px solid #313244;
            }
            QListView::item:selected { 
                background-color: rgba(137, 180, 250, 0.2); 
                color: #89b4fa; 
                font-weight: bold; 
                border-left: 3px solid #89b4fa;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e2e;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #45475a;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #585b70;
            }
        """)
        
        self.word_model = QStringListModel()
        self.completer.setModel(self.word_model)
        
        self.editor.installEventFilter(self)
        self.editor.viewport().installEventFilter(self)
        
        self.diagnostic_timer = QTimer(self)
        self.diagnostic_timer.setSingleShot(True)
        self.diagnostic_timer.timeout.connect(self.run_diagnostics)
        
        self.python_keywords = ['def', 'class', 'import', 'from', 'return', 'if', 'elif', 'else', 'try', 'except', 
                                'True', 'False', 'None', 'self', 'print', 'with', 'as', 'pass', 'break', 'continue', 
                                'and', 'or', 'not', 'in', 'is', 'lambda', 'yield', 'async', 'await']

        if hasattr(self.editor, 'textChanged'):
            self.editor.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        self.diagnostic_timer.start(1000) 
        if self._is_inserting: return
        self._handle_autocomplete_popup()

    def run_diagnostics(self):
        if not hasattr(self.editor, 'toPlainText'): return
        code = self.editor.toPlainText()
        
        if not self.file_path or not self.file_path.endswith('.py'): return
            
        try:
            if jedi:
                script = jedi.Script(code, path=self.file_path)
                errors = script.get_syntax_errors()
                if errors:
                    err = errors[0]
                    self._show_diagnostic_error(err.line, err.get_message())
                    return
                else:
                    self._clear_diagnostics()
            else:
                ast.parse(code)
                self._clear_diagnostics()
        except SyntaxError as e:
            self._show_diagnostic_error(e.lineno, e.msg)
        except Exception:
            pass
            
    def _clear_diagnostics(self):
        if hasattr(self.editor, 'setExtraSelections'):
            current_selections = self.editor.extraSelections()
            filtered = [sel for sel in current_selections if sel.format.background().color().name() != '#f38ba8']
            self.editor.setExtraSelections(filtered)
            
        mw = self.editor.window()
        if hasattr(mw, 'status_label'):
            mw.status_label.setStyleSheet("color: #cdd6f4;")
            if hasattr(self.editor, 'update_cursor_info'):
                self.editor.update_cursor_info()
                
    def _show_diagnostic_error(self, lineno, msg):
        if not lineno or not hasattr(self.editor, 'setExtraSelections'): return
        
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(243, 139, 168, 40)) 
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.format.setUnderlineStyle(QTextFormat.UnderlineStyle.SpellCheckUnderline)
        selection.format.setUnderlineColor(QColor("#f38ba8"))
        
        tc = self.editor.textCursor()
        tc.setPosition(0)
        tc.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, lineno - 1)
        selection.cursor = tc
        
        current_selections = self.editor.extraSelections()
        self.editor.setExtraSelections(current_selections + [selection])
        
        mw = self.editor.window()
        if hasattr(mw, 'status_label'):
            mw.status_label.setStyleSheet("color: #f38ba8; font-weight: bold;")
            mw.status_label.setText(f"❌ Syntax Error (Line {lineno}): {msg}")

    def eventFilter(self, obj, event):
        # 🚀 FIX: جلوگیری از کرش کردن در زمان بسته شدن نرم‌افزار
        if not hasattr(self, 'editor') or self.editor is None:
            return super().eventFilter(obj, event)

        # 🚀 FIX: Intercept ToolTip events on the viewport!
        if obj == self.editor.viewport() and event.type() == QEvent.Type.ToolTip:
            self._handle_hover_tooltip(event)
            return True
                
        if obj == self.editor and event.type() == QEvent.Type.KeyPress:
            c = self.completer
            is_popup_visible = c and c.popup() and c.popup().isVisible()
            
            if is_popup_visible:
                if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_Up, Qt.Key.Key_Down):
                    if event.key() == Qt.Key.Key_Escape:
                        c.popup().hide()
                        return True
                    elif event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Tab):
                        return False # Let completer handle it naturally
                    return False 
            
            # Manual trigger via Ctrl+Space
            is_shortcut = (event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Space)
            if is_shortcut:
                self._handle_autocomplete_popup(force=True)
                return True
                
        return super().eventFilter(obj, event)

    def _handle_hover_tooltip(self, event: QHelpEvent):
        if not jedi or not self.file_path.endswith('.py'):
            return
            
        pos = event.pos()
        tc = self.editor.cursorForPosition(pos)
        
        rect = self.editor.cursorRect(tc)
        if not rect.contains(pos) and abs(rect.x() - pos.x()) > 20:
            QToolTip.hideText()
            return

        line = tc.blockNumber() + 1
        col = tc.positionInBlock()
        code = self.editor.toPlainText()
        
        try:
            script = jedi.Script(code, path=self.file_path)
            definitions = script.infer(line, col)
            
            if definitions:
                d = definitions[0]
                doc_string = d.docstring(raw=True)
                type_name = d.type.capitalize() if d.type else "Object"
                full_name = d.full_name or d.name
                
                doc_html = html.escape(doc_string).replace('\n', '<br>') if doc_string else "<i>No documentation available.</i>"
                
                tooltip_html = f"""
                <div style='background-color:#1e1e2e; color:#cdd6f4; font-family:Consolas, monospace; padding: 5px; border-radius: 5px;'>
                    <div style='color:#89b4fa; font-weight:bold; font-size:14px; margin-bottom: 5px;'>
                        <span style='color:#f38ba8;'>[{type_name}]</span> {full_name}
                    </div>
                    <hr style='border: 1px solid #45475a;'>
                    <div style='margin-top: 5px; font-size:12px; line-height: 1.4;'>
                        {doc_html}
                    </div>
                </div>
                """
                QToolTip.showText(event.globalPos(), tooltip_html, self.editor)
            else:
                QToolTip.hideText()
        except Exception:
            QToolTip.hideText()

    def _handle_autocomplete_popup(self, force=False):
        if not self.completer: return
        
        tc = self.editor.textCursor()
        block_text = tc.block().text()
        col = tc.positionInBlock()
        text_before_cursor = block_text[:col]
        
        match = re.search(r'([a-zA-Z_]\w*)$', text_before_cursor)
        word = match.group(1) if match else ""
        
        if not word and not text_before_cursor.endswith('.') and not force:
            self.completer.popup().hide()
            return

        code = self.editor.toPlainText()
        raw_suggestions = []
        
        if jedi and self.file_path.endswith('.py'):
            try:
                line = tc.blockNumber() + 1
                script = jedi.Script(code, path=self.file_path)
                completions = script.complete(line, col)
                for c in completions:
                    name = c.name
                    if c.type == 'function':
                        name = f"{name}()"
                    raw_suggestions.append(name)
            except Exception:
                pass
                
        if not raw_suggestions:
            words_in_file = list(set(re.findall(r'\b[a-zA-Z_]\w{2,}\b', code)))
            raw_suggestions = list(set(words_in_file + self.python_keywords))
            
        suggestions = [w for w in raw_suggestions if w.lower().startswith(word.lower())]
        suggestions = sorted(list(set(suggestions)))

        if not suggestions or (len(suggestions) == 1 and suggestions[0].replace('()', '') == word):
            self.completer.popup().hide()
            return
            
        self.word_model.setStringList(suggestions)
        self.completer.setCompletionPrefix("") 
        
        self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))
        
        cr = self.editor.cursorRect()
        popup_width = self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width() + 60
        cr.setWidth(max(popup_width, 250)) 
        self.completer.complete(cr)

    def _insert_completion(self, completion):
        self._is_inserting = True
        try:
            tc = self.editor.textCursor()
            block_text = tc.block().text()
            col = tc.positionInBlock()
            text_before_cursor = block_text[:col]
            
            clean_completion = completion.replace('()', '')
            
            match = re.search(r'([a-zA-Z_]\w*)$', text_before_cursor)
            if match:
                prefix_len = len(match.group(1))
                tc.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, prefix_len)
                tc.removeSelectedText()
                
            tc.insertText(clean_completion)
            self.editor.setTextCursor(tc)
            
            if completion.endswith('()'):
                tc.insertText("()")
                tc.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, 1)
                self.editor.setTextCursor(tc)
                
        finally:
            self._is_inserting = False
            
        if self.completer and self.completer.popup():
            self.completer.popup().hide()