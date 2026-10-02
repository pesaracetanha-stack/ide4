# -*- coding: utf-8 -*-
# codesaver/widgets/project_explorer.py
import os
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QFileIconProvider
from PySide6.QtCore import Qt, Signal, QSize, QFileInfo
from PySide6.QtGui import QBrush, QAction, QColor

from ..core.project_tree import ProjectTreeLoader, FileListLoader
from ..core.theme_manager import ThemeIcons, ThemeColors

_icon_provider = QFileIconProvider()

class ProjectExplorer(QTreeWidget):
    file_opened = Signal(str)          
    status_message = Signal(str)       

    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.project_mgr = self.mw.project_mgr
        self.git_mgr = self.mw.git_mgr
        self.config_mgr = self.mw.config_mgr
        
        self.active_loaders = set()
        
        self.setHeaderLabels(["Name"])
        self.setColumnWidth(0, 300)
        
        self.setIconSize(QSize(18, 18))
        self.setAlternatingRowColors(True)
        
        # 🚀 FIX 3: Injecting dynamic ThemeColors to override the default purple bands
        self.setStyleSheet(f"""
            QTreeView {{ 
                alternate-background-color: {ThemeColors.BG_INPUT}; 
                background-color: transparent;
                outline: none;
                border: none;
            }} 
            QTreeView::item:selected {{ 
                background-color: {ThemeColors.ACCENT_BLUE}; 
                color: #ffffff; 
            }}
            QTreeView::item:hover {{
                background-color: {ThemeColors.BORDER_DEFAULT};
            }}
        """)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemExpanded.connect(self._on_item_expanded)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def get_file_icon(self, ext, full_path):
        ext = str(ext).lower() if ext else ""
        if ext and not ext.startswith('.'):
            ext = '.' + ext
            
        icon_map = {
            '.py': 'icon_file_python.svg', '.pyw': 'icon_file_python.svg',
            '.js': 'icon_file_js.svg', '.ts': 'icon_file_js.svg', '.jsx': 'icon_file_js.svg', '.tsx': 'icon_file_js.svg', '.vue': 'icon_file_js.svg',
            '.html': 'icon_file_html.svg', '.htm': 'icon_file_html.svg',
            '.css': 'icon_file_css.svg',
            '.json': 'icon_file_json.svg',
            '.png': 'icon_file_image.svg', '.jpg': 'icon_file_image.svg', '.jpeg': 'icon_file_image.svg', '.svg': 'icon_file_image.svg', '.bmp': 'icon_file_image.svg', '.ico': 'icon_file_image.svg'
        }
        icon_name = icon_map.get(ext, 'icon_file_unknown.svg')
        
        custom_icon = ThemeIcons.get_icon(icon_name, ThemeColors.TEXT_MUTED)
        if custom_icon and not custom_icon.isNull():
            return custom_icon
        else:
            info = QFileInfo(full_path)
            return _icon_provider.icon(info)

    def show_empty_tree(self):
        self.clear()
        item = QTreeWidgetItem(self)
        item.setText(0, "No project loaded.\nClick 'File > Open Project Folder'.")
        item.setForeground(0, QBrush(QColor(ThemeColors.TEXT_MUTED)))

    def refresh_tree(self):
        if not self.project_mgr.project_root:
            self.show_empty_tree()
            return
            
        self.mw.git_mgr.update_git_status(self.project_mgr.project_root)
        
        self.clear()
        self.mw.path_to_item.clear()
        
        root_path = self.project_mgr.project_root
        root_item = QTreeWidgetItem(self)
        root_item.setText(0, os.path.basename(root_path))
        root_item.setData(0, Qt.ItemDataRole.UserRole, root_path)
        
        custom_icon = ThemeIcons.get_icon("icon_folder_opened.svg", ThemeColors.ACCENT_TEAL)
        if custom_icon and not custom_icon.isNull():
            root_item.setIcon(0, custom_icon)
        else:
            root_item.setIcon(0, _icon_provider.icon(QFileIconProvider.IconType.Folder))
        
        color = self.git_mgr.get_item_color(root_path, True)
        root_item.setForeground(0, QBrush(QColor(color)))
        root_item.setData(0, Qt.ItemDataRole.UserRole + 1, False)
        
        dummy = QTreeWidgetItem(root_item)
        dummy.setText(0, "Click to load...")
        
        self.mw.path_to_item[root_path] = root_item
        root_item.setExpanded(True)
        self.status_message.emit("Project loaded.")

    def _on_item_expanded(self, item):
        if item.data(0, Qt.ItemDataRole.UserRole + 1): 
            return 
            
        dir_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not dir_path or not os.path.isdir(dir_path): 
            return
            
        if item.childCount() == 1 and item.child(0).text(0) in ("Click to load...", "Loading..."):
            item.takeChildren()
            
        if dir_path not in self.project_mgr.file_watcher.directories():
            self.project_mgr.file_watcher.addPath(dir_path)
            
        loader = ProjectTreeLoader(dir_path, hidden_folders=self.project_mgr.hidden_folders)
        self.active_loaders.add(loader)
        loader.error_occurred.connect(lambda msg: QMessageBox.warning(self.mw, "Access Error", msg))
        loader.chunk_ready.connect(lambda chunk: self._populate_folder_children(item, chunk))
        loader.finished.connect(lambda: self._on_dir_loader_finished(loader, item, dir_path))
        loader.start()

    def _on_dir_loader_finished(self, loader, item, dir_path):
        if loader in self.active_loaders:
            self.active_loaders.discard(loader)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, True)
        self._load_files_into_folder(item, dir_path)

    def _populate_folder_children(self, parent_item, entries):
        if not entries: return
        
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        try:
            for name, full_path, is_dir, size, mtime, ext in entries:
                if is_dir and (full_path in self.project_mgr.hidden_folders or name in self.project_mgr.hidden_folders): 
                    continue
                if is_dir:
                    sub = QTreeWidgetItem(parent_item)
                    sub.setText(0, name)
                    sub.setData(0, Qt.ItemDataRole.UserRole, full_path)
                    
                    custom_icon = ThemeIcons.get_icon("icon_folder_closed.svg", ThemeColors.ACCENT_TEAL)
                    if custom_icon and not custom_icon.isNull():
                        sub.setIcon(0, custom_icon)
                    else:
                        sub.setIcon(0, _icon_provider.icon(QFileIconProvider.IconType.Folder))
                    
                    color = self.git_mgr.get_item_color(full_path, True)
                    sub.setForeground(0, QBrush(QColor(color)))
                    sub.setData(0, Qt.ItemDataRole.UserRole + 1, False)
                    
                    dummy = QTreeWidgetItem(sub)
                    dummy.setText(0, "Click to load...")
                    self.mw.path_to_item[full_path] = sub
        finally:
            self.setUpdatesEnabled(True)
            self.blockSignals(False)

    def _load_files_into_folder(self, parent_item, dir_path):
        if parent_item.data(0, Qt.ItemDataRole.UserRole + 2): return
        loader = FileListLoader(dir_path)
        self.active_loaders.add(loader)
        loader.error_occurred.connect(lambda msg: QMessageBox.warning(self.mw, "Access Error", msg))
        loader.chunk_ready.connect(lambda chunk: self._add_file_children(parent_item, chunk))
        loader.finished.connect(lambda: self.active_loaders.discard(loader))
        loader.start()
        parent_item.setData(0, Qt.ItemDataRole.UserRole + 2, True)

    def _add_file_children(self, parent_item, entries):
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        try:
            for name, full_path, is_dir, size, mtime, ext in entries:
                if not is_dir:
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, name)
                    file_item.setData(0, Qt.ItemDataRole.UserRole, full_path)
                    
                    file_item.setIcon(0, self.get_file_icon(ext, full_path))
                    
                    color = self.git_mgr.get_item_color(full_path, False)
                    file_item.setForeground(0, QBrush(QColor(color)))
                    self.mw.path_to_item[full_path] = file_item
        finally:
            self.setUpdatesEnabled(True)
            self.blockSignals(False)

    def _on_item_double_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and os.path.isfile(path): 
            self.file_opened.emit(path)

    def _show_context_menu(self, position):
        item = self.itemAt(position)
        if not item: return
        
        self.setCurrentItem(item)
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path: return
        
        is_dir = os.path.isdir(path)
        menu = QMenu()
        
        new_file_act = QAction(ThemeIcons.get_icon("new_file.svg", ThemeColors.TEXT_MAIN), "New File", self)
        new_file_act.triggered.connect(self.project_mgr.create_new_file)
        menu.addAction(new_file_act)
        
        new_folder_act = QAction(ThemeIcons.get_icon("new_folder.svg", ThemeColors.TEXT_MAIN), "New Folder", self)
        new_folder_act.triggered.connect(self.project_mgr.create_new_folder)
        menu.addAction(new_folder_act)
        
        menu.addSeparator()
        
        rename_act = QAction(ThemeIcons.get_icon("rename.svg", ThemeColors.TEXT_MAIN), "Rename", self)
        rename_act.triggered.connect(lambda: self.project_mgr.rename_selected(path))
        menu.addAction(rename_act)
        
        delete_act = QAction(ThemeIcons.get_icon("delete.svg", ThemeColors.ERROR), "Delete", self)
        delete_act.triggered.connect(lambda: self.project_mgr.delete_selected(path))
        menu.addAction(delete_act)
        
        if is_dir:
            menu.addSeparator()
            if path in self.project_mgr.hidden_folders:
                action_show = QAction("Show All Hidden Folders", self)
                action_show.triggered.connect(lambda: self._toggle_folder_visibility(path, show=True))
                menu.addAction(action_show)
            else:
                action_hide = QAction("Hide this folder", self)
                action_hide.triggered.connect(lambda: self._toggle_folder_visibility(path, show=False))
                menu.addAction(action_hide)
                
        menu.exec(self.viewport().mapToGlobal(position))

    def _toggle_folder_visibility(self, folder_path, show):
        if show: 
            self.project_mgr.hidden_folders.discard(folder_path)
        else: 
            self.project_mgr.hidden_folders.add(folder_path)
        self.refresh_tree()
        self.mw._save_config()

    def get_selected_path(self):
        items = self.selectedItems()
        return items[0].data(0, Qt.ItemDataRole.UserRole) if items else None