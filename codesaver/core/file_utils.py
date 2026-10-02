# -*- coding: utf-8 -*-
# codesaver/core/file_utils.py
import os
import datetime
from PySide6.QtGui import QIcon, QPainter, QColor

def load_colored_icon(filepath, color="#007AAC"):
    """Unified safe icon colorizer to prevent any circular import issues"""
    if not os.path.exists(filepath):
        return QIcon()
    
    icon = QIcon(filepath)
    new_icon = QIcon()
    for size in [16, 18, 20, 24, 32, 48, 64]:
        pixmap = icon.pixmap(size, size)
        if not pixmap.isNull():
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))
            painter.end()
            new_icon.addPixmap(pixmap)
            
    return new_icon if not new_icon.isNull() else icon

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def format_time(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

def is_text_file(file_path):
    text_extensions = {
        '.txt', '.md', '.rst', '.tex', '.latex',
        '.py', '.pyw', '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx',
        '.html', '.htm', '.css', '.scss', '.sass', '.less',
        '.json', '.yaml', '.yml', '.xml', '.svg', '.xhtml',
        '.c', '.cpp', '.h', '.hpp', '.cc', '.cxx',
        '.java', '.kt', '.kts', '.scala', '.groovy',
        '.go', '.rs', '.rb', '.php', '.pm', '.t',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
        '.sql', '.r', '.m', '.jl', '.lua', '.pl', '.pyx',
        '.ini', '.cfg', '.conf', '.properties', '.toml',
        '.csv', '.tsv', '.log'
    }
    ext = os.path.splitext(file_path)[1].lower()
    if ext in text_extensions:
        return True
        
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(512)
            if b'\0' in chunk:
                return False
        return True
    except Exception:
        return False