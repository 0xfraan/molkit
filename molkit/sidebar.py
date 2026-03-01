from pymol.Qt import QtWidgets, QtCore, QtGui

from .theme import (
    BG, SURFACE, HOVER, BORDER, TEXT, TEXT_MUTED, ACCENT,
    FONT_SIZE_BASE, FONT_SIZE_SM, RADIUS,
)

Qt = QtCore.Qt

# Unicode chevrons (thin)
_CHEVRON_RIGHT = "\u203a"   # ›
_CHEVRON_DOWN = "\u2304"    # ⌄


class CollapsibleSection(QtWidgets.QWidget):
    """A collapsible section with a toggle button and content area."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._expanded = False

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self.toggle_btn = QtWidgets.QPushButton()
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self.toggle_btn)

        # Content area
        self.content = QtWidgets.QWidget()
        self.content.setVisible(False)
        self.content_layout = QtWidgets.QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(16, 8, 12, 12)
        self.content_layout.setSpacing(8)
        layout.addWidget(self.content)

        self._title = title
        self._apply_style()
        self._update_label()

    def _apply_style(self):
        # Active sections get an accent left border
        left_border = f"2px solid {ACCENT}" if self._expanded else f"2px solid transparent"
        text_color = TEXT if self._expanded else TEXT_MUTED
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 10px 12px;
                font-weight: 600;
                font-size: {FONT_SIZE_BASE};
                letter-spacing: 0.01em;
                border: none;
                border-left: {left_border};
                background: transparent;
                color: {text_color};
            }}
            QPushButton:hover {{
                background: {HOVER};
                border-radius: {RADIUS};
                color: {TEXT};
            }}
        """)

    def _update_label(self):
        chevron = _CHEVRON_DOWN if self._expanded else _CHEVRON_RIGHT
        self.toggle_btn.setText(f" {chevron}   {self._title}")

    def _toggle(self):
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        self._apply_style()
        self._update_label()

    def collapse(self):
        self._expanded = False
        self.content.setVisible(False)
        self._apply_style()
        self._update_label()

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


class MolKitSidebarWidget(QtWidgets.QWidget):
    """Main sidebar widget with collapsible sections."""

    def __init__(self, parent=None, window=None):
        super().__init__(parent)
        self.window = window
        from pymol import cmd
        self.cmd = cmd
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)

        # Scroll area for sections
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        container = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout(container)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(2)

        # Tab bar is set externally via set_tab_bar()
        self.tab_bar = None

        # 1. Search / Load
        from .sections.loader import LoaderSection
        self.loader_section = CollapsibleSection("search / load")
        self.loader = LoaderSection(self.cmd, self)
        self.loader_section.add_widget(self.loader)
        self.main_layout.addWidget(self.loader_section)

        # 2. Structures
        from .sections.structure import StructureSection
        self.structure_section = CollapsibleSection("structures")
        self.structure_manager = StructureSection(self.cmd, self)
        self.structure_section.add_widget(self.structure_manager)
        self.main_layout.addWidget(self.structure_section)

        # 3. View
        from .sections.view import ViewSection
        self.view_section = CollapsibleSection("view")
        self.view_panel = ViewSection(self.cmd, self)
        self.view_section.add_widget(self.view_panel)
        self.main_layout.addWidget(self.view_section)

        # 4. Colors
        from .sections.colors import ColorsSection
        self.colors_section = CollapsibleSection("colors")
        self.colors_panel = ColorsSection(self.cmd, self)
        self.colors_section.add_widget(self.colors_panel)
        self.main_layout.addWidget(self.colors_section)

        # 5. Selection
        from .sections.selection import SelectionSection
        self.selection_section = CollapsibleSection("selection")
        self.selection_panel = SelectionSection(self.cmd, self)
        self.selection_section.add_widget(self.selection_panel)
        self.selection_section.collapse()
        self.main_layout.addWidget(self.selection_section)

        # 6. Measurements
        from .sections.measurements import MeasurementsSection
        self.measurements_section = CollapsibleSection("measurements")
        self.measurements_panel = MeasurementsSection(self.cmd, self)
        self.measurements_section.add_widget(self.measurements_panel)
        self.measurements_section.collapse()
        self.main_layout.addWidget(self.measurements_section)

        # 7. Scripts
        from .sections.scripts import ScriptsSection
        self.scripts_section = CollapsibleSection("scripts")
        self.scripts_panel = ScriptsSection(self.cmd, self)
        self.scripts_section.add_widget(self.scripts_panel)
        self.main_layout.addWidget(self.scripts_section)

        # 8. Export
        from .sections.export import ExportSection
        self.export_section = CollapsibleSection("export")
        self.export_panel = ExportSection(self.cmd, self)
        self.export_section.add_widget(self.export_panel)
        self.export_section.collapse()
        self.main_layout.addWidget(self.export_section)

        self.main_layout.addStretch()

        scroll.setWidget(container)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_tab_bar(self, tab_bar):
        """Connect an external tab bar to the sidebar signals."""
        self.tab_bar = tab_bar

        # Connect loader -> add tab + refresh
        def _on_structure_loaded(name):
            self.tab_bar._save_current_view()
            self.tab_bar.add_tab(name)
            self.structure_manager.refresh()

        self.loader.structure_loaded.connect(_on_structure_loaded)

        # Connect tab close -> refresh structure list
        self.tab_bar.tab_closed.connect(lambda _: self.structure_manager.refresh())

        # Connect tab change -> inspector
        def _on_tab_for_inspector(name):
            window = self.window
            if hasattr(window, '_molkit_inspector'):
                window._molkit_inspector.inspector.load_entry(name)

        self.tab_bar.tab_changed.connect(_on_tab_for_inspector)

        # Sync timer
        self._sync_timer = QtCore.QTimer(self)
        self._sync_timer.timeout.connect(self.tab_bar.sync_with_pymol)
        self._sync_timer.start(3000)

    def search_input_focus(self):
        """Scroll to top and focus the search input."""
        self.loader.search_input.setFocus()
        self.loader.search_input.selectAll()

class MolKitSidebar(QtWidgets.QDockWidget):
    """Dockable sidebar wrapper."""

    def __init__(self, window, parent=None):
        super().__init__(parent or window)
        self.setWindowTitle("MolKit")
        self.setObjectName("molkit_sidebar")
        self.widget_inner = MolKitSidebarWidget(self, window=window)
        self.setWidget(self.widget_inner)
        self.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
