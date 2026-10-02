# -*- coding: utf-8 -*-
# codesaver/core/project_manager.py
import os
import shutil
import zipfile
import json
from PySide6.QtCore import QObject, Signal, QTimer, QFileSystemWatcher
from PySide6.QtWidgets import QInputDialog, QMessageBox

class ProjectManager(QObject):
    project_changed = Signal(str)
    tree_refresh_needed = Signal()
    directory_changed_signal = Signal(str)

    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.project_root = None
        self.hidden_folders = set()
        self.auto_hide_folders = {'node_modules', '.git', '__pycache__', 'venv', 'env', 'dist', 'build', '.idea', '.vscode'}
        
        self.file_watcher = QFileSystemWatcher(self)
        self.file_watcher.directoryChanged.connect(self._on_directory_changed)
        
        self._watcher_timer = QTimer(self)
        self._watcher_timer.setSingleShot(True)
        self._watcher_timer.timeout.connect(self._process_directory_changes)
        self._changed_directories = set()

    def set_project_root(self, path):
        if self.file_watcher.directories():
            self.file_watcher.removePaths(self.file_watcher.directories())
        
        self.project_root = path
        self.mw.project_root = path
        
        if not self.hidden_folders:
            for hide_name in self.auto_hide_folders:
                hide_path = os.path.join(self.project_root, hide_name)
                if os.path.isdir(hide_path):
                    self.hidden_folders.add(hide_path)
        
        self.file_watcher.addPath(self.project_root)
        self.project_changed.emit(path)
        self.tree_refresh_needed.emit()

    def _on_directory_changed(self, path):
        self._changed_directories.add(path)
        self._watcher_timer.start(500)

    def _process_directory_changes(self):
        for path in self._changed_directories:
            self.directory_changed_signal.emit(path)
        self._changed_directories.clear()

    def create_new_file(self):
        if not self.project_root: return
        name, ok = QInputDialog.getText(self.mw, "New File", "Enter file name (relative to project root):")
        if not ok or not name.strip(): return
        abs_path = os.path.join(self.project_root, name.strip())
        
        # 🚀 FIX: Protected file creation block
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write("")
            self.tree_refresh_needed.emit()
        except PermissionError as e:
            QMessageBox.warning(self.mw, "Access Error", f"Access is denied. Could not create file:\n{str(e)}")
        except Exception as e:
            QMessageBox.warning(self.mw, "Error", f"Failed to create file:\n{str(e)}")

    def create_new_folder(self):
        if not self.project_root: return
        name, ok = QInputDialog.getText(self.mw, "New Folder", "Enter folder name (relative):")
        if not ok or not name.strip(): return
        abs_path = os.path.join(self.project_root, name.strip())
        os.makedirs(abs_path, exist_ok=True)
        self.tree_refresh_needed.emit()

    def delete_selected(self, path):
        if not path: return
        reply = QMessageBox.question(self.mw, "Confirm Delete", f"Are you sure you want to delete?\n{os.path.basename(path)}", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.tree_refresh_needed.emit()

    def rename_selected(self, path):
        if not path: return
        new_name, ok = QInputDialog.getText(self.mw, "Rename", "New name:", text=os.path.basename(path))
        if ok and new_name.strip():
            os.rename(path, os.path.join(os.path.dirname(path), new_name.strip()))
            self.tree_refresh_needed.emit()

    def export_workspace(self, zip_path, open_tabs_paths):
        if not self.project_root:
            return False, "No project is open."

        rel_tabs = []
        for abs_path in open_tabs_paths:
            try:
                rel_tabs.append(os.path.relpath(abs_path, self.project_root))
            except Exception:
                pass

        workspace_data = {
            "project_root_name": os.path.basename(self.project_root),
            "hidden_folders": list(self.hidden_folders),
            "open_tabs": rel_tabs
        }

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("meta.json", json.dumps(workspace_data, indent=4))
                for root, dirs, files in os.walk(self.project_root):
                    if ".codesaver" in root.split(os.sep) or "__pycache__" in root.split(os.sep):
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.abspath(file_path) == os.path.abspath(zip_path):
                            continue
                        arcname = os.path.relpath(file_path, self.project_root)
                        zipf.write(file_path, arcname)
            return True, f"Project successfully saved to file {os.path.basename(zip_path)}."
        except Exception as e:
            return False, f"Error saving project:\n{str(e)}"

    def extract_workspace(self, zip_path, dest_folder):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(dest_folder)
            
            meta_path = os.path.join(dest_folder, "meta.json")
            meta_data = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                self.hidden_folders = set(meta_data.get("hidden_folders", []))
            
            return True, meta_data
        except Exception as e:
            return False, f"Error loading project:\n{str(e)}"

    def get_tree_structure(self, max_depth=3):
        if not self.project_root:
            return "No project is open."
            
        tree_out = []
        project_name = os.path.basename(self.project_root)
        tree_out.append(f"{project_name}/")
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.auto_hide_folders and os.path.join(root, d) not in self.hidden_folders]
            
            level = root.replace(self.project_root, '').count(os.sep)
            if level > max_depth:
                del dirs[:]
                continue
                
            indent = '    ' * level
            for f in files:
                tree_out.append(f"{indent}├── {f}")
            for d in dirs:
                tree_out.append(f"{indent}├── {d}/")
                
        return '\n'.join(tree_out)