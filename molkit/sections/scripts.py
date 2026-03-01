import os

from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt


class ScriptItem(QtWidgets.QFrame):
    """Single .pml script row with name and run button."""
    run_requested = QtCore.Signal(str)  # emits full path

    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        name = os.path.basename(filepath)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        label = QtWidgets.QLabel(name)
        label.setToolTip(filepath)
        layout.addWidget(label, 1)

        run_btn = QtWidgets.QPushButton("Run")
        run_btn.setFixedWidth(50)
        run_btn.clicked.connect(lambda: self.run_requested.emit(self.filepath))
        layout.addWidget(run_btn)


class ScriptsSection(QtWidgets.QWidget):
    """File explorer for .pml scripts in a user-specified directory."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self._dir = ""

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Directory picker
        dir_row = QtWidgets.QHBoxLayout()
        self.dir_input = QtWidgets.QLineEdit()
        self.dir_input.setPlaceholderText("Path to scripts folder...")
        self.dir_input.returnPressed.connect(self._set_dir_from_input)
        dir_row.addWidget(self.dir_input)

        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status)

        # Script list
        self.list_container = QtWidgets.QWidget()
        self.list_layout = QtWidgets.QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        layout.addWidget(self.list_container)

        layout.addStretch()

    def _browse(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Scripts Folder", self._dir or os.path.expanduser("~")
        )
        if d:
            self.dir_input.setText(d)
            self._load_dir(d)

    def _set_dir_from_input(self):
        d = self.dir_input.text().strip()
        if d:
            d = os.path.expanduser(d)
            self.dir_input.setText(d)
            self._load_dir(d)

    def _load_dir(self, path):
        self._clear_list()
        if not os.path.isdir(path):
            self.status.setText("Directory not found.")
            self.status.setStyleSheet("color: red; font-size: 11px;")
            return

        self._dir = path
        scripts = sorted(
            f for f in os.listdir(path) if f.endswith(".pml")
        )

        if not scripts:
            self.status.setText("No .pml files found.")
            self.status.setStyleSheet("color: orange; font-size: 11px;")
            return

        self.status.setText(f"{len(scripts)} script(s)")
        self.status.setStyleSheet("color: gray; font-size: 11px;")

        for name in scripts:
            filepath = os.path.join(path, name)
            item = ScriptItem(filepath, self.list_container)
            item.run_requested.connect(self._run_script)
            self.list_layout.addWidget(item)

    def _run_script(self, filepath):
        self.status.setText(f"Running {os.path.basename(filepath)}...")
        self.status.setStyleSheet("color: gray; font-size: 11px;")
        QtWidgets.QApplication.processEvents()
        try:
            self.cmd.do(f"@{filepath}")
            self.status.setText(f"Done: {os.path.basename(filepath)}")
            self.status.setStyleSheet("color: green; font-size: 11px;")
        except Exception as e:
            self.status.setText(f"Error: {e}")
            self.status.setStyleSheet("color: red; font-size: 11px;")

    def _clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
