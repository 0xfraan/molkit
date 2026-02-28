# Search, Tabs & Inspector — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add PDB text search with results, model tabs for switching between loaded structures, and a rich molecule inspector panel on the right that shows publications, domains, chains, ligands, binding sites — all clickable.

**Architecture:** Three independent features built as modules within the existing MolKit plugin (`pymol-open-source/data/startup/molkit/`). The RCSB client module handles all API calls (Search API for text search, GraphQL for metadata). Tabs are a QTabBar widget wired into the sidebar. Inspector is a new QDockWidget on the right side. All features use `pymol.cmd` for viewport interaction.

**Tech Stack:** Python 3.9+, PySide6 (via `pymol.Qt`), `urllib.request` for HTTP (no external deps), RCSB Search API + GraphQL Data API

**Key existing files:**
- Plugin entry: `pymol-open-source/data/startup/molkit/__init__.py`
- Sidebar: `pymol-open-source/data/startup/molkit/sidebar.py`
- Loader: `pymol-open-source/data/startup/molkit/sections/loader.py`
- Structure manager: `pymol-open-source/data/startup/molkit/sections/structure.py`
- CollapsibleSection widget: defined in `sidebar.py`

---

### Task 1: RCSB API Client Module

**Files:**
- Create: `pymol-open-source/data/startup/molkit/rcsb_client.py`

**Step 1: Write the RCSB client**

Create `pymol-open-source/data/startup/molkit/rcsb_client.py`:

```python
"""
RCSB PDB API client.
Uses only stdlib (urllib) — no external dependencies.
"""

import json
import urllib.request
import urllib.error
from typing import Optional


SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
GRAPHQL_URL = "https://data.rcsb.org/graphql"


def _post_json(url: str, payload: dict, timeout: float = 10.0) -> dict:
    """POST JSON and return parsed response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_pdb(query: str, max_results: int = 10) -> list[str]:
    """
    Full-text search on RCSB. Returns list of PDB IDs.
    """
    payload = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": query},
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": max_results},
            "results_content_type": ["experimental"],
        },
    }
    try:
        result = _post_json(SEARCH_URL, payload)
        return [r["identifier"] for r in result.get("result_set", [])]
    except Exception:
        return []


# GraphQL query that fetches everything we need for the inspector
_ENTRY_QUERY = """
query($id: String!) {
  entry(entry_id: $id) {
    rcsb_id
    struct { title }
    exptl { method }
    rcsb_entry_info {
      resolution_combined
      molecular_weight
      deposited_atom_count
      polymer_entity_count
      nonpolymer_entity_count
      polymer_composition
    }
    rcsb_accession_info { deposit_date initial_release_date }
    rcsb_primary_citation {
      title journal_abbrev year
      pdbx_database_id_PubMed pdbx_database_id_DOI
      rcsb_authors
    }
    citation {
      id title journal_abbrev year
      pdbx_database_id_PubMed pdbx_database_id_DOI
      rcsb_authors
    }
    polymer_entities {
      rcsb_id
      rcsb_polymer_entity { pdbx_description formula_weight }
      entity_poly {
        pdbx_seq_one_letter_code_can type rcsb_entity_polymer_type
      }
      rcsb_entity_source_organism { ncbi_scientific_name }
      rcsb_polymer_entity_annotation {
        annotation_id type
        annotation_lineage { id name }
      }
      rcsb_polymer_entity_feature {
        type name
        feature_positions { beg_seq_id end_seq_id }
      }
      polymer_entity_instances {
        rcsb_id
        rcsb_polymer_instance_annotation {
          annotation_id type
          annotation_lineage { id name }
        }
        rcsb_polymer_instance_feature {
          type name
          feature_positions { beg_seq_id end_seq_id }
        }
      }
    }
    nonpolymer_entities {
      rcsb_nonpolymer_entity { pdbx_description formula_weight }
      nonpolymer_comp {
        chem_comp { name type formula }
      }
    }
  }
}
"""

# Lighter query for search result cards (batch)
_BATCH_QUERY = """
query($ids: [String!]!) {
  entries(entry_ids: $ids) {
    rcsb_id
    struct { title }
    exptl { method }
    rcsb_entry_info { resolution_combined molecular_weight }
    rcsb_accession_info { deposit_date }
    polymer_entities {
      rcsb_polymer_entity { pdbx_description }
      rcsb_entity_source_organism { ncbi_scientific_name }
    }
  }
}
"""


def fetch_entry_metadata(pdb_id: str) -> Optional[dict]:
    """Fetch full metadata for a single PDB entry. Returns raw GraphQL data."""
    try:
        result = _post_json(GRAPHQL_URL, {
            "query": _ENTRY_QUERY,
            "variables": {"id": pdb_id.upper()},
        })
        return result.get("data", {}).get("entry")
    except Exception:
        return None


def fetch_batch_metadata(pdb_ids: list[str]) -> list[dict]:
    """Fetch summary metadata for multiple PDB entries."""
    if not pdb_ids:
        return []
    try:
        result = _post_json(GRAPHQL_URL, {
            "query": _BATCH_QUERY,
            "variables": {"ids": [pid.upper() for pid in pdb_ids]},
        })
        return result.get("data", {}).get("entries") or []
    except Exception:
        return []


def parse_entry_summary(entry: dict) -> dict:
    """Parse a GraphQL entry into a flat summary dict for display."""
    if not entry:
        return {}

    info = entry.get("rcsb_entry_info") or {}
    exptl = (entry.get("exptl") or [{}])[0]
    acc = entry.get("rcsb_accession_info") or {}

    # Find primary organism
    organism = ""
    for pe in entry.get("polymer_entities") or []:
        for org in pe.get("rcsb_entity_source_organism") or []:
            name = org.get("ncbi_scientific_name", "")
            if name:
                organism = name
                break
        if organism:
            break

    res = info.get("resolution_combined")
    resolution = res[0] if res else None

    return {
        "pdb_id": entry.get("rcsb_id", ""),
        "title": (entry.get("struct") or {}).get("title", ""),
        "method": exptl.get("method", ""),
        "resolution": resolution,
        "molecular_weight": info.get("molecular_weight"),
        "atom_count": info.get("deposited_atom_count"),
        "polymer_count": info.get("polymer_entity_count"),
        "organism": organism,
        "deposit_date": (acc.get("deposit_date") or "")[:10],
    }
```

**Step 2: Test manually**

```bash
cd pymol-open-source && python -c "
import sys; sys.path.insert(0, 'data/startup')
from molkit.rcsb_client import search_pdb, fetch_batch_metadata, fetch_entry_metadata, parse_entry_summary

# Test search
ids = search_pdb('hemoglobin')
print('Search results:', ids[:5])

# Test batch
entries = fetch_batch_metadata(ids[:3])
for e in entries:
    s = parse_entry_summary(e)
    print(f'{s[\"pdb_id\"]}: {s[\"title\"][:60]}... | {s[\"organism\"]} | {s[\"resolution\"]}A')

# Test full entry
full = fetch_entry_metadata('1ATP')
print(f'Full entry chains: {len(full.get(\"polymer_entities\", []))}')
print(f'Citations: {len(full.get(\"citation\", []))}')
"
```

**Step 3: Commit**

```bash
git add data/startup/molkit/rcsb_client.py
git commit -m "feat: RCSB API client for search and metadata"
```

---

### Task 2: PDB Search in Loader

**Files:**
- Modify: `pymol-open-source/data/startup/molkit/sections/loader.py`

**Step 1: Rewrite loader with search**

Replace the contents of `pymol-open-source/data/startup/molkit/sections/loader.py` with the version below. Key changes:
- Input field accepts both 4-char codes AND text queries
- No maxLength restriction
- Debounce timer (500ms) triggers search when text >= 3 chars
- Search results shown as cards with metadata
- 4-char exact input still does instant fetch
- Examples section remains at bottom

```python
import os

from pymol.Qt import QtWidgets, QtCore, QtGui

Qt = QtCore.Qt


EXAMPLES = [
    ("Hemoglobin", "1HHO", "Oxygen transport protein"),
    ("Insulin", "4INS", "Hormone regulating blood sugar"),
    ("GFP", "1GFL", "Green fluorescent protein"),
    ("DNA double helix", "1BNA", "B-form DNA"),
    ("Lysozyme", "1AKI", "Classic enzyme structure"),
    ("ATP Synthase", "5ARA", "Molecular motor"),
]


class SearchWorker(QtCore.QThread):
    """Background thread for RCSB search + metadata fetch."""
    results_ready = QtCore.Signal(list)  # list of summary dicts

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.query = query

    def run(self):
        from molkit.rcsb_client import search_pdb, fetch_batch_metadata, parse_entry_summary
        ids = search_pdb(self.query, max_results=8)
        if not ids:
            self.results_ready.emit([])
            return
        entries = fetch_batch_metadata(ids)
        summaries = [parse_entry_summary(e) for e in entries]
        self.results_ready.emit(summaries)


class SearchResultCard(QtWidgets.QFrame):
    """Single search result as a clickable card."""
    load_requested = QtCore.Signal(str)  # emits PDB ID

    def __init__(self, summary: dict, parent=None):
        super().__init__(parent)
        self.pdb_id = summary.get("pdb_id", "")
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            SearchResultCard {
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px;
                margin: 2px 0px;
            }
            SearchResultCard:hover {
                border-color: palette(highlight);
                background: palette(midlight);
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        # Top row: PDB ID + method + resolution
        top = QtWidgets.QHBoxLayout()
        id_label = QtWidgets.QLabel(f"<b>{self.pdb_id}</b>")
        top.addWidget(id_label)

        method = summary.get("method", "")
        res = summary.get("resolution")
        meta_parts = []
        if method:
            meta_parts.append(method.replace("X-RAY DIFFRACTION", "X-ray")
                             .replace("ELECTRON MICROSCOPY", "Cryo-EM")
                             .replace("SOLUTION NMR", "NMR"))
        if res:
            meta_parts.append(f"{res:.1f} A")
        if meta_parts:
            meta = QtWidgets.QLabel(" | ".join(meta_parts))
            meta.setStyleSheet("color: gray; font-size: 11px;")
            top.addWidget(meta)

        top.addStretch()

        load_btn = QtWidgets.QPushButton("Load")
        load_btn.setFixedWidth(50)
        load_btn.clicked.connect(lambda: self.load_requested.emit(self.pdb_id))
        top.addWidget(load_btn)

        layout.addLayout(top)

        # Title
        title = summary.get("title", "")
        if title:
            title_label = QtWidgets.QLabel(title[:120] + ("..." if len(title) > 120 else ""))
            title_label.setWordWrap(True)
            title_label.setStyleSheet("font-size: 11px;")
            layout.addWidget(title_label)

        # Organism + date
        bottom_parts = []
        org = summary.get("organism", "")
        if org:
            bottom_parts.append(f"<i>{org}</i>")
        date = summary.get("deposit_date", "")
        if date:
            bottom_parts.append(date[:4])
        if bottom_parts:
            bottom = QtWidgets.QLabel(" | ".join(bottom_parts))
            bottom.setStyleSheet("color: gray; font-size: 10px;")
            layout.addWidget(bottom)


class LoaderSection(QtWidgets.QWidget):
    """Welcome screen with PDB search, file open, and example structures."""

    structure_loaded = QtCore.Signal(str)  # emits PDB ID or object name

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self._worker = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- Search Input ---
        search_label = QtWidgets.QLabel("Search or enter PDB code:")
        search_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(search_label)

        search_row = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("e.g. 1ATP or hemoglobin kinase...")
        self.search_input.returnPressed.connect(self._on_enter)
        self.search_input.textChanged.connect(self._on_text_changed)
        search_row.addWidget(self.search_input)

        self.search_btn = QtWidgets.QPushButton("Go")
        self.search_btn.setFixedWidth(50)
        self.search_btn.clicked.connect(self._on_enter)
        search_row.addWidget(self.search_btn)
        layout.addLayout(search_row)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # --- Search Results (hidden until search) ---
        self.results_container = QtWidgets.QWidget()
        self.results_layout = QtWidgets.QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(4)
        self.results_container.setVisible(False)
        layout.addWidget(self.results_container)

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
        self.examples_widget = QtWidgets.QWidget()
        examples_layout = QtWidgets.QVBoxLayout(self.examples_widget)
        examples_layout.setContentsMargins(0, 0, 0, 0)
        examples_layout.setSpacing(4)

        examples_label = QtWidgets.QLabel("Examples to explore:")
        examples_label.setStyleSheet("font-weight: bold;")
        examples_layout.addWidget(examples_label)

        for name, pdb_id, desc in EXAMPLES:
            btn = QtWidgets.QPushButton(f"{name}  ({pdb_id})")
            btn.setToolTip(desc)
            btn.setStyleSheet("text-align: left; padding: 4px 8px;")
            btn.clicked.connect(lambda checked, pid=pdb_id: self._do_fetch(pid))
            examples_layout.addWidget(btn)

        layout.addWidget(self.examples_widget)
        layout.addStretch()

        # Debounce timer for search
        self._debounce = QtCore.QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(500)
        self._debounce.timeout.connect(self._do_search)

    def _on_text_changed(self, text):
        text = text.strip()
        # If it looks like a PDB code, don't auto-search
        if len(text) == 4 and text.isalnum():
            self._debounce.stop()
            return
        if len(text) >= 3:
            self._debounce.start()
        else:
            self._debounce.stop()
            self._clear_results()

    def _on_enter(self):
        text = self.search_input.text().strip()
        if not text:
            return
        # 4-char alphanumeric = PDB code → direct fetch
        if len(text) == 4 and text.isalnum():
            self._do_fetch(text.upper())
        else:
            self._debounce.stop()
            self._do_search()

    def _do_search(self):
        query = self.search_input.text().strip()
        if len(query) < 3:
            return
        self.status_label.setText(f"Searching '{query}'...")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        self._clear_results()

        self._worker = SearchWorker(query, self)
        self._worker.results_ready.connect(self._show_results)
        self._worker.start()

    def _show_results(self, summaries):
        self._clear_results()
        if not summaries:
            self.status_label.setText("No results found.")
            self.status_label.setStyleSheet("color: orange; font-size: 11px;")
            return

        self.status_label.setText(f"{len(summaries)} results:")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        self.results_container.setVisible(True)
        self.examples_widget.setVisible(False)

        for s in summaries:
            card = SearchResultCard(s, self.results_container)
            card.load_requested.connect(self._do_fetch)
            self.results_layout.addWidget(card)

    def _clear_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.results_container.setVisible(False)
        self.examples_widget.setVisible(True)

    def _do_fetch(self, code):
        self.search_input.setText(code)
        self.status_label.setText(f"Fetching {code}...")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        self._clear_results()
        QtWidgets.QApplication.processEvents()
        try:
            # Disable all existing objects so new one opens in its own "tab"
            for obj in self.cmd.get_object_list():
                self.cmd.disable(obj)

            self.cmd.fetch(code, quiet=0)
            self.cmd.orient()
            self.cmd.hide("everything", code)
            self.cmd.show("cartoon", f"{code} and polymer")
            self.cmd.show("sticks", f"{code} and organic")
            self.cmd.show("spheres", f"{code} and inorganic")
            self.cmd.hide("everything", f"{code} and solvent")
            self.cmd.util.cbag(f"{code} and organic")
            self.cmd.util.cbc(f"{code} and polymer")
            self.cmd.set("ray_shadow", 0)
            self.status_label.setText(
                f"Loaded {code} "
                f"({self.cmd.count_atoms(code)} atoms)"
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
            # Disable existing objects
            for obj in self.cmd.get_object_list():
                self.cmd.disable(obj)

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

**Step 2: Test manually**

```bash
cd pymol-open-source && python -m pymol
# In MolKit:
# Type "hemoglobin" → wait 500ms → search results appear as cards
# Type "1ATP" → Enter → immediate fetch
# Click "Load" on a search result → loads that structure
# Click example button → loads example
```

**Step 3: Commit**

```bash
git add data/startup/molkit/sections/loader.py
git commit -m "feat: PDB text search with result cards and debounce"
```

---

### Task 3: Model Tabs (QTabBar)

**Files:**
- Create: `pymol-open-source/data/startup/molkit/tabs.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`
- Modify: `pymol-open-source/data/startup/molkit/__init__.py`

**Step 1: Write tabs widget**

Create `pymol-open-source/data/startup/molkit/tabs.py`:

```python
from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt


class ModelTabBar(QtWidgets.QWidget):
    """Tab bar for switching between loaded models."""

    tab_changed = QtCore.Signal(str)  # emits active object name
    tab_closed = QtCore.Signal(str)   # emits closed object name
    add_requested = QtCore.Signal()   # user clicked [+]

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self._views = {}       # object_name -> view tuple
        self._show_all = False

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab bar
        self.tab_bar = QtWidgets.QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close)
        layout.addWidget(self.tab_bar, 1)

        # Add button
        add_btn = QtWidgets.QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setToolTip("Load another structure")
        add_btn.clicked.connect(self.add_requested.emit)
        layout.addWidget(add_btn)

        # Show All checkbox
        self.show_all_cb = QtWidgets.QCheckBox("Show all")
        self.show_all_cb.setToolTip("Overlay all models in viewport")
        self.show_all_cb.toggled.connect(self._on_show_all)
        layout.addWidget(self.show_all_cb)

        self.setMaximumHeight(36)

    def add_tab(self, name: str):
        """Add a tab for a newly loaded model."""
        # Check if tab already exists
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i) == name:
                self.tab_bar.setCurrentIndex(i)
                return

        idx = self.tab_bar.addTab(name)
        self.tab_bar.setTabData(idx, name)
        self.tab_bar.setCurrentIndex(idx)

    def remove_tab(self, name: str):
        """Remove tab by object name."""
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i) == name:
                self.tab_bar.removeTab(i)
                self._views.pop(name, None)
                return

    def _save_current_view(self):
        """Save camera view for current tab."""
        idx = self.tab_bar.currentIndex()
        if idx < 0:
            return
        name = self.tab_bar.tabData(idx)
        if name:
            try:
                self._views[name] = self.cmd.get_view()
            except Exception:
                pass

    def _on_tab_changed(self, index):
        if index < 0:
            return

        name = self.tab_bar.tabData(index)
        if not name:
            return

        if not self._show_all:
            # Save view of previous tab before switching
            # (already saved when leaving, but be safe)
            # Disable all, enable active
            try:
                for obj in self.cmd.get_object_list():
                    self.cmd.disable(obj)
                self.cmd.enable(name)

                # Restore saved view
                if name in self._views:
                    self.cmd.set_view(self._views[name])
            except Exception:
                pass

        self.tab_changed.emit(name)

    def _on_tab_close(self, index):
        name = self.tab_bar.tabData(index)
        if not name:
            return

        self.tab_bar.removeTab(index)
        self._views.pop(name, None)

        try:
            self.cmd.delete(name)
        except Exception:
            pass

        self.tab_closed.emit(name)

    def _on_show_all(self, checked):
        self._show_all = checked
        try:
            if checked:
                for obj in self.cmd.get_object_list():
                    self.cmd.enable(obj)
            else:
                # Switch back to single-tab mode
                self._on_tab_changed(self.tab_bar.currentIndex())
        except Exception:
            pass

    def sync_with_pymol(self):
        """Sync tabs with actual PyMOL objects."""
        try:
            objects = set(self.cmd.get_object_list())
        except Exception:
            return

        # Remove tabs for deleted objects
        for i in range(self.tab_bar.count() - 1, -1, -1):
            name = self.tab_bar.tabData(i)
            if name not in objects:
                self.tab_bar.removeTab(i)
                self._views.pop(name, None)

        # Add tabs for new objects (don't auto-add — only via loader)
```

**Step 2: Wire tabs into sidebar and __init__**

Modify `pymol-open-source/data/startup/molkit/sidebar.py`:

Add the tab bar at the very top of `MolKitSidebarWidget.__init__`, BEFORE the loader section:

```python
# In MolKitSidebarWidget.__init__, add before the loader:

# Model tabs
from .tabs import ModelTabBar
self.tab_bar = ModelTabBar(self.cmd, self)
self.main_layout.addWidget(self.tab_bar)
```

Then connect the signals at the end of `__init__`, replacing the existing connect:

```python
# Connect loader → add tab + refresh
def _on_structure_loaded(name):
    self.tab_bar._save_current_view()
    self.tab_bar.add_tab(name)
    self.structure_manager.refresh()

self.loader.structure_loaded.connect(_on_structure_loaded)

# Connect tab [+] → scroll to loader
self.tab_bar.add_requested.connect(
    lambda: self.search_input_focus()
)

# Connect tab close → refresh structure list
self.tab_bar.tab_closed.connect(lambda _: self.structure_manager.refresh())

# Sync timer
self._sync_timer = QtCore.QTimer(self)
self._sync_timer.timeout.connect(self.tab_bar.sync_with_pymol)
self._sync_timer.start(3000)
```

Add this method to `MolKitSidebarWidget`:

```python
def search_input_focus(self):
    """Scroll to top and focus the search input."""
    self.loader.search_input.setFocus()
    self.loader.search_input.selectAll()
```

**Step 3: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Load 1ATP → tab "1ATP" appears
# Load 1HHO → tab "1HHO" appears, 1ATP hidden
# Click "1ATP" tab → switches view, 1HHO hidden
# Check "Show all" → both visible
# Uncheck → back to single model
# Click X on tab → model deleted
# Click [+] → focus goes to search input
```

**Step 4: Commit**

```bash
git add data/startup/molkit/tabs.py data/startup/molkit/sidebar.py
git commit -m "feat: model tabs with view save/restore and show-all toggle"
```

---

### Task 4: Inspector Panel — Shell + Overview

**Files:**
- Create: `pymol-open-source/data/startup/molkit/inspector.py`
- Modify: `pymol-open-source/data/startup/molkit/__init__.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Write inspector shell with Overview section**

Create `pymol-open-source/data/startup/molkit/inspector.py`:

```python
import webbrowser

from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt


class InspectorWidget(QtWidgets.QWidget):
    """Right-side panel showing rich info about the active structure."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self._data = None  # raw GraphQL entry data
        self._pdb_id = None
        self.setMinimumWidth(260)
        self.setMaximumWidth(380)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        container = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout(container)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)

        self.placeholder = QtWidgets.QLabel(
            "<i style='color:gray;'>Load a structure to see details</i>"
        )
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.placeholder)
        self.main_layout.addStretch()

        scroll.setWidget(container)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def load_entry(self, pdb_id: str):
        """Fetch data from RCSB and populate all sections."""
        self._pdb_id = pdb_id.upper()
        self._clear()

        # Show loading state
        loading = QtWidgets.QLabel(f"Loading info for {self._pdb_id}...")
        loading.setStyleSheet("color: gray;")
        self._add(loading)

        # Fetch in background thread
        self._worker = _FetchWorker(self._pdb_id, self)
        self._worker.data_ready.connect(self._populate)
        self._worker.start()

    def _clear(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add(self, widget):
        count = self.main_layout.count()
        # Insert before stretch if exists
        self.main_layout.addWidget(widget)

    def _add_header(self, text):
        label = QtWidgets.QLabel(f"<b>{text}</b>")
        label.setStyleSheet("font-size: 13px; padding-top: 8px;")
        self._add(label)

    def _add_separator(self):
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setStyleSheet("margin: 4px 0px;")
        self._add(sep)

    def _add_info_row(self, label, value):
        row = QtWidgets.QLabel(f"<b>{label}:</b> {value}")
        row.setWordWrap(True)
        row.setStyleSheet("font-size: 11px;")
        self._add(row)

    def _add_clickable(self, text, tooltip, callback):
        btn = QtWidgets.QPushButton(text)
        btn.setStyleSheet(
            "text-align: left; padding: 3px 6px; font-size: 11px; border: 1px solid palette(mid); border-radius: 3px;"
        )
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        self._add(btn)

    def _select_and_zoom(self, selection, zoom=True):
        try:
            self.cmd.select("sele", selection)
            n = self.cmd.count_atoms("sele")
            if zoom and n > 0:
                self.cmd.zoom("sele", 5)
        except Exception:
            pass

    def _populate(self, data):
        self._clear()
        if not data:
            self._add(QtWidgets.QLabel("<i>Could not fetch data</i>"))
            return
        self._data = data
        self._build_overview()
        self._build_publications()
        self._build_chains()
        self._build_domains()
        self._build_ligands()
        self._build_binding_sites()
        self._build_secondary_structure()
        self._build_function()
        self._build_quality()
        self.main_layout.addStretch()

    # ── Overview ──────────────────────────────────────────

    def _build_overview(self):
        d = self._data
        info = d.get("rcsb_entry_info") or {}
        exptl = (d.get("exptl") or [{}])[0]
        acc = d.get("rcsb_accession_info") or {}

        title = (d.get("struct") or {}).get("title", "")
        pdb_id = d.get("rcsb_id", "")

        header = QtWidgets.QLabel(f"<h3>{pdb_id}</h3>")
        self._add(header)

        if title:
            t = QtWidgets.QLabel(title)
            t.setWordWrap(True)
            t.setStyleSheet("font-size: 11px; color: palette(text);")
            self._add(t)

        self._add_separator()

        method = exptl.get("method", "?")
        res = info.get("resolution_combined")
        res_str = f"{res[0]:.2f} A" if res else "N/A"
        self._add_info_row("Method", method)
        self._add_info_row("Resolution", res_str)

        # Organism
        organism = ""
        for pe in d.get("polymer_entities") or []:
            for org in pe.get("rcsb_entity_source_organism") or []:
                name = org.get("ncbi_scientific_name")
                if name:
                    organism = name
                    break
            if organism:
                break
        if organism:
            self._add_info_row("Organism", f"<i>{organism}</i>")

        mw = info.get("molecular_weight")
        if mw:
            self._add_info_row("Weight", f"{mw:.1f} kDa")
        atoms = info.get("deposited_atom_count")
        if atoms:
            self._add_info_row("Atoms", f"{atoms:,}")
        comp = info.get("polymer_composition")
        if comp:
            self._add_info_row("Composition", comp)

        date = (acc.get("deposit_date") or "")[:10]
        if date:
            self._add_info_row("Deposited", date)

        # Link to RCSB
        link_btn = QtWidgets.QPushButton(f"View on RCSB.org")
        link_btn.setStyleSheet("font-size: 11px; padding: 3px;")
        link_btn.clicked.connect(
            lambda: webbrowser.open(f"https://www.rcsb.org/structure/{pdb_id}")
        )
        self._add(link_btn)

    # ── Publications ──────────────────────────────────────

    def _build_publications(self):
        citations = self._data.get("citation") or []
        if not citations:
            return

        self._add_separator()
        self._add_header("Publications")

        for cit in citations:
            title = cit.get("title", "")
            journal = cit.get("journal_abbrev", "")
            year = cit.get("year", "")
            authors = cit.get("rcsb_authors") or []
            doi = cit.get("pdbx_database_id_DOI")
            pubmed = cit.get("pdbx_database_id_PubMed")

            # Author list (first 3 + et al)
            if len(authors) > 3:
                author_str = ", ".join(authors[:3]) + " et al."
            else:
                author_str = ", ".join(authors)

            text = f"<b>{title[:100]}{'...' if len(title) > 100 else ''}</b>"
            if author_str:
                text += f"<br/><span style='font-size:10px;'>{author_str}</span>"
            if journal or year:
                text += f"<br/><span style='font-size:10px; color:gray;'>{journal} ({year})</span>"

            label = QtWidgets.QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 11px; padding: 4px; border: 1px solid palette(mid); border-radius: 3px; margin: 2px 0;")
            self._add(label)

            # DOI / PubMed links
            links = QtWidgets.QHBoxLayout()
            if doi:
                doi_btn = QtWidgets.QPushButton("DOI")
                doi_btn.setFixedHeight(22)
                doi_btn.setStyleSheet("font-size: 10px;")
                doi_btn.clicked.connect(
                    lambda checked, d=doi: webbrowser.open(f"https://doi.org/{d}")
                )
                links.addWidget(doi_btn)
            if pubmed:
                pm_btn = QtWidgets.QPushButton("PubMed")
                pm_btn.setFixedHeight(22)
                pm_btn.setStyleSheet("font-size: 10px;")
                pm_btn.clicked.connect(
                    lambda checked, p=pubmed: webbrowser.open(
                        f"https://pubmed.ncbi.nlm.nih.gov/{p}/"
                    )
                )
                links.addWidget(pm_btn)
            links.addStretch()
            links_w = QtWidgets.QWidget()
            links_w.setLayout(links)
            self._add(links_w)

    # ── Chains ────────────────────────────────────────────

    def _build_chains(self):
        polys = self._data.get("polymer_entities") or []
        if not polys:
            return

        self._add_separator()
        self._add_header("Chains")

        for pe in polys:
            desc = (pe.get("rcsb_polymer_entity") or {}).get("pdbx_description", "?")
            weight = (pe.get("rcsb_polymer_entity") or {}).get("formula_weight")
            ep = pe.get("entity_poly") or {}
            seq = ep.get("pdbx_seq_one_letter_code_can", "")
            poly_type = ep.get("rcsb_entity_polymer_type", "")

            orgs = pe.get("rcsb_entity_source_organism") or []
            org = orgs[0].get("ncbi_scientific_name", "") if orgs else ""

            instances = pe.get("polymer_entity_instances") or []
            chain_ids = [inst["rcsb_id"].split(".")[-1] for inst in instances]
            chain_str = ", ".join(chain_ids)

            # Info text
            parts = []
            if seq:
                parts.append(f"{len(seq)} residues")
            if weight:
                parts.append(f"{weight:.1f} kDa")
            if org:
                parts.append(f"<i>{org}</i>")
            info = " | ".join(parts)

            text = f"<b>Chain {chain_str}</b> - {desc}<br/><span style='font-size:10px;color:gray;'>{info}</span>"
            label = QtWidgets.QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 11px;")
            self._add(label)

            # Buttons
            btn_row = QtWidgets.QHBoxLayout()
            for chain_id in chain_ids:
                sel_expr = f"{self._pdb_id} and chain {chain_id}"
                s_btn = QtWidgets.QPushButton(f"Select {chain_id}")
                s_btn.setFixedHeight(22)
                s_btn.setStyleSheet("font-size: 10px;")
                s_btn.clicked.connect(
                    lambda checked, s=sel_expr: self._select_and_zoom(s)
                )
                btn_row.addWidget(s_btn)
            btn_row.addStretch()
            btn_w = QtWidgets.QWidget()
            btn_w.setLayout(btn_row)
            self._add(btn_w)

    # ── Domains & Motifs ──────────────────────────────────

    def _build_domains(self):
        polys = self._data.get("polymer_entities") or []
        domains = []

        for pe in polys:
            instances = pe.get("polymer_entity_instances") or []
            for inst in instances:
                chain_id = inst["rcsb_id"].split(".")[-1]

                # Instance-level annotations (CATH, SCOP, ECOD)
                for ann in inst.get("rcsb_polymer_instance_annotation") or []:
                    lineage = ann.get("annotation_lineage") or []
                    names = [l["name"] for l in lineage if l.get("name")]
                    if names:
                        domains.append({
                            "type": ann.get("type", ""),
                            "name": " > ".join(names[:3]),
                            "chain": chain_id,
                        })

                # Instance-level features (Pfam, CATH domains with positions)
                for feat in inst.get("rcsb_polymer_instance_feature") or []:
                    ftype = feat.get("type", "")
                    if ftype in ("CATH", "SCOP", "SCOP2B_SUPERFAMILY", "ECOD", "Pfam"):
                        name = feat.get("name", "")
                        positions = feat.get("feature_positions") or []
                        for pos in positions:
                            beg = pos.get("beg_seq_id")
                            end = pos.get("end_seq_id")
                            if beg:
                                domains.append({
                                    "type": ftype,
                                    "name": name,
                                    "chain": chain_id,
                                    "beg": beg,
                                    "end": end,
                                })

            # Entity-level features (Pfam)
            for feat in pe.get("rcsb_polymer_entity_feature") or []:
                if feat.get("type") == "Pfam":
                    positions = feat.get("feature_positions") or []
                    chain_ids_here = [i["rcsb_id"].split(".")[-1] for i in instances]
                    for pos in positions:
                        beg = pos.get("beg_seq_id")
                        end = pos.get("end_seq_id")
                        if beg:
                            domains.append({
                                "type": "Pfam",
                                "name": feat.get("name", ""),
                                "chain": chain_ids_here[0] if chain_ids_here else "",
                                "beg": beg,
                                "end": end,
                            })

            # InterPro from entity annotations
            for ann in pe.get("rcsb_polymer_entity_annotation") or []:
                if ann.get("type") == "InterPro":
                    lineage = ann.get("annotation_lineage") or []
                    names = [l["name"] for l in lineage if l.get("name")]
                    chain_ids_here = [i["rcsb_id"].split(".")[-1] for i in instances]
                    if names:
                        domains.append({
                            "type": "InterPro",
                            "name": names[0],
                            "chain": chain_ids_here[0] if chain_ids_here else "",
                        })

        if not domains:
            return

        # Deduplicate
        seen = set()
        unique = []
        for d in domains:
            key = (d["type"], d["name"], d.get("beg"), d.get("end"))
            if key not in seen:
                seen.add(key)
                unique.append(d)

        self._add_separator()
        self._add_header("Domains & Motifs")

        for d in unique:
            beg = d.get("beg")
            end = d.get("end")
            chain = d.get("chain", "")
            range_str = f" ({beg}-{end})" if beg and end else f" ({beg})" if beg else ""

            text = f"{d['type']}: {d['name']}{range_str}"

            if beg:
                resi_range = f"{beg}-{end}" if end else str(beg)
                sel = f"{self._pdb_id} and chain {chain} and resi {resi_range}"
                self._add_clickable(
                    text, f"Select and zoom to {d['name']}",
                    lambda checked, s=sel: self._select_and_zoom(s)
                )
            else:
                label = QtWidgets.QLabel(text)
                label.setStyleSheet("font-size: 11px; padding: 2px;")
                self._add(label)

    # ── Ligands ───────────────────────────────────────────

    def _build_ligands(self):
        nonpolys = self._data.get("nonpolymer_entities") or []
        if not nonpolys:
            return

        self._add_separator()
        self._add_header("Ligands")

        for np_ent in nonpolys:
            np_info = np_ent.get("rcsb_nonpolymer_entity") or {}
            comp = (np_ent.get("nonpolymer_comp") or {}).get("chem_comp") or {}

            desc = np_info.get("pdbx_description", "?")
            formula = comp.get("formula", "")
            weight = np_info.get("formula_weight")
            comp_name = comp.get("name", desc)

            parts = []
            if formula:
                parts.append(formula)
            if weight:
                parts.append(f"{weight * 1000:.0f} Da")

            text = f"{comp_name}"
            if parts:
                text += f"  ({', '.join(parts)})"

            sel = f"{self._pdb_id} and resn {desc.split()[0][:3]}"
            self._add_clickable(
                text, f"Select and zoom to {comp_name}",
                lambda checked, s=f"{self._pdb_id} and hetatm and not solvent": self._select_and_zoom(s)
            )

    # ── Binding Sites ─────────────────────────────────────

    def _build_binding_sites(self):
        polys = self._data.get("polymer_entities") or []
        sites = []

        for pe in polys:
            for inst in pe.get("polymer_entity_instances") or []:
                chain_id = inst["rcsb_id"].split(".")[-1]
                for feat in inst.get("rcsb_polymer_instance_feature") or []:
                    if feat.get("type") in ("BINDING_SITE", "LIGAND_INTERACTION"):
                        name = feat.get("name", "binding site")
                        for pos in feat.get("feature_positions") or []:
                            beg = pos.get("beg_seq_id")
                            if beg:
                                sites.append({
                                    "name": name,
                                    "chain": chain_id,
                                    "resi": beg,
                                })

        if not sites:
            return

        # Group by name
        from collections import defaultdict
        grouped = defaultdict(list)
        for s in sites:
            key = (s["name"], s["chain"])
            grouped[key].append(s["resi"])

        self._add_separator()
        self._add_header("Binding Sites")

        for (name, chain), residues in grouped.items():
            residues = sorted(set(residues))
            resi_str = "+".join(str(r) for r in residues)
            text = f"{name} (chain {chain}, {len(residues)} residues)"
            sel = f"{self._pdb_id} and chain {chain} and resi {resi_str}"
            self._add_clickable(
                text, f"Select binding site residues",
                lambda checked, s=sel: self._select_and_zoom(s)
            )

    # ── Secondary Structure ───────────────────────────────

    def _build_secondary_structure(self):
        polys = self._data.get("polymer_entities") or []
        helices = []
        sheets = []

        for pe in polys:
            for inst in pe.get("polymer_entity_instances") or []:
                chain_id = inst["rcsb_id"].split(".")[-1]
                for feat in inst.get("rcsb_polymer_instance_feature") or []:
                    ftype = feat.get("type", "")
                    for pos in feat.get("feature_positions") or []:
                        beg = pos.get("beg_seq_id")
                        end = pos.get("end_seq_id")
                        if beg and end:
                            if "HELIX" in ftype:
                                helices.append((chain_id, beg, end))
                            elif "SHEET" in ftype:
                                sheets.append((chain_id, beg, end))

        if not helices and not sheets:
            return

        self._add_separator()
        self._add_header("Secondary Structure")

        if helices:
            resi_all = "+".join(
                f"{b}-{e}" for _, b, e in helices
            )
            chain = helices[0][0]
            sel = f"{self._pdb_id} and chain {chain} and resi {resi_all}"
            self._add_clickable(
                f"Helices ({len(helices)})",
                "Select all helices",
                lambda checked, s=f"{self._pdb_id} and ss h": self._select_and_zoom(s, zoom=False)
            )

        if sheets:
            self._add_clickable(
                f"Sheets ({len(sheets)})",
                "Select all beta sheets",
                lambda checked, s=f"{self._pdb_id} and ss s": self._select_and_zoom(s, zoom=False)
            )

    # ── Function (GO) ─────────────────────────────────────

    def _build_function(self):
        polys = self._data.get("polymer_entities") or []

        # Collect GO terms grouped by top-level category
        mol_func = []
        bio_proc = []
        cell_comp = []

        for pe in polys:
            for ann in pe.get("rcsb_polymer_entity_annotation") or []:
                if ann.get("type") != "GO":
                    continue
                lineage = ann.get("annotation_lineage") or []
                names = [l.get("name", "") for l in lineage if l.get("name")]
                if not names:
                    continue

                term_name = names[0]  # most specific name
                # Categorize by checking lineage for top-level GO categories
                all_names = " ".join(names).lower()
                if "molecular_function" in all_names or "binding" in all_names or "activity" in all_names or "catalytic" in all_names:
                    mol_func.append(term_name)
                elif "biological_process" in all_names or "regulation" in all_names or "metabolic" in all_names or "response" in all_names:
                    bio_proc.append(term_name)
                elif "cellular_component" in all_names or "organelle" in all_names or "complex" in all_names or "membrane" in all_names:
                    cell_comp.append(term_name)
                else:
                    bio_proc.append(term_name)

        # Deduplicate
        mol_func = list(dict.fromkeys(mol_func))
        bio_proc = list(dict.fromkeys(bio_proc))
        cell_comp = list(dict.fromkeys(cell_comp))

        if not mol_func and not bio_proc and not cell_comp:
            return

        self._add_separator()
        self._add_header("Function (GO)")

        for category, terms in [
            ("Molecular Function", mol_func),
            ("Biological Process", bio_proc),
            ("Cellular Component", cell_comp),
        ]:
            if not terms:
                continue
            cat_label = QtWidgets.QLabel(f"<b>{category}:</b>")
            cat_label.setStyleSheet("font-size: 11px; padding-top: 4px;")
            self._add(cat_label)
            for term in terms[:8]:  # limit to avoid overwhelming
                t = QtWidgets.QLabel(f"  - {term}")
                t.setStyleSheet("font-size: 10px; color: palette(text);")
                t.setWordWrap(True)
                self._add(t)
            if len(terms) > 8:
                more = QtWidgets.QLabel(f"  <i>... and {len(terms) - 8} more</i>")
                more.setStyleSheet("font-size: 10px; color: gray;")
                self._add(more)

    # ── Quality ───────────────────────────────────────────

    def _build_quality(self):
        polys = self._data.get("polymer_entities") or []
        issues = []

        for pe in polys:
            for inst in pe.get("polymer_entity_instances") or []:
                chain_id = inst["rcsb_id"].split(".")[-1]
                for feat in inst.get("rcsb_polymer_instance_feature") or []:
                    ftype = feat.get("type", "")
                    if ftype in ("CLASHES", "BOND_OUTLIERS", "ANGLE_OUTLIERS",
                                 "CHIRAL_OUTLIERS", "PLANE_OUTLIERS"):
                        count = len(feat.get("feature_positions") or [])
                        if count:
                            issues.append(f"{ftype.replace('_', ' ').title()}: {count} (chain {chain_id})")

        if not issues:
            return

        self._add_separator()
        self._add_header("Quality")

        for issue in issues:
            label = QtWidgets.QLabel(issue)
            label.setStyleSheet("font-size: 10px; color: orange;")
            self._add(label)


class _FetchWorker(QtCore.QThread):
    data_ready = QtCore.Signal(object)  # emits dict or None

    def __init__(self, pdb_id, parent=None):
        super().__init__(parent)
        self.pdb_id = pdb_id

    def run(self):
        from molkit.rcsb_client import fetch_entry_metadata
        data = fetch_entry_metadata(self.pdb_id)
        self.data_ready.emit(data)


class InspectorDock(QtWidgets.QDockWidget):
    """Dockable inspector wrapper."""

    def __init__(self, cmd, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inspector")
        self.setObjectName("molkit_inspector")
        self.inspector = InspectorWidget(cmd, self)
        self.setWidget(self.inspector)
        self.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
```

**Step 2: Wire inspector into __init__.py and sidebar**

Modify `pymol-open-source/data/startup/molkit/__init__.py` — in `open_molkit()`, after adding the sidebar, add the inspector on the right:

```python
    if not hasattr(window, '_molkit_inspector'):
        from .inspector import InspectorDock
        from pymol import cmd

        window._molkit_inspector = InspectorDock(cmd, window)
        window.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            window._molkit_inspector,
        )
```

Modify `pymol-open-source/data/startup/molkit/sidebar.py` — in `MolKitSidebarWidget.__init__`, connect loader signal to also update inspector. Add after the `_on_structure_loaded` connection:

```python
# Connect loader → inspector
def _on_structure_for_inspector(name):
    window = self.window
    if hasattr(window, '_molkit_inspector'):
        window._molkit_inspector.inspector.load_entry(name)

self.loader.structure_loaded.connect(_on_structure_for_inspector)
```

Also connect tab changes to inspector:

```python
# Connect tab change → inspector
def _on_tab_for_inspector(name):
    window = self.window
    if hasattr(window, '_molkit_inspector'):
        window._molkit_inspector.inspector.load_entry(name)

self.tab_bar.tab_changed.connect(_on_tab_for_inspector)
```

**Step 3: Test manually**

```bash
cd pymol-open-source && python -m pymol
# Load 1ATP → Inspector panel on right shows:
#   Overview: title, method, resolution, organism, weight, atoms
#   Publications: primary citation + related papers with DOI/PubMed buttons
#   Chains: Chain A (protein kinase), Chain B (peptide inhibitor) with Select/Zoom
#   Domains: Pfam, CATH, SCOP, InterPro entries — clickable
#   Ligands: ATP, MN — clickable
#   Binding Sites: ATP binding, MN binding — clickable
#   Secondary Structure: Helices (14), Sheets (3) — clickable
#   Function: GO terms grouped by MF/BP/CC
#   Quality: validation issues
# Click "Select A" → chain A highlighted + zoomed
# Click DOI button → opens browser
# Click Pfam domain → residues selected + zoomed
# Switch tab to different model → inspector refreshes
```

**Step 4: Commit**

```bash
git add data/startup/molkit/inspector.py data/startup/molkit/__init__.py data/startup/molkit/sidebar.py
git commit -m "feat: molecule inspector with publications, chains, domains, ligands, binding sites, GO terms"
```

---

### Task 5: Final Wiring & Edge Cases

**Files:**
- Modify: `pymol-open-source/data/startup/molkit/__init__.py`
- Modify: `pymol-open-source/data/startup/molkit/sidebar.py`

**Step 1: Handle file-loaded structures (no RCSB data)**

The inspector should gracefully handle structures loaded from files (where RCSB data won't exist). Modify `InspectorWidget.load_entry()` in `inspector.py`:

```python
def load_entry(self, pdb_id: str):
    """Fetch data from RCSB and populate all sections."""
    self._pdb_id = pdb_id.upper()
    self._clear()

    # Check if this looks like a PDB code (4 chars alphanumeric)
    if len(pdb_id) == 4 and pdb_id.isalnum():
        loading = QtWidgets.QLabel(f"Loading info for {self._pdb_id}...")
        loading.setStyleSheet("color: gray;")
        self._add(loading)

        self._worker = _FetchWorker(self._pdb_id, self)
        self._worker.data_ready.connect(self._populate)
        self._worker.start()
    else:
        # Local file — show what we can from PyMOL
        self._build_local_info(pdb_id)
```

Add a method for local-only info:

```python
def _build_local_info(self, name):
    """Show basic info from PyMOL for file-loaded structures."""
    header = QtWidgets.QLabel(f"<h3>{name}</h3>")
    self._add(header)

    try:
        n_atoms = self.cmd.count_atoms(name)
        self._add_info_row("Atoms", f"{n_atoms:,}")

        chains = set()
        self.cmd.iterate(name, "chains.add(chain)", space={"chains": chains})
        if chains - {""}:
            self._add_info_row("Chains", ", ".join(sorted(chains - {""})))

        n_res = self.cmd.count_atoms(f"{name} and name CA")
        if n_res:
            self._add_info_row("Residues (approx)", str(n_res))
    except Exception:
        pass

    self._add(QtWidgets.QLabel(
        "<i style='color:gray; font-size:10px;'>Detailed info available only for PDB structures</i>"
    ))
    self.main_layout.addStretch()
```

**Step 2: Handle inspector visibility toggle**

Add to sidebar's console section or as a separate toggle — a button to show/hide inspector:

In `sidebar.py`, add to the console section area:

```python
# Inspector toggle
inspector_btn = QtWidgets.QPushButton("Toggle Inspector Panel")
inspector_btn.clicked.connect(self._toggle_inspector)
self.console_section.add_widget(inspector_btn)
```

```python
def _toggle_inspector(self):
    if hasattr(self.window, '_molkit_inspector'):
        insp = self.window._molkit_inspector
        if insp.isVisible():
            insp.hide()
        else:
            insp.show()
```

**Step 3: Test full flow end to end**

```bash
cd pymol-open-source && python -m pymol
# Full flow:
# 1. App opens with sidebar + inspector
# 2. Search "kinase inhibitor" → results appear
# 3. Click Load on a result → model loads, tab appears, inspector populates
# 4. Load another via PDB code → new tab, inspector switches
# 5. Click tabs to switch → inspector refreshes for each
# 6. Click domains/chains/ligands in inspector → viewport highlights
# 7. Click DOI → browser opens paper
# 8. Load file from disk → inspector shows basic info
# 9. "Show all" checkbox → all models visible
# 10. Toggle inspector on/off from sidebar
```

**Step 4: Commit**

```bash
git add data/startup/molkit/
git commit -m "feat: final wiring — search, tabs, inspector with edge case handling"
```
