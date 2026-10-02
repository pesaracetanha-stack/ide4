# -*- coding: utf-8 -*-
# codesaver/widgets/code_editor.py
import re
import json
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QMessageBox
from PySide6.QtGui import QColor, QPainter, QTextFormat, QTextCursor, QFont, QPalette
from PySide6.QtCore import Qt, QRect, QSize, Signal

# Safely import the snippet management system
try:
    from ..core.snippet_manager import SnippetManager
except ImportError:
    SnippetManager = None

# 🚀 NEW: Import the advanced LSP Provider
try:
    from ..core.lsp_provider import PythonLSP
except ImportError:
    PythonLSP = None


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    cursorInfoChanged = Signal(int, int, int, int, int) # line, col, total, words, chars

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._file_path = "" 
        self.search_text = ""
        self.search_case_sensitive = False
        self.lsp = None  # To hold the LSP instance
        
        # Initialize snippet system
        self.snippet_mgr = SnippetManager() if SnippetManager else None
        
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.update_cursor_info)

        font = QFont("Consolas", 12)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        p = self.palette()
        p.setColor(QPalette.Base, QColor("#1e1e1e"))
        p.setColor(QPalette.Text, QColor("#d4d4d4"))
        self.setPalette(p)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    # 🚀 NEW: Dynamic LSP Initialization when file is set
    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        self._file_path = value
        if value and PythonLSP and not self.lsp:
            self.lsp = PythonLSP(self, value)

    # ---------- Code Auto-Formatter ----------
    def auto_format(self):
        """Automatic sorting and formatting of code using actual standards"""
        text = self.toPlainText()
        if not text.strip(): return
        
        ext = ""
        if hasattr(self, 'file_path') and self.file_path:
            ext = self.file_path.split('.')[-1].lower()
            
        formatted_text = text
        
        if ext == 'json':
            try:
                obj = json.loads(text)
                formatted_text = json.dumps(obj, indent=4, ensure_ascii=False)
            except Exception:
                pass
                
        elif ext in ('py', 'pyw'):
            try:
                # Use the professional autopep8 library for Python
                import autopep8
                formatted_text = autopep8.fix_code(text, options={'aggressive': 1})
            except ImportError:
                QMessageBox.warning(self, "Formatter Missing", "Please install autopep8 to format Python code:\n\npip install autopep8")
                # Fallback to simple system if library is missing
                lines = text.split('\n')
                cleaned_lines = [line.rstrip() for line in lines]
                formatted_text = '\n'.join(cleaned_lines)
        else:
            # Clean up extra whitespaces for other languages
            lines = text.split('\n')
            cleaned_lines = [line.rstrip() for line in lines]
            formatted_text = '\n'.join(cleaned_lines)
            
        if not formatted_text.endswith('\n'):
            formatted_text += '\n'
                
        if formatted_text != text:
            cursor = self.textCursor()
            old_pos = cursor.position()
            
            self.setPlainText(formatted_text)
            
            new_cursor = self.textCursor()
            new_cursor.setPosition(min(old_pos, len(self.toPlainText())))
            self.setTextCursor(new_cursor)


    def keyPressEvent(self, e):
        # ---------- Snippets Integration (Tab Key) ----------
        if self.snippet_mgr and e.key() == Qt.Key.Key_Tab:
            tc = self.textCursor()
            # Select word under or right before the cursor
            tc.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.KeepAnchor)
            word = tc.selectedText().strip()
            
            if word:
                snippet = self.snippet_mgr.get_snippet(word)
                if snippet:
                    tc.removeSelectedText() # Clear the trigger word (e.g., html5, pydoc)
                    
                    # Clean up snippet placeholders for clean direct insertion
                    clean_snippet = re.sub(r'\$\{\d+:(.*?)\}', r'\1', snippet)
                    clean_snippet = clean_snippet.replace('${0}', '').replace('${0:pass}', 'pass')
                    
                    tc.insertText(clean_snippet)
                    self.setTextCursor(tc)
                    return # Prevent default Tab behavior

        # Default handler
        super().keyPressEvent(e)

    # ---------- Line Numbers & UI ----------
    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        return 15 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2d2d2d")) 

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#2a2d2e"))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        if self.search_text:
            doc = self.document()
            from PySide6.QtGui import QTextDocument # Local import
            cursor = QTextCursor(doc)
            flags = QTextDocument.FindFlag.FindCaseSensitively if self.search_case_sensitive else QTextDocument.FindFlag(0)
            
            while not cursor.isNull() and not cursor.atEnd():
                cursor = doc.find(self.search_text, cursor, flags)
                if not cursor.isNull():
                    sel = QTextEdit.ExtraSelection()
                    sel.cursor = cursor
                    if self.textCursor().hasSelection() and self.textCursor().selectedText() == self.search_text and self.textCursor().selectionStart() == cursor.selectionStart():
                        sel.format.setBackground(QColor("#ff5722"))
                        sel.format.setForeground(QColor("#ffffff"))
                    else:
                        sel.format.setBackground(QColor("#ffeb3b"))
                        sel.format.setForeground(QColor("#000000"))
                    extra_selections.append(sel)

        self.setExtraSelections(extra_selections)

    def update_cursor_info(self):
        tc = self.textCursor()
        line = tc.blockNumber() + 1
        col = tc.columnNumber() + 1
        text = self.toPlainText()
        total_lines = self.blockCount()
        words = len(re.findall(r'\w+', text))
        chars = len(text)
        self.cursorInfoChanged.emit(line, col, total_lines, words, chars)

    # ---------- Search & Replace ----------
    def update_search_highlights(self, text, case_sensitive=False):
        self.search_text = text
        self.search_case_sensitive = case_sensitive
        self.highlight_current_line()
        if not text: return 0
        flags = 0 if case_sensitive else re.IGNORECASE
        return len(re.findall(re.escape(text), self.toPlainText(), flags=flags))

    def find_text(self, text, case_sensitive, backward):
        if not text: return
        from PySide6.QtGui import QTextDocument # Local import
        flags = QTextDocument.FindFlag(0)
        if case_sensitive: flags |= QTextDocument.FindFlag.FindCaseSensitively
        if backward: flags |= QTextDocument.FindFlag.FindBackward
        cursor = self.document().find(text, self.textCursor(), flags)
        if cursor.isNull():
            cursor = self.document().find(text, self.textCursor().document().characterCount() if backward else 0, flags)
        if not cursor.isNull():
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

    def replace_current(self, find_text, replace_text, case_sensitive):
        tc = self.textCursor()
        if tc.hasSelection() and (tc.selectedText() == find_text or (not case_sensitive and tc.selectedText().lower() == find_text.lower())):
            tc.insertText(replace_text)
            self.find_text(find_text, case_sensitive, False)

    def replace_all(self, find_text, replace_text, case_sensitive):
        if not find_text: return
        text = self.toPlainText()
        flags = 0 if case_sensitive else re.IGNORECASE
        new_text = re.sub(re.escape(find_text), replace_text, text, flags=flags)
        if new_text != text:
            self.setPlainText(new_text)