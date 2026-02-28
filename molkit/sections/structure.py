from pymol.Qt import QtWidgets, QtCore, QtGui

Qt = QtCore.Qt


class ObjectRow(QtWidgets.QWidget):
    """Single row showing one loaded object with visibility toggle and delete."""

    def __init__(self, name, cmd, parent=None):
        super().__init__(parent)
        self.name = name
        self.cmd = cmd

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 2, 0, 2)

        self.vis_cb = QtWidgets.QCheckBox()
        self.vis_cb.setChecked(True)
        self.vis_cb.toggled.connect(self._toggle_vis)
        row.addWidget(self.vis_cb)

        info = self._get_info()
        label = QtWidgets.QLabel(f"<b>{name}</b>  <span style='color:gray;'>{info}</span>")
        row.addWidget(label, 1)

        del_btn = QtWidgets.QPushButton("x")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet("border: none; color: red; font-weight: bold;")
        del_btn.setToolTip("Delete object")
        del_btn.clicked.connect(self._delete)
        row.addWidget(del_btn)

    def _get_info(self):
        try:
            n = self.cmd.count_atoms(self.name)
            chains = set()
            self.cmd.iterate(self.name, "chains.add(chain)", space={"chains": chains})
            chain_str = ",".join(sorted(chains)) if chains else ""
            return f"{n} atoms" + (f" | chains {chain_str}" if chain_str else "")
        except Exception:
            return ""

    def _toggle_vis(self, checked):
        if checked:
            self.cmd.enable(self.name)
        else:
            self.cmd.disable(self.name)

    def _delete(self):
        self.cmd.delete(self.name)
        self.setParent(None)
        self.deleteLater()


class StructureSection(QtWidgets.QWidget):
    """Shows list of loaded objects with controls."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.list_layout = QtWidgets.QVBoxLayout()
        self.list_layout.setSpacing(2)
        layout.addLayout(self.list_layout)

        self.empty_label = QtWidgets.QLabel(
            "<i style='color:gray;'>No structures loaded</i>"
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        # Refresh timer to sync with PyMOL state
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(2000)  # every 2s

        self._known_objects = set()

    def refresh(self):
        """Sync object list with PyMOL."""
        try:
            current = set(self.cmd.get_object_list())
        except Exception:
            return

        if current == self._known_objects:
            return

        # Clear old rows
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rebuild
        self._known_objects = current
        self.empty_label.setVisible(len(current) == 0)

        for name in sorted(current):
            row = ObjectRow(name, self.cmd, self)
            self.list_layout.addWidget(row)
