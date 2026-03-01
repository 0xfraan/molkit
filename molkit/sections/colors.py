from pymol.Qt import QtWidgets, QtCore, QtGui

from ..theme import BORDER

Qt = QtCore.Qt

COLOR_SCHEMES = [
    ("By element (CPK)", "element"),
    ("By chain", "chain"),
    ("By secondary structure", "ss"),
    ("Rainbow (N\u2192C)", "rainbow"),
    ("By B-factor", "bfactor"),
    ("Single color...", "single"),
]

SINGLE_COLORS = [
    ("Red", "red"),
    ("Blue", "blue"),
    ("Green", "green"),
    ("Yellow", "yellow"),
    ("Orange", "orange"),
    ("Cyan", "cyan"),
    ("Magenta", "magenta"),
    ("White", "white"),
    ("Gray", "gray70"),
    ("Salmon", "salmon"),
    ("Slate", "slate"),
    ("Forest", "forest"),
    ("Deep Teal", "deepteal"),
    ("Light Pink", "lightpink"),
    ("Wheat", "wheat"),
    ("Pale Cyan", "palecyan"),
]


class ColorsSection(QtWidgets.QWidget):
    """Color controls for loaded structures."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # --- Target ---
        target_row = QtWidgets.QHBoxLayout()
        target_row.addWidget(QtWidgets.QLabel("Apply to:"))
        self.target_combo = QtWidgets.QComboBox()
        self.target_combo.addItems([
            "Everything", "Protein", "Ligands", "Selection (sele)"
        ])
        target_row.addWidget(self.target_combo, 1)
        layout.addLayout(target_row)

        # --- Color scheme ---
        scheme_label = QtWidgets.QLabel("Color scheme:")
        scheme_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(scheme_label)

        self.scheme_combo = QtWidgets.QComboBox()
        for label, _ in COLOR_SCHEMES:
            self.scheme_combo.addItem(label)
        self.scheme_combo.currentIndexChanged.connect(self._on_scheme_changed)
        layout.addLayout(self._labeled_row("Scheme:", self.scheme_combo))

        # --- Single color picker (hidden until "Single color" selected) ---
        self.single_color_widget = QtWidgets.QWidget()
        single_layout = QtWidgets.QVBoxLayout(self.single_color_widget)
        single_layout.setContentsMargins(0, 0, 0, 0)
        single_layout.setSpacing(4)

        # Grid of color buttons
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(3)
        for i, (name, color) in enumerate(SINGLE_COLORS):
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(28, 28)
            btn.setToolTip(name)
            # Try to set button color
            try:
                rgb = self.cmd.get_color_tuple(color)
                r, g, b = int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
                btn.setStyleSheet(
                    f"background-color: rgb({r},{g},{b}); border: 1px solid {BORDER};"
                )
            except Exception:
                btn.setText(name[:2])
            btn.clicked.connect(
                lambda checked, c=color: self._apply_single_color(c)
            )
            grid.addWidget(btn, i // 4, i % 4)
        single_layout.addLayout(grid)

        # Custom color picker
        custom_btn = QtWidgets.QPushButton("Custom color...")
        custom_btn.clicked.connect(self._pick_custom_color)
        single_layout.addWidget(custom_btn)

        self.single_color_widget.setVisible(False)
        layout.addWidget(self.single_color_widget)

        # Apply button
        apply_btn = QtWidgets.QPushButton("Apply Color Scheme")
        apply_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        apply_btn.clicked.connect(self._apply_scheme)
        layout.addWidget(apply_btn)

    def _labeled_row(self, label, widget):
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(label))
        row.addWidget(widget, 1)
        return row

    def _get_target(self):
        targets = ["all", "polymer", "organic", "sele"]
        idx = self.target_combo.currentIndex()
        return targets[idx] if idx < len(targets) else "all"

    def _on_scheme_changed(self, index):
        _, scheme = COLOR_SCHEMES[index]
        self.single_color_widget.setVisible(scheme == "single")

    def _apply_scheme(self):
        target = self._get_target()
        _, scheme = COLOR_SCHEMES[self.scheme_combo.currentIndex()]

        try:
            if scheme == "element":
                self.cmd.util.cbag(target)
            elif scheme == "chain":
                self.cmd.util.cbc(target)
            elif scheme == "ss":
                self.cmd.util.ss(target)
            elif scheme == "rainbow":
                self.cmd.util.rainbow(target)
            elif scheme == "bfactor":
                self.cmd.spectrum("b", "blue_white_red", target)
            elif scheme == "single":
                pass  # handled by color buttons
        except Exception as e:
            print(f"Color error: {e}")

    def _apply_single_color(self, color):
        target = self._get_target()
        try:
            self.cmd.color(color, target)
        except Exception as e:
            print(f"Color error: {e}")

    def _pick_custom_color(self):
        color = QtWidgets.QColorDialog.getColor(parent=self)
        if color.isValid():
            r = color.redF()
            g = color.greenF()
            b = color.blueF()
            target = self._get_target()
            try:
                self.cmd.set_color("molkit_custom", [r, g, b])
                self.cmd.color("molkit_custom", target)
            except Exception as e:
                print(f"Color error: {e}")
