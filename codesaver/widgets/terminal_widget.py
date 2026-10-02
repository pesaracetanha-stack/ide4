# -*- coding: utf-8 -*-
# codesaver/widgets/terminal_widget.py
import sys
import os
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit
from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent, QTextCursor

from ..core.theme_manager import ThemeColors

class CommandLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.history_index = -1
        self.temp_command = ""

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down:
            self.navigate_history(1)
        else:
            super().keyPressEvent(event)

    def navigate_history(self, direction):
        if not self.history:
            return
        if self.history_index == -1:
            self.temp_command = self.text()
        new_index = self.history_index + direction
        if 0 <= new_index < len(self.history):
            self.history_index = new_index
            self.setText(self.history[self.history_index])
        elif direction == -1 and new_index == -1:
            self.history_index = -1
            self.setText(self.temp_command)
        elif direction == 1 and new_index == len(self.history):
            self.history_index = -1
            self.setText(self.temp_command)
            self.temp_command = ""

    def add_command(self, command):
        if command and (not self.history or self.history[-1] != command):
            self.history.append(command)
        self.history_index = -1
        self.temp_command = ""


class TerminalWidget(QWidget):
    error_detected = Signal(str)

    def __init__(self, parent=None, working_dir=None):
        super().__init__(parent)
        self.working_dir = working_dir
        self.process = None
        self.started = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 12))
        
        # 🚀 CHANGED: Using ThemeColors directly for terminal distinct parts
        self.output.setStyleSheet("border: none;") 
        layout.addWidget(self.output)
        
        self.input_line = CommandLineEdit()
        self.input_line.setPlaceholderText("Type command and press Enter...")
        self.input_line.returnPressed.connect(self.execute_command)
        self.input_line.setStyleSheet(f"color: {ThemeColors.SUCCESS}; border: none; border-top: 1px solid {ThemeColors.BORDER_DEFAULT}; font-family: Consolas; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.input_line)

    def start_shell(self):
        if self.started:
            return
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyRead.connect(self.on_output)
        
        if sys.platform == 'win32':
            self.process.start("cmd.exe")
        else:
            self.process.start("bash")
            
        if self.working_dir and os.path.isdir(self.working_dir):
            self.process.setWorkingDirectory(self.working_dir)
        
        self.started = True

    def execute_command(self):
        if not self.started:
            self.start_shell()
        cmd = self.input_line.text().strip()
        if not cmd:
            return
        self.input_line.add_command(cmd)
        self.output.appendPlainText(f"\n> {cmd}")
        self.process.write((cmd + '\n').encode())
        self.input_line.clear()

    def send_command(self, command):
        if not self.started:
            self.start_shell()
        self.input_line.setText(command)
        self.execute_command()
        
    def auto_run_project(self):
        if not self.working_dir:
            self.output.appendPlainText("\n[System] No project loaded.")
            return
            
        entry_points = ['main.py', 'app.py', 'run.py', 'index.js']
        for f in entry_points:
            if os.path.exists(os.path.join(self.working_dir, f)):
                cmd = f"python {f}" if f.endswith('.py') else f"node {f}"
                self.output.appendPlainText(f"\n[System] Found entry point: {f}")
                self.send_command(cmd)
                return
                
        self.output.appendPlainText("\n[System] Could not find a standard entry point (main.py, app.py, etc.).")

    def on_output(self):
        data = self.process.readAll().data().decode(errors='replace')
        
        if re.search(r'(?i)(error|exception|traceback|syntaxerror|nameerror)', data):
            self.error_detected.emit(data)

        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output.setTextCursor(cursor)
        self.output.insertPlainText(data)
        self.output.ensureCursorVisible()

    def kill(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)

    def change_working_directory(self, new_dir):
        if not new_dir or not os.path.isdir(new_dir):
            return
        self.working_dir = new_dir
        if self.started:
            cd_cmd = f'cd /d "{new_dir}"' if sys.platform == 'win32' else f'cd "{new_dir}"'
            self.process.write((cd_cmd + '\n').encode())
            msg = f"\n[System] Working directory changed to: {new_dir}"
            self.output.appendPlainText(msg)
        else:
            self.start_shell()