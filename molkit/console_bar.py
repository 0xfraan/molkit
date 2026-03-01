from pymol.Qt import QtWidgets, QtCore

from .theme import SURFACE, BORDER, HOVER, TEXT_MUTED, TEXT, FONT_SIZE_SM, RADIUS

Qt = QtCore.Qt


class ConsoleBar(QtWidgets.QWidget):
    """Bottom bar with Console and Inspector toggle buttons."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self._window = window

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        btn_style = f"""
            QPushButton {{
                padding: 4px 12px;
                font-size: {FONT_SIZE_SM};
                border: 1px solid {BORDER};
                border-radius: {RADIUS};
                background: {SURFACE};
                color: {TEXT_MUTED};
            }}
            QPushButton:hover {{
                background: {HOVER};
                color: {TEXT};
            }}
            QPushButton:checked {{
                color: {TEXT};
                border-color: {TEXT_MUTED};
            }}
        """

        self.console_btn = QtWidgets.QPushButton("console")
        self.console_btn.setCheckable(True)
        self.console_btn.setStyleSheet(btn_style)
        self.console_btn.setToolTip("Toggle PyMOL console")
        self.console_btn.clicked.connect(self._toggle_console)
        layout.addWidget(self.console_btn)

        self.inspector_btn = QtWidgets.QPushButton("inspector")
        self.inspector_btn.setCheckable(True)
        self.inspector_btn.setChecked(True)
        self.inspector_btn.setStyleSheet(btn_style)
        self.inspector_btn.setToolTip("Toggle inspector panel")
        self.inspector_btn.clicked.connect(self._toggle_inspector)
        layout.addWidget(self.inspector_btn)

        layout.addStretch()

        self.setMaximumHeight(32)

    def _toggle_console(self):
        """Toggle the embedded console panel below this bar."""
        holder = getattr(self._window, '_molkit_ext_holder', None)
        if holder is None:
            return
        visible = holder.isVisible()
        holder.setVisible(not visible)
        self.console_btn.setChecked(not visible)

    def _toggle_inspector(self):
        if hasattr(self._window, '_molkit_inspector'):
            insp = self._window._molkit_inspector
            if insp.isVisible():
                insp.hide()
                self.inspector_btn.setChecked(False)
            else:
                insp.show()
                self.inspector_btn.setChecked(True)
