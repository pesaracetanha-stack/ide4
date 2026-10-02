# -*- coding: utf-8 -*-
# codesaver/widgets/terminal_panel.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                               QLabel, QPushButton)
from PySide6.QtCore import Signal, Qt, QTimer, QSize

from .terminal_widget import TerminalWidget
from ..core.theme_manager import ThemeIcons, ThemeColors

class EnhancedTerminalPanel(QWidget):
    error_detected = Signal(str)

    def __init__(self, project_root=None, parent=None):
        super().__init__(parent)
        self.mw = parent
        self.project_root = project_root or os.getcwd()
        self.last_error_buffer = ""
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # --- TOP TOOLBAR ---
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        # 🚀 CHANGED: Using ThemeIcons centrally
        lbl_title = QLabel()
        lbl_title.setPixmap(ThemeIcons.get_icon("quick_command.svg", ThemeColors.TEXT_MAIN).pixmap(20, 20))
        lbl_title.setToolTip("Quick Commands")
        top_row.addWidget(lbl_title)
        
        self.cmd_combo = QComboBox()
        self.commands_data = [
            {"cmd": "npm install", "desc": "Install Node.js packages (React/Vue prerequisite)"},
            {"cmd": "npm run dev", "desc": "Run development server (Vite/React)"},
            {"cmd": "python -m venv venv", "desc": "Create a Python virtual environment"},
            {"cmd": "venv\\Scripts\\activate", "desc": "Activate Python virtual environment (Windows)"},
            {"cmd": "pip install -r requirements.txt", "desc": "Auto-install Python libraries (requirements.txt)"},
            {"cmd": "git init", "desc": "Initialize Git repository"},
        ]
        
        for item in self.commands_data:
            self.cmd_combo.addItem(item["cmd"])
            
        self.cmd_combo.currentIndexChanged.connect(self._on_command_changed)
        top_row.addWidget(self.cmd_combo)
        
        self.btn_run_cmd = QPushButton()
        self.btn_run_cmd.setIcon(ThemeIcons.get_icon("run_project.svg", ThemeColors.ACCENT_BLUE))
        self.btn_run_cmd.setIconSize(QSize(18, 18))
        self.btn_run_cmd.setToolTip("Run selected command")
        self.btn_run_cmd.setFixedSize(30, 30)
        self.btn_run_cmd.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run_cmd.clicked.connect(self._run_predefined_command)
        top_row.addWidget(self.btn_run_cmd)

        self.btn_auto_run = QPushButton()
        self.btn_auto_run.setIcon(ThemeIcons.get_icon("run_project.svg", ThemeColors.SUCCESS))
        self.btn_auto_run.setIconSize(QSize(18, 18))
        self.btn_auto_run.setToolTip("Run Smart Project (F5)")
        self.btn_auto_run.setFixedSize(30, 30)
        self.btn_auto_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auto_run.clicked.connect(self.auto_run_project)
        top_row.addWidget(self.btn_auto_run)

        top_row.addStretch()

        self.btn_ai_debug = QPushButton()
        self.btn_ai_debug.setIcon(ThemeIcons.get_icon("ai_debug.svg", ThemeColors.ACCENT_TEAL))
        self.btn_ai_debug.setIconSize(QSize(18, 18))
        self.btn_ai_debug.setToolTip("Debug error with AI")
        self.btn_ai_debug.setFixedSize(30, 30)
        self.btn_ai_debug.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ai_debug.hide()
        self.btn_ai_debug.clicked.connect(self.trigger_ai_debugger)
        top_row.addWidget(self.btn_ai_debug)

        self.btn_clear = QPushButton()
        self.btn_clear.setIcon(ThemeIcons.get_icon("clear_terminal.svg", ThemeColors.TEXT_MAIN))
        self.btn_clear.setIconSize(QSize(18, 18))
        self.btn_clear.setToolTip("Clear Terminal")
        self.btn_clear.setFixedSize(30, 30)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_terminal)
        top_row.addWidget(self.btn_clear)

        layout.addLayout(top_row)
        
        self.desc_label = QLabel()
        # Minimal style for description
        self.desc_label.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px; font-style: italic; background: transparent; border: none;")
        layout.addWidget(self.desc_label)
        self._on_command_changed(0)
        
        self.terminal_widget = TerminalWidget(parent=self, working_dir=self.project_root)
        self.terminal_widget.error_detected.connect(self.on_error_detected)
        layout.addWidget(self.terminal_widget, stretch=1)

    def clear_terminal(self):
        self.terminal_widget.output.clear()
        self.btn_ai_debug.hide()

    def change_working_directory(self, path):
        if os.path.exists(path):
            self.project_root = path
            self.terminal_widget.change_working_directory(path)

    def _on_command_changed(self, index):
        if 0 <= index < len(self.commands_data):
            self.desc_label.setText(self.commands_data[index]["desc"])

    def _run_predefined_command(self):
        command = self.cmd_combo.currentText()
        if command:
            self.terminal_widget.send_command(command)

    def on_error_detected(self, error_text):
        self.last_error_buffer = error_text
        self.btn_ai_debug.show()

    def trigger_ai_debugger(self):
        if self.last_error_buffer:
            self.error_detected.emit(self.last_error_buffer)
            self.btn_ai_debug.hide()
            if hasattr(self.mw, 'chatbot_dock') and not self.mw.chatbot_dock.isVisible():
                self.mw.chatbot_dock.setVisible(True)

    def start_shell(self):
        self.terminal_widget.start_shell()

    def _find_framework_marker(self, start_dir, marker_name):
        current = start_dir
        while current and current.startswith(self.project_root):
            if os.path.exists(os.path.join(current, marker_name)):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return None

    def auto_run_project(self):
        if not self.project_root or not os.path.exists(self.project_root):
            self.terminal_widget.output.appendPlainText("\n[System] ⚠️ Error: No project is open!")
            return
            
        if hasattr(self.mw, 'tab_mgr'):
            try:
                for idx in range(self.mw.editor_tab_widget.count()):
                    tab = self.mw.editor_tab_widget.widget(idx)
                    if hasattr(tab, 'is_modified') and tab.is_modified:
                        tab.save_content()
            except Exception:
                pass

        active_tab_path = None
        if hasattr(self.mw, 'current_editor_tab') and self.mw.current_editor_tab:
            active_tab_path = getattr(self.mw.current_editor_tab, 'file_path', None)

        command = ""
        working_dir = self.project_root
        search_base = os.path.dirname(active_tab_path) if active_tab_path else self.project_root
        
        node_root = self._find_framework_marker(search_base, "package.json")
        django_root = self._find_framework_marker(search_base, "manage.py")

        if node_root:
            working_dir = node_root
            try:
                import json
                with open(os.path.join(node_root, "package.json"), "r", encoding="utf-8") as f:
                    scripts = json.load(f).get("scripts", {})
                    if "dev" in scripts: command = "npm run dev"
                    elif "start" in scripts: command = "npm start"
                    else: command = "node index.js"
            except:
                command = "npm start"
                
        elif django_root:
            working_dir = django_root
            command = "python manage.py runserver"
            
        elif active_tab_path:
            working_dir = os.path.dirname(active_tab_path)
            file_name = os.path.basename(active_tab_path)
            ext = os.path.splitext(file_name)[1].lower()
            
            if ext in ['.py', '.pyw']:
                command = f'python -u "{file_name}"'
            elif ext == '.js':
                command = f'node "{file_name}"'
            elif ext in ['.html', '.htm']:
                command = 'python -m http.server 8000 --bind 127.0.0.1'
            elif ext == '.php':
                command = 'php -S 127.0.0.1:8000 -t .'
            else:
                self.terminal_widget.output.appendPlainText(f"\n[System] ⚠️ The application doesn't know how to run a {ext} file.")
                return
        else:
            self.terminal_widget.output.appendPlainText("\n[System] ⚠️ Please open a file in the editor first so the application knows what to run.")
            return

        self.terminal_widget.change_working_directory(working_dir)
        self.terminal_widget.output.appendPlainText(f"\n[Smart Run] Ready to execute in {os.path.basename(working_dir)}...")
        QTimer.singleShot(600, lambda: self.terminal_widget.send_command(command))