from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt


class MeasurementsSection(QtWidgets.QWidget):
    """Distance, angle, and interaction measurement controls."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self._measurement_count = 0

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # --- One-click analysis ---
        auto_label = QtWidgets.QLabel("Automatic Analysis:")
        auto_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(auto_label)

        hbond_btn = QtWidgets.QPushButton("Show Hydrogen Bonds")
        hbond_btn.setToolTip("Show H-bonds around ligand or selection")
        hbond_btn.clicked.connect(self._show_hbonds)
        layout.addWidget(hbond_btn)

        polar_btn = QtWidgets.QPushButton("Show Polar Contacts")
        polar_btn.setToolTip("Show polar contacts within selection")
        polar_btn.clicked.connect(self._show_polar_contacts)
        layout.addWidget(polar_btn)

        # --- Manual measurement ---
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep)

        manual_label = QtWidgets.QLabel("Manual Measurement:")
        manual_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(manual_label)

        info = QtWidgets.QLabel(
            "<i style='color:gray;'>Click atoms in the viewport to pick them, "
            "then click a button below.</i>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        dist_btn = QtWidgets.QPushButton("Distance (2 atoms)")
        dist_btn.setToolTip("Measure distance between pk1 and pk2")
        dist_btn.clicked.connect(self._measure_distance)
        layout.addWidget(dist_btn)

        angle_btn = QtWidgets.QPushButton("Angle (3 atoms)")
        angle_btn.setToolTip("Measure angle between pk1, pk2, pk3")
        angle_btn.clicked.connect(self._measure_angle)
        layout.addWidget(angle_btn)

        dihedral_btn = QtWidgets.QPushButton("Dihedral (4 atoms)")
        dihedral_btn.setToolTip("Measure dihedral between pk1, pk2, pk3, pk4")
        dihedral_btn.clicked.connect(self._measure_dihedral)
        layout.addWidget(dihedral_btn)

        # Status
        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet("color: gray; font-size: 11px;")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        # --- Clear ---
        sep2 = QtWidgets.QFrame()
        sep2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep2)

        clear_btn = QtWidgets.QPushButton("Clear All Measurements")
        clear_btn.setStyleSheet("color: red;")
        clear_btn.clicked.connect(self._clear_measurements)
        layout.addWidget(clear_btn)

    def _show_hbonds(self):
        try:
            # Try ligand-protein H-bonds first
            n_lig = self.cmd.count_atoms("organic")
            if n_lig > 0:
                donor = "organic"
                acceptor = "byres(organic around 4) and polymer"
            else:
                donor = "sele"
                acceptor = "all and not sele"

            self.cmd.delete("hbonds")
            self.cmd.distance(
                "hbonds", donor, acceptor,
                mode=2, cutoff=3.5, quiet=1
            )
            self.cmd.set("dash_color", "yellow", "hbonds")
            self.cmd.set("dash_gap", 0.2, "hbonds")
            self.cmd.set("dash_radius", 0.06, "hbonds")

            self.status.setText("H-bonds displayed (yellow dashes)")
            self.status.setStyleSheet("color: green; font-size: 11px;")
        except Exception as e:
            self.status.setText(f"Error: {e}")
            self.status.setStyleSheet("color: red; font-size: 11px;")

    def _show_polar_contacts(self):
        try:
            self.cmd.delete("polar_contacts")
            self.cmd.distance(
                "polar_contacts",
                "(elem N+O)", "(elem N+O)",
                mode=2, cutoff=3.5, quiet=1,
            )
            self.cmd.set("dash_color", "cyan", "polar_contacts")
            self.cmd.set("dash_gap", 0.3, "polar_contacts")
            self.cmd.set("dash_radius", 0.05, "polar_contacts")
            self.status.setText("Polar contacts displayed (cyan dashes)")
            self.status.setStyleSheet("color: green; font-size: 11px;")
        except Exception as e:
            self.status.setText(f"Error: {e}")
            self.status.setStyleSheet("color: red; font-size: 11px;")

    def _measure_distance(self):
        self._measurement_count += 1
        name = f"dist_{self._measurement_count}"
        try:
            d = self.cmd.get_distance("pk1", "pk2")
            self.cmd.distance(name, "pk1", "pk2")
            self.status.setText(f"Distance: {d:.2f} A")
            self.status.setStyleSheet("color: green; font-size: 11px;")
            self.cmd.unpick()
        except Exception:
            self.status.setText("Pick 2 atoms first (click on them in viewport)")
            self.status.setStyleSheet("color: orange; font-size: 11px;")

    def _measure_angle(self):
        self._measurement_count += 1
        name = f"angle_{self._measurement_count}"
        try:
            self.cmd.angle(name, "pk1", "pk2", "pk3")
            a = self.cmd.get_angle("pk1", "pk2", "pk3")
            self.status.setText(f"Angle: {a:.1f} deg")
            self.status.setStyleSheet("color: green; font-size: 11px;")
            self.cmd.unpick()
        except Exception:
            self.status.setText("Pick 3 atoms first (click on them in viewport)")
            self.status.setStyleSheet("color: orange; font-size: 11px;")

    def _measure_dihedral(self):
        self._measurement_count += 1
        name = f"dihe_{self._measurement_count}"
        try:
            self.cmd.dihedral(name, "pk1", "pk2", "pk3", "pk4")
            d = self.cmd.get_dihedral("pk1", "pk2", "pk3", "pk4")
            self.status.setText(f"Dihedral: {d:.1f} deg")
            self.status.setStyleSheet("color: green; font-size: 11px;")
            self.cmd.unpick()
        except Exception:
            self.status.setText("Pick 4 atoms first (click on them in viewport)")
            self.status.setStyleSheet("color: orange; font-size: 11px;")

    def _clear_measurements(self):
        try:
            self.cmd.delete("hbonds")
            self.cmd.delete("polar_contacts")
            for i in range(1, self._measurement_count + 1):
                self.cmd.delete(f"dist_{i}")
                self.cmd.delete(f"angle_{i}")
                self.cmd.delete(f"dihe_{i}")
            self._measurement_count = 0
            self.status.setText("All measurements cleared")
            self.status.setStyleSheet("color: gray; font-size: 11px;")
        except Exception:
            pass
