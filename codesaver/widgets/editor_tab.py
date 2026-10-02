# -*- coding: utf-8 -*-
# codesaver/widgets/editor_tab.py
import os
from PySide6.QtCore import Signal, Qt, QRect, QPoint, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPlainTextEdit, QMessageBox
from PySide6.QtGui import QFont, QPainter, QColor, QTextOption

from .code_editor import CodeEditor
from .diff_dialog import DiffDialog
from ..core.theme_manager import ThemeColors

class MinimapEditor(QPlainTextEdit):
    def __init__(self, main_editor: QPlainTextEdit):
        super().__init__()
        self.main_editor = main_editor
        
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedWidth(100)
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setCursorWidth(0)
        
        self.setStyleSheet(f"""
            background-color: {ThemeColors.BG_INPUT}; 
            color: {ThemeColors.TEXT_DISABLED}; 
            border-left: 1px solid {ThemeColors.BORDER_DEFAULT};
            font-size: 2px;
        """)

        if hasattr(self.main_editor, 'font'):
            font = QFont(self.main_editor.font().family())
            font.setPixelSize(2) 
            self.setFont(font)
            
        if hasattr(self.main_editor, 'toPlainText'):
            self.setPlainText(self.main_editor.toPlainText())
        
        self.sync_timer = QTimer(self)
        self.sync_timer.setSingleShot(True)
        self.sync_timer.timeout.connect(self._sync_text_action)
        
        self._is_dragging = False

        if hasattr(self.main_editor, 'textChanged'):
            self.main_editor.textChanged.connect(self._sync_text)
        if hasattr(self.main_editor, 'verticalScrollBar'):
            self.main_editor.verticalScrollBar().valueChanged.connect(self._sync_scroll)
        if hasattr(self.main_editor, 'updateRequest'):
            self.main_editor.updateRequest.connect(self._update_highlight)

    def _sync_text(self):
        self.sync_timer.start(500)

    def _sync_text_action(self):
        v_val = self.verticalScrollBar().value()
        h_val = self.horizontalScrollBar().value()
        self.setPlainText(self.main_editor.toPlainText())
        self.verticalScrollBar().setValue(v_val)
        self.horizontalScrollBar().setValue(h_val)

    def _sync_scroll(self, value=None):
        main_bar = self.main_editor.verticalScrollBar()
        mini_bar = self.verticalScrollBar()
        if main_bar.maximum() > 0:
            ratio = main_bar.value() / main_bar.maximum()
            mini_bar.setValue(int(ratio * mini_bar.maximum()))
        self.viewport().update()

    def _update_highlight(self, rect, dy):
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not hasattr(self.main_editor, 'firstVisibleBlock'):
            return
            
        painter = QPainter(self.viewport())
        first_visible = self.main_editor.firstVisibleBlock()
        top_block_num = first_visible.blockNumber()
        
        mini_top_block = self.document().findBlockByNumber(top_block_num)
        mini_top_y = int(self.blockBoundingGeometry(mini_top_block).translated(self.contentOffset()).top())
        
        lines_visible = self.main_editor.viewport().height() / max(1, self.main_editor.fontMetrics().lineSpacing())
        mini_height = int(lines_visible * self.fontMetrics().lineSpacing())
        if mini_height < 15: mini_height = 15 
        
        highlight_rect = QRect(0, mini_top_y, self.width(), mini_height)
        
        highlight_color = QColor(ThemeColors.ACCENT_BLUE)
        highlight_color.setAlpha(40)
        painter.fillRect(highlight_rect, highlight_color) 

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._scroll_to_mouse(event.pos().y())

    def mouseMoveEvent(self, event):
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            self._scroll_to_mouse(event.pos().y())
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False

    def _scroll_to_mouse(self, y):
        cursor = self.cursorForPosition(QPoint(0, int(y)))
        main_bar = self.main_editor.verticalScrollBar()
        total_blocks = max(1, self.document().blockCount())
        ratio = cursor.blockNumber() / total_blocks
        main_bar.setValue(int(ratio * main_bar.maximum()))


class EditorTab(QWidget):
    saved = Signal(str)

    def __init__(self, file_path: str, version_mgr, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.version_mgr = version_mgr
        self.is_modified = False
        self.find_bar = None
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.editor = CodeEditor()
        self.editor.file_path = file_path 
        
        self.minimap = MinimapEditor(self.editor)
        
        main_layout.addWidget(self.editor, stretch=1)
        main_layout.addWidget(self.minimap)
        
        if hasattr(self.editor, 'textChanged'):
            self.editor.textChanged.connect(self._on_text_changed)
            
        self._load_content()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.find_bar and self.find_bar.isVisible():
            if not getattr(self.find_bar, 'user_moved', False):
                self._position_find_bar()

    def _position_find_bar(self):
        if self.find_bar:
            padding_top = 10
            padding_right = self.minimap.width() + 30 
            x = self.width() - self.find_bar.width() - padding_right
            self.find_bar.move(x, padding_top)
            self.find_bar.raise_()

    def _apply_highlighter(self):
        try:
            from .syntax_highlighter import get_highlighter_for_file
            highlighter_class = get_highlighter_for_file(self.file_path)
            
            if hasattr(self, '_highlighter') and self._highlighter:
                self._highlighter.deleteLater()
            if hasattr(self, '_mini_highlighter') and self._mini_highlighter:
                self._mini_highlighter.deleteLater()
                
            if highlighter_class:
                self._highlighter = highlighter_class(self.editor.document())
                self._mini_highlighter = highlighter_class(self.minimap.document())
            else:
                self._highlighter = None
                self._mini_highlighter = None
        except Exception:
            pass 

    def _load_content(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if hasattr(self.editor, 'setPlainText'):
                self.editor.setPlainText(content)
            elif hasattr(self.editor, 'setText'):
                self.editor.setText(content)
                
            self.is_modified = False
            self._apply_highlighter()
            
            if not self.version_mgr.get_versions(self.file_path):
                self.version_mgr.save_version(self.file_path, content)
        except Exception as e:
            pass 

    def reload_content_if_changed(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                disk_content = f.read()
                
            current_text = ""
            if hasattr(self.editor, 'toPlainText'):
                current_text = self.editor.toPlainText()
            
            if current_text != disk_content:
                self.editor.blockSignals(True)
                if hasattr(self.editor, 'setPlainText'):
                    self.editor.setPlainText(disk_content)
                self.editor.blockSignals(False)
                
                self.is_modified = False
                self._update_tab_title()
        except Exception:
            pass

    def _update_tab_title(self):
        parent_tab = self.parent()
        if parent_tab and hasattr(parent_tab, 'setTabText'):
            idx = parent_tab.indexOf(self)
            if idx >= 0:
                base = os.path.basename(self.file_path)
                mark = " *" if self.is_modified else ""
                parent_tab.setTabText(idx, base + mark)

    def save_content(self):
        try:
            new_content = ""
            if hasattr(self.editor, 'toPlainText'):
                new_content = self.editor.toPlainText()
            
            old_content = ""
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    old_content = f.read()
            
            if new_content != old_content:
                dialog = DiffDialog(self.file_path, old_content, new_content, self)
                if dialog.exec() != DiffDialog.DialogCode.Accepted:
                    return False
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.is_modified = False
            self._update_tab_title()
            
            self.version_mgr.save_version(self.file_path, new_content)
            self.saved.emit(self.file_path)
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return False

    def _on_text_changed(self):
        if not self.is_modified:
            self.is_modified = True
            self._update_tab_title()