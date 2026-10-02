# -*- coding: utf-8 -*-
# codesaver/widgets/chatbot_panel.py
import os
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QScrollArea, 
                               QApplication, QFileDialog)
from PySide6.QtCore import Signal, Qt, QSize, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage, QPixmap

# Modular imports from new architecture
from .ai_tools.settings import SettingsDialog
from .ai_tools.worker import ApiWorker
from .ai_tools.highlighter import PythonHighlighter
from .ai_tools.chat_inputs import ChatInputBox
from .ai_tools.chat_bubbles import MessageBubble, LoadingBubble, get_colored_icon
from ..core.graphify_engine import GraphifyEngine


def image_to_base64(image: QImage) -> str:
    """Convert image to Base64 format to send to OpenAI server"""
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    image.save(buf, "PNG")
    return ba.toBase64().data().decode("utf-8")


class AIChatbotPanel(QWidget):
    inject_code_requested = Signal(str, str)
    revert_requested = Signal()               
    context_fetch_requested = Signal(dict)    

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mw = parent
        
        self.settings_dialog = SettingsDialog(self)
        self.api_settings = self.settings_dialog.get_all_settings()
        self.loading_bubble = None
        self.pending_images = [] 
        self.sandbox_enabled = False 
        
        self.setup_ui()
        # 🚀 REMOVED: self.apply_theme() is no longer needed! We use ThemeManager centrally.

    def setup_ui(self):
        # 🚀 REMOVED: QSettings Theme retrieval. We use generic icon coloring now.
        # Fallback to white/gray for icons if the global theme dictates it implicitly.
        self.icon_color = "#cdd6f4" 
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        top_layout = QHBoxLayout()
        
        self.btn_settings = QPushButton(" API Settings")
        self.btn_settings.setIcon(get_colored_icon("api_setting.svg", self.icon_color))
        self.btn_settings.setIconSize(QSize(18, 18))
        self.btn_settings.setFixedHeight(30)
        self.btn_settings.clicked.connect(self.open_settings)
        
        self.btn_revert = QPushButton(" Revert Changes")
        self.btn_revert.setIcon(get_colored_icon("revert_ai_action.svg", "#11111b"))
        self.btn_revert.setIconSize(QSize(18, 18))
        self.btn_revert.setFixedHeight(30)
        # 🚀 CHANGED: Removed manual background styling, letting ThemeManager handle the base button,
        # but added a specific class or minimal style if it's an "action/warning" button.
        self.btn_revert.setStyleSheet("background-color: #f38ba8; color: #11111b;") # Kept only core override
        self.btn_revert.clicked.connect(self.on_revert_clicked)
        self.btn_revert.hide()

        top_layout.addWidget(self.btn_settings)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_revert)
        self.layout.addLayout(top_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 🚀 REMOVED: Border removal styles; ThemeManager styles QScrollArea globally.
        self.scroll_content = QWidget()
        self.chat_layout = QVBoxLayout(self.scroll_content)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setContentsMargins(5, 10, 5, 10)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area, stretch=4)

        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout(self.preview_container)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_container.hide()
        self.layout.addWidget(self.preview_container)

        input_layout = QHBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        self.btn_attach = QPushButton("")
        self.btn_attach.setIcon(get_colored_icon("ai_attach_image.svg", self.icon_color))
        self.btn_attach.setIconSize(QSize(24, 24))
        self.btn_attach.setFixedSize(45, 60)
        self.btn_attach.setToolTip("Attach Image")
        # 🚀 REMOVED: Manual background color for attach button
        self.btn_attach.clicked.connect(self.attach_image_dialog)
        input_layout.addWidget(self.btn_attach, alignment=Qt.AlignmentFlag.AlignBottom)
        
        self.input_box = ChatInputBox()
        self.input_box.setPlaceholderText("Type your request or paste an image (Ctrl+V)...")
        self.input_box.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.input_box.return_pressed.connect(self.send_query)
        self.input_box.image_pasted.connect(self.add_image_to_preview) 
        self.highlighter = PythonHighlighter(self.input_box.document())
        input_layout.addWidget(self.input_box)

        self.btn_send = QPushButton("")
        self.btn_send.setIcon(get_colored_icon("send_message.svg", self.icon_color))
        self.btn_send.setIconSize(QSize(28, 28))
        self.btn_send.setFixedHeight(60)
        self.btn_send.setFixedWidth(60)
        self.btn_send.setToolTip("Send Message")
        self.btn_send.clicked.connect(self.send_query)
        input_layout.addWidget(self.btn_send, alignment=Qt.AlignmentFlag.AlignBottom)

        self.layout.addLayout(input_layout)

    def attach_image_dialog(self):
        title = "Select Image"
        paths, _ = QFileDialog.getOpenFileNames(self, title, "", "Images (*.png *.jpg *.jpeg *.bmp)")
        for path in paths:
            img = QImage(path)
            if not img.isNull():
                self.add_image_to_preview(img)

    def add_image_to_preview(self, image: QImage):
        self.pending_images.append(image)
        
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 5, 0)
        
        btn_remove = QPushButton()
        btn_remove.setIcon(get_colored_icon("action_delete.svg", "#11111b"))
        btn_remove.setIconSize(QSize(12, 12))
        btn_remove.setFixedSize(20, 20)
        btn_remove.setToolTip("Remove Image")
        btn_remove.setStyleSheet("background-color: #f38ba8; border-radius: 10px; border: none;") # Kept core override
        btn_remove.clicked.connect(lambda: self.remove_pending_image(container, image))
        
        img_lbl = QLabel()
        pix = QPixmap.fromImage(image).scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        img_lbl.setPixmap(pix)
        img_lbl.setStyleSheet("border-radius: 4px; border: 1px solid #45475a;") # Soft border
        
        lay.addWidget(btn_remove, alignment=Qt.AlignmentFlag.AlignRight)
        lay.addWidget(img_lbl)
        
        self.preview_layout.addWidget(container)
        self.preview_container.show()
        
    def remove_pending_image(self, widget, image):
        if image in self.pending_images:
            self.pending_images.remove(image)
        widget.deleteLater()
        if not self.pending_images:
            self.preview_container.hide()

    # 🚀 REMOVED: apply_theme() completely!

    def open_settings(self):
        if self.settings_dialog.exec():
            self.api_settings = self.settings_dialog.get_all_settings()

    def scroll_to_bottom(self):
        QApplication.processEvents() 
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_chat(self):
        for i in reversed(range(self.chat_layout.count())):
            widget = self.chat_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.pending_images.clear()
        
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.preview_container.hide()
        
        msg_text = "Chat history cleared."
        msg = MessageBubble(msg_text, parent_width=self.scroll_area.width())
        self.chat_layout.addWidget(msg)
        self.scroll_to_bottom()
        
    def toggle_sandbox(self, state):
        self.sandbox_enabled = state
        if state:
            msg = "🛡️ **Sandbox Mode Activated:**\nAI can only suggest code and cannot automatically modify files. You must use the **Inject** button to apply codes."
        else:
            msg = "⚠️ **Sandbox Mode Deactivated:**\nAI can now automatically create or modify files."
            
        bubble = MessageBubble(msg, parent_width=self.scroll_area.width())
        self.chat_layout.addWidget(bubble)
        self.scroll_to_bottom()

    def send_query(self):
        query = self.input_box.toPlainText().strip()
        
        if not query and not self.pending_images: 
            return

        user_bubble = MessageBubble(query, is_user=True, parent_width=self.scroll_area.width(), images=self.pending_images.copy())
        self.chat_layout.addWidget(user_bubble)
        
        self.input_box.clear()
        base64_images = [image_to_base64(img) for img in self.pending_images]
        self.pending_images.clear()
        
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.preview_container.hide()
        
        self.scroll_to_bottom()
        
        p_root = getattr(self.mw, 'project_root', None)
        
        tree = ""
        if hasattr(self.mw, 'project_mgr'):
            tree = self.mw.project_mgr.get_tree_structure()
            
        try:
            graph_engine = GraphifyEngine(p_root)
            graph_data = graph_engine.generate_ai_context()
            if graph_data:
                tree += "\n\n" + graph_data
        except Exception as e:
            err_msg = f"[System Error: Graphify Engine failed to scan the project: {str(e)}]"
            tree += f"\n\n{err_msg}"
            print(err_msg)
            
        active_name = "Unknown"
        active_content = ""
        if hasattr(self.mw, 'current_editor_tab') and self.mw.current_editor_tab and hasattr(self.mw.current_editor_tab, 'editor'):
            active_name = os.path.basename(getattr(self.mw.current_editor_tab, 'file_path', 'Unknown'))
            active_content = self.mw.current_editor_tab.editor.toPlainText()

        self.btn_send.setEnabled(False)
        self.btn_attach.setEnabled(False)
        self.input_box.setEnabled(False)
        
        self.loading_bubble = LoadingBubble(parent_width=self.scroll_area.width())
        self.chat_layout.addWidget(self.loading_bubble)
        self.scroll_to_bottom()

        self.worker = ApiWorker(
            self.api_settings, 
            query, 
            p_root, 
            tree, 
            active_file_name=active_name, 
            active_file_content=active_content, 
            images=base64_images
        )
        self.worker.status_update.connect(self.update_loading_status)
        self.worker.auto_inject_requested.connect(self.execute_auto_inject)
        self.worker.response_received.connect(self.handle_final_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished_task.connect(self.reactivate_input)
        self.worker.start()

    def update_loading_status(self, msg):
        if self.loading_bubble and isinstance(self.loading_bubble, LoadingBubble):
            self.loading_bubble.set_text("⚙️ " + msg)
        self.scroll_to_bottom()

    def execute_auto_inject(self, file_path, new_code):
        if self.sandbox_enabled:
            warn_msg = f"🛡️ Auto-inject prevented in `{file_path}`."
            self.update_loading_status(warn_msg)
            return
            
        self.inject_code_requested.emit(file_path, new_code)
        self.btn_revert.show()

    def handle_final_response(self, text_response):
        if self.loading_bubble:
            self.chat_layout.removeWidget(self.loading_bubble)
            self.loading_bubble.deleteLater()
            self.loading_bubble = None

        ai_bubble = MessageBubble(text_response, parent_width=self.scroll_area.width())
        ai_bubble.inject_requested.connect(self.on_manual_inject_clicked)
        
        self.chat_layout.addWidget(ai_bubble)
        self.scroll_to_bottom()
        
    def on_manual_inject_clicked(self, code_content):
        lines = code_content.split('\n')
        
        target_file = "Unknown"
        if hasattr(self.mw, 'current_editor_tab') and self.mw.current_editor_tab and hasattr(self.mw.current_editor_tab, 'editor'):
            target_file = os.path.basename(getattr(self.mw.current_editor_tab, 'file_path', 'Unknown'))
            
        if not target_file or target_file == "Unknown":
            target_file = "generated_by_ai.py"

        if lines and 'FILE:' in lines[0]:
            match = re.search(r'FILE:\s*([a-zA-Z0-9_/\.\-]+)', lines[0])
            if match:
                target_file = match.group(1).strip()
                code_content = '\n'.join(lines[1:]).strip()

        self.inject_code_requested.emit(target_file, code_content)
        self.btn_revert.show()
        
        success_msg = f"✅ Code successfully injected into `{target_file}`."
        success_bubble = MessageBubble(success_msg, is_user=False, parent_width=self.scroll_area.width())
        self.chat_layout.addWidget(success_bubble)
        self.scroll_to_bottom()

    def handle_error(self, error_msg):
        if self.loading_bubble:
            self.chat_layout.removeWidget(self.loading_bubble)
            self.loading_bubble.deleteLater()
            self.loading_bubble = None
            
        err_bubble = MessageBubble("❌ " + error_msg, parent_width=self.scroll_area.width())
        self.chat_layout.addWidget(err_bubble)
        self.scroll_to_bottom()

    def reactivate_input(self):
        self.btn_send.setEnabled(True)
        self.btn_attach.setEnabled(True)
        self.input_box.setEnabled(True)
        self.input_box.setFocus()

    def on_revert_clicked(self):
        self.revert_requested.emit()
        msg = "⚠️ Changes reverted."
        rev_bubble = MessageBubble(msg, parent_width=self.scroll_area.width())
        self.chat_layout.addWidget(rev_bubble)
        self.scroll_to_bottom()
        self.btn_revert.hide()

    def handle_terminal_error(self, error_message):
        err = f"I encountered this error, please review and fix it:\n\n{error_message}"
        self.input_box.setText(err)
        self.input_box.adjust_height()