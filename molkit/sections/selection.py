from pymol.Qt import QtWidgets, QtCore

from ..theme import FONT_SIZE_SM, TEXT_MUTED, status_style

Qt = QtCore.Qt


class SelectionSection(QtWidgets.QWidget):
    """Visual selection builder -- no command syntax needed."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # --- Quick selections ---
        quick_label = QtWidgets.QLabel("Quick Select:")
        quick_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(quick_label)

        quick_grid = QtWidgets.QGridLayout()
        quick_grid.setSpacing(4)
        quick_buttons = [
            ("Protein", "polymer.protein"),
            ("Ligands", "organic"),
            ("Water", "solvent"),
            ("Ions", "inorganic"),
            ("Backbone", "backbone"),
            ("Side chains", "sidechain"),
            ("Helices", "ss h"),
            ("Sheets", "ss s"),
        ]
        for i, (label, sel_expr) in enumerate(quick_buttons):
            btn = QtWidgets.QPushButton(label)
            btn.setStyleSheet(f"padding: 3px 6px; font-size: {FONT_SIZE_SM};")
            btn.clicked.connect(
                lambda checked, s=sel_expr, n=label: self._quick_select(s, n)
            )
            quick_grid.addWidget(btn, i // 2, i % 2)
        layout.addLayout(quick_grid)

        # --- Builder ---
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep)

        build_label = QtWidgets.QLabel("Build Selection:")
        build_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(build_label)

        # Chain selector
        chain_row = QtWidgets.QHBoxLayout()
        chain_row.addWidget(QtWidgets.QLabel("Chain:"))
        self.chain_combo = QtWidgets.QComboBox()
        self.chain_combo.addItem("All chains")
        chain_row.addWidget(self.chain_combo, 1)
        layout.addLayout(chain_row)

        # Residue range
        res_row = QtWidgets.QHBoxLayout()
        res_row.addWidget(QtWidgets.QLabel("Residues:"))
        self.res_from = QtWidgets.QSpinBox()
        self.res_from.setRange(0, 9999)
        self.res_from.setSpecialValueText("start")
        res_row.addWidget(self.res_from)
        res_row.addWidget(QtWidgets.QLabel("to"))
        self.res_to = QtWidgets.QSpinBox()
        self.res_to.setRange(0, 9999)
        self.res_to.setSpecialValueText("end")
        res_row.addWidget(self.res_to)
        layout.addLayout(res_row)

        # Around distance
        around_row = QtWidgets.QHBoxLayout()
        self.around_cb = QtWidgets.QCheckBox("Within")
        around_row.addWidget(self.around_cb)
        self.around_dist = QtWidgets.QDoubleSpinBox()
        self.around_dist.setRange(1.0, 30.0)
        self.around_dist.setValue(5.0)
        self.around_dist.setSuffix(" A")
        self.around_dist.setDecimals(1)
        around_row.addWidget(self.around_dist)
        around_row.addWidget(QtWidgets.QLabel("of ligand"))
        layout.addLayout(around_row)

        # Apply
        apply_btn = QtWidgets.QPushButton("Select")
        apply_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        apply_btn.clicked.connect(self._apply_selection)
        layout.addWidget(apply_btn)

        # Status
        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet(status_style("muted"))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        # --- Saved selections ---
        sep2 = QtWidgets.QFrame()
        sep2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep2)

        saved_label = QtWidgets.QLabel("Saved Selections:")
        saved_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(saved_label)

        self.saved_list = QtWidgets.QVBoxLayout()
        self.saved_list.setSpacing(2)
        layout.addLayout(self.saved_list)

        self.no_sel_label = QtWidgets.QLabel(
            f"<i style='color:{TEXT_MUTED};'>No saved selections</i>"
        )
        layout.addWidget(self.no_sel_label)

        # Refresh chains on show
        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_chains)
        self._refresh_timer.start(3000)

    def _refresh_chains(self):
        """Update chain dropdown from loaded objects."""
        try:
            chains = set()
            self.cmd.iterate("all", "chains.add(chain)", space={"chains": chains})
            chains = sorted(chains - {""})

            current = self.chain_combo.currentText()
            self.chain_combo.blockSignals(True)
            self.chain_combo.clear()
            self.chain_combo.addItem("All chains")
            for c in chains:
                self.chain_combo.addItem(f"Chain {c}")

            # Restore selection
            idx = self.chain_combo.findText(current)
            if idx >= 0:
                self.chain_combo.setCurrentIndex(idx)
            self.chain_combo.blockSignals(False)
        except Exception:
            pass

    def _quick_select(self, expr, name):
        try:
            self.cmd.select("sele", expr)
            n = self.cmd.count_atoms("sele")
            self.status.setText(f"Selected '{name}': {n} atoms")
        except Exception as e:
            self.status.setText(f"Error: {e}")

    def _build_expression(self):
        parts = []

        # Chain
        chain_text = self.chain_combo.currentText()
        if chain_text != "All chains":
            chain_id = chain_text.replace("Chain ", "")
            parts.append(f"chain {chain_id}")

        # Residue range
        res_from = self.res_from.value()
        res_to = self.res_to.value()
        if res_from > 0 and res_to > 0:
            parts.append(f"resi {res_from}-{res_to}")
        elif res_from > 0:
            parts.append(f"resi {res_from}-")
        elif res_to > 0:
            parts.append(f"resi 1-{res_to}")

        base = " and ".join(parts) if parts else "all"

        # Around ligand
        if self.around_cb.isChecked():
            dist = self.around_dist.value()
            base = f"byres({base} and (all within {dist} of organic))"

        return base

    def _apply_selection(self):
        expr = self._build_expression()
        try:
            self.cmd.select("sele", expr)
            n = self.cmd.count_atoms("sele")
            self.status.setText(f"Selected {n} atoms\n({expr})")
            self.status.setStyleSheet(status_style("success"))
        except Exception as e:
            self.status.setText(f"Error: {e}")
            self.status.setStyleSheet(status_style("error"))
