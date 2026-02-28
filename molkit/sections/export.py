import os

from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt


class ExportSection(QtWidgets.QWidget):
    """Screenshot, ray-trace, and file export controls."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # --- Screenshot ---
        img_label = QtWidgets.QLabel("Image Export:")
        img_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(img_label)

        # Resolution
        res_row = QtWidgets.QHBoxLayout()
        res_row.addWidget(QtWidgets.QLabel("Size:"))
        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(100, 8000)
        self.width_spin.setValue(1920)
        self.width_spin.setSuffix(" px")
        res_row.addWidget(self.width_spin)
        res_row.addWidget(QtWidgets.QLabel("x"))
        self.height_spin = QtWidgets.QSpinBox()
        self.height_spin.setRange(100, 8000)
        self.height_spin.setValue(1080)
        self.height_spin.setSuffix(" px")
        res_row.addWidget(self.height_spin)
        layout.addLayout(res_row)

        # Quick screenshot
        quick_btn = QtWidgets.QPushButton("Quick Screenshot (PNG)")
        quick_btn.setToolTip("Fast OpenGL capture")
        quick_btn.clicked.connect(self._quick_screenshot)
        layout.addWidget(quick_btn)

        # Ray-traced
        ray_btn = QtWidgets.QPushButton("Ray-traced Image (high quality)")
        ray_btn.setToolTip("Slow but beautiful ray-traced render")
        ray_btn.clicked.connect(self._ray_screenshot)
        layout.addWidget(ray_btn)

        self.img_status = QtWidgets.QLabel("")
        self.img_status.setStyleSheet("color: gray; font-size: 11px;")
        self.img_status.setWordWrap(True)
        layout.addWidget(self.img_status)

        # --- Session ---
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep)

        session_label = QtWidgets.QLabel("Session:")
        session_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(session_label)

        save_session_btn = QtWidgets.QPushButton("Save Session (.pse)")
        save_session_btn.setToolTip("Save entire PyMOL state to reopen later")
        save_session_btn.clicked.connect(self._save_session)
        layout.addWidget(save_session_btn)

        # --- Structure export ---
        sep2 = QtWidgets.QFrame()
        sep2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep2)

        struct_label = QtWidgets.QLabel("Export Structure:")
        struct_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(struct_label)

        export_btn = QtWidgets.QPushButton("Export as PDB / CIF / MOL2...")
        export_btn.clicked.connect(self._export_structure)
        layout.addWidget(export_btn)

    def _get_save_path(self, title, filter_str):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, title, "", filter_str,
        )
        return fname

    def _quick_screenshot(self):
        fname = self._get_save_path(
            "Save Screenshot", "PNG Image (*.png)"
        )
        if not fname:
            return
        if not fname.endswith(".png"):
            fname += ".png"

        w = self.width_spin.value()
        h = self.height_spin.value()
        self.img_status.setText("Rendering...")
        QtWidgets.QApplication.processEvents()
        try:
            self.cmd.draw(w, h)
            self.cmd.png(fname, dpi=150)
            self.img_status.setText(f"Saved: {os.path.basename(fname)}")
            self.img_status.setStyleSheet("color: green; font-size: 11px;")
        except Exception as e:
            self.img_status.setText(f"Error: {e}")
            self.img_status.setStyleSheet("color: red; font-size: 11px;")

    def _ray_screenshot(self):
        fname = self._get_save_path(
            "Save Ray-traced Image", "PNG Image (*.png)"
        )
        if not fname:
            return
        if not fname.endswith(".png"):
            fname += ".png"

        w = self.width_spin.value()
        h = self.height_spin.value()
        self.img_status.setText("Ray-tracing... (this may take a moment)")
        QtWidgets.QApplication.processEvents()
        try:
            self.cmd.ray(w, h)
            self.cmd.png(fname, dpi=300)
            self.img_status.setText(f"Saved: {os.path.basename(fname)}")
            self.img_status.setStyleSheet("color: green; font-size: 11px;")
        except Exception as e:
            self.img_status.setText(f"Error: {e}")
            self.img_status.setStyleSheet("color: red; font-size: 11px;")

    def _save_session(self):
        fname = self._get_save_path(
            "Save Session", "PyMOL Session (*.pse)"
        )
        if not fname:
            return
        if not fname.endswith(".pse"):
            fname += ".pse"
        try:
            self.cmd.save(fname)
            self.img_status.setText(f"Session saved: {os.path.basename(fname)}")
            self.img_status.setStyleSheet("color: green; font-size: 11px;")
        except Exception as e:
            self.img_status.setText(f"Error: {e}")
            self.img_status.setStyleSheet("color: red; font-size: 11px;")

    def _export_structure(self):
        fname = self._get_save_path(
            "Export Structure",
            "PDB (*.pdb);;mmCIF (*.cif);;MOL2 (*.mol2);;SDF (*.sdf);;XYZ (*.xyz)",
        )
        if not fname:
            return
        try:
            self.cmd.save(fname, "all")
            self.img_status.setText(f"Exported: {os.path.basename(fname)}")
            self.img_status.setStyleSheet("color: green; font-size: 11px;")
        except Exception as e:
            self.img_status.setText(f"Error: {e}")
            self.img_status.setStyleSheet("color: red; font-size: 11px;")
