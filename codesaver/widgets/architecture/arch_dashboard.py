# -*- coding: utf-8 -*-
# codesaver/widgets/arch_dashboard.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
from PySide6.QtCore import Qt

from ...core.theme_manager import ThemeColors

class HealthDashboard(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Architecture Health Dashboard")
        self.setFixedSize(500, 480)
        
        layout = QVBoxLayout(self)
        score_color = ThemeColors.SUCCESS if data['score'] > 80 else ThemeColors.WARNING if data['score'] > 50 else ThemeColors.ERROR
        
        lbl_score = QLabel(f"Health Score: {data['score']} / 100")
        lbl_score.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {score_color}; text-align: center; margin-bottom: 10px;")
        lbl_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_score)

        cycles_html = ""
        if data.get('cycle_paths'):
            cycles_html = f"<br><b style='color:{ThemeColors.ERROR}; font-size:15px;'>🔴 Circular Dependencies (Import Loops):</b>"
            cycles_html += f"<div style='color:{ThemeColors.TEXT_MUTED}; font-size:11px; margin-bottom:5px;'>Tip: To fix, move shared dependencies to a common helper file or import locally inside functions.</div>"
            cycles_html += f"<ul style='margin-top: 5px; color:{ThemeColors.ERROR}; font-size:12px; background:{ThemeColors.BG_INPUT}; padding:10px 10px 10px 25px; border: 1px solid {ThemeColors.BORDER_DEFAULT}; border-radius:6px;'>"
            for cp in data['cycle_paths']:
                cycles_html += f"<li style='margin-bottom: 8px; word-wrap: break-word;'>{cp}</li>"
            cycles_html += "</ul>"
        else:
            cycles_html = f"<br><span style='color:{ThemeColors.SUCCESS};'>✅ No circular dependencies detected!</span><br><br>"
        
        info_html = f"""
        <div style='line-height: 1.8; font-size: 14px;'>
            <div>📁 Total Project Files: <b style='color:{ThemeColors.ACCENT_BLUE};'>{data['total_files']}</b></div>
            <div>🔄 Buggy Cycles: <b style='color:{ThemeColors.ERROR};'>{data['cycles_count']}</b></div>
            {cycles_html}
            <div>💀 Dead (Isolated) Code: <b style='color:#a371f7;'>{data['isolated_count']}</b></div>
            <hr style='border:1px solid {ThemeColors.BORDER_DEFAULT};'>
            <b>Top 5 Sensitive/Hub Files:</b><br>
            <span style='color:{ThemeColors.WARNING};'>{', '.join(data['top_hubs']) if data['top_hubs'] else 'None'}</span>
        </div>
        """
            
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_info = QLabel(info_html)
        lbl_info.setWordWrap(True)
        content_layout.addWidget(lbl_info)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)