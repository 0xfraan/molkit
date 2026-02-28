from pymol.Qt import QtWidgets, QtCore, QtGui

Qt = QtCore.Qt


class CollapsibleSection(QtWidgets.QWidget):
    """A collapsible section with a toggle button and content area."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._expanded = True

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self.toggle_btn = QtWidgets.QPushButton(f"\u25bc {title}")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-bottom: 1px solid palette(mid);
                background: palette(window);
            }
            QPushButton:hover {
                background: palette(midlight);
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self.toggle_btn)

        # Content area
        self.content = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 8, 12, 8)
        self.content_layout.setSpacing(6)
        layout.addWidget(self.content)

        self._title = title

    def _toggle(self):
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        arrow = "\u25bc" if self._expanded else "\u25b6"
        self.toggle_btn.setText(f"{arrow} {self._title}")

    def collapse(self):
        self._expanded = False
        self.content.setVisible(False)
        self.toggle_btn.setText(f"\u25b6 {self._title}")

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
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Model tabs
        from .tabs import ModelTabBar
        self.tab_bar = ModelTabBar(self.cmd, self)
        self.main_layout.addWidget(self.tab_bar)

        # Welcome / Loader (always visible at top)
        from .sections.loader import LoaderSection
        self.loader = LoaderSection(self.cmd, self)
        self.main_layout.addWidget(self.loader)

        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.main_layout.addWidget(sep)

        # 2. Structures
        from .sections.structure import StructureSection
        self.structure_section = CollapsibleSection("Structures")
        self.structure_manager = StructureSection(self.cmd, self)
        self.structure_section.add_widget(self.structure_manager)
        self.main_layout.addWidget(self.structure_section)

        # 3. View
        from .sections.view import ViewSection
        self.view_section = CollapsibleSection("View")
        self.view_panel = ViewSection(self.cmd, self)
        self.view_section.add_widget(self.view_panel)
        self.main_layout.addWidget(self.view_section)

        # 4. Colors
        from .sections.colors import ColorsSection
        self.colors_section = CollapsibleSection("Colors")
        self.colors_panel = ColorsSection(self.cmd, self)
        self.colors_section.add_widget(self.colors_panel)
        self.main_layout.addWidget(self.colors_section)

        # 5. Selection
        from .sections.selection import SelectionSection
        self.selection_section = CollapsibleSection("Selection")
        self.selection_panel = SelectionSection(self.cmd, self)
        self.selection_section.add_widget(self.selection_panel)
        self.selection_section.collapse()
        self.main_layout.addWidget(self.selection_section)

        # 6. Measurements
        from .sections.measurements import MeasurementsSection
        self.measurements_section = CollapsibleSection("Measurements")
        self.measurements_panel = MeasurementsSection(self.cmd, self)
        self.measurements_section.add_widget(self.measurements_panel)
        self.measurements_section.collapse()
        self.main_layout.addWidget(self.measurements_section)

        # 7. Export
        from .sections.export import ExportSection
        self.export_section = CollapsibleSection("Export")
        self.export_panel = ExportSection(self.cmd, self)
        self.export_section.add_widget(self.export_panel)
        self.export_section.collapse()
        self.main_layout.addWidget(self.export_section)

        # 8. Console toggle (hidden by default)
        self.console_section = CollapsibleSection("Console (advanced)")
        console_btn = QtWidgets.QPushButton("Show PyMOL Console")
        console_btn.clicked.connect(self._toggle_console)
        self.console_section.add_widget(console_btn)
        inspector_btn = QtWidgets.QPushButton("Toggle Inspector Panel")
        inspector_btn.clicked.connect(self._toggle_inspector)
        self.console_section.add_widget(inspector_btn)
        self.console_section.collapse()
        self.main_layout.addWidget(self.console_section)

        # Connect loader -> add tab + refresh
        def _on_structure_loaded(name):
            self.tab_bar._save_current_view()
            self.tab_bar.add_tab(name)
            self.structure_manager.refresh()

        self.loader.structure_loaded.connect(_on_structure_loaded)

        # Connect tab [+] -> scroll to loader
        self.tab_bar.add_requested.connect(
            lambda: self.search_input_focus()
        )

        # Connect tab close -> refresh structure list
        self.tab_bar.tab_closed.connect(lambda _: self.structure_manager.refresh())

        # Connect tab change -> inspector (also fires on first load via add_tab)
        def _on_tab_for_inspector(name):
            window = self.window
            if hasattr(window, '_molkit_inspector'):
                window._molkit_inspector.inspector.load_entry(name)

        self.tab_bar.tab_changed.connect(_on_tab_for_inspector)

        # Sync timer
        self._sync_timer = QtCore.QTimer(self)
        self._sync_timer.timeout.connect(self.tab_bar.sync_with_pymol)
        self._sync_timer.start(3000)

        self.main_layout.addStretch()

        scroll.setWidget(container)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def search_input_focus(self):
        """Scroll to top and focus the search input."""
        self.loader.search_input.setFocus()
        self.loader.search_input.selectAll()

    def _toggle_console(self):
        """Toggle the PyMOL external GUI (console)."""
        if hasattr(self.window, 'ext_window'):
            if self.window.ext_window.isVisible():
                self.window.ext_window.hide()
            else:
                self.window.ext_window.show()

    def _toggle_inspector(self):
        """Toggle the inspector panel visibility."""
        if hasattr(self.window, '_molkit_inspector'):
            insp = self.window._molkit_inspector
            if insp.isVisible():
                insp.hide()
            else:
                insp.show()


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
