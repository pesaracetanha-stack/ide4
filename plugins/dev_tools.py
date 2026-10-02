# plugins/dev_tools.py
import json
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtWidgets import QMessageBox

def register_plugin(main_window):
    # 1. JSON Formatter & Beautifier Tool
    format_json_act = QAction("🧹 JSON Formatter & Beautifier", main_window)
    
    def format_json():
        editor_tab = getattr(main_window, 'current_editor_tab', None)
        if not editor_tab or not hasattr(editor_tab, 'editor'):
            QMessageBox.warning(main_window, "Error", "No file is open for editing!")
            return
        
        editor = editor_tab.editor
        text = editor.toPlainText()
        
        try:
            parsed = json.loads(text)
            formatted = json.dumps(parsed, indent=4, ensure_ascii=False)
            
            cursor = editor.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(formatted)
            cursor.endEditBlock()
            
            QMessageBox.information(main_window, "Success", "JSON code formatted successfully!")
        except Exception as e:
            QMessageBox.critical(main_window, "JSON Error", f"Invalid JSON file!\n{str(e)}")

    format_json_act.triggered.connect(format_json)
    
    # 2. Empty Line Cleaner Tool
    remove_empty_act = QAction("🗑️ Clean Empty Lines", main_window)
    
    def remove_empty_lines():
        editor_tab = getattr(main_window, 'current_editor_tab', None)
        if not editor_tab or not hasattr(editor_tab, 'editor'):
            QMessageBox.warning(main_window, "Error", "No file is open for editing!")
            return
            
        editor = editor_tab.editor
        text = editor.toPlainText()
        
        lines = text.split('\n')
        non_empty = [line for line in lines if line.strip() != ""]
        new_text = '\n'.join(non_empty)
        
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.insertText(new_text)
        cursor.endEditBlock()
        
        QMessageBox.information(main_window, "Success", "Extra empty lines removed!")
        
    remove_empty_act.triggered.connect(remove_empty_lines)
    
    # === Connect to the main centralized menu (fix duplicate menu issue) ===
    if hasattr(main_window, 'plugin_menu'):
        main_window.plugin_menu.addAction(format_json_act)
        main_window.plugin_menu.addAction(remove_empty_act)