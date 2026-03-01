from pymol.Qt import QtWidgets, QtCore
from pymol import cgo

from ..theme import RADIUS

Qt = QtCore.Qt

GRID_OBJ_NAME = "_molkit_grid"
GRID_RANGE = 50  # half-extent in angstroms
GRID_SPACING = 5  # spacing between grid points/lines


def _build_dot_grid(spacing=GRID_SPACING, extent=GRID_RANGE):
    """Build a CGO 2D dot grid on the XY plane (z=0)."""
    obj = [cgo.BEGIN, cgo.POINTS]
    obj.extend([cgo.COLOR, 0.35, 0.35, 0.35])
    coords = range(-extent, extent + 1, spacing)
    for x in coords:
        for y in coords:
            obj.extend([cgo.VERTEX, float(x), float(y), 0.0])
    obj.append(cgo.END)
    return obj


def _build_line_grid(spacing=GRID_SPACING, extent=GRID_RANGE):
    """Build a CGO 2D line grid on the XY plane (z=0)."""
    obj = [cgo.BEGIN, cgo.LINES]
    obj.extend([cgo.COLOR, 0.25, 0.25, 0.25])
    coords = range(-extent, extent + 1, spacing)
    for x in coords:
        # vertical lines (along Y)
        obj.extend([cgo.VERTEX, float(x), float(-extent), 0.0])
        obj.extend([cgo.VERTEX, float(x), float(extent), 0.0])
    for y in coords:
        # horizontal lines (along X)
        obj.extend([cgo.VERTEX, float(-extent), float(y), 0.0])
        obj.extend([cgo.VERTEX, float(extent), float(y), 0.0])
    obj.append(cgo.END)
    return obj

REPRESENTATIONS = [
    ("Cartoon (ribbon)", "cartoon"),
    ("Sticks (bonds)", "sticks"),
    ("Lines (wireframe)", "lines"),
    ("Spheres (CPK)", "spheres"),
    ("Surface", "surface"),
    ("Mesh", "mesh"),
    ("Ball & Stick", "_ball_and_stick"),  # custom preset
    ("Dots", "dots"),
]

PRESETS = [
    ("Default Overview", "default"),
    ("Publication Quality", "publication"),
    ("Binding Site Focus", "binding_site"),
    ("B-Factor (flexibility)", "bfactor"),
    ("All-atom detail", "technical"),
    ("Ligand Interactions", "ligand_interactions"),
]


class ViewSection(QtWidgets.QWidget):
    """Controls for molecular representation and presets."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # --- Representation ---
        rep_label = QtWidgets.QLabel("Representation:")
        rep_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(rep_label)

        # Protein representation
        prot_row = QtWidgets.QHBoxLayout()
        prot_row.addWidget(QtWidgets.QLabel("Protein:"))
        self.protein_rep = QtWidgets.QComboBox()
        for label, _ in REPRESENTATIONS:
            self.protein_rep.addItem(label)
        self.protein_rep.setCurrentIndex(0)  # cartoon
        self.protein_rep.currentIndexChanged.connect(self._apply_protein_rep)
        prot_row.addWidget(self.protein_rep, 1)
        layout.addLayout(prot_row)

        # Ligand representation
        lig_row = QtWidgets.QHBoxLayout()
        lig_row.addWidget(QtWidgets.QLabel("Ligands:"))
        self.ligand_rep = QtWidgets.QComboBox()
        for label, _ in REPRESENTATIONS:
            self.ligand_rep.addItem(label)
        self.ligand_rep.setCurrentIndex(1)  # sticks
        self.ligand_rep.currentIndexChanged.connect(self._apply_ligand_rep)
        lig_row.addWidget(self.ligand_rep, 1)
        layout.addLayout(lig_row)

        # --- Toggles ---
        toggles_label = QtWidgets.QLabel("Show / Hide:")
        toggles_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(toggles_label)

        self.water_cb = QtWidgets.QCheckBox("Water molecules")
        self.water_cb.setChecked(False)
        self.water_cb.toggled.connect(self._toggle_water)
        layout.addWidget(self.water_cb)

        self.hydrogen_cb = QtWidgets.QCheckBox("Hydrogens")
        self.hydrogen_cb.setChecked(False)
        self.hydrogen_cb.toggled.connect(self._toggle_hydrogens)
        layout.addWidget(self.hydrogen_cb)

        self.hetatm_cb = QtWidgets.QCheckBox("Ions & heteroatoms")
        self.hetatm_cb.setChecked(True)
        self.hetatm_cb.toggled.connect(self._toggle_hetatm)
        layout.addWidget(self.hetatm_cb)

        # --- Presets ---
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep)

        preset_label = QtWidgets.QLabel("Quick Presets:")
        preset_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preset_label)

        for label, preset_id in PRESETS:
            btn = QtWidgets.QPushButton(label)
            btn.setStyleSheet(f"text-align: left; padding: 4px 8px; border-radius: {RADIUS};")
            btn.clicked.connect(lambda checked, pid=preset_id: self._apply_preset(pid))
            layout.addWidget(btn)

        # --- Background ---
        sep2 = QtWidgets.QFrame()
        sep2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep2)

        bg_row = QtWidgets.QHBoxLayout()
        bg_row.addWidget(QtWidgets.QLabel("Background:"))
        self.bg_combo = QtWidgets.QComboBox()
        self.bg_combo.addItems(["Black", "White", "Gray", "Light Blue"])
        self.bg_combo.currentIndexChanged.connect(self._change_bg)
        bg_row.addWidget(self.bg_combo, 1)
        layout.addLayout(bg_row)

        # --- 3D Grid ---
        grid_row = QtWidgets.QHBoxLayout()
        grid_row.addWidget(QtWidgets.QLabel("3D Grid:"))
        self.grid_combo = QtWidgets.QComboBox()
        self.grid_combo.addItems(["Off", "Dots", "Lines"])
        self.grid_combo.currentIndexChanged.connect(self._change_grid)
        grid_row.addWidget(self.grid_combo, 1)
        layout.addLayout(grid_row)

    def _apply_rep(self, selection, rep_key):
        self.cmd.hide("everything", selection)
        if rep_key == "_ball_and_stick":
            self.cmd.show("sticks", selection)
            self.cmd.show("spheres", selection)
            self.cmd.set("sphere_scale", 0.25, selection)
            self.cmd.set("stick_radius", 0.15, selection)
        else:
            self.cmd.show(rep_key, selection)

    def _apply_protein_rep(self, index):
        _, rep_key = REPRESENTATIONS[index]
        self._apply_rep("polymer", rep_key)

    def _apply_ligand_rep(self, index):
        _, rep_key = REPRESENTATIONS[index]
        self._apply_rep("organic", rep_key)

    def _toggle_water(self, show):
        if show:
            self.cmd.show("nonbonded", "solvent")
        else:
            self.cmd.hide("everything", "solvent")

    def _toggle_hydrogens(self, show):
        if show:
            self.cmd.show("sticks", "elem H")
        else:
            self.cmd.hide("everything", "elem H")

    def _toggle_hetatm(self, show):
        if show:
            self.cmd.show("spheres", "inorganic")
        else:
            self.cmd.hide("everything", "inorganic")

    def _apply_preset(self, preset_id):
        try:
            if preset_id == "default":
                self.cmd.hide("everything", "all")
                self.cmd.show("cartoon", "polymer")
                self.cmd.show("sticks", "organic")
                self.cmd.util.cbc("polymer")
                self.cmd.util.cbag("organic")
                self.cmd.orient()

            elif preset_id == "publication":
                self.cmd.hide("everything", "all")
                self.cmd.show("cartoon", "polymer")
                self.cmd.show("sticks", "organic")
                self.cmd.hide("everything", "solvent")
                self.cmd.util.cbc("polymer")
                self.cmd.util.cbag("organic")
                self.cmd.set("ray_shadow", 0)
                self.cmd.set("antialias", 2)
                self.cmd.set("ambient", 0.5)
                self.cmd.set("spec_reflect", 0.3)
                self.cmd.bg_color("white")
                self.cmd.orient()

            elif preset_id == "binding_site":
                self.cmd.hide("everything", "all")
                self.cmd.show("cartoon", "polymer")
                self.cmd.set("cartoon_transparency", 0.7, "polymer")
                self.cmd.show("sticks", "organic")
                self.cmd.util.cbag("organic")
                sel = "byres(organic around 5) and polymer"
                self.cmd.show("sticks", sel)
                self.cmd.show("lines", sel)
                self.cmd.util.cbag(sel)
                self.cmd.zoom(sel, 5)
                self.cmd.center("organic")

            elif preset_id == "bfactor":
                self.cmd.hide("everything", "all")
                self.cmd.show("cartoon", "polymer")
                self.cmd.cartoon("putty", "polymer")
                self.cmd.spectrum("b", "blue_white_red", "polymer")
                self.cmd.orient()

            elif preset_id == "technical":
                self.cmd.hide("everything", "all")
                self.cmd.show("sticks", "all")
                self.cmd.show("spheres", "all")
                self.cmd.set("sphere_scale", 0.2)
                self.cmd.set("stick_radius", 0.1)
                self.cmd.util.cbag("all")
                self.cmd.orient()

            elif preset_id == "ligand_interactions":
                self.cmd.hide("everything", "all")
                self.cmd.show("cartoon", "polymer")
                self.cmd.set("cartoon_transparency", 0.75, "polymer")
                self.cmd.show("sticks", "organic")
                self.cmd.util.cbag("organic")
                # Show binding site residues
                sel = "byres(organic around 4) and polymer"
                self.cmd.show("sticks", sel)
                self.cmd.util.cbag(sel)
                # Polar contacts
                self.cmd.distance(
                    "polar_contacts", "organic", sel,
                    mode=2, cutoff=3.5, quiet=1
                )
                self.cmd.set("dash_color", "yellow", "polar_contacts")
                self.cmd.set("dash_gap", 0.3, "polar_contacts")
                self.cmd.set("dash_radius", 0.06, "polar_contacts")
                self.cmd.zoom("organic", 6)

        except Exception as e:
            print(f"Preset error: {e}")

    def _change_bg(self, index):
        colors = ["black", "white", "gray", "lightblue"]
        if index < len(colors):
            self.cmd.bg_color(colors[index])

    def _change_grid(self, index):
        # 0=Off, 1=Dots, 2=Lines
        try:
            self.cmd.delete(GRID_OBJ_NAME)
        except Exception:
            pass
        if index == 1:
            self.cmd.load_cgo(_build_dot_grid(), GRID_OBJ_NAME)
        elif index == 2:
            self.cmd.load_cgo(_build_line_grid(), GRID_OBJ_NAME)
