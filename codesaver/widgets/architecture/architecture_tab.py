# -*- coding: utf-8 -*-
# codesaver/widgets/architecture/architecture_tab.py

import os
import sys
import json
import subprocess
from PySide6.QtWidgets import QWidget, QPushButton, QFileDialog
from PySide6.QtCore import QUrl, QFileSystemWatcher, QTimer, Signal
from PySide6.QtWebChannel import QWebChannel

from ...core.graph_analyzer import GraphWorker
from ...core.theme_manager import ThemeColors
from .arch_bridge import Bridge
from .arch_dashboard import HealthDashboard
from .arch_exporter import ArchitectureExporter
from .ui_builder import ArchUIBuilder

def get_template_path():
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, "templates", "graph_template.html")

class ArchitectureTab(QWidget):
    open_file_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        
        self.is_rendered = False
        self.health_data = None
        self.git_commits = []
        self.graph_nodes = []
        self.graph_links = []
        self.project_root = None
        self.ext_buttons = {}
        self.live_watch_enabled = False
        
        # رنگ‌بندی پسوندهای زبان‌ها
        self.extensions_pool = {
            '.py': ('Python', '#9b59b6'), '.js': ('JavaScript', '#f1c40f'), 
            '.tsx': ('React (tsx)', '#2980b9'), '.jsx': ('React (jsx)', '#f39c12'), 
            '.ts': ('TypeScript', '#3498db'), '.vue': ('Vue', '#1abc9c'), 
            '.css': ('CSS', '#e056fd'), '.html': ('HTML', '#2ecc71'),
            '.java': ('Java', '#e74c3c'), '.cs': ('C#', '#16a085'), 
            '.cpp': ('C/C++', '#34495e'), '.php': ('PHP', '#8e44ad'), 
            '.go': ('Go', '#00cec9'), '.rs': ('Rust', '#d35400'),
            '.swift': ('Swift', '#ff7f50'), '.kt': ('Kotlin', '#7f8c8d'),
            '.json': ('JSON', '#e67e22'), '.yaml': ('YAML', '#f39c12'), 
            '.md': ('Markdown', '#bdc3c7'), '.sql': ('SQL', '#d35400'), 
            '.sh': ('Shell', '#2c3e50')
        }

        # ساخت رابط کاربری ایزوله شده
        ui_builder = ArchUIBuilder(self)
        ui_builder.build_ui()
        
        self.open_file_requested.connect(self._open_file_in_editor)
        
        # File Watcher
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.on_file_changed)
        self.watcher.fileChanged.connect(self.on_file_changed)
        
        # Timers
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.animate_loading)
        self.dot_count = 0
        
        self._connect_signals()
        self._setup_web_bridge()
        self.load_static_template()

    def _connect_signals(self):
        self.search_input.textChanged.connect(self.search_graph)
        self.btn_watch.toggled.connect(self.toggle_watch)
        self.btn_health.clicked.connect(self.show_health)
        self.btn_draw.clicked.connect(lambda: self.start_analysis(None))
        self.btn_export_md.clicked.connect(lambda: ArchitectureExporter.export_to_md(
            self, self.graph_nodes, self.graph_links, self.health_data
        ))
        
        self.git_slider.valueChanged.connect(self.on_timeline_scrub)
        self.git_slider.sliderReleased.connect(self.on_timeline_select)
        self.browser.page().profile().downloadRequested.connect(self.handle_download)

    def _setup_web_bridge(self):
        self.channel = QWebChannel()
        self.bridge = Bridge(self)
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

    def load_static_template(self):
        try:
            template_path = get_template_path()
            with open(template_path, 'r', encoding='utf-8') as f:
                html = f.read()

            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            vis_js_url = QUrl.fromLocalFile(os.path.join(base_path, "templates", "assets", "vis-network.min.js")).toString()

            html = html.replace("__LANG__", "en") \
                       .replace("__DIR_STR__", "ltr") \
                       .replace("__ALIGN_STR__", "left") \
                       .replace("__ALIGN_OPPOSITE__", "right") \
                       .replace("__MAP_TITLE__", "🗺️ Project Radar") \
                       .replace("__VIS_JS_PATH__", vis_js_url)

            self.browser.setHtml(html, baseUrl=QUrl.fromLocalFile(os.path.dirname(template_path)))
        except Exception as e:
            self.log_console.append(f"Failed to load HTML template: {str(e)}")

    def _open_file_in_editor(self, rel_path):
        if not self.project_root: return
        abs_path = os.path.normpath(os.path.join(self.project_root, rel_path))
        main_win = self.main_window
        if hasattr(main_win, 'tab_mgr'):
            main_win.tab_mgr.open_file_in_tab(abs_path)
            if hasattr(main_win, 'right_tabs'):
                main_win.right_tabs.setCurrentIndex(0)
        
    def set_project_root(self, path):
        self.project_root = path
        if path and os.path.exists(path):
            self.check_git_repo(path)
            self.start_analysis(None)
        else:
            self.browser.page().runJavaScript(f"document.body.innerHTML = \"<h2 style='color: {ThemeColors.TEXT_MUTED}; text-align: center; margin-top: 50px; font-family: Tahoma;'>No project loaded for Architecture Map.</h2>\";")
            self.git_frame.setVisible(False)
            self.log_console.clear()

    def handle_download(self, download_item):
        suggested_name = download_item.downloadFileName()
        default_path = os.path.join(os.path.expanduser('~'), 'Downloads', suggested_name)
        path, _ = QFileDialog.getSaveFileName(self, "Save File", default_path)
        if path:
            download_item.setDownloadDirectory(os.path.dirname(path))
            download_item.setDownloadFileName(os.path.basename(path))
            download_item.accept()
            self.append_log(f"✅ File successfully saved:\n{path}")
        else:
            download_item.cancel()

    def append_log(self, msg): 
        self.log_console.append(msg)

    def animate_loading(self):
        self.dot_count = (self.dot_count + 1) % 4
        self.loading_label.setText("⏳ Processing and rendering graph" + "." * self.dot_count)

    def check_git_repo(self, path):
        if os.path.exists(os.path.join(path, '.git')):
            try:
                result = subprocess.run(['git', 'log', '--pretty=format:%h|%ad|%s', '--date=short'], cwd=path, capture_output=True, text=True, check=True)
                lines = result.stdout.strip().split('\n')
                self.git_commits = []
                for line in reversed(lines):
                    parts = line.split('|', 2)
                    if len(parts) == 3: self.git_commits.append({"hash": parts[0], "date": parts[1], "msg": parts[2]})
                
                if self.git_commits:
                    self.git_frame.setVisible(True)
                    self.git_slider.setEnabled(True)
                    self.git_slider.setMaximum(len(self.git_commits)) 
                    self.git_slider.setValue(len(self.git_commits))
                    self.git_info.setText("Current System State (Live)")
            except:
                self.git_frame.setVisible(False)
        else:
            self.git_frame.setVisible(False)

    def rebuild_dynamic_filters(self, detected_exts):
        while self.filters_layout.count():
            item = self.filters_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
            
        self.ext_buttons.clear()
        
        for ext in sorted(detected_exts):
            if ext in self.extensions_pool:
                name, color = self.extensions_pool[ext]
                btn = QPushButton(name)
                btn.setCheckable(True)
                btn.setChecked(True)
                btn.setStyleSheet(f"QPushButton {{ background: transparent; border: 1px solid {color}; border-radius: 12px; padding: 4px 10px; color: {color}; font-size: 11px; font-family: Tahoma;}} QPushButton:checked {{ background: {color}; color: white; border: none; font-weight: bold;}}")
                btn.toggled.connect(self.apply_filters)
                self.ext_buttons[ext] = btn
                self.filters_layout.addWidget(btn)
                
        self.filters_layout.addStretch()

    def on_timeline_scrub(self, index):
        if index == len(self.git_commits): 
            self.git_info.setText("Current System State (Live)")
        else:
            c = self.git_commits[index]
            self.git_info.setText(f"{c['date']} - {c['msg']} ({c['hash']})")

    def on_timeline_select(self):
        index = self.git_slider.value()
        if index == len(self.git_commits): self.start_analysis(None)
        else: self.start_analysis(self.git_commits[index]['hash'])

    def toggle_watch(self, checked):
        self.live_watch_enabled = checked
        self.btn_watch.setText("🟢 Live (On)" if checked else "🔴 Live (Off)")

    def on_file_changed(self, path):
        if self.live_watch_enabled and self.btn_draw.isEnabled():
            QTimer.singleShot(500, lambda: self.start_analysis(None))

    def show_health(self):
        if not self.health_data: return
        dialog = HealthDashboard(self.health_data, self)
        dialog.exec()

    def apply_filters(self):
        if not self.is_rendered: return
        active_exts = [ext for ext, btn in self.ext_buttons.items() if btn.isChecked()]
        if '.html' in active_exts: active_exts.extend(['.htm', '.json'])
        if '.yaml' in active_exts: active_exts.append('.yml')
        ext_str = ",".join(active_exts)
        self.browser.page().runJavaScript(f"if(window.filterNodes) window.filterNodes('{ext_str}');")

    def start_analysis(self, commit_hash=None):
        if not self.project_root or not os.path.exists(self.project_root): return
        
        self.log_console.clear()
        self.btn_draw.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.loading_label.setVisible(True)
        self.loading_timer.start(500)
        
        if self.watcher.directories(): self.watcher.removePaths(self.watcher.directories())
        
        self.worker = GraphWorker(self.project_root, self.extensions_pool, commit_hash)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.log_msg.connect(self.append_log)
        self.worker.start()

    def on_finished(self, data):
        self.btn_draw.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.loading_timer.stop()
        
        if "error" in data:
            self.browser.page().runJavaScript(f"document.body.innerHTML = \"{data['error']}\";")
            return
            
        self.loading_label.setText("✅ Graph processing completed.")
        QTimer.singleShot(3000, lambda: self.loading_label.setVisible(False))
        
        self.health_data = data["health"]
        self.graph_nodes = data.get("nodes", [])
        self.graph_links = data.get("links", [])
        
        self.rebuild_dynamic_filters(data["detected_exts"])
        
        if not getattr(self.worker, 'commit_hash', None):
            for d in self.health_data['watched_dirs']: self.watcher.addPath(d)
        
        nodes_json = json.dumps(self.graph_nodes)
        links_json = json.dumps(self.graph_links)
        exts_json = json.dumps(list(self.extensions_pool.keys()) + ['.htm', '.yml'])
        
        js_code = f"window.updateGraphData({nodes_json}, {links_json}, {exts_json});"
        self.browser.page().runJavaScript(js_code)
        
        self.is_rendered = True
        QTimer.singleShot(1000, self.apply_filters)

    def search_graph(self, text):
        if not self.is_rendered or len(text) < 2: return
        self.browser.page().runJavaScript(f"if(window.searchNode) window.searchNode('{text}');")