from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt


class ModelTabBar(QtWidgets.QWidget):
    """Tab bar for switching between loaded models."""

    tab_changed = QtCore.Signal(str)  # emits active object name
    tab_closed = QtCore.Signal(str)   # emits closed object name
    add_requested = QtCore.Signal()   # user clicked [+]

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self._views = {}       # object_name -> view tuple
        self._show_all = False

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab bar
        self.tab_bar = QtWidgets.QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close)
        layout.addWidget(self.tab_bar, 1)

        # Show All checkbox
        self.show_all_cb = QtWidgets.QCheckBox("Show all")
        self.show_all_cb.setToolTip("Overlay all models in viewport")
        self.show_all_cb.toggled.connect(self._on_show_all)
        layout.addWidget(self.show_all_cb)

        self.setMaximumHeight(36)

    def add_tab(self, name: str):
        """Add a tab for a newly loaded model."""
        # Check if tab already exists
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i) == name:
                self.tab_bar.setCurrentIndex(i)
                return

        idx = self.tab_bar.addTab(name)
        self.tab_bar.setTabData(idx, name)
        self.tab_bar.setCurrentIndex(idx)

    def remove_tab(self, name: str):
        """Remove tab by object name."""
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i) == name:
                self.tab_bar.removeTab(i)
                self._views.pop(name, None)
                return

    def _save_current_view(self):
        """Save camera view for current tab."""
        idx = self.tab_bar.currentIndex()
        if idx < 0:
            return
        name = self.tab_bar.tabData(idx)
        if name:
            try:
                self._views[name] = self.cmd.get_view()
            except Exception:
                pass

    def _on_tab_changed(self, index):
        if index < 0:
            return

        name = self.tab_bar.tabData(index)
        if not name:
            return

        if not self._show_all:
            # Save view of previous tab before switching
            # (already saved when leaving, but be safe)
            # Disable all, enable active
            try:
                for obj in self.cmd.get_object_list():
                    self.cmd.disable(obj)
                self.cmd.enable(name)

                # Restore saved view
                if name in self._views:
                    self.cmd.set_view(self._views[name])
            except Exception:
                pass

        self.tab_changed.emit(name)

    def _on_tab_close(self, index):
        name = self.tab_bar.tabData(index)
        if not name:
            return

        self.tab_bar.removeTab(index)
        self._views.pop(name, None)

        try:
            self.cmd.delete(name)
        except Exception:
            pass

        self.tab_closed.emit(name)

    def _on_show_all(self, checked):
        self._show_all = checked
        try:
            if checked:
                for obj in self.cmd.get_object_list():
                    self.cmd.enable(obj)
            else:
                # Switch back to single-tab mode
                self._on_tab_changed(self.tab_bar.currentIndex())
        except Exception:
            pass

    def sync_with_pymol(self):
        """Sync tabs with actual PyMOL objects."""
        try:
            objects = set(self.cmd.get_object_list())
        except Exception:
            return

        # Remove tabs for deleted objects
        for i in range(self.tab_bar.count() - 1, -1, -1):
            name = self.tab_bar.tabData(i)
            if name not in objects:
                self.tab_bar.removeTab(i)
                self._views.pop(name, None)

        # Add tabs for new objects (don't auto-add — only via loader)
