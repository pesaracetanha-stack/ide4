# -*- coding: utf-8 -*-
# codesaver/widgets/syntax_highlighter.py
import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt

def create_format(hex_color, style=''):
    """A helper function to quickly create text styles with custom colors"""
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(hex_color))
    if 'bold' in style:
        fmt.setFontWeight(QFont.Bold)
    if 'italic' in style:
        fmt.setFontItalic(True)
    return fmt

class PythonHighlighter(QSyntaxHighlighter):
    """Advanced and dedicated highlighter for Python"""
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        
        # Attractive and modern Catppuccin Mocha color palette
        keyword_format = create_format("#cba6f7", "bold")     # Purple for keywords
        builtin_format = create_format("#fab387")             # Peach for built-in functions
        string_format = create_format("#a6e3a1")              # Green for text strings
        comment_format = create_format("#6c7086", "italic")   # Dim gray for comments
        number_format = create_format("#f38ba8")              # Pink/Red for numbers
        func_format = create_format("#89b4fa", "bold")        # Blue for function names
        class_format = create_format("#f9e2af", "bold")       # Yellow for class names
        decorator_format = create_format("#f5c2e7", "italic") # Light pink for decorators
        
        # 1. Keywords
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield", "async", "await"
        ]
        self.rules.append((r'\b(%s)\b' % '|'.join(keywords), keyword_format))
        
        # 2. Built-in functions
        builtins = ["print", "len", "range", "list", "dict", "set", "str", "int", "float", "bool", "super", "Exception"]
        self.rules.append((r'\b(%s)\b' % '|'.join(builtins), builtin_format))
        
        # 3. Functions and classes
        self.rules.append((r'\bdef\b\s+([a-zA-Z_]\w*)', func_format))
        self.rules.append((r'\bclass\b\s+([a-zA-Z_]\w*)', class_format))
        
        # 4. Numbers and decorators
        self.rules.append((r'\b[0-9]+(\.[0-9]+)?\b', number_format))
        self.rules.append((r'@[a-zA-Z_]\w*', decorator_format))
        
        # 5. Single-line strings and comments
        self.rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        self.rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", string_format))
        self.rules.append((r'#[^\n]*', comment_format))
        
        # Handle Python multi-line strings (Docstrings)
        self.multi_line_format = string_format
        self.tri_single_start = re.compile(r"'''")
        self.tri_single_end = re.compile(r"'''")
        self.tri_double_start = re.compile(r'"""')
        self.tri_double_end = re.compile(r'"""')

    def highlightBlock(self, text):
        """Apply highlighting rules to each line (Block) of text"""
        # Apply base colors
        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)
                
        # Accurate color correction for function and class names (separate from def and class keywords)
        for match in re.finditer(r'\bdef\s+([a-zA-Z_]\w*)', text):
            self.setFormat(match.start(1), match.end(1) - match.start(1), create_format("#89b4fa", "bold"))
        for match in re.finditer(r'\bclass\s+([a-zA-Z_]\w*)', text):
            self.setFormat(match.start(1), match.end(1) - match.start(1), create_format("#f9e2af", "bold"))

        self.setCurrentBlockState(0)
        
        # Handle multi-line string highlighting
        self._apply_multiline(text, self.tri_single_start, self.tri_single_end, 1)
        if self.currentBlockState() == 0:
            self._apply_multiline(text, self.tri_double_start, self.tri_double_end, 2)

    def _apply_multiline(self, text, start_regex, end_regex, state):
        start_index = 0
        if self.previousBlockState() != state:
            match = start_regex.search(text)
            start_index = match.start() if match else -1
                
        while start_index >= 0:
            match_end = end_regex.search(text, start_index + 3)
            if match_end:
                length = match_end.end() - start_index
                self.setFormat(start_index, length, self.multi_line_format)
                match = start_regex.search(text, start_index + length)
                start_index = match.start() if match else -1
            else:
                self.setCurrentBlockState(state)
                self.setFormat(start_index, len(text) - start_index, self.multi_line_format)
                start_index = -1

class WebHighlighter(QSyntaxHighlighter):
    """Highlighter for web family languages (JavaScript, HTML, CSS, JSON)"""
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        
        keyword_format = create_format("#cba6f7", "bold")
        string_format = create_format("#a6e3a1")
        comment_format = create_format("#6c7086", "italic")
        tag_format = create_format("#f38ba8")
        
        keywords = ["function", "const", "let", "var", "if", "else", "return", "class", "import", "from", "export", "default", "null", "undefined", "true", "false", "await", "async", "new"]
        self.rules.append((r'\b(%s)\b' % '|'.join(keywords), keyword_format))
        
        # HTML tags
        self.rules.append((r'</?\w+', tag_format))
        self.rules.append((r'>', tag_format))
        
        # Strings
        self.rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        self.rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", string_format))
        self.rules.append((r'`[^`\\]*(\\.[^`\\]*)*`', string_format))
        
        # Comments
        self.rules.append((r'//[^\n]*', comment_format))
        self.rules.append((r'<!--[^\n]*', comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


def get_highlighter_for_file(file_path):
    """
    Factory function that checks the file type and returns the appropriate highlighter.
    This function is directly called by TabManager.
    """
    if not file_path:
        return PythonHighlighter
        
    ext = file_path.split('.')[-1].lower()
    
    if ext in ['py', 'pyw']:
        return PythonHighlighter
    elif ext in ['js', 'ts', 'jsx', 'tsx', 'html', 'htm', 'css', 'json', 'vue']:
        return WebHighlighter
        
    return PythonHighlighter