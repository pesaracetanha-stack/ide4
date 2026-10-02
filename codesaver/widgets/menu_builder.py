# -*- coding: utf-8 -*-
# codesaver/widgets/menu_builder.py
import os
import shutil
from PySide6.QtWidgets import QMenu, QToolBar, QFileDialog, QMessageBox
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QSettings

from .dialogs import ProfileDialog
from ..core.theme_manager import ThemeIcons, ThemeColors

class MenuBuilder:
    def __init__(self, main_window, icon_dir):
        self.mw = main_window
        self.icon_dir = icon_dir

    def build_menu(self):
        menubar = self.mw.menuBar()
        menubar.clear()

        # 🚀 CHANGED: Standard icon color for menus
        icon_color = ThemeColors.ICON_COLOR
        shortcut_settings = QSettings("GitiArts", "CodeSaver_Shortcuts")
        
        def get_icon(filename):
            return ThemeIcons.get_icon(filename, icon_color)

        def get_sh(key, default_shortcut):
            val = shortcut_settings.value(key, default_shortcut)
            if val and val != "---":
                return QKeySequence(val)
            return QKeySequence()

        # ==================== File Menu ====================
        file_menu = menubar.addMenu("File")
        
        new_proj_act = QAction(get_icon("new_folder.svg"), "New Project", self.mw, shortcut=get_sh("shortcut_new_project", "Ctrl+Alt+N"))
        new_proj_act.triggered.connect(self.mw._new_project)
        
        new_file = QAction(get_icon("new_file.svg"), "New File", self.mw, shortcut=get_sh("shortcut_new_file", "Ctrl+N"))
        new_file.triggered.connect(self.mw.project_mgr.create_new_file)
        
        new_folder = QAction(get_icon("new_folder.svg"), "New Folder", self.mw, shortcut=get_sh("shortcut_new_folder", "Ctrl+Shift+N"))
        new_folder.triggered.connect(self.mw.project_mgr.create_new_folder)
        
        open_proj_folder = QAction(get_icon("open_folder.svg"), "Open Project", self.mw, shortcut=get_sh("shortcut_open_folder", "Ctrl+Shift+D"))
        open_proj_folder.triggered.connect(self.mw._open_project_folder)
        
        open_proj = QAction(get_icon("workspace.svg"), "Open Workspace", self.mw, shortcut=get_sh("shortcut_open_workspace", "Ctrl+O"))
        open_proj.triggered.connect(self.mw._open_project_workspace)
        
        file_menu.addActions([new_proj_act, new_file, new_folder, open_proj_folder, open_proj])
        
        self.recent_menu = QMenu("Recent Projects", self.mw)
        self.recent_menu.setIcon(get_icon("history.svg"))
        file_menu.addMenu(self.recent_menu)
        self.build_recent_menu()
        
        file_menu.addSeparator()
        
        save_file = QAction(get_icon("save.svg"), "Save File", self.mw, shortcut=get_sh("shortcut_save_file", "Ctrl+S"))
        save_file.triggered.connect(self.mw._save_current_file)
        
        save_proj = QAction(get_icon("save_all.svg"), "Save All", self.mw, shortcut=get_sh("shortcut_save_project", "Ctrl+Shift+S"))
        save_proj.triggered.connect(self.mw._save_project)
        
        save_as_proj = QAction(get_icon("save_as.svg"), "Save As...", self.mw, shortcut=get_sh("shortcut_save_as", "Ctrl+Shift+Alt+S"))
        save_as_proj.triggered.connect(self.mw._save_project_as)
        
        close_proj = QAction(get_icon("close_project.svg"), "Close Project", self.mw, shortcut=get_sh("shortcut_close_project", ""))
        close_proj.triggered.connect(self.mw._close_project)
        
        file_menu.addActions([save_file, save_proj, save_as_proj, close_proj])
        file_menu.addSeparator()
        
        export = QAction(get_icon("export.svg"), "Export Project", self.mw)
        export.triggered.connect(self.mw._open_export_window)
        
        restore_menu = file_menu.addMenu("Restore Points")
        restore_menu.setIcon(get_icon("history.svg"))
        create_rp = QAction("Create Restore Point", self.mw)
        create_rp.triggered.connect(self.mw._create_restore_point)
        restore_from_rp = QAction("Restore from Point", self.mw)
        restore_from_rp.triggered.connect(self.mw._restore_from_restore_point)
        restore_menu.addActions([create_rp, restore_from_rp])
        
        file_menu.addAction(export)
        file_menu.addSeparator()
        
        pref_act = QAction(get_icon("general_settings.svg"), "Preferences", self.mw, shortcut=get_sh("shortcut_preferences", "Ctrl+,"))
        pref_act.triggered.connect(self.mw._open_preferences)
        file_menu.addAction(pref_act)
        
        file_menu.addSeparator()
        
        exit_action = QAction(get_icon("exit.svg"), "Exit", self.mw, shortcut=get_sh("shortcut_exit", "Ctrl+Q"))
        exit_action.triggered.connect(self.mw.close)
        file_menu.addAction(exit_action)

        # ==================== Edit Menu ====================
        edit_menu = menubar.addMenu("Edit")
        
        self.mw.undo_project = QAction(get_icon("undo.svg"), "Undo", self.mw, shortcut=get_sh("shortcut_undo", "Ctrl+Z"))
        self.mw.undo_project.triggered.connect(self.mw._undo_project)
        self.mw.redo_project = QAction(get_icon("redo.svg"), "Redo", self.mw, shortcut=get_sh("shortcut_redo", "Ctrl+Y"))
        self.mw.redo_project.triggered.connect(self.mw._redo_project)
        edit_menu.addActions([self.mw.undo_project, self.mw.redo_project])
        edit_menu.addSeparator()

        cut = QAction(get_icon("cut.svg"), "Cut", self.mw, shortcut=get_sh("shortcut_cut", "Ctrl+X"))
        cut.triggered.connect(self.mw._cut)
        copy = QAction(get_icon("copy.svg"), "Copy", self.mw, shortcut=get_sh("shortcut_copy", "Ctrl+C"))
        copy.triggered.connect(self.mw._copy)
        paste = QAction(get_icon("paste.svg"), "Paste", self.mw, shortcut=get_sh("shortcut_paste", "Ctrl+V"))
        paste.triggered.connect(self.mw._paste)
        
        delete = QAction(get_icon("delete.svg"), "Delete", self.mw, shortcut=get_sh("shortcut_delete", "Del"))
        delete.triggered.connect(self.mw._delete_selected)
        rename = QAction(get_icon("rename.svg"), "Rename", self.mw, shortcut=get_sh("shortcut_rename", "F2"))
        rename.triggered.connect(self.mw._rename_selected)
        
        edit_menu.addActions([cut, copy, paste, delete, rename])
        edit_menu.addSeparator()

        find_action = QAction(get_icon("find.svg"), "Find", self.mw, shortcut=get_sh("shortcut_find", "Ctrl+F"))
        find_action.triggered.connect(self.mw._show_find_bar)
        global_search_act = QAction(get_icon("global_search.svg"), "Global Search", self.mw, shortcut=get_sh("shortcut_global_search", "Ctrl+Shift+F"))
        global_search_act.triggered.connect(self.mw._show_global_search)
        symbol_search_act = QAction(get_icon("symbol_search.svg"), "Symbol Search", self.mw, shortcut=get_sh("shortcut_symbol_search", "Ctrl+Shift+O"))
        symbol_search_act.triggered.connect(self.mw._show_symbol_palette)
        
        edit_menu.addActions([find_action, global_search_act, symbol_search_act])
        edit_menu.addSeparator()

        format_act = QAction(get_icon("format_code.svg"), "Format Code", self.mw, shortcut=get_sh("shortcut_format", "Shift+Alt+F"))
        format_act.triggered.connect(self.mw._format_current_file)
        edit_menu.addAction(format_act)

        # ==================== View Menu ====================
        view_menu = menubar.addMenu("View")
        
        cmd_palette_act = QAction(get_icon("command_palette.svg"), "Command Palette", self.mw, shortcut=get_sh("shortcut_command_palette", "Ctrl+Shift+P"))
        cmd_palette_act.triggered.connect(self.mw.command_palette.show_palette)
        view_menu.addAction(cmd_palette_act)
        view_menu.addSeparator()
        
        self.toggle_tree_act = QAction(get_icon("toggle_explorer.svg"), "File Explorer", self.mw, checkable=True)
        if hasattr(self.mw, 'btn_explorer'):
            self.toggle_tree_act.setChecked(self.mw.btn_explorer.isChecked())
            self.toggle_tree_act.toggled.connect(self.mw.btn_explorer.setChecked)
            self.mw.btn_explorer.toggled.connect(self.toggle_tree_act.setChecked)
        view_menu.addAction(self.toggle_tree_act)

        self.toggle_history_act = QAction(get_icon("history.svg"), "Version History", self.mw, checkable=True)
        if hasattr(self.mw, 'btn_hist'):
            self.toggle_history_act.setChecked(self.mw.btn_hist.isChecked())
            self.toggle_history_act.toggled.connect(self.mw.btn_hist.setChecked)
            self.mw.btn_hist.toggled.connect(self.toggle_history_act.setChecked)
        view_menu.addAction(self.toggle_history_act)

        self.toggle_ai_act = QAction(get_icon("chat_bot.svg"), "AI Assistant Panel", self.mw, checkable=True, shortcut=get_sh("shortcut_ai_chat", "Ctrl+Shift+A"))
        if hasattr(self.mw, 'btn_ai'):
            self.toggle_ai_act.setChecked(self.mw.btn_ai.isChecked())
            self.toggle_ai_act.toggled.connect(self.mw.btn_ai.setChecked)
            self.mw.btn_ai.toggled.connect(self.toggle_ai_act.setChecked)
        view_menu.addAction(self.toggle_ai_act)
        
        view_menu.addSeparator()

        term_act = QAction(get_icon("terminal.svg"), "Terminal", self.mw, shortcut=get_sh("shortcut_terminal", "Ctrl+`"))
        if hasattr(self.mw, 'btn_term'):
            term_act.triggered.connect(lambda: self.mw.btn_term.setChecked(not self.mw.btn_term.isChecked()))
        view_menu.addAction(term_act)
        view_menu.addSeparator()
        
        show_hidden_menu = view_menu.addMenu(get_icon("toggle_hidden_folder.svg"), "Hidden Folders")
        show_all_act = QAction("Toggle Hidden Folders", self.mw)
        show_all_act.triggered.connect(self.mw._show_all_hidden_folders)
        show_hidden_menu.addAction(show_all_act)

        # ==================== Run Menu ====================
        run_menu = menubar.addMenu("Run")
        run_proj_act = QAction(get_icon("run_project.svg"), "Run Smart Project", self.mw, shortcut=get_sh("shortcut_run", "F5"))
        run_proj_act.triggered.connect(lambda: self.mw.terminal.auto_run_project() if hasattr(self.mw, 'terminal') and hasattr(self.mw.terminal, 'auto_run_project') else None)
        run_menu.addAction(run_proj_act)

        # ==================== Tools Menu ====================
        tools_menu = menubar.addMenu("Tools")
        
        ai_menu = tools_menu.addMenu(get_icon("chat_bot.svg"), "AI Assistant")
        
        clear_chat_act = QAction(get_icon("clear_chat.svg"), "Clear Chat History", self.mw)
        if hasattr(self.mw, 'chatbot_panel') and hasattr(self.mw.chatbot_panel, 'clear_chat'):
            clear_chat_act.triggered.connect(self.mw.chatbot_panel.clear_chat)
        ai_menu.addAction(clear_chat_act)
        
        self.mw.sandbox_act = QAction(get_icon("sandbox_mode.svg"), "Sandbox Mode", self.mw, checkable=True)
        self.mw.sandbox_act.setChecked(False) 
        if hasattr(self.mw, 'chatbot_panel') and hasattr(self.mw.chatbot_panel, 'toggle_sandbox'):
            self.mw.sandbox_act.toggled.connect(self.mw.chatbot_panel.toggle_sandbox)
        ai_menu.addAction(self.mw.sandbox_act)
        
        ai_settings_act = QAction(get_icon("ai_setting.svg"), "API Connection Settings", self.mw)
        if hasattr(self.mw, 'chatbot_panel') and hasattr(self.mw.chatbot_panel, 'open_settings'):
            ai_settings_act.triggered.connect(self.mw.chatbot_panel.open_settings)
        ai_menu.addAction(ai_settings_act)
        
        tools_menu.addSeparator()

        self.mw.plugin_menu = tools_menu.addMenu(get_icon("plugins.svg"), "Plugins")
        install_plugin_act = QAction("➕ Install New Plugin...", self.mw)
        install_plugin_act.triggered.connect(self.install_new_plugin)
        self.mw.plugin_menu.addAction(install_plugin_act)
        self.mw.plugin_menu.addSeparator()

        # ==================== Help Menu ====================
        help_menu = menubar.addMenu("Help")
        
        profile_action = QAction(get_icon("profile.svg"), "User Profile", self.mw)
        profile_action.triggered.connect(self.show_profile_dialog)
        help_menu.addAction(profile_action)
        help_menu.addSeparator()
        
        shortcuts_action = QAction(get_icon("command_palette.svg"), "Keyboard Shortcuts", self.mw)
        shortcuts_action.triggered.connect(self.show_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)
        
        help_action = QAction(get_icon("documentation.svg"), "Documentation", self.mw, shortcut=get_sh("shortcut_docs", "F1"))
        help_action.triggered.connect(self.mw._show_help)
        help_menu.addAction(help_action)
        
        log_action = QAction(get_icon("system_log.svg"), "View Logs", self.mw)
        log_action.triggered.connect(self.mw._show_error_logs)
        help_menu.addAction(log_action)

    def show_profile_dialog(self):
        dlg = ProfileDialog(self.mw.config_mgr, self.mw)
        dlg.exec()

    def show_shortcuts_dialog(self):
        from .shortcuts_reference import ShortcutsReferenceDialog
        dlg = ShortcutsReferenceDialog(self.mw)
        dlg.exec()

    def build_recent_menu(self):
        if not hasattr(self, 'recent_menu'): return
        self.recent_menu.clear()
        
        settings = QSettings("HPR", "CodeSaver")
        recent = settings.value("recent_projects", [])
        recent = [] if not isinstance(recent, list) else recent
            
        valid_recent = []
        for path in recent:
            if os.path.exists(path):
                valid_recent.append(path)
                display_text = f"{os.path.basename(path)} ({path})"
                action = QAction(display_text, self.mw)
                action.triggered.connect(lambda checked=False, p=path: self.mw._open_recent_project(p))
                self.recent_menu.addAction(action)
                
        if len(valid_recent) != len(recent):
            settings.setValue("recent_projects", valid_recent)

        if not valid_recent:
            empty_action = QAction("No recent projects", self.mw)
            empty_action.setEnabled(False)
            self.recent_menu.addAction(empty_action)
        else:
            self.recent_menu.addSeparator()
            clear_action = QAction("Clear History", self.mw)
            clear_action.triggered.connect(lambda: [settings.setValue("recent_projects", []), self.build_recent_menu()])
            self.recent_menu.addAction(clear_action)

    def build_toolbar(self):
        if hasattr(self.mw, 'main_toolbar') and self.mw.main_toolbar is not None:
            self.mw.removeToolBar(self.mw.main_toolbar)
            
        self.mw.main_toolbar = QToolBar("Main")
        self.mw.main_toolbar.setMovable(False)
        self.mw.addToolBar(self.mw.main_toolbar)
        
        icon_color = ThemeColors.TEXT_MAIN
        def get_icon(filename):
            return ThemeIcons.get_icon(filename, icon_color)

        run_act = QAction(get_icon("run_project.svg"), "Run Project", self.mw)
        run_act.setToolTip("Run Smart Project (F5)")
        run_act.triggered.connect(lambda: self.mw.terminal.auto_run_project() if hasattr(self.mw, 'terminal') and hasattr(self.mw.terminal, 'auto_run_project') else None)
        self.mw.main_toolbar.addAction(run_act)
        self.mw.main_toolbar.addSeparator()

        open_act = QAction(get_icon("open_folder.svg"), "Open Project", self.mw)
        open_act.triggered.connect(self.mw._open_project_folder)
        
        save_act = QAction(get_icon("save.svg"), "Save File", self.mw)
        save_act.triggered.connect(self.mw._save_current_file)
        
        self.mw.main_toolbar.addActions([open_act, save_act])
        self.mw.main_toolbar.addSeparator()
        
        new_file_act = QAction(get_icon("new_file.svg"), "New File", self.mw)
        new_file_act.triggered.connect(self.mw.project_mgr.create_new_file)
        
        new_folder_act = QAction(get_icon("new_folder.svg"), "New Folder", self.mw)
        new_folder_act.triggered.connect(self.mw.project_mgr.create_new_folder)
        
        delete_act = QAction(get_icon("delete.svg"), "Delete", self.mw)
        delete_act.triggered.connect(self.mw._delete_selected)
        
        self.mw.main_toolbar.addActions([new_file_act, new_folder_act, delete_act])

    def install_new_plugin(self):
        filepath, _ = QFileDialog.getOpenFileName(self.mw, "Select Plugin File", "", "Python Files (*.py)")
        if filepath:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            plugins_dir = os.path.join(base_dir, "plugins")
            os.makedirs(plugins_dir, exist_ok=True)
            
            try:
                shutil.copy(filepath, plugins_dir)
                QMessageBox.information(self.mw, "Success", "New plugin installed successfully.\nPlease restart the application to apply changes.")
            except Exception as e:
                QMessageBox.critical(self.mw, "Error", f"Failed to copy plugin:\n{str(e)}")