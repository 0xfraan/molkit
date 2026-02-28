# AGENTS.md

This file gives AI coding agents full context to work on MolKit effectively.

## Project Overview

MolKit is a PySide6/Qt6 plugin for PyMOL that replaces the CLI-heavy interface with a visual sidebar and inspector panel. Users can search for protein structures, change representations, color molecules, build selections, take measurements, and export images -- all without typing PyMOL commands.

## Tech Stack

- **Python 3.9+**
- **PySide6 (Qt6)** -- bundled with PyMOL, NOT a separate dependency
- **Zero external dependencies** -- everything uses stdlib (`urllib` for HTTP, `json` for parsing)
- **RCSB APIs** -- Search API (`search.rcsb.org`) for PDB text search, GraphQL API (`data.rcsb.org/graphql`) for structure metadata

## File Map

```
molkit/                       Plugin package (all source lives here)
  __init__.py                 Entry point: registers "MolKit" menu item via
                              plugins.addmenuitemqt(), auto-opens sidebar
                              500ms after PyMOL startup
  sidebar.py                  Left sidebar: MolKitSidebar (QDockWidget) wrapping
                              MolKitSidebarWidget with CollapsibleSection accordion
  inspector.py                Right panel: InspectorDock shows RCSB metadata
                              (publications, chains, domains, ligands, quality)
  tabs.py                     ModelTabBar: tab bar for switching loaded structures,
                              saves/restores camera view per tab
  rcsb_client.py              RCSB PDB API client: search_pdb(), fetch_entry_metadata(),
                              fetch_batch_metadata(), parse_entry_summary()
  sections/                   Independent UI modules, one per sidebar section:
    loader.py                   PDB search with SearchWorker (QThread), result cards,
                                example structures grid
    structure.py                Object list with visibility toggles, atom counts, delete
    view.py                     Representation selector (cartoon/sticks/surface/etc.),
                                presets, toggles (water/hydrogen/ions)
    colors.py                   Color by element/chain/structure/B-factor/rainbow,
                                custom color picker
    selection.py                Visual selection builder (chain, residue range, proximity)
    measurements.py             Distance/angle/dihedral tools, H-bond and polar contact
                                detectors
    export.py                   Screenshot, ray-trace with quality slider, session save,
                                format export

pymol-open-source/            PyMOL source (git submodule, Schrodinger upstream)
scripts/
  setup-dev.sh                Inits submodule, symlinks molkit/ into PyMOL's
                              data/startup/ directory for development
docs/
  plans/                      Design documents and implementation plans
```

## Architecture

### Plugin Lifecycle

1. PyMOL loads `molkit/__init__.py` on startup (it lives in `data/startup/molkit/`).
2. `__init_plugin__()` registers a "MolKit" menu item and schedules `open_molkit()` via `QTimer.singleShot(500, ...)`.
3. `open_molkit()` finds the QMainWindow, creates `MolKitSidebar` (left dock) and `InspectorDock` (right dock), hides PyMOL's default external GUI.

### Widget Hierarchy

```
QMainWindow (PyMOL)
  +-- MolKitSidebar (QDockWidget, left)
  |     +-- MolKitSidebarWidget
  |           +-- ModelTabBar
  |           +-- LoaderSection
  |           +-- CollapsibleSection("Structures") -> StructureSection
  |           +-- CollapsibleSection("View")       -> ViewSection
  |           +-- CollapsibleSection("Colors")     -> ColorsSection
  |           +-- CollapsibleSection("Selection")  -> SelectionSection
  |           +-- CollapsibleSection("Measurements") -> MeasurementsSection
  |           +-- CollapsibleSection("Export")      -> ExportSection
  |           +-- CollapsibleSection("Console")
  +-- InspectorDock (QDockWidget, right)
        +-- InspectorWidget
```

### Communication Between Widgets

- **Qt signals/slots** connect everything. Sections never reference each other directly.
- `LoaderSection.structure_loaded` signal -> `ModelTabBar.add_tab()` + `StructureSection.refresh()`.
- `ModelTabBar.tab_changed` signal -> `InspectorWidget.load_entry()` (fetches RCSB metadata).
- `ModelTabBar.add_requested` signal -> scrolls to and focuses the search input.
- `ModelTabBar.tab_closed` signal -> `StructureSection.refresh()`.
- A `QTimer` (3-second interval) calls `ModelTabBar.sync_with_pymol()` to keep tabs in sync with PyMOL's object list.

### Async Pattern

Network requests (RCSB API) run in `QThread` workers to avoid blocking the UI. Pattern:

```python
class SearchWorker(QtCore.QThread):
    results_ready = QtCore.Signal(list)
    def run(self):
        results = search_pdb(self.query)
        self.results_ready.emit(results)
```

The worker emits a signal when done; the UI slot updates widgets on the main thread.

## PyMOL API Reference

All viewport operations use `from pymol import cmd`. Key methods:

| Method | Purpose |
|---|---|
| `cmd.fetch(pdb_id)` | Download and load a PDB structure |
| `cmd.load(filepath)` | Load a local file |
| `cmd.show(rep, selection)` | Show a representation (cartoon, sticks, surface, etc.) |
| `cmd.hide(rep, selection)` | Hide a representation |
| `cmd.color(color, selection)` | Color atoms |
| `cmd.select(name, sel_string)` | Create a named selection |
| `cmd.set(setting, value)` | Change a setting (e.g., `cmd.set("internal_gui", 0)`) |
| `cmd.get_object_list()` | List all loaded objects |
| `cmd.count_atoms(selection)` | Count atoms matching a selection |
| `cmd.get_view()` / `cmd.set_view()` | Save/restore camera position |
| `cmd.enable(name)` / `cmd.disable(name)` | Toggle object visibility |
| `cmd.delete(name)` | Delete an object |
| `cmd.zoom(selection, buffer)` | Zoom camera to selection |
| `cmd.iterate(sel, expr, space=)` | Run Python expression per atom |
| `cmd.bg_color(color)` | Set background color |

Qt imports come from PyMOL's wrapper: `from pymol.Qt import QtWidgets, QtCore, QtGui`.

## Conventions

- **No external dependencies.** Only stdlib + PyMOL's bundled PySide6.
- **Relative imports** within the plugin: `from .sidebar import ...`, `from .rcsb_client import ...`.
- **Sections are independent modules.** They communicate via Qt signals, never by holding direct references to each other.
- **Internal PyMOL objects** are prefixed with `_molkit_` (e.g., `_molkit_grid`) to avoid colliding with user objects.
- **Window attributes** are prefixed with `_molkit_` (e.g., `window._molkit_sidebar`, `window._molkit_inspector`).
- **Error handling**: PyMOL `cmd` calls are wrapped in `try/except` because they can fail if the object was deleted or the state changed.

## Development Workflow

```bash
# One-time setup
git clone --recursive <repo-url>
cd molkit
bash scripts/setup-dev.sh     # inits submodule, creates symlink

# Build PyMOL (requires C++17 compiler, CMake, OpenGL libs)
cd pymol-open-source && pip install .

# Run
pymol

# Edit-test cycle
# 1. Edit files in molkit/
# 2. Restart PyMOL to pick up changes
# 3. Exercise the UI manually
```

The `setup-dev.sh` script symlinks `molkit/` into `pymol-open-source/data/startup/molkit`. Edits to files in `molkit/` are immediately available on the next PyMOL restart -- no copy step needed.

## Testing

Currently manual. Launch PyMOL, load a structure (e.g., type "1aki" in the search bar), and exercise each sidebar section. There are no automated tests yet.

## Adding a New Sidebar Section

1. Create `molkit/sections/newsection.py` with a class inheriting `QtWidgets.QWidget`.
2. Accept `cmd` and `parent` in `__init__`, store `self.cmd = cmd`.
3. In `molkit/sidebar.py`, import the section, wrap it in a `CollapsibleSection`, and add it to `self.main_layout`.
4. If the section needs to react to structure changes, connect to existing signals (e.g., `self.tab_bar.tab_changed`).
5. Keep it independent -- emit signals for other sections to consume, never import sibling sections.
