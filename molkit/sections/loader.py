import os

from pymol.Qt import QtWidgets, QtCore, QtGui

from ..rcsb_client import search_pdb, fetch_batch_metadata, parse_entry_summary

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
        # 4-char alphanumeric = PDB code -> direct fetch
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
