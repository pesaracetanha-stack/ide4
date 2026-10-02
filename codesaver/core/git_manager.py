# -*- coding: utf-8 -*-
# codesaver/core/git_manager.py
import os
import subprocess
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QColor, QBrush
from .theme_manager import ThemeColors

class GitStatusWorker(QThread):
    status_ready = Signal(dict)
    error_occurred = Signal(str)  # 🚀 سیگنال جدید برای گزارش خطاهای حیاتی به UI

    def __init__(self, project_root):
        super().__init__()
        self.project_root = project_root

    def run(self):
        git_states = {}
        if not self.project_root:
            self.status_ready.emit(git_states)
            return
            
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            res = subprocess.run(
                ['git', 'status', '--porcelain'], 
                cwd=self.project_root, 
                capture_output=True, 
                text=True, 
                startupinfo=startupinfo
            )
            
            # 🚀 مدیریت خطاهای مربوط به عدم وجود مخزن گیت در پوشه فعلی
            if res.returncode != 0:
                if "not a git repository" in res.stderr.lower():
                    self.error_occurred.emit("NOT_A_REPO")
                else:
                    self.error_occurred.emit(f"GIT_ERROR: {res.stderr.strip()}")
                self.status_ready.emit(git_states)
                return

            for line in res.stdout.splitlines():
                if len(line) > 3:
                    state = line[:2].strip()
                    rel_path = line[3:].strip()
                    
                    if rel_path.startswith('"') and rel_path.endswith('"'):
                        rel_path = rel_path[1:-1]
                        
                    abs_path = os.path.normpath(os.path.join(self.project_root, rel_path))
                    git_states[abs_path] = state

        except FileNotFoundError:
            # 🚀 کشف خطای نصب نبودن موتور گیت در سیستم‌عامل
            self.error_occurred.emit("GIT_NOT_FOUND")
        except Exception as e:
            self.error_occurred.emit(f"UNKNOWN_ERROR: {str(e)}")
            
        self.status_ready.emit(git_states)


class GitManager(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.git_states = {}
        self.git_worker = None
        self._git_missing_warned = False  # برای جلوگیری از اسپم شدن هشدار در UI

    def _run_cmd(self, args, cwd):
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            res = subprocess.run(['git'] + args, cwd=cwd, capture_output=True, text=True, startupinfo=startupinfo)
            return res.returncode == 0, res.stdout if res.returncode == 0 else res.stderr
        except FileNotFoundError:
            # 🚀 جلوگیری از کرش سیستم هنگام کامیت یا پوش بدون گیت
            return False, "Git is not installed or not found in system PATH. Please install Git first."
        except Exception as e:
            return False, str(e)

    def git_commit_all(self, cwd, message):
        add_success, add_err = self._run_cmd(['add', '.'], cwd)
        if not add_success:
            return False, add_err
            
        return self._run_cmd(['commit', '-m', message], cwd)

    def git_push(self, cwd):
        return self._run_cmd(['push'], cwd)

    def update_git_status(self, project_root):
        if not project_root:
            self.git_states.clear()
            self.apply_git_colors()
            return
            
        if self.git_worker and self.git_worker.isRunning():
            return
            
        self.git_worker = GitStatusWorker(project_root)
        self.git_worker.status_ready.connect(self._on_git_status_ready)
        self.git_worker.error_occurred.connect(self._on_git_error)
        self.git_worker.start()

    def _on_git_error(self, error_type):
        """مدیریت هوشمند خطاهای گزارش شده از سمت Worker"""
        if error_type == "GIT_NOT_FOUND" and not self._git_missing_warned:
            if hasattr(self.mw, 'status_label'):
                self.mw.status_label.setText("⚠️ Git is missing! Version control features are disabled.")
                self.mw.status_label.setStyleSheet(f"color: {ThemeColors.WARNING};")
            self._git_missing_warned = True

    def _on_git_status_ready(self, states):
        self.git_states = states
        self.apply_git_colors()
        
        if hasattr(self.mw, 'git_panel') and hasattr(self.mw.git_panel, 'update_changes_list'):
            self.mw.git_panel.update_changes_list()

    def apply_git_colors(self):
        if not hasattr(self.mw, 'path_to_item'):
            return
            
        for full_path, item in self.mw.path_to_item.items():
            is_dir = os.path.isdir(full_path)
            color = self.get_item_color(full_path, is_dir)
            item.setForeground(0, QBrush(color))

    def get_item_color(self, full_path, is_dir):
        default_color = QColor(ThemeColors.TEXT_MAIN)
        
        if is_dir:
            for p in self.git_states:
                if p.startswith(full_path + os.sep):
                    return QColor(ThemeColors.WARNING)
            return default_color
        else:
            state = self.git_states.get(full_path, "")
            if state in ('M', 'AM', 'MM'): 
                return QColor(ThemeColors.WARNING)
            elif state in ('??', 'A'): 
                return QColor(ThemeColors.SUCCESS)
            elif state in ('D', 'AD'): 
                return QColor(ThemeColors.ERROR)
            return default_color