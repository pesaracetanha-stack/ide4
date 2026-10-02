# -*- coding: utf-8 -*-
# codesaver/widgets/shortcuts_reference.py
import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget,
                               QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton,
                               QMessageBox, QFormLayout, QLabel, QWidget, QCheckBox, 
                               QRadioButton, QComboBox, QGridLayout)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QColor, QFont, QKeySequence

from ..core.theme_manager import ThemeColors

class ShortcutBuilderWidget(QWidget):
    def __init__(self, current_shortcut="", parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.set_shortcut(current_shortcut)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        mod_layout = QHBoxLayout()
        self.chk_ctrl = QCheckBox("Ctrl")
        self.chk_shift = QCheckBox("Shift")
        self.chk_alt = QCheckBox("Alt")
        
        mod_layout.addWidget(self.chk_ctrl)
        mod_layout.addWidget(self.chk_shift)
        mod_layout.addWidget(self.chk_alt)
        mod_layout.addStretch()
        layout.addLayout(mod_layout)

        key_layout = QGridLayout()
        key_layout.setSpacing(10)

        self.radio_letter = QRadioButton("Letter / Number:")
        self.txt_letter = QLineEdit()
        self.txt_letter.setMaxLength(1)
        self.txt_letter.setPlaceholderText("e.g. N")
        self.txt_letter.textChanged.connect(lambda t: self.txt_letter.setText(t.upper()))

        self.radio_fkey = QRadioButton("Function / Special:")
        self.cmb_fkey = QComboBox()
        
        special_keys = [f"F{i}" for i in range(1, 13)] + [
            "Esc", "Tab", "Space", "Return", "Enter", "Del", "Ins",
            "Home", "End", "PgUp", "PgDown", "Up", "Down", "Left", "Right",
            "~", "`", "-", "=", "[", "]", "\\", ";", "'", ",", ".", "/"
        ]
        self.cmb_fkey.addItems(special_keys)

        key_layout.addWidget(self.radio_letter, 0, 0)
        key_layout.addWidget(self.txt_letter, 0, 1)
        key_layout.addWidget(self.radio_fkey, 1, 0)
        key_layout.addWidget(self.cmb_fkey, 1, 1)

        layout.addLayout(key_layout)

        self.radio_letter.toggled.connect(self._toggle_inputs)
        self.radio_letter.setChecked(True)

    def _toggle_inputs(self):
        is_letter = self.radio_letter.isChecked()
        self.txt_letter.setEnabled(is_letter)
        self.cmb_fkey.setEnabled(not is_letter)
        if is_letter:
            self.txt_letter.setFocus()

    def get_shortcut(self):
        parts = []
        if self.chk_ctrl.isChecked(): parts.append("Ctrl")
        if self.chk_shift.isChecked(): parts.append("Shift")
        if self.chk_alt.isChecked(): parts.append("Alt")

        if self.radio_letter.isChecked():
            key = self.txt_letter.text().strip().upper()
            if not key:
                return ""
            parts.append(key)
        else:
            parts.append(self.cmb_fkey.currentText())

        return "+".join(parts)

    def set_shortcut(self, shortcut):
        if not shortcut or shortcut == "---":
            self.chk_ctrl.setChecked(False)
            self.chk_shift.setChecked(False)
            self.chk_alt.setChecked(False)
            self.radio_letter.setChecked(True)
            self.txt_letter.setText("")
            return

        parts = [p.strip() for p in shortcut.split("+")]
        
        self.chk_ctrl.setChecked("Ctrl" in parts)
        self.chk_shift.setChecked("Shift" in parts)
        self.chk_alt.setChecked("Alt" in parts)

        main_key = parts[-1] if parts else ""
        f_keys = [self.cmb_fkey.itemText(i) for i in range(self.cmb_fkey.count())]

        if main_key in f_keys:
            self.radio_fkey.setChecked(True)
            self.cmb_fkey.setCurrentText(main_key)
        else:
            self.radio_letter.setChecked(True)
            self.txt_letter.setText(main_key)

class ShortcutEditDialog(QDialog):
    def __init__(self, command_name, current_shortcut, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Shortcut")
        self.resize(400, 250)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        lbl_info = QLabel(f"Set new shortcut for:<br><b style='color:{ThemeColors.ACCENT_BLUE}; font-size:16px;'>{command_name}</b>")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)
        
        self.builder = ShortcutBuilderWidget(current_shortcut, self)
        layout.addWidget(self.builder)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_shortcut(self):
        return self.builder.get_shortcut()


class ShortcutAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Shortcut")
        self.resize(450, 280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("e.g., Run My Script")
        form_layout.addRow("Command Name:", self.cmd_input)
        layout.addLayout(form_layout)
        
        lbl_divider = QLabel("Shortcut Keys:")
        lbl_divider.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_divider)
        
        self.builder = ShortcutBuilderWidget("", self)
        layout.addWidget(self.builder)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Add Shortcut")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_data(self):
        return self.cmd_input.text().strip(), self.builder.get_shortcut()


class ShortcutsReferenceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts Manager")
        self.resize(650, 650)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.shortcut_settings = QSettings("GitiArts", "CodeSaver_Shortcuts")
        self.row_keys = {}

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search command or shortcut...")
        self.search_box.textChanged.connect(self.filter_table)
        layout.addWidget(self.search_box)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Command", "Shortcut"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.itemDoubleClicked.connect(self.edit_shortcut)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Custom")
        self.btn_edit = QPushButton("✏️ Edit Selected")
        self.btn_delete = QPushButton("🗑️ Clear / Delete")
        self.btn_reset = QPushButton("🔄 Reset to Defaults")
        
        self.btn_add.clicked.connect(self.add_shortcut)
        self.btn_edit.clicked.connect(self.edit_shortcut)
        self.btn_delete.clicked.connect(self.delete_shortcut)
        self.btn_reset.clicked.connect(self.reset_shortcuts)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_reset)
        layout.addLayout(btn_layout)

    def load_data(self):
        self.table.setRowCount(0)
        self.row_keys.clear()

        self.shortcuts_data = {
            "shortcut_new_project": ("New Project", "Ctrl+Alt+N"),
            "shortcut_new_file": ("New File", "Ctrl+N"),
            "shortcut_new_folder": ("New Folder", "Ctrl+Shift+N"),
            "shortcut_open_folder": ("Open Folder", "Ctrl+Shift+D"),
            "shortcut_open_workspace": ("Open Workspace", "Ctrl+O"),
            "shortcut_save_file": ("Save File", "Ctrl+S"),
            "shortcut_save_project": ("Save Project", "Ctrl+Shift+S"),
            "shortcut_save_as": ("Save As", "Ctrl+Shift+Alt+S"),
            "shortcut_close_project": ("Close Project", ""),
            "shortcut_exit": ("Exit", "Ctrl+Q"),
            "shortcut_undo": ("Undo", "Ctrl+Z"),
            "shortcut_redo": ("Redo", "Ctrl+Y"),
            "shortcut_cut": ("Cut", "Ctrl+X"),
            "shortcut_copy": ("Copy", "Ctrl+C"),
            "shortcut_paste": ("Paste", "Ctrl+V"),
            "shortcut_delete": ("Delete", "Del"),
            "shortcut_rename": ("Rename", "F2"),
            "shortcut_find": ("Find in File", "Ctrl+F"),
            "shortcut_global_search": ("Global Search", "Ctrl+Shift+F"),
            "shortcut_symbol_search": ("Symbol Search", "Ctrl+Shift+O"),
            "shortcut_format": ("Format Code", "Shift+Alt+F"),
            "shortcut_command_palette": ("Command Palette", "Ctrl+Shift+P"),
            "shortcut_terminal": ("Open Terminal", "Ctrl+`"),
            "shortcut_run": ("Run Project", "F5"),
            "shortcut_ai_chat": ("AI Panel", "Ctrl+Shift+A"),
            "shortcut_docs": ("Documentation", "F1"),
            "shortcut_preferences": ("Preferences", "Ctrl+,")
        }

        row = 0
        for key, (label, default_val) in self.shortcuts_data.items():
            current_val = self.shortcut_settings.value(key, default_val)
            self._insert_row(row, key, label, current_val, is_custom=False)
            row += 1

        customs_json = self.shortcut_settings.value("custom_shortcuts_dict", "{}")
        try:
            self.custom_shortcuts = json.loads(customs_json)
        except Exception:
            self.custom_shortcuts = {}
            
        for label, val in self.custom_shortcuts.items():
            self._insert_row(row, label, label, val, is_custom=True)
            row += 1

    def _insert_row(self, row, key, label, val, is_custom):
        if not val: val = "---"
        self.table.insertRow(row)
        self.row_keys[row] = {"key": key, "is_custom": is_custom}

        display_label = f"{label} (Custom)" if is_custom else label
        item_lbl = QTableWidgetItem(display_label)
        item_val = QTableWidgetItem(val)

        font = QFont("Consolas", 11, QFont.Weight.Bold)
        item_val.setForeground(QColor(ThemeColors.SUCCESS))
        item_val.setFont(font)
        item_val.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table.setItem(row, 0, item_lbl)
        self.table.setItem(row, 1, item_val)

    def filter_table(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            lbl = self.table.item(row, 0).text().lower()
            val = self.table.item(row, 1).text().lower()
            if text in lbl or text in val:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def add_shortcut(self):
        dlg = ShortcutAddDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            cmd, seq = dlg.get_data()
            if not cmd:
                QMessageBox.warning(self, "Error", "Command name cannot be empty.")
                return
            if not seq:
                QMessageBox.warning(self, "Error", "Shortcut sequence cannot be empty.")
                return
            
            self.custom_shortcuts[cmd] = seq
            self.shortcut_settings.setValue("custom_shortcuts_dict", json.dumps(self.custom_shortcuts))
            self.load_data()
            self._notify_restart()

    def edit_shortcut(self):
        selected = self.table.currentRow()
        if selected < 0: return
        
        row_data = self.row_keys[selected]
        key = row_data["key"]
        is_custom = row_data["is_custom"]
        
        cmd_name = self.table.item(selected, 0).text().replace(" (Custom)", "")
        current_seq = self.table.item(selected, 1).text()
        
        dlg = ShortcutEditDialog(cmd_name, current_seq, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_seq = dlg.get_shortcut()
            if not new_seq:
                QMessageBox.warning(self, "Error", "Shortcut sequence cannot be empty.")
                return
            
            if is_custom:
                self.custom_shortcuts[key] = new_seq
                self.shortcut_settings.setValue("custom_shortcuts_dict", json.dumps(self.custom_shortcuts))
            else:
                self.shortcut_settings.setValue(key, new_seq)
                
            self.load_data()
            self.table.selectRow(selected)
            self._notify_restart()

    def delete_shortcut(self):
        selected = self.table.currentRow()
        if selected < 0: return
        
        row_data = self.row_keys[selected]
        key = row_data["key"]
        
        if row_data["is_custom"]:
            reply = QMessageBox.question(self, "Delete Custom Shortcut", "Are you sure you want to permanently delete this custom shortcut?")
            if reply == QMessageBox.StandardButton.Yes:
                self.custom_shortcuts.pop(key, None)
                self.shortcut_settings.setValue("custom_shortcuts_dict", json.dumps(self.custom_shortcuts))
                self.load_data()
        else:
            reply = QMessageBox.question(self, "Clear Shortcut", "Clear shortcut for this system command?")
            if reply == QMessageBox.StandardButton.Yes:
                self.shortcut_settings.setValue(key, "")
                self.load_data()
                self.table.selectRow(selected)
                self._notify_restart()

    def reset_shortcuts(self):
        reply = QMessageBox.question(self, "Reset All", "Are you sure you want to restore all shortcuts to their default values? (Custom shortcuts will NOT be deleted)", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for key in self.shortcuts_data.keys():
                self.shortcut_settings.remove(key)
            self.load_data()
            self._notify_restart()

    def _notify_restart(self):
        QMessageBox.information(self, "Restart Required", "To apply shortcut changes fully to the main interface, please restart the IDE.")