# codesaver/widgets/ai_tools/chat_bubbles.py
import os
import sys
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QLabel, QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QRectF, QTimer, QSettings, QSize, QByteArray
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QPixmap, QIcon

from .highlighter import PythonHighlighter
from .chat_inputs import ClickableImageLabel, ImageViewerDialog

def get_colored_icon(icon_name, color_hex="#cdd6f4"):
    try:
        if hasattr(sys, '_MEIPASS'):
            icon_dir = os.path.join(sys._MEIPASS, "codesaver_icons")
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_dir = os.path.join(base_dir, "codesaver_icons")
            
        icon_path = os.path.join(icon_dir, icon_name)
        if not os.path.exists(icon_path):
            return QIcon()
            
        with open(icon_path, 'r', encoding='utf-8') as f:
            svg_data = f.read()
            
        svg_data = re.sub(r'fill="[^"]+"', f'fill="{color_hex}"', svg_data)
        svg_data = re.sub(r'stroke="[^"]+"', f'stroke="{color_hex}"', svg_data)
        
        ba = QByteArray(svg_data.encode('utf-8'))
        pixmap = QPixmap()
        pixmap.loadFromData(ba, "SVG")
        return QIcon(pixmap)
    except Exception:
        return QIcon()


class ChatTextBrowser(QTextEdit):
    def __init__(self, text):
        super().__init__()
        self.setFrameStyle(0)
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px; color: #e0e0e0; font-size: 15px;")
        self.setMarkdown(text)
        self.document().documentLayout().documentSizeChanged.connect(self.adjust_size)

    def adjust_size(self):
        size = self.document().size().toSize()
        self.setFixedHeight(int(size.height()) + 10)


class BubbleFrame(QFrame):
    def __init__(self, is_user=False):
        super().__init__()
        self.is_user = is_user
        self.bg_color = QColor("#313244") if is_user else QColor("#1e1e2e")
        self.border_color = QColor("#313244") if is_user else QColor("#45475a")
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        tail_width = 10
        radius = 16

        if self.is_user:
            bubble_rect = QRectF(rect.x(), rect.y(), rect.width() - tail_width, rect.height())
            path.addRoundedRect(bubble_rect, radius, radius)
            tail = QPainterPath()
            tail.moveTo(bubble_rect.right() - 1, bubble_rect.bottom() - radius - 2)
            tail.lineTo(rect.right(), rect.bottom())
            tail.lineTo(bubble_rect.right() - radius + 5, bubble_rect.bottom() - 1)
            tail.closeSubpath()
            path = path.united(tail)
        else:
            bubble_rect = QRectF(rect.x() + tail_width, rect.y(), rect.width() - tail_width, rect.height())
            path.addRoundedRect(bubble_rect, radius, radius)
            tail = QPainterPath()
            tail.moveTo(bubble_rect.left() + 1, bubble_rect.bottom() - radius - 2)
            tail.lineTo(rect.left(), rect.bottom())
            tail.lineTo(bubble_rect.left() + radius - 5, bubble_rect.bottom() - 1)
            tail.closeSubpath()
            path = path.united(tail)

        painter.setBrush(self.bg_color)
        painter.setPen(QPen(self.border_color, 1)) if not self.is_user else painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)


class LoadingBubble(QWidget):
    def __init__(self, parent_width=400):
        super().__init__()
        theme = QSettings("GitiArts", "CodeSaver_Theme")
        self.icon_color = theme.value("icon_color", "#89b4fa")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.bubble_frame = BubbleFrame(is_user=False)
        self.bubble_frame.setMaximumWidth(int(parent_width * 0.95))
        
        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(25, 12, 15, 12)
        
        header_layout = QHBoxLayout()
        avatar_lbl = QLabel()
        avatar_lbl.setPixmap(get_colored_icon("ai_avatar.svg", self.icon_color).pixmap(18, 18))
        
        self.base_text = "Processing"
        self.status_label = QLabel(self.base_text)
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 14px; font-weight: bold; font-style: italic;")
        
        header_layout.addWidget(avatar_lbl)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        
        bubble_layout.addLayout(header_layout)
        
        main_layout.addStretch()
        main_layout.addWidget(self.bubble_frame)

        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(400)

    def update_animation(self):
        self.dots = (self.dots + 1) % 4
        self.status_label.setText(self.base_text + " " + "." * self.dots)

    def set_text(self, text):
        self.base_text = text
        self.update_animation()


class MessageBubble(QWidget):
    inject_requested = Signal(str)

    def __init__(self, text, is_user=False, parent_width=400, images=None):
        super().__init__()
        theme = QSettings("GitiArts", "CodeSaver_Theme")
        self.icon_color = theme.value("icon_color", "#89b4fa")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.bubble_frame = BubbleFrame(is_user)
        self.bubble_frame.setMaximumWidth(int(parent_width * 0.95))
        
        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(15, 12, 25, 12) if is_user else bubble_layout.setContentsMargins(25, 12, 15, 12)
        bubble_layout.setSpacing(10)
        
        sender_layout = QHBoxLayout()
        avatar_lbl = QLabel()
        if is_user:
            avatar_lbl.setPixmap(get_colored_icon("ai_user_avatar.svg", "#a6adc8").pixmap(18, 18))
            name_lbl = QLabel("You")
        else:
            avatar_lbl.setPixmap(get_colored_icon("ai_avatar.svg", self.icon_color).pixmap(18, 18))
            name_lbl = QLabel("AI Assistant")
            
        name_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #a6adc8;")
        sender_layout.addWidget(avatar_lbl)
        sender_layout.addWidget(name_lbl)
        sender_layout.addStretch()
        bubble_layout.addLayout(sender_layout)
        
        if is_user:
            if text.strip():
                tb = ChatTextBrowser(text)
                tb.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                bubble_layout.addWidget(tb)
            
            if images:
                img_container = QWidget()
                img_lay = QHBoxLayout(img_container)
                img_lay.setContentsMargins(0, 5, 0, 0)
                img_lay.setAlignment(Qt.AlignmentFlag.AlignRight)
                for img in images:
                    lbl = ClickableImageLabel(img)
                    pix = QPixmap.fromImage(img).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    lbl.setPixmap(pix)
                    lbl.setStyleSheet("border-radius: 6px; border: 1px solid #45475a;")
                    lbl.clicked.connect(self.show_fullscreen_image)
                    img_lay.addWidget(lbl)
                bubble_layout.addWidget(img_container)
                
            main_layout.addWidget(self.bubble_frame)
            main_layout.addStretch()
        else:
            self._render_mixed_content(text, bubble_layout)
            main_layout.addStretch()
            main_layout.addWidget(self.bubble_frame)

    def show_fullscreen_image(self, img):
        dialog = ImageViewerDialog(img, parent=self.window())
        dialog.exec()

    def _render_mixed_content(self, text, parent_layout):
        parts = re.split(r'```(.*?)```', text, flags=re.DOTALL)
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part: continue
            
            if i % 2 == 1:
                code_lang = ""
                idx = part.find('\n')
                if idx != -1 and ' ' not in part[:idx]:
                    code_lang = part[:idx].strip()
                    code_text = part[idx+1:].strip()
                else:
                    code_text = part
                
                code_container = QWidget()
                code_layout = QVBoxLayout(code_container)
                code_layout.setContentsMargins(0, 0, 0, 0)
                code_layout.setSpacing(0)
                
                header_container = QWidget()
                header_container.setStyleSheet("background: #181825; border-top-left-radius: 6px; border-top-right-radius: 6px;")
                h_lay = QHBoxLayout(header_container)
                h_lay.setContentsMargins(10, 4, 10, 4)
                
                file_icon_lbl = QLabel()
                file_icon_lbl.setPixmap(get_colored_icon("icon_file_unknown.svg", "#a6adc8").pixmap(16, 16))
                
                header_lbl = QLabel(" " + (code_lang if code_lang else "Code"))
                header_lbl.setStyleSheet("color: #a6adc8; font-size: 13px; font-weight: bold;")
                
                h_lay.addWidget(file_icon_lbl)
                h_lay.addWidget(header_lbl)
                h_lay.addStretch()
                
                inject_btn = QPushButton(" Inject")
                inject_btn.setIcon(get_colored_icon("inject_code.svg", "#11111b"))
                inject_btn.setIconSize(QSize(14, 14))
                inject_btn.setFixedSize(80, 26)
                inject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                inject_btn.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; border-radius: 4px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #94e2d5; }")
                inject_btn.clicked.connect(lambda _, c=code_text: self.inject_requested.emit(c))
                h_lay.addWidget(inject_btn)
                
                code_layout.addWidget(header_container)
                
                editor = QTextEdit()
                editor.setPlainText(code_text)
                editor.setReadOnly(True)
                editor.setStyleSheet("background: #11111b; color: #e0e0e0; border: none; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; font-family: Consolas, Tahoma; font-size: 14px;")
                PythonHighlighter(editor.document())
                
                doc_height = int(editor.document().size().height())
                editor.setFixedHeight(min(doc_height + 25, 400))
                
                code_layout.addWidget(editor)
                parent_layout.addWidget(code_container)
            else:
                tb = ChatTextBrowser(part)
                tb.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                parent_layout.addWidget(tb)