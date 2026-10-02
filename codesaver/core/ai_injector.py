# -*- coding: utf-8 -*-
# codesaver/core/ai_injector.py
import os
from PySide6.QtGui import QTextCursor

class AIInjector:
    """Manages smart AI code injection into the editor. (100% UI Independent)"""
    def __init__(self, main_window):
        self.mw = main_window
        self._last_inject_state = {}

        if hasattr(self.mw, 'chatbot_panel'):
            self.mw.chatbot_panel.inject_code_requested.connect(self.handle_inject)
            self.mw.chatbot_panel.revert_requested.connect(self.handle_revert)

    def _get_editor_tab(self, abs_path):
        if not hasattr(self.mw, 'open_tabs'): return None
        target = os.path.normcase(os.path.normpath(abs_path))
        for path, idx in self.mw.open_tabs.items():
            if os.path.normcase(os.path.normpath(path)) == target:
                return self.mw.editor_tab_widget.widget(idx)
        return None

    def handle_inject(self, file_path, new_code):
        if not os.path.isabs(file_path):
            if hasattr(self.mw, 'project_root') and self.mw.project_root:
                abs_path = os.path.join(self.mw.project_root, file_path)
            else:
                abs_path = os.path.abspath(file_path)
        else:
            abs_path = file_path

        old_content = ""
        is_open = False
        
        editor_tab = self._get_editor_tab(abs_path)
        if editor_tab:
            is_open = True
            if hasattr(editor_tab, 'editor') and hasattr(editor_tab.editor, 'toPlainText'):
                old_content = editor_tab.editor.toPlainText()
        else:
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        old_content = f.read()
                except Exception:
                    pass

        # --- ARCHITECTURE FIX: UI Delegation ---
        # به جای ایمپورت کردنِ دیالوگ، از لایه‌ی UI درخواست می‌کنیم آن را نمایش دهد
        approved = True
        if hasattr(self.mw, 'show_diff_dialog'):
            approved = self.mw.show_diff_dialog(abs_path, old_content, new_code)
            
        if not approved:
            if hasattr(self.mw, 'status_label'):
                self.mw.status_label.setText("Code injection canceled.")
            return
        # ----------------------------------------
            
        self._last_inject_state = {
            'file_path': abs_path,
            'old_content': old_content,
            'was_open': is_open
        }

        self._apply_code_to_editor(abs_path, new_code, editor_tab)

    def _apply_code_to_editor(self, abs_path, code, editor_tab=None):
        if not editor_tab:
            if not os.path.exists(abs_path):
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write("")
            
            if hasattr(self.mw, 'tab_mgr'):
                self.mw.tab_mgr.open_file_in_tab(abs_path)
                editor_tab = self._get_editor_tab(abs_path)

        if editor_tab and hasattr(editor_tab, 'editor'):
            cursor = editor_tab.editor.textCursor()
            cursor.beginEditBlock()
            
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(code)
            
            cursor.endEditBlock()
            
            editor_tab.is_modified = True
            if hasattr(editor_tab, '_update_tab_title'):
                editor_tab._update_tab_title()
            
            if hasattr(self.mw, 'status_label'):
                self.mw.status_label.setText(f"✨ Code successfully applied to {os.path.basename(abs_path)} (Press Ctrl+S to save).")

    def handle_revert(self):
        if not self._last_inject_state:
            if hasattr(self.mw, 'status_label'):
                self.mw.status_label.setText("⚠️ Error: No restore point found!")
            return

        abs_path = self._last_inject_state['file_path']
        old_content = self._last_inject_state['old_content']

        editor_tab = self._get_editor_tab(abs_path)
        self._apply_code_to_editor(abs_path, old_content, editor_tab)
        
        if hasattr(self.mw, 'status_label'):
            self.mw.status_label.setStyleSheet("color: #f38ba8;")
            self.mw.status_label.setText(f"↩️ Changes to {os.path.basename(abs_path)} reverted.")