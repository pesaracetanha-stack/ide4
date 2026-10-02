# -*- coding: utf-8 -*-
# codesaver/widgets/export_worker.py
import os
import json
from PySide6.QtCore import QThread, Signal, QMarginsF
from PySide6.QtGui import (
    QFont, QTextCursor, QTextCharFormat, QTextBlockFormat, 
    QTextFormat, QPageSize, QTextDocument, QTextOption, QPageLayout
)
from PySide6.QtPrintSupport import QPrinter

class ExportWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)

    def __init__(self, dest_dir, tree_diagram, checked_files, root_path, formats):
        super().__init__()
        self.dest_dir = dest_dir
        self.tree_diagram = tree_diagram
        self.checked_files = checked_files
        self.root_path = root_path
        self.formats = formats

    def run(self):
        try:
            if self.formats.get('txt', False):
                self.generate_txt()
            self.progress.emit(33)
            
            if self.formats.get('json', False):
                self.generate_json()
            self.progress.emit(66)
            
            if self.formats.get('pdf', False):
                self.generate_pdf()
            self.progress.emit(100)
            
            self.finished.emit("")
        except Exception as e:
            self.finished.emit(str(e))

    def generate_txt(self):
        path = os.path.join(self.dest_dir, "project_export.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=== Project Tree ===\n")
            f.write(self.tree_diagram)
            f.write("\n\n")
            for file_path in self.checked_files:
                rel_path = os.path.relpath(file_path, self.root_path)
                f.write(f"----- CODE_SAVER_FILE_START: {rel_path} -----\n")
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as src:
                        content = src.read()
                    f.write(content)
                    if not content.endswith("\n"):
                        f.write("\n")
                except Exception as e:
                    f.write(f"# Error reading file: {e}\n")
                f.write(f"----- CODE_SAVER_FILE_END: {rel_path} -----\n")

    def generate_json(self):
        path = os.path.join(self.dest_dir, "project_export.json")
        data = {
            "project_tree": self.tree_diagram,
            "files": []
        }
        for file_path in self.checked_files:
            rel_path = os.path.relpath(file_path, self.root_path)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as src:
                    content = src.read()
                data["files"].append({
                    "path": rel_path,
                    "content": content
                })
            except Exception as e:
                data["files"].append({
                    "path": rel_path,
                    "error": str(e)
                })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def generate_pdf(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(os.path.join(self.dest_dir, "project_export.pdf"))

        page_size = QPageSize(QPageSize.A4)
        margins = QMarginsF(20, 20, 20, 20)
        page_layout = QPageLayout(page_size, QPageLayout.Portrait, margins)
        printer.setPageLayout(page_layout)

        doc = QTextDocument()
        doc.setDefaultFont(QFont("Courier New", 10))
        
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        doc.setDefaultTextOption(text_option)

        page_rect_mm = printer.pageRect(QPrinter.Millimeter)
        text_width_mm = page_rect_mm.width() - margins.left() - margins.right()
        text_width_pixels = text_width_mm * 96 / 25.4
        doc.setTextWidth(text_width_pixels)

        cursor = QTextCursor(doc)
        header_format = QTextCharFormat()
        header_format.setFontFamily("Courier New")
        header_format.setFontPointSize(12)
        header_format.setFontWeight(QFont.Bold)

        mono_format = QTextCharFormat()
        mono_format.setFontFamily("Courier New")
        mono_format.setFontPointSize(10)

        cursor.insertText("Project Tree:\n", header_format)
        cursor.insertText(self.tree_diagram + "\n", mono_format)

        for file_path in self.checked_files:
            rel_path = os.path.relpath(file_path, self.root_path)
            
            block_format = QTextBlockFormat()
            block_format.setPageBreakPolicy(QTextFormat.PageBreak_AlwaysBefore)
            cursor.insertBlock(block_format)

            cursor.insertText(f"File: {rel_path}\n", header_format)
            
            normal_block = QTextBlockFormat()
            cursor.insertBlock(normal_block)
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as src:
                    code = src.read()
            except Exception as e:
                code = f"# Error reading file: {e}"
                
            cursor.insertText(code, mono_format)
            if not code.endswith("\n"):
                cursor.insertText("\n", mono_format)

        doc.print_(printer)