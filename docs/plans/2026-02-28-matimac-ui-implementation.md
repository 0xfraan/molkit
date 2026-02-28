# MolKit UI — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a PyMOL Qt plugin that adds a friendly sidebar UI — welcome screen, structure loader, view/color controls, and export — hiding the CLI by default.

**Architecture:** PySide6 dockable sidebar plugin loaded from `data/startup/molkit/`. The plugin registers itself via `__init_plugin__()`, creates a `QDockWidget` on the left side of the PyMOL window, and hides the default external GUI (CLI/feedback). All PyMOL operations go through `pymol.cmd` API. The sidebar uses accordion-style collapsible sections (`QToolBox` or custom collapsible `QGroupBox`).

**Tech Stack:** Python 3.9+, PySide6 (via `pymol.Qt`), `pymol.cmd` API

**Key reference files:**
- Plugin loading: `modules/pymol/plugins/__init__.py`
- Qt main window: `modules/pmg_qt/pymol_qt_gui.py`
- Builder panel pattern: `modules/pmg_qt/builder.py`
- File dialogs: `modules/pmg_qt/file_dialogs.py`
- PyMOL Qt imports: `from pymol.Qt import QtWidgets, QtCore, QtGui`
- Plugin menu: `plugins.addmenuitemqt(label, callback)`

---

### Task 1: Plugin Skeleton + Sidebar Shell

**Files:**
- Create: `pymol-open-source/data/startup/molkit/__init__.py`
- Create: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Create plugin directory**

```bash
mkdir -p pymol-open-source/data/startup/molkit
```

**Step 2: Write plugin entry point**

Create `pymol-open-source/data/startup/molkit/__init__.py`:

```python
"""
MolKit - Friendly PyMOL Interface
Version: 0.1.0
"""


def __init_plugin__(app=None):
    from pymol import plugins
    plugins.addmenuitemqt('MolKit', open_molkit)


def open_molkit():
    from pymol import plugins
    from .sidebar import MolKitSidebar

    app = plugins.get_pmgapp()

    if not hasattr(app, '_molkit_sidebar'):
        app._molkit_sidebar = MolKitSidebar(app)
        app.addDockWidget(
            __import__('pymol.Qt.QtCore', fromlist=['Qt']).Qt.DockWidgetArea.LeftDockWidgetArea,
            app._molkit_sidebar,
        )
        # Hide the default external GUI (CLI)
        if hasattr(app, 'ext_window'):
            app.ext_window.hide()

    app._molkit_sidebar.show()
    app._molkit_sidebar.raise_()
```

**Step 3: Write sidebar shell**

Create `pymol-open-source/data/startup/molkit/sidebar.py`:

```python
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
        self.toggle_btn = QtWidgets.QPushButton(f"▼ {title}")
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
        arrow = "▼" if self._expanded else "▶"
        self.toggle_btn.setText(f"{arrow} {self._title}")

    def collapse(self):
        self._expanded = False
        self.content.setVisible(False)
        self.toggle_btn.setText(f"▶ {self._title}")

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


class MolKitSidebarWidget(QtWidgets.QWidget):
    """Main sidebar widget with collapsible sections."""

    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self.cmd = app.pymol.cmd
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

        # Sections will be added by Task 2-6
        self.main_layout.addStretch()

        scroll.setWidget(container)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def add_section(self, section):
        """Insert section before the stretch."""
        count = self.main_layout.count()
        self.main_layout.insertWidget(count - 1, section)


class MolKitSidebar(QtWidgets.QDockWidget):
    """Dockable sidebar wrapper."""

    def __init__(self, app, parent=None):
        super().__init__(parent or app)
        self.setWindowTitle("MolKit")
        self.setObjectName("molkit_sidebar")
        self.widget_inner = MolKitSidebarWidget(self, app=app)
        self.setWidget(self.widget_inner)
        self.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
```

**Step 4: Test manually**

Run PyMOL, open Plugin > MolKit. Verify:
- Empty sidebar appears docked on the left
- CLI/external GUI is hidden
- Sidebar can be resized, moved, floated

```bash
cd pymol-open-source && python -m pymol
# Then: Plugin > MolKit
```

**Step 5: Commit**

```bash
git add data/startup/molkit/
git commit -m "feat: molkit plugin skeleton with collapsible sidebar"
```

---

### Task 2: Welcome & Structure Loader Section

**Files:**
- Create: `pymol-open-source/data/startup/molkit/sections/___init__.py`
- Create: `pymol-open-source/data/startup/molkit/sections/loader.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Create sections package**

```bash
mkdir -p pymol-open-source/data/startup/molkit/sections
touch pymol-open-source/data/startup/molkit/sections/__init__.py
```

**Step 2: Write loader section**

Create `pymol-open-source/data/startup/molkit/sections/loader.py`:

```python
import os

from pymol.Qt import QtWidgets, QtCore, QtGui

Qt = QtCore.Qt


# Example structures for beginners
EXAMPLES = [
    ("Hemoglobina", "1HHO", "Oxygen transport protein"),
    ("Insulina", "4INS", "Hormone regulating blood sugar"),
    ("GFP", "1GFL", "Green fluorescent protein"),
    ("DNA double helix", "1BNA", "B-form DNA"),
    ("Lysozyme", "1AKI", "Classic enzyme structure"),
    ("ATP Synthase", "5ARA", "Molecular motor"),
]


class LoaderSection(QtWidgets.QWidget):
    """Welcome screen with PDB fetch, file open, and example structures."""

    structure_loaded = QtCore.Signal(str)  # emits object name

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- PDB Code Input ---
        pdb_label = QtWidgets.QLabel("Load from PDB:")
        pdb_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(pdb_label)

        pdb_row = QtWidgets.QHBoxLayout()
        self.pdb_input = QtWidgets.QLineEdit()
        self.pdb_input.setPlaceholderText("e.g. 1ATP")
        self.pdb_input.setMaxLength(4)
        self.pdb_input.returnPressed.connect(self._fetch_pdb)
        pdb_row.addWidget(self.pdb_input)

        fetch_btn = QtWidgets.QPushButton("Fetch")
        fetch_btn.clicked.connect(self._fetch_pdb)
        fetch_btn.setFixedWidth(60)
        pdb_row.addWidget(fetch_btn)
        layout.addLayout(pdb_row)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # --- File Open ---
        file_btn = QtWidgets.QPushButton("Open file from disk...")
        file_btn.clicked.connect(self._open_file)
        layout.addWidget(file_btn)

        # --- Separator ---
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # --- Examples ---
        examples_label = QtWidgets.QLabel("Examples to explore:")
        examples_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(examples_label)

        for name, pdb_id, desc in EXAMPLES:
            btn = QtWidgets.QPushButton(f"{name}  ({pdb_id})")
            btn.setToolTip(desc)
            btn.setStyleSheet("text-align: left; padding: 4px 8px;")
            btn.clicked.connect(lambda checked, pid=pdb_id: self._fetch_example(pid))
            layout.addWidget(btn)

        layout.addStretch()

    def _fetch_pdb(self):
        code = self.pdb_input.text().strip().upper()
        if not code or len(code) != 4:
            self.status_label.setText("Enter a 4-character PDB code.")
            self.status_label.setStyleSheet("color: red; font-size: 11px;")
            return
        self._do_fetch(code)

    def _fetch_example(self, pdb_id):
        self.pdb_input.setText(pdb_id)
        self._do_fetch(pdb_id)

    def _do_fetch(self, code):
        self.status_label.setText(f"Fetching {code}...")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        QtWidgets.QApplication.processEvents()
        try:
            self.cmd.fetch(code, quiet=0)
            self.cmd.orient()
            self.cmd.hide("everything", "all")
            self.cmd.show("cartoon", "polymer")
            self.cmd.show("sticks", "organic")
            self.cmd.show("spheres", "inorganic")
            self.cmd.hide("everything", "solvent")
            self.cmd.util.cbag("organic")
            self.cmd.util.cbc("polymer")
            self.cmd.bg_color("white")
            self.cmd.set("ray_shadow", 0)
            self.status_label.setText(
                f"Loaded {code} "
                f"({self.cmd.count_atoms('all')} atoms)"
            )
            self.status_label.setStyleSheet("color: green; font-size: 11px;")
            self.structure_loaded.emit(code)
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            self.status_label.setStyleSheet("color: red; font-size: 11px;")

    def _open_file(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Structure",
            "",
            "Structure files (*.pdb *.cif *.mol2 *.sdf *.mol *.xyz *.mae);;"
            "All files (*)",
        )
        if fname:
            self.status_label.setText(f"Loading {os.path.basename(fname)}...")
            QtWidgets.QApplication.processEvents()
            try:
                self.cmd.load(fname, quiet=0)
                self.cmd.orient()
                name = os.path.splitext(os.path.basename(fname))[0]
                self.status_label.setText(f"Loaded {name}")
                self.status_label.setStyleSheet("color: green; font-size: 11px;")
                self.structure_loaded.emit(name)
            except Exception as e:
                self.status_label.setText(f"Error: {e}")
                self.status_label.setStyleSheet("color: red; font-size: 11px;")
```

**Step 3: Wire loader into sidebar**

Modify `pymol-open-source/data/startup/molkit/sidebar.py` — add to `MolKitSidebarWidget.__init__()` after the stretch:

```python
# In __init__, before self.main_layout.addStretch():
from .sections.loader import LoaderSection
self.loader_section = LoaderSection(self.cmd, self)
self.main_layout.addWidget(self.loader_section)
# Then addStretch after
```

The full `__init__` becomes:

```python
def __init__(self, parent=None, app=None):
    super().__init__(parent)
    self.app = app
    self.cmd = app.pymol.cmd
    self.setMinimumWidth(280)
    self.setMaximumWidth(400)

    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

    container = QtWidgets.QWidget()
    self.main_layout = QtWidgets.QVBoxLayout(container)
    self.main_layout.setContentsMargins(0, 0, 0, 0)
    self.main_layout.setSpacing(0)

    # Welcome / Loader (always visible at top)
    from .sections.loader import LoaderSection
    self.loader = LoaderSection(self.cmd, self)
    self.main_layout.addWidget(self.loader)

    # Separator
    sep = QtWidgets.QFrame()
    sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
    self.main_layout.addWidget(sep)

    # Collapsible sections added by later tasks
    self.sections = {}

    self.main_layout.addStretch()

    scroll.setWidget(container)
    outer = QtWidgets.QVBoxLayout(self)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(scroll)
```

**Step 4: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Plugin > MolKit
# Type "1ATP" → Fetch → should load and show cartoon
# Click "Hemoglobina" → should load 1HHO
# Click "Open file..." → file dialog should appear
```

**Step 5: Commit**

```bash
git add data/startup/molkit/sections/
git commit -m "feat: welcome & structure loader section"
```

---

### Task 3: Structure Manager Section (Object List)

**Files:**
- Create: `pymol-open-source/data/startup/molkit/sections/structure.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Write structure manager**

Create `pymol-open-source/data/startup/molkit/sections/structure.py`:

```python
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
```

**Step 2: Wire into sidebar**

Modify `pymol-open-source/data/startup/molkit/sidebar.py` — add after the loader section:

```python
# After self.loader and separator, before self.main_layout.addStretch():
from .sections.structure import StructureSection
from .sidebar import CollapsibleSection

self.structure_section = CollapsibleSection("Structures")
self.structure_manager = StructureSection(self.cmd, self)
self.structure_section.add_widget(self.structure_manager)
self.main_layout.addWidget(self.structure_section)

# Connect loader signal to refresh structure list
self.loader.structure_loaded.connect(lambda _: self.structure_manager.refresh())
```

**Step 3: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Load 2 structures via loader
# Verify: both appear in Structures section with atom counts & chains
# Toggle visibility checkbox → object hides/shows
# Click 'x' → object deleted
# Wait 2s → list auto-refreshes
```

**Step 4: Commit**

```bash
git add data/startup/molkit/sections/structure.py
git commit -m "feat: structure manager section with object list"
```

---

### Task 4: View Section (Representations & Presets)

**Files:**
- Create: `pymol-open-source/data/startup/molkit/sections/view.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Write view section**

Create `pymol-open-source/data/startup/molkit/sections/view.py`:

```python
from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt

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
            btn.setStyleSheet("text-align: left; padding: 4px 8px;")
            btn.clicked.connect(lambda checked, pid=preset_id: self._apply_preset(pid))
            layout.addWidget(btn)

        # --- Background ---
        sep2 = QtWidgets.QFrame()
        sep2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(sep2)

        bg_row = QtWidgets.QHBoxLayout()
        bg_row.addWidget(QtWidgets.QLabel("Background:"))
        self.bg_combo = QtWidgets.QComboBox()
        self.bg_combo.addItems(["White", "Black", "Gray", "Light Blue"])
        self.bg_combo.currentIndexChanged.connect(self._change_bg)
        bg_row.addWidget(self.bg_combo, 1)
        layout.addLayout(bg_row)

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
        colors = ["white", "black", "gray", "lightblue"]
        if index < len(colors):
            self.cmd.bg_color(colors[index])
```

**Step 2: Wire into sidebar**

Add to `sidebar.py` `__init__` after the structure section:

```python
from .sections.view import ViewSection

self.view_section = CollapsibleSection("View")
self.view_panel = ViewSection(self.cmd, self)
self.view_section.add_widget(self.view_panel)
self.main_layout.addWidget(self.view_section)
```

**Step 3: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Load a structure, then:
# Change protein rep dropdown → cartoon/sticks/surface should switch
# Change ligand rep → sticks/spheres etc
# Toggle water/hydrogens checkboxes
# Click presets — especially "Binding Site Focus" and "Ligand Interactions"
# Change background color
```

**Step 4: Commit**

```bash
git add data/startup/molkit/sections/view.py
git commit -m "feat: view section with representations, toggles, and presets"
```

---

### Task 5: Colors Section

**Files:**
- Create: `pymol-open-source/data/startup/molkit/sections/colors.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Write colors section**

Create `pymol-open-source/data/startup/molkit/sections/colors.py`:

```python
from pymol.Qt import QtWidgets, QtCore, QtGui

Qt = QtCore.Qt

COLOR_SCHEMES = [
    ("By element (CPK)", "element"),
    ("By chain", "chain"),
    ("By secondary structure", "ss"),
    ("Rainbow (N→C)", "rainbow"),
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
                    f"background-color: rgb({r},{g},{b}); border: 1px solid gray;"
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
```

**Step 2: Wire into sidebar**

Add to `sidebar.py` `__init__` after view section:

```python
from .sections.colors import ColorsSection

self.colors_section = CollapsibleSection("Colors")
self.colors_panel = ColorsSection(self.cmd, self)
self.colors_section.add_widget(self.colors_panel)
self.main_layout.addWidget(self.colors_section)
```

**Step 3: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Load structure, then:
# Change target to "Protein" → apply "By chain" → chains get different colors
# Change target to "Ligands" → apply "By element" → CPK colors on ligand
# Select "Single color" → click red button → target turns red
# Click "Custom color..." → OS color picker → apply custom color
```

**Step 4: Commit**

```bash
git add data/startup/molkit/sections/colors.py
git commit -m "feat: colors section with schemes, palette, and custom picker"
```

---

### Task 6: Selection Builder Section

**Files:**
- Create: `pymol-open-source/data/startup/molkit/sections/selection.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Write selection builder**

Create `pymol-open-source/data/startup/molkit/sections/selection.py`:

```python
from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt


class SelectionSection(QtWidgets.QWidget):
    """Visual selection builder — no command syntax needed."""

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
            btn.setStyleSheet("padding: 3px 6px; font-size: 11px;")
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
        self.status.setStyleSheet("color: gray; font-size: 11px;")
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
            "<i style='color:gray;'>No saved selections</i>"
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
            self.status.setStyleSheet("color: green; font-size: 11px;")
        except Exception as e:
            self.status.setText(f"Error: {e}")
            self.status.setStyleSheet("color: red; font-size: 11px;")
```

**Step 2: Wire into sidebar**

Add to `sidebar.py` `__init__`:

```python
from .sections.selection import SelectionSection

self.selection_section = CollapsibleSection("Selection")
self.selection_panel = SelectionSection(self.cmd, self)
self.selection_section.add_widget(self.selection_panel)
self.selection_section.collapse()  # collapsed by default
self.main_layout.addWidget(self.selection_section)
```

**Step 3: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Load structure, then:
# Quick Select: click "Protein" → highlights protein
# Quick Select: click "Ligands" → highlights ligands
# Builder: select Chain A, residues 40-60 → Select → verify selection
# Builder: check "Within 5A of ligand" → Select → binding site selected
```

**Step 4: Commit**

```bash
git add data/startup/molkit/sections/selection.py
git commit -m "feat: visual selection builder with quick selects and chain/residue picker"
```

---

### Task 7: Measurements Section

**Files:**
- Create: `pymol-open-source/data/startup/molkit/sections/measurements.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Write measurements section**

Create `pymol-open-source/data/startup/molkit/sections/measurements.py`:

```python
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

            n = self.cmd.count_atoms("hbonds") if self.cmd.get_names_of_type("object:measurement") else 0
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
```

**Step 2: Wire into sidebar**

Add to `sidebar.py` `__init__`:

```python
from .sections.measurements import MeasurementsSection

self.measurements_section = CollapsibleSection("Measurements")
self.measurements_panel = MeasurementsSection(self.cmd, self)
self.measurements_section.add_widget(self.measurements_panel)
self.measurements_section.collapse()
self.main_layout.addWidget(self.measurements_section)
```

**Step 3: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Load structure with ligand (e.g. 1ATP), then:
# Click "Show Hydrogen Bonds" → yellow dashes appear
# Click "Show Polar Contacts" → cyan dashes
# Click 2 atoms in viewport → Distance button → shows measurement
# Click "Clear All Measurements" → all dashes removed
```

**Step 4: Commit**

```bash
git add data/startup/molkit/sections/measurements.py
git commit -m "feat: measurements section with H-bonds, polar contacts, distances"
```

---

### Task 8: Export Section

**Files:**
- Create: `pymol-open-source/data/startup/molkit/sections/export.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Write export section**

Create `pymol-open-source/data/startup/molkit/sections/export.py`:

```python
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
```

**Step 2: Wire into sidebar**

Add to `sidebar.py` `__init__`:

```python
from .sections.export import ExportSection

self.export_section = CollapsibleSection("Export")
self.export_panel = ExportSection(self.cmd, self)
self.export_section.add_widget(self.export_panel)
self.export_section.collapse()
self.main_layout.addWidget(self.export_section)
```

**Step 3: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Load structure, set up nice view, then:
# Quick Screenshot → file dialog → saves PNG
# Ray-traced Image → slower, higher quality
# Save Session → saves .pse
# Export Structure → PDB/CIF dialog
```

**Step 4: Commit**

```bash
git add data/startup/molkit/sections/export.py
git commit -m "feat: export section with screenshot, ray-trace, session, and structure export"
```

---

### Task 9: Wire Everything Together + Auto-open on Startup

**Files:**
- Modify: `pymol-open-source/data/startup/molkit/__init__.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Finalize sidebar.py with all sections**

The final `MolKitSidebarWidget.__init__` should have all sections in order:

```python
def __init__(self, parent=None, app=None):
    super().__init__(parent)
    self.app = app
    self.cmd = app.pymol.cmd
    self.setMinimumWidth(280)
    self.setMaximumWidth(400)

    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

    container = QtWidgets.QWidget()
    self.main_layout = QtWidgets.QVBoxLayout(container)
    self.main_layout.setContentsMargins(0, 0, 0, 0)
    self.main_layout.setSpacing(0)

    # 1. Loader (always visible)
    from .sections.loader import LoaderSection
    self.loader = LoaderSection(self.cmd, self)
    self.main_layout.addWidget(self.loader)

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
    self.console_section.collapse()
    self.main_layout.addWidget(self.console_section)

    self.main_layout.addStretch()

    scroll.setWidget(container)
    outer = QtWidgets.QVBoxLayout(self)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(scroll)

    # Connect loader → structure refresh
    self.loader.structure_loaded.connect(
        lambda _: self.structure_manager.refresh()
    )

def _toggle_console(self):
    """Toggle the PyMOL external GUI (console)."""
    if hasattr(self.app, 'ext_window'):
        if self.app.ext_window.isVisible():
            self.app.ext_window.hide()
        else:
            self.app.ext_window.show()
```

**Step 2: Update __init__.py for auto-open**

Update `pymol-open-source/data/startup/molkit/__init__.py`:

```python
"""
MolKit - Friendly PyMOL Interface
Version: 0.1.0
"""

from pymol.Qt import QtCore


def __init_plugin__(app=None):
    from pymol import plugins
    plugins.addmenuitemqt('MolKit', open_molkit)

    # Auto-open on startup (slight delay to let PyMOL finish init)
    QtCore.QTimer.singleShot(500, open_molkit)


def open_molkit():
    from pymol import plugins
    from pymol.Qt import QtCore

    Qt = QtCore.Qt

    app = plugins.get_pmgapp()
    if app is None:
        return

    if not hasattr(app, '_molkit_sidebar'):
        from .sidebar import MolKitSidebar

        app._molkit_sidebar = MolKitSidebar(app)
        app.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea,
            app._molkit_sidebar,
        )

        # Hide the default external GUI (CLI)
        if hasattr(app, 'ext_window'):
            app.ext_window.hide()

        # Hide internal GUI elements
        try:
            from pymol import cmd
            cmd.set("internal_gui", 0)
            cmd.set("internal_feedback", 0)
        except Exception:
            pass

    app._molkit_sidebar.show()
    app._molkit_sidebar.raise_()
```

**Step 3: Test full flow**

```bash
cd pymol-open-source && python -m pymol
# On startup: MolKit sidebar should auto-appear on the left
# CLI should be hidden
# Full workflow:
# 1. Type "1ATP" → Fetch → protein loads with nice defaults
# 2. Structures section shows "1ATP" with atom count
# 3. View: change protein to Surface → surface appears
# 4. Colors: select "By chain" → Apply → chains colored
# 5. Selection: Quick Select "Ligands" → ligand highlighted
# 6. Measurements: "Show H-bonds" → yellow dashes
# 7. Export: Quick Screenshot → save PNG
# 8. Console: click "Show PyMOL Console" → CLI appears
```

**Step 4: Commit**

```bash
git add data/startup/molkit/
git commit -m "feat: wire all sections together, auto-open on startup, hide CLI"
```

---

### Task 10: Final Testing & Polish

**Step 1: Test with multiple structures**

```bash
cd pymol-open-source && python -m pymol
# Load multiple structures:
# 1. Fetch 1ATP
# 2. Fetch 1HHO
# Verify structure manager shows both
# Toggle visibility of each
# Delete one
# Change colors independently
```

**Step 2: Test edge cases**

- Open with no structures loaded — sidebar should show loader
- Fetch invalid PDB code — should show error message
- Open very large structure — verify performance
- Resize sidebar — verify scrolling works
- Float sidebar — verify it works as floating window
- Re-dock sidebar — verify it docks back

**Step 3: Commit final state**

```bash
git add data/startup/molkit/
git commit -m "chore: final testing and polish for molkit v0.1.0"
```
