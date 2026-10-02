# -*- coding: utf-8 -*-
# codesaver/widgets/project_exporter.py
import os
import re
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox, 
    QProgressBar, QCheckBox, QGroupBox
)

from ..core.theme_manager import ThemeColors
from .export_worker import ExportWorker  # 🚀 جادوی ماژولار شدن!

class ProjectExporter(QMainWindow):
    def __init__(self, parent=None, default_root=None, hidden_folders=None):
        super().__init__(parent)
        self.setWindowTitle("Project Export")
        self.setMinimumSize(900, 600)
        
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {ThemeColors.BG_BASE}; }}
            QWidget {{ color: {ThemeColors.TEXT_MAIN}; }}
            QGroupBox {{ 
                border: 1px solid {ThemeColors.BORDER_DEFAULT}; 
                border-radius: 6px; 
                margin-top: 10px; 
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
        """)
        
        self.default_root = default_root
        self.hidden_folders = hidden_folders if hidden_folders is not None else set()
        self.root_path = default_root

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        group = QGroupBox("Select Export Formats")
        check_layout = QHBoxLayout()
        self.chk_json = QCheckBox(".json"); self.chk_json.setChecked(True)
        self.chk_pdf = QCheckBox(".pdf"); self.chk_pdf.setChecked(True)
        self.chk_txt = QCheckBox(".txt"); self.chk_txt.setChecked(True)
        check_layout.addWidget(self.chk_json)
        check_layout.addWidget(self.chk_pdf)
        check_layout.addWidget(self.chk_txt)
        group.setLayout(check_layout)
        main_layout.addWidget(group)

        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("Open Folder")
        self.btn_export = QPushButton("Start Export")
        self.btn_restore = QPushButton("Restore from TXT")
        self.btn_export.setEnabled(False)

        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Project files (check to include in export)")
        self.tree.setAlternatingRowColors(True)
        
        self.tree.setStyleSheet(f"""
            QTreeView {{ 
                alternate-background-color: {ThemeColors.BG_INPUT}; 
                background-color: {ThemeColors.BG_PANEL};
                border: 1px solid {ThemeColors.BORDER_DEFAULT};
                border-radius: 6px;
                outline: none;
            }} 
            QTreeView::item:selected {{ 
                background-color: {ThemeColors.ACCENT_BLUE}; 
                color: #ffffff; 
            }}
        """)
        
        main_layout.addWidget(self.tree)

        self.btn_open.clicked.connect(self.open_folder)
        self.btn_export.clicked.connect(self.export_files)
        self.btn_restore.clicked.connect(self.restore_from_text)

        self._updating_checks = False
        self.tree.itemChanged.connect(self.on_item_changed)

        if self.default_root and os.path.isdir(self.default_root):
            self.populate_tree(self.default_root)
            self.btn_export.setEnabled(True)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select project folder")
        if not folder:
            return
        self.root_path = folder
        self.populate_tree(folder)
        self.btn_export.setEnabled(True)

    def populate_tree(self, root_path):
        self.tree.blockSignals(True)
        self.tree.clear()

        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, os.path.basename(root_path))
        root_item.setData(0, Qt.UserRole, root_path)
        root_item.setCheckState(0, Qt.Checked)
        self._add_children(root_item, root_path)

        self.tree.expandAll()
        self.tree.blockSignals(False)

    def _add_children(self, parent_item, parent_path):
        try:
            entries = sorted(os.listdir(parent_path))
        except PermissionError:
            return
        for name in entries:
            full = os.path.join(parent_path, name)
            if full in self.hidden_folders:
                continue
            
            child = QTreeWidgetItem(parent_item)
            child.setText(0, name)
            child.setData(0, Qt.UserRole, full)
            if os.path.isdir(full):
                self._add_children(child, full)
                child.setCheckState(0, Qt.Checked)
            else:
                child.setCheckState(0, Qt.Checked)

    def on_item_changed(self, item, column):
        if column != 0 or self._updating_checks:
            return
        self._updating_checks = True
        state = item.checkState(0)
        self._set_children_check(item, state)
        self._updating_checks = False

    def _set_children_check(self, parent, state):
        for i in range(parent.childCount()):
            child = parent.child(i)
            child.setCheckState(0, state)
            if child.childCount() > 0:
                self._set_children_check(child, state)

    def get_checked_files(self):
        checked = []
        def recurse(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.childCount() == 0:
                    if child.checkState(0) == Qt.Checked:
                        path = child.data(0, Qt.UserRole)
                        if path and os.path.isfile(path):
                            checked.append(path)
                else:
                    recurse(child)
        recurse(self.tree.invisibleRootItem())
        return checked

    def build_tree_diagram(self):
        if not self.root_path:
            return ""
        root_item = self.tree.topLevelItem(0)
        if not root_item or root_item.checkState(0) != Qt.Checked:
            return ""
            
        lines = []
        lines.append(root_item.text(0))
        self._tree_diagram_from_item(root_item, "", lines)
        return "\n".join(lines)

    def _tree_diagram_from_item(self, parent_item, prefix, lines):
        valid_children = []
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.checkState(0) == Qt.Checked:
                valid_children.append(child)
                
        child_count = len(valid_children)
        for idx, child in enumerate(valid_children):
            is_last = (idx == child_count - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{child.text(0)}")
            
            if child.childCount() > 0:
                extension = "    " if is_last else "│   "
                self._tree_diagram_from_item(child, prefix + extension, lines)

    def export_files(self):
        checked_files = self.get_checked_files()
        if not checked_files:
            QMessageBox.warning(self, "No files", "No files are selected for export.")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "Select output folder")
        if not dest_dir:
            return

        formats = {
            'json': self.chk_json.isChecked(),
            'pdf': self.chk_pdf.isChecked(),
            'txt': self.chk_txt.isChecked()
        }

        if not any(formats.values()):
            QMessageBox.warning(self, "Warning", "Please select at least one export format.")
            return

        tree_diagram = self.build_tree_diagram()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_export.setEnabled(False)

        self.worker = ExportWorker(dest_dir, tree_diagram, checked_files, self.root_path, formats)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_export_finished)
        self.worker.start()

    def on_export_finished(self, error):
        self.progress_bar.setVisible(False)
        self.btn_export.setEnabled(True)
        if error:
            QMessageBox.critical(self, "Error", f"Export failed:\n{error}")
        else:
            QMessageBox.information(self, "Success", "Export completed successfully.")

    def restore_from_text(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open exported TXT file", "", "Text files (*.txt);;All files (*)")
        if not file_path:
            return

        dest_folder = QFileDialog.getExistingDirectory(self, "Select destination folder to restore project")
        if not dest_folder:
            return

        reply = QMessageBox.question(
            self, "Confirm Restore",
            f"This will create/overwrite files and folders inside:\n{dest_folder}\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot read file:\n{e}")
            return

        pattern = r"----- CODE_SAVER_FILE_START: (.+?) -----\n(.*?)----- CODE_SAVER_FILE_END: \1 -----"
        matches = re.findall(pattern, content, re.DOTALL)
        if not matches:
            QMessageBox.warning(self, "Format Error", "No valid file sections found.")
            return

        restored_count = 0
        for rel_path, file_content in matches:
            abs_dest_path = os.path.join(dest_folder, rel_path.strip())
            dir_name = os.path.dirname(abs_dest_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            try:
                with open(abs_dest_path, "w", encoding="utf-8") as out:
                    out.write(file_content.rstrip())
                    if not file_content.endswith("\n"):
                        out.write("\n")
                restored_count += 1
            except Exception as e:
                QMessageBox.warning(self, "Write Error", f"Could not write {abs_dest_path}\n{e}")

        QMessageBox.information(self, "Restore Complete", f"Restored {restored_count} file(s) to:\n{dest_folder}")