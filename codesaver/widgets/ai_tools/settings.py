# codesaver/widgets/ai_tools/settings.py
import os
import json
import base64
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QComboBox, QPushButton, QHBoxLayout, QLabel,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, 
                               QInputDialog, QMessageBox)
from PySide6.QtCore import QSettings, Qt, QUrl, QObject, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

def get_colored_icon(icon_name, color_hex="#cdd6f4"):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    icon_dir = os.path.join(base_dir, "codesaver_icons")
    filepath = os.path.join(icon_dir, icon_name)
    
    if not os.path.exists(filepath):
        return QIcon()
    
    icon = QIcon(filepath)
    new_icon = QIcon()
    for size in [16, 24, 32]:
        pixmap = icon.pixmap(size, size)
        if not pixmap.isNull():
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color_hex))
            painter.end()
            new_icon.addPixmap(pixmap)
            
    return new_icon if not new_icon.isNull() else icon


def cipher_api_key(data: str, decrypt=False) -> str:
    if not data: return data
    secret_key = "IDE_Master_Secure_Key_2026"
    try:
        if decrypt:
            data = base64.b64decode(data.encode('utf-8')).decode('utf-8')
        result = "".join([chr(ord(c) ^ ord(secret_key[i % len(secret_key)])) for i, c in enumerate(data)])
        if not decrypt:
            result = base64.b64encode(result.encode('utf-8')).decode('utf-8')
        return result
    except Exception:
        return data


class IconFetcher(QObject):
    icon_ready = Signal(str, QIcon)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.on_finished)
        self.reply_to_provider = {}

    def fetch(self, provider_name, url_str):
        if not url_str: return
        req = QNetworkRequest(QUrl(url_str))
        req.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        reply = self.manager.get(req)
        self.reply_to_provider[reply] = provider_name

    def on_finished(self, reply: QNetworkReply):
        provider = self.reply_to_provider.pop(reply, None)
        if provider and reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                self.icon_ready.emit(provider, QIcon(pixmap))
        reply.deleteLater()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Management")
        self.setMinimumWidth(650)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            
        self.settings = QSettings("GitiArts", "CodeSaver_AI")
        self.theme_settings = QSettings("GitiArts", "CodeSaver_Theme")
        self.saved_keys = {}
        
        self.providers = {
            "Google Gemini (Official)": {
                "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-8b"],
                "icon_url": "https://www.gstatic.com/lamda/images/gemini_favicon_f069958c85030456e93de685481c559f160ea06b.png"
            },
            "OpenAI (ChatGPT)": {
                "url": "https://api.openai.com/v1",
                "models": ["gpt-4o-mini", "gpt-4o", "o3-mini", "o1-mini"],
                "icon_url": "https://openai.com/favicon.ico"
            },
            "DeepSeek (Code Expert)": {
                "url": "https://api.deepseek.com/v1",
                "models": ["deepseek-coder", "deepseek-reasoner", "deepseek-chat"],
                "icon_url": "https://chat.deepseek.com/favicon.ico"
            },
            "Anthropic & Meta (via OpenRouter)": {
                "url": "https://openrouter.ai/api/v1",
                "models": ["anthropic/claude-3.7-sonnet", "anthropic/claude-3.5-sonnet", "meta-llama/llama-3.3-70b-instruct"],
                "icon_url": "https://openrouter.ai/favicon.ico"
            },
            "Groq (Ultra Fast Inference)": {
                "url": "https://api.groq.com/openai/v1",
                "models": ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
                "icon_url": "https://groq.com/favicon.ico"
            },
            "Mistral AI (Codestral)": {
                "url": "https://api.mistral.ai/v1",
                "models": ["codestral-latest", "mistral-large-latest"],
                "icon_url": "https://mistral.ai/favicon.ico"
            },
            "LM Studio / Ollama (Local Server)": {
                "url": "http://localhost:1234/v1",
                "models": ["local-model"],
                "icon_url": ""
            },
            "Custom Proxy": {
                "url": "",
                "models": ["gpt-4o-mini", "gpt-3.5-turbo"],
                "icon_url": ""
            }
        }

        self.fetcher = IconFetcher(self)
        self.fetcher.icon_ready.connect(self.update_combo_icon)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        icon_color = self.theme_settings.value("icon_color", "#89b4fa")
        
        layout.addWidget(QLabel("Saved Keys List:"))
        self.table_keys = QTableWidget(0, 2)
        self.table_keys.setHorizontalHeaderLabels(["Key Name", "Value (Hidden)"])
        self.table_keys.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_keys.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table_keys)

        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton()
        self.btn_add.setToolTip("Add New Key")
        self.btn_add.setIcon(get_colored_icon("pref_add.svg", icon_color))
        self.btn_add.setIconSize(QSize(18, 18))
        self.btn_add.setFixedSize(30, 30)
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self.add_key_ui)
        
        self.btn_edit = QPushButton()
        self.btn_edit.setToolTip("Edit Key")
        self.btn_edit.setIcon(get_colored_icon("pref_edit.svg", icon_color))
        self.btn_edit.setIconSize(QSize(18, 18))
        self.btn_edit.setFixedSize(30, 30)
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit.clicked.connect(self.edit_selected_key)
        
        self.btn_del = QPushButton()
        self.btn_del.setToolTip("Delete Key")
        self.btn_del.setIcon(get_colored_icon("action_delete.svg", "#f38ba8"))
        self.btn_del.setIconSize(QSize(18, 18))
        self.btn_del.setFixedSize(30, 30)
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.clicked.connect(self.delete_selected_key)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        form = QFormLayout()
        form.setContentsMargins(0, 15, 0, 10)
        
        self.combo_active_key = QComboBox()
        self.combo_active_key.setToolTip("The key you want to use right now")
        form.addRow("Active Key (API Key):", self.combo_active_key)

        self.combo_provider = QComboBox()
        self.combo_provider.setIconSize(QSize(24, 24))
        for name, data in self.providers.items():
            self.combo_provider.addItem(name)
            if data["icon_url"]:
                self.fetcher.fetch(name, data["icon_url"])
        self.combo_provider.currentTextChanged.connect(self.on_provider_changed)
        form.addRow("Provider:", self.combo_provider)

        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("Example: https://api.openai.com/v1")
        form.addRow("Server Address (Base URL):", self.input_url)

        self.combo_model = QComboBox()
        self.combo_model.setEditable(True) 
        form.addRow("Model Name:", self.combo_model)

        layout.addLayout(form)

        action_layout = QHBoxLayout()
        btn_save = QPushButton(" Save & Connect")
        btn_save.setIcon(get_colored_icon("apply_&_save.svg", "#11111b"))
        btn_save.setIconSize(QSize(18, 18))
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_save.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        
        btn_cancel = QPushButton(" Cancel")
        btn_cancel.setIcon(get_colored_icon("cancel.svg", "#11111b"))
        btn_cancel.setIconSize(QSize(18, 18))
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 8px; border-radius: 4px;")
        
        action_layout.addWidget(btn_cancel)
        action_layout.addWidget(btn_save)
        layout.addLayout(action_layout)

        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Tahoma', 'IRANSans', sans-serif; font-size: 13px; }
            QLabel { color: #cdd6f4; }
            QLineEdit, QComboBox { background-color: #11111b; color: #cdd6f4; padding: 6px; border: 1px solid #45475a; border-radius: 4px; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #89b4fa; }
            QComboBox::drop-down { border-left: 1px solid #45475a; }
            QTableWidget { background-color: #11111b; border: 1px solid #45475a; color: #cdd6f4; border-radius: 4px; }
            QHeaderView::section { background-color: #313244; color: #cdd6f4; border: none; border-bottom: 1px solid #45475a; padding: 4px; font-weight: bold; }
            QTableWidget::item:selected { background-color: #89b4fa; color: #11111b; }
            QPushButton { background-color: #313244; color: #cdd6f4; border-radius: 4px; padding: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #45475a; }
        """)

    def update_combo_icon(self, provider_name, icon):
        idx = self.combo_provider.findText(provider_name)
        if idx >= 0:
            self.combo_provider.setItemIcon(idx, icon)

    def on_provider_changed(self, provider_name):
        data = self.providers.get(provider_name, {})
        url = data.get("url", "")
        
        if provider_name == "Custom Proxy":
            self.input_url.setReadOnly(False)
            self.input_url.setStyleSheet("background-color: #11111b; color: #cdd6f4; border: 1px solid #89b4fa; border-radius: 4px;")
        else:
            self.input_url.setText(url)
            self.input_url.setReadOnly(True)
            self.input_url.setStyleSheet("background-color: #313244; color: #a6adc8; border: 1px solid #45475a; border-radius: 4px;")
            
        self.combo_model.clear()
        self.combo_model.addItems(data.get("models", []))

    def load_settings(self):
        keys_json = self.settings.value("saved_api_keys", "{}")
        try:
            raw_keys = json.loads(keys_json)
            self.saved_keys = {k: cipher_api_key(v, decrypt=True) for k, v in raw_keys.items()}
        except:
            self.saved_keys = {}
            
        self.refresh_table()
        
        active_key_name = self.settings.value("current_api_key_name", "")
        if active_key_name in self.saved_keys:
            self.combo_active_key.setCurrentText(active_key_name)

        prov = self.settings.value("provider", "Google Gemini (Official)")
        if prov in self.providers:
            self.combo_provider.setCurrentText(prov)
        else:
            self.combo_provider.setCurrentIndex(0)
            
        self.on_provider_changed(self.combo_provider.currentText()) 
        
        saved_url = self.settings.value("base_url", "")
        if saved_url:
            self.input_url.setText(saved_url)
            
        saved_model = self.settings.value("model_name", "")
        if saved_model == "gemma2-9b-it":
            saved_model = "llama-3.1-8b-instant"
            
        if saved_model:
            self.combo_model.setCurrentText(saved_model)

    def refresh_table(self):
        current_active = self.combo_active_key.currentText()
        self.table_keys.setRowCount(0)
        self.combo_active_key.clear()
        
        for name, value in self.saved_keys.items():
            row = self.table_keys.rowCount()
            self.table_keys.insertRow(row)
            
            item_name = QTableWidgetItem(name)
            item_val = QTableWidgetItem("*****************")
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_val.setFlags(item_val.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.table_keys.setItem(row, 0, item_name)
            self.table_keys.setItem(row, 1, item_val)
            self.combo_active_key.addItem(name)
            
        if current_active in self.saved_keys:
            self.combo_active_key.setCurrentText(current_active)

    def add_key_ui(self):
        name, ok1 = QInputDialog.getText(self, "Key Name", "Enter a custom name:")
        if ok1 and name.strip():
            name = name.strip()
            if name in self.saved_keys:
                QMessageBox.warning(self, "Error", "This name is already registered in your list.")
                return
                
            key_val, ok2 = QInputDialog.getText(self, "Key Value", f"Enter the API code for '{name}':")
            if ok2 and key_val.strip():
                self.saved_keys[name] = key_val.strip()
                self.refresh_table()
                self.combo_active_key.setCurrentText(name)

    def edit_selected_key(self):
        selected = self.table_keys.currentRow()
        if selected >= 0:
            name = self.table_keys.item(selected, 0).text()
            current_val = self.saved_keys.get(name, "")
            
            val, ok = QInputDialog.getText(self, "Edit", f"New value for '{name}':", text=current_val)
            if ok and val.strip():
                self.saved_keys[name] = val.strip()
                self.refresh_table()
        else:
            QMessageBox.information(self, "Notice", "Please select a key from the table first.")

    def delete_selected_key(self):
        selected = self.table_keys.currentRow()
        if selected >= 0:
            name = self.table_keys.item(selected, 0).text()
            reply = QMessageBox.question(self, "Delete Key", f"Are you sure you want to delete the key '{name}'?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.saved_keys[name]
                self.refresh_table()
        else:
            QMessageBox.information(self, "Notice", "Please select a key from the table first.")

    def save_and_close(self):
        encrypted_keys = {k: cipher_api_key(v, decrypt=False) for k, v in self.saved_keys.items()}
        self.settings.setValue("saved_api_keys", json.dumps(encrypted_keys))
        self.settings.setValue("provider", self.combo_provider.currentText())
        self.settings.setValue("base_url", self.input_url.text().strip())
        self.settings.setValue("model_name", self.combo_model.currentText().strip())
        self.settings.setValue("current_api_key_name", self.combo_active_key.currentText())
        self.accept()

    def get_all_settings(self):
        keys_json = self.settings.value("saved_api_keys", "{}")
        try:
            raw_keys = json.loads(keys_json)
            keys = {k: cipher_api_key(v, decrypt=True) for k, v in raw_keys.items()}
        except:
            keys = {}
            
        current_key_name = self.settings.value("current_api_key_name", "")
        api_key_value = keys.get(current_key_name, "")
        saved_model = self.settings.value("model_name", "gemini-2.5-flash")
        
        if saved_model == "gemma2-9b-it":
            saved_model = "llama-3.1-8b-instant"
        
        return {
            "base_url": self.settings.value("base_url", "https://generativelanguage.googleapis.com/v1beta/openai/"),
            "model_name": saved_model,
            "api_key": api_key_value
        }