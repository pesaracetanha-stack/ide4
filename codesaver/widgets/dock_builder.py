# -*- coding: utf-8 -*-
# codesaver/widgets/dock_builder.py
import sys
from PySide6.QtWidgets import (QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTabWidget, 
                               QDockWidget, QPushButton, QButtonGroup, QStackedWidget, QLabel)
from PySide6.QtCore import Qt, QSize

from .version_history_dock import VersionHistoryDock
from .project_explorer import ProjectExplorer
from .global_search import GlobalSearchOverlay
from .symbol_palette import SymbolPalette
from .terminal_panel import EnhancedTerminalPanel
from .architecture.architecture_tab import ArchitectureTab
from .chatbot_panel import AIChatbotPanel
from .command_palette import CommandPalette
from .git_panel import GitPanel
from .snippet_panel import SnippetPanel
from .plugin_panel import PluginPanel
from .store_panel import StorePanel
from ..core.theme_manager import ThemeIcons, ThemeColors


class ActivityBar(QWidget):
    def __init__(self, position="left", parent=None):
        super().__init__(parent)
        self.setFixedWidth(50)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 10)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.buttons = []
        self.position = position
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

    def add_tool(self, icon_name, tooltip, widget_to_toggle=None, color=ThemeColors.TEXT_MUTED, active_color=ThemeColors.ACCENT_TEAL, custom_callback=None, is_checkable=True):
        btn = QPushButton()
        # 🚀 FIX: Forced color mapping for all icons from the central theme
        btn.setIcon(ThemeIcons.get_icon(icon_name, color))
        btn.setIconSize(QSize(28, 28))
        btn.setToolTip(tooltip)
        btn.setCheckable(is_checkable)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-{self.position}: 3px solid transparent;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.BORDER_ACTIVE};
            }}
            QPushButton:checked {{
                border-{self.position}: 3px solid {active_color};
                background-color: {ThemeColors.BG_BASE};
            }}
        """)
        
        self.layout.addWidget(btn)
        self.buttons.append(btn)
        
        if is_checkable:
            self.button_group.addButton(btn)
            
            def on_click():
                for b in self.buttons:
                    if b != btn and b.isChecked():
                        b.setChecked(False)
            
            btn.clicked.connect(on_click)
            
            def on_toggle(checked):
                if checked:
                    btn.setIcon(ThemeIcons.get_icon(icon_name, active_color))
                    if widget_to_toggle: widget_to_toggle.setVisible(True)
                else:
                    btn.setIcon(ThemeIcons.get_icon(icon_name, color))
                    if widget_to_toggle: widget_to_toggle.setVisible(False)
                    
                if custom_callback:
                    custom_callback(checked)
                    
            btn.toggled.connect(on_toggle)
        else:
            if custom_callback:
                btn.clicked.connect(lambda: custom_callback(False))
                
        return btn


class DockBuilder:
    @staticmethod
    def build_core_layout(mw):
        mw.main_container = QWidget()
        mw.main_layout = QHBoxLayout(mw.main_container)
        mw.main_layout.setContentsMargins(0, 0, 0, 0)
        mw.main_layout.setSpacing(0)
        mw.setCentralWidget(mw.main_container)

        # 1. Left Activity Bar
        mw.left_activity_bar = ActivityBar(position="left", parent=mw)
        mw.main_layout.addWidget(mw.left_activity_bar)

        mw.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        mw.main_layout.addWidget(mw.main_splitter, stretch=1)

        # 2. Left Panel Stack
        mw.left_panel = QStackedWidget()
        mw.main_splitter.addWidget(mw.left_panel)
        
        mw.tree = ProjectExplorer(mw)
        mw.tree.status_message.connect(lambda msg: getattr(mw, 'status_label', None) and mw.status_label.setText(msg))
        mw.left_panel.addWidget(mw.tree)
        
        mw.global_search_overlay = GlobalSearchOverlay(mw)
        mw.global_search_overlay.file_selected.connect(mw._on_global_search_result)
        mw.global_search_overlay.find_next.connect(lambda t, cs: mw._on_global_find_action(t, cs, False))
        mw.global_search_overlay.find_prev.connect(lambda t, cs: mw._on_global_find_action(t, cs, True))
        mw.global_search_overlay.replace_current.connect(mw._on_global_replace_current)
        mw.global_search_overlay.replace_all.connect(mw._on_global_replace_all)
        mw.global_search_overlay.search_updated.connect(mw._update_global_find_count)
        mw.left_panel.addWidget(mw.global_search_overlay)
        
        mw.git_panel = GitPanel(main_window=mw)
        mw.left_panel.addWidget(mw.git_panel)

        mw.snippet_panel = SnippetPanel(main_window=mw)
        mw.left_panel.addWidget(mw.snippet_panel)

        mw.plugin_panel = PluginPanel(main_window=mw)
        mw.left_panel.addWidget(mw.plugin_panel)
        
        mw.store_panel = StorePanel(main_window=mw)
        mw.left_panel.addWidget(mw.store_panel)

        # 3. Center Stack
        mw.center_stack = QStackedWidget()
        mw.main_splitter.addWidget(mw.center_stack)
        
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        mw.address_bar = QLineEdit()
        mw.address_bar.returnPressed.connect(mw.load_from_address_bar)
        editor_layout.addWidget(mw.address_bar)

        mw.symbol_palette = SymbolPalette(mw)
        mw.symbol_palette.setVisible(False)
        mw.symbol_palette.symbol_selected.connect(mw._on_symbol_selected)
        mw.symbol_palette.close_requested.connect(lambda: mw.symbol_palette.setVisible(False))
        editor_layout.addWidget(mw.symbol_palette)

        mw.editor_tab_widget = QTabWidget()
        mw.editor_tab_widget.setTabsClosable(True)
        mw.editor_tab_widget.setDocumentMode(True) 
        editor_layout.addWidget(mw.editor_tab_widget)
        
        mw.center_stack.addWidget(editor_container)

        mw.arch_map = ArchitectureTab(parent=mw)
        mw.center_stack.addWidget(mw.arch_map)

        # 4. Map Left Activity Bar Buttons
        def switch_left_panel(checked, widget):
            if checked:
                mw.left_panel.setCurrentWidget(widget)
                mw.center_stack.setCurrentWidget(editor_container)
            elif not any(b.isChecked() for b in mw.left_activity_bar.buttons if b.isCheckable()):
                mw.center_stack.setCurrentWidget(editor_container)

        def on_arch_toggled(checked):
            if checked:
                mw.center_stack.setCurrentWidget(mw.arch_map)
            else:
                mw.center_stack.setCurrentWidget(editor_container)

        mw.btn_home = mw.left_activity_bar.add_tool("home.svg", "Welcome Screen", is_checkable=False, custom_callback=lambda c: getattr(mw, 'tab_mgr', None) and mw.tab_mgr.add_empty_tab())
        mw.btn_explorer = mw.left_activity_bar.add_tool("toggle_explorer.svg", "File Explorer", widget_to_toggle=mw.left_panel, custom_callback=lambda c: switch_left_panel(c, mw.tree))
        mw.btn_search = mw.left_activity_bar.add_tool("global_search.svg", "Global Search", widget_to_toggle=mw.left_panel, custom_callback=lambda c: switch_left_panel(c, mw.global_search_overlay))
        mw.btn_git = mw.left_activity_bar.add_tool("source_control.svg", "Source Control", widget_to_toggle=mw.left_panel, custom_callback=lambda c: switch_left_panel(c, mw.git_panel))
        mw.btn_snippets = mw.left_activity_bar.add_tool("snippets.svg", "Snippet Manager", widget_to_toggle=mw.left_panel, custom_callback=lambda c: switch_left_panel(c, mw.snippet_panel))
        mw.btn_plugins = mw.left_activity_bar.add_tool("plugins.svg", "Extensions", widget_to_toggle=mw.left_panel, custom_callback=lambda c: switch_left_panel(c, mw.plugin_panel))
        mw.btn_store = mw.left_activity_bar.add_tool("store.svg", "Plugin & API Store", widget_to_toggle=mw.left_panel, custom_callback=lambda c: switch_left_panel(c, mw.store_panel))
        mw.btn_arch = mw.left_activity_bar.add_tool("architecture.svg", "Architecture Map", widget_to_toggle=None, custom_callback=on_arch_toggled)
        
        mw.btn_explorer.setChecked(True)

        # 5. Right Panel Stack
        mw.right_panel = QStackedWidget()
        mw.main_splitter.addWidget(mw.right_panel)
        
        mw.chatbot_panel = AIChatbotPanel(mw)
        mw.right_panel.addWidget(mw.chatbot_panel)
        
        mw.terminal = EnhancedTerminalPanel(project_root=mw.project_root, parent=mw)
        mw.right_panel.addWidget(mw.terminal)
        
        mw.history_dock = VersionHistoryDock(mw)
        mw.history_dock.version_selected.connect(mw._restore_version)
        mw.right_panel.addWidget(mw.history_dock)

        mw.right_panel.hide()
        mw.main_splitter.setSizes([300, 950, 0])

        # 6. Right Activity Bar
        mw.right_activity_bar = ActivityBar(position="right", parent=mw)
        mw.main_layout.addWidget(mw.right_activity_bar)
        
        def handle_right_panel_visibility(checked, widget):
            if checked:
                mw.right_panel.setCurrentWidget(widget)
                mw.right_panel.show()
                sizes = mw.main_splitter.sizes()
                if sizes[2] == 0:
                    mw.main_splitter.setSizes([sizes[0], sizes[1] - 300, 300])
            else:
                if not any(b.isChecked() for b in mw.right_activity_bar.buttons if b.isCheckable()):
                    mw.right_panel.hide()
                    sizes = mw.main_splitter.sizes()
                    mw.main_splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])

        mw.btn_ai = mw.right_activity_bar.add_tool("chat_bot.svg", "AI Assistant", widget_to_toggle=None, custom_callback=lambda c: handle_right_panel_visibility(c, mw.chatbot_panel))
        mw.btn_term = mw.right_activity_bar.add_tool("terminal.svg", "Terminal", widget_to_toggle=None, custom_callback=lambda c: handle_right_panel_visibility(c, mw.terminal))
        mw.btn_term.toggled.connect(lambda c: mw.terminal.start_shell() if c else None)
        mw.btn_hist = mw.right_activity_bar.add_tool("history.svg", "Version History", widget_to_toggle=None, custom_callback=lambda c: handle_right_panel_visibility(c, mw.history_dock))

        mw.command_palette = CommandPalette(mw)