# codesaver/widgets/ai_tools/chat_inputs.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTextEdit, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap


class ImageViewerDialog(QDialog):
    """Dialog window for displaying full-size images"""
    def __init__(self, image: QImage, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Viewer")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setStyleSheet("background-color: #11111b;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel()
        pixmap = QPixmap.fromImage(image)
        
        screen_rect = QApplication.primaryScreen().availableGeometry()
        max_w = screen_rect.width() * 0.8
        max_h = screen_rect.height() * 0.8
        
        if pixmap.width() > max_w or pixmap.height() > max_h:
            pixmap = pixmap.scaled(int(max_w), int(max_h), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


class ClickableImageLabel(QLabel):
    """Image label with click support"""
    clicked = Signal(QImage)

    def __init__(self, image: QImage, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = image
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to enlarge")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image)
        super().mousePressEvent(event)


class ChatInputBox(QTextEdit):
    """Advanced chatbot input box with auto-resize and paste support"""
    return_pressed = Signal()
    image_pasted = Signal(QImage)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.textChanged.connect(self.adjust_height)
        self.min_height = 60
        self.max_height = 300
        self.setFixedHeight(self.min_height)

    def adjust_height(self):
        doc_height = int(self.document().size().height())
        margins = self.contentsMargins()
        target_height = doc_height + margins.top() + margins.bottom() + 15 
        if target_height <= self.min_height:
            self.setFixedHeight(self.min_height)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        elif target_height >= self.max_height:
            self.setFixedHeight(self.max_height)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setFixedHeight(target_height)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.return_pressed.emit()
                event.accept() 
                
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
            clipboard = QApplication.clipboard()
            if clipboard.mimeData().hasImage():
                img = clipboard.image()
                if not img.isNull():
                    self.image_pasted.emit(img)
                    event.accept()
                    return
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)