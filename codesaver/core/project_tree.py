# codesaver/core/project_tree.py
import os
from PySide6.QtCore import QThread, Signal
# Call reference function from utility file
from .file_utils import is_text_file

class ProjectTreeLoader(QThread):
    """Ultra-fast folder loading in background"""
    chunk_ready = Signal(list)
    finished = Signal()
    # New signal to send errors to the UI without crashing the thread
    error_occurred = Signal(str) 

    def __init__(self, dir_path, hidden_folders=None, chunk_size=150):
        super().__init__()
        self.dir_path = dir_path
        self.chunk_size = chunk_size
        self.hidden_folders = hidden_folders or {'.git', '__pycache__', 'node_modules', '.venv', 'env', 'dist', 'build', '.idea', '.vscode'}

    def run(self):
        chunk = []
        try:
            with os.scandir(self.dir_path) as it:
                for entry in it:
                    if entry.name.startswith('.'):
                        continue
                    if entry.is_dir():
                        if entry.name in self.hidden_folders or entry.path in self.hidden_folders:
                            continue
                        
                        chunk.append((entry.name, entry.path, True, 0, 0, ""))
                        
                        if len(chunk) >= self.chunk_size:
                            self.chunk_ready.emit(chunk)
                            chunk = []
                            self.msleep(1)
            
            if chunk:
                self.chunk_ready.emit(chunk)
                
        except PermissionError:
            self.error_occurred.emit(f"Permission denied: You don't have access to folder '{os.path.basename(self.dir_path)}'.")
            self.chunk_ready.emit([("Access denied", "", True, 0, 0, "")])
        except Exception as e:
            self.error_occurred.emit(f"Error loading folder '{os.path.basename(self.dir_path)}': {str(e)}")
            
        self.finished.emit()


class FileListLoader(QThread):
    """Loading files of a directory in the background"""
    chunk_ready = Signal(list)
    finished = Signal()
    error_occurred = Signal(str) 

    def __init__(self, dir_path, chunk_size=150):
        super().__init__()
        self.dir_path = dir_path
        self.chunk_size = chunk_size

    def run(self):
        chunk = []
        entries = []
        try:
            with os.scandir(self.dir_path) as it:
                for entry in it:
                    if entry.is_file():
                        # Use centralized function instead of duplicated one
                        if not is_text_file(entry.path):
                            continue
                            
                        ext = os.path.splitext(entry.name)[1].lower()
                        entries.append((entry.name, entry.path, False, 0, 0, ext))
            
            entries.sort(key=lambda x: x[0].lower())
            
            for item in entries:
                chunk.append(item)
                if len(chunk) >= self.chunk_size:
                    self.chunk_ready.emit(chunk)
                    chunk = []
                    self.msleep(1)
                    
            if chunk:
                self.chunk_ready.emit(chunk)
                
        except PermissionError:
            self.error_occurred.emit(f"Permission denied: Cannot read files in '{os.path.basename(self.dir_path)}'.")
        except Exception as e:
            self.error_occurred.emit(f"Error reading files in '{os.path.basename(self.dir_path)}': {str(e)}")
            
        self.finished.emit()