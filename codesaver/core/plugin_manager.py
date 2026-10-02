# codesaver/core/plugin_manager.py
import os
import importlib.util
import traceback
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QSettings

class PluginManager:
    """Plugin management system for injecting external code dynamically"""
    def __init__(self, main_window):
        self.mw = main_window
        
        # Find the project root path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.plugins_dir = os.path.join(base_dir, "plugins")
        self.loaded_plugins = []
        
        # 🚀 NEW: Settings to remember enabled/disabled state
        self.settings = QSettings("GitiArts", "CodeSaver_Plugins")
        
        self._ensure_plugin_dir()
        self.load_all_plugins()

    def _ensure_plugin_dir(self):
        if not os.path.exists(self.plugins_dir):
            try:
                os.makedirs(self.plugins_dir)
                self._create_sample_plugin()
            except Exception as e:
                print(f"Error creating plugins directory: {e}")

    def get_available_plugins(self):
        """Returns a dictionary of {filename: is_enabled} for the UI"""
        if not os.path.exists(self.plugins_dir):
            return {}
            
        plugins = {}
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                is_enabled = self.settings.value(filename, True, type=bool)
                plugins[filename] = is_enabled
        return plugins

    def toggle_plugin_state(self, filename, state):
        """Saves the state for a specific plugin"""
        self.settings.setValue(filename, state)

    def load_all_plugins(self):
        """Scan folder and load ONLY enabled Python files"""
        if not os.path.exists(self.plugins_dir):
            return
            
        self.loaded_plugins.clear()
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                is_enabled = self.settings.value(filename, True, type=bool)
                if is_enabled:
                    self._load_single_plugin(filename)

    def _load_single_plugin(self, filename):
        filepath = os.path.join(self.plugins_dir, filename)
        module_name = f"plugins.{filename[:-3]}"
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "register_plugin"):
                    module.register_plugin(self.mw)
                    self.loaded_plugins.append(filename)
                    print(f"[Plugin System] Loaded successfully: {filename}")
                else:
                    print(f"[Plugin System] Warning: {filename} has no 'register_plugin' function.")
                    
        except Exception as e:
            error_msg = traceback.format_exc()
            print(f"[Plugin System] Failed to load {filename}:\n{error_msg}")

    def _create_sample_plugin(self):
        sample_path = os.path.join(self.plugins_dir, "hello_plugin.py")
        code = '''\
# Sample Plugin
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

def register_plugin(main_window):
    hello_action = QAction("👋 Hello World Plugin", main_window)
    def show_msg():
        QMessageBox.information(main_window, "Plugin", "Hello! I am an external script injected into your software!")
    hello_action.triggered.connect(show_msg)
    
    menubar = main_window.menuBar()
    plugin_menu = None
    for action in menubar.actions():
        if action.text() == "🧩 Plugins":
            plugin_menu = action.menu()
            break
            
    if not plugin_menu:
        plugin_menu = menubar.addMenu("🧩 Plugins")
        
    plugin_menu.addAction(hello_action)
'''
        with open(sample_path, 'w', encoding='utf-8') as f:
            f.write(code)