# -*- coding: utf-8 -*-
# codesaver/widgets/actions/action_mixin.py
import sys
import os
import webbrowser
from PySide6.QtWidgets import QMessageBox, QInputDialog, QDialog, QVBoxLayout, QPlainTextEdit
from PySide6.QtGui import QTextCursor, QFont

# 🚀 FIX: مسیر اصلاح‌شده برای دسترسی به هسته از داخل پوشه‌ی actions
from ...core.theme_manager import ThemeColors

class EditorActionsMixin:
    """
    این کلاس شامل تمام اکشن‌های فرعی، دیالوگ‌ها و جستجوهاست.
    با ارث‌بریِ MainWindow از این کلاس، فایل main.py به شدت خلوت و خوانا می‌شود.
    """

    def _delete_selected(self):
        if p := self.tree.get_selected_path(): self.project_mgr.delete_selected(p)

    def _rename_selected(self):
        if p := self.tree.get_selected_path(): self.project_mgr.rename_selected(p)

    def _save_current_file(self):
        self.tab_mgr.save_current_file()

    def _format_current_file(self):
        if self.current_editor_tab and hasattr(self.current_editor_tab, 'editor'):
            self.current_editor_tab.editor.auto_format()
            self.status_label.setText("Document successfully formatted.")

    def load_from_address_bar(self):
        if (rel_path := self.address_bar.text().strip()) and self.project_root:
            if os.path.isfile(abs_path := os.path.join(self.project_root, rel_path)): 
                self.tab_mgr.open_file_in_tab(abs_path)

    def _on_file_saved(self, file_path):
        self.project_mgr.tree_refresh_needed.emit()
        self.history_dock.load_versions(self.version_mgr.get_versions(file_path))
        self.status_label.setText(f"Saved: {os.path.basename(file_path)}")

    def _update_editor_status(self, line, col, total_lines, words, chars):
        self.status_label.setText(f"Ln {line}, Col {col} | {total_lines} Lines")

    def _show_global_search(self):
        if not self.project_root:
            QMessageBox.warning(self, "No Project", "Please open a project first.")
            return
        self.global_search_overlay.set_project_root(self.project_root)
        self.global_search_overlay.setVisible(True)
        self.global_search_overlay.search_edit.setFocus()
        self.global_search_overlay.search_edit.selectAll()

    def _on_global_search_result(self, file_path, search_term):
        self.tab_mgr.open_file_in_tab(file_path)
        cs = self.global_search_overlay.btn_case.isChecked()
        if self.current_editor_tab:
            self._update_global_find_count(search_term, cs)
            self.current_editor_tab.editor.find_text(search_term, cs, False)
            self.current_editor_tab.editor.setFocus()

    def _on_global_find_action(self, text, cs, backward):
        if self.current_editor_tab:
            self.current_editor_tab.editor.find_text(text, cs, backward)
            self._update_global_find_count(text, cs)

    def _on_global_replace_current(self, find_text, rep_text, cs):
        if self.current_editor_tab: self.current_editor_tab.editor.replace_current(find_text, rep_text, cs)

    def _on_global_replace_all(self, find_text, rep_text, cs):
        if self.current_editor_tab: self.current_editor_tab.editor.replace_all(find_text, rep_text, cs)

    def _update_global_find_count(self, text, case_sensitive):
        if self.current_editor_tab:
            c = self.current_editor_tab.editor.update_search_highlights(text, case_sensitive)
            self.global_search_overlay.count_label.setText(f"{c} results" if text else "0 results")

    def _show_find_bar(self):
        if not self.current_editor_tab: return
        if not getattr(self.current_editor_tab, 'find_bar', None):
            # 🚀 FIX: مسیر اصلاح‌شده برای ویجت‌ها
            from ..find_replace_bar import FindReplaceBar
            bar = FindReplaceBar(self.current_editor_tab)
            bar.find_next.connect(lambda t, cs: self._on_find_action(t, cs, False))
            bar.find_prev.connect(lambda t, cs: self._on_find_action(t, cs, True))
            bar.replace_current.connect(self.current_editor_tab.editor.replace_current)
            bar.replace_all.connect(self.current_editor_tab.editor.replace_all)
            bar.closed.connect(lambda: self.current_editor_tab.editor.update_search_highlights(""))
            bar.search_updated.connect(self._update_find_count)
            self.current_editor_tab.find_bar = bar

        self.current_editor_tab.find_bar.setVisible(True)
        self.current_editor_tab.find_bar.adjustSize()
        if not getattr(self.current_editor_tab.find_bar, 'user_moved', False):
            self.current_editor_tab._position_find_bar()
        self.current_editor_tab.find_bar.find_edit.setFocus()
        self.current_editor_tab.find_bar.find_edit.selectAll()

    def _on_find_action(self, text, cs, backward):
        if self.current_editor_tab:
            self.current_editor_tab.editor.find_text(text, cs, backward)
            self._update_find_count(text, cs)

    def _update_find_count(self, text, case_sensitive):
        if self.current_editor_tab:
            c = self.current_editor_tab.editor.update_search_highlights(text, case_sensitive)
            self.current_editor_tab.find_bar.count_label.setText(f"{c} results" if text else "No results")

    def _show_symbol_palette(self):
        if self.current_editor_tab:
            self.symbol_palette.load_symbols_from_text(self.current_editor_tab.editor.toPlainText())
            self.symbol_palette.setVisible(True)
            self.symbol_palette.search_edit.setFocus()

    def _on_symbol_selected(self, line_number):
        if self.current_editor_tab:
            cursor = self.current_editor_tab.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_number - 1)
            self.current_editor_tab.editor.setTextCursor(cursor)
            self.current_editor_tab.editor.ensureCursorVisible()
            self.current_editor_tab.editor.setFocus()

    def _restore_version(self, file_path, timestamp):
        if (content := self.version_mgr.load_version(file_path, timestamp)) is not None:
            if file_path in self.open_tabs:
                idx = self.open_tabs[file_path]
                tab = self.editor_tab_widget.widget(idx)
                tab.editor.setPlainText(content)
                tab.is_modified = True
                self.editor_tab_widget.setTabText(idx, os.path.basename(file_path) + " *")
                self.status_label.setText(f"Restored version: {timestamp.strftime('%H:%M:%S')}")

    def _create_restore_point(self):
        if not self.project_root: return
        name, ok = QInputDialog.getText(self, "Create Restore Point", "Enter name:")
        if ok and name.strip():
            self.restore_mgr.create_restore_point(name.strip())
            QMessageBox.information(self, "Success", "Restore point created.")

    def _restore_from_restore_point(self):
        if not self.project_root or not (points := self.restore_mgr.list_restore_points()): return
        items = [f"{name} ({ts})" for name, ts in points]
        selected, ok = QInputDialog.getItem(self, "Select Restore Point", "Choose:", items, 0, False)
        if ok and selected:
            self.restore_mgr.restore_restore_point(points[items.index(selected)][0])
            self._load_project_env(self.project_root)

    def _open_terminal(self):
        self.right_tabs.setCurrentWidget(self.terminal)
        self.terminal.start_shell()

    def _on_terminal_tab_clicked(self, idx):
        if self.right_tabs.widget(idx) == self.terminal: self.terminal.start_shell()

    def _open_export_window(self):
        # 🚀 FIX: مسیر اصلاح‌شده
        from ..project_exporter import ProjectExporter
        self.export_window = ProjectExporter(self, default_root=self.project_root, hidden_folders=self.project_mgr.hidden_folders)
        self.export_window.show()

    def _open_preferences(self):
        # 🚀 FIX: مسیر اصلاح‌شده
        from ..preferences_dialog import PreferencesDialog
        if PreferencesDialog(self.config_mgr, self).exec():
            self.project_mgr.hidden_folders = set(self.config_mgr.hidden_folders)
            self.tree.refresh_tree()
            new_font = QFont(self.config_mgr.font_family, self.config_mgr.font_size)
            for i in range(self.editor_tab_widget.count()):
                if hasattr(tab := self.editor_tab_widget.widget(i), 'editor'): tab.editor.setFont(new_font)
            self._save_config()
            self.ui_builder.apply_base_dark_theme()

    def _show_all_hidden_folders(self):
        self.project_mgr.hidden_folders.clear()
        self.tree.refresh_tree()
        self._save_config()

    def _cut(self): 
        if hasattr(w := self.focusWidget(), 'cut'): w.cut()
    def _copy(self): 
        if hasattr(w := self.focusWidget(), 'copy'): w.copy()
    def _paste(self): 
        if hasattr(w := self.focusWidget(), 'paste'): w.paste()
    def _undo_project(self): pass
    def _redo_project(self): pass

    def _show_help(self):
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        help_path = os.path.join(base_path, "docs", "index.html")
        if os.path.exists(help_path): webbrowser.open(f"file:///{help_path.replace(os.sep, '/')}")
        else: QMessageBox.warning(self, "Error", f"Help file not found!\n{help_path}")

    def _show_error_logs(self):
        log_path = os.path.join(os.path.expanduser("~"), "codesaver_system.log")
        if os.path.exists(log_path):
            dlg = QDialog(self)
            dlg.setWindowTitle("System Logs")
            dlg.resize(800, 600)
            layout = QVBoxLayout(dlg)
            te = QPlainTextEdit()
            te.setReadOnly(True)
            te.setStyleSheet(f"background: {ThemeColors.BG_INPUT}; color: {ThemeColors.TEXT_MUTED}; font-family: Consolas;")
            with open(log_path, "r", encoding="utf-8") as f: te.setPlainText(f.read())
            c = te.textCursor()
            c.movePosition(QTextCursor.MoveOperation.End)
            te.setTextCursor(c)
            layout.addWidget(te)
            dlg.exec()
        else:
            QMessageBox.information(self, "Logs", "No system logs found.")

    def show_diff_dialog(self, file_path, old_content, new_code):
        # 🚀 FIX: مسیر اصلاح‌شده
        from ..diff_dialog import DiffDialog
        from PySide6.QtWidgets import QDialog
        
        dialog = DiffDialog(file_path, old_content, new_code, self)
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted