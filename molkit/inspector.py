import webbrowser

from pymol.Qt import QtWidgets, QtCore

from .rcsb_client import fetch_entry_metadata
from .theme import (
    BG, SURFACE, HOVER, BORDER, TEXT, TEXT_MUTED, ACCENT,
    FONT_SIZE_SM, FONT_SIZE_BASE, RADIUS, RADIUS_SM,
    STATUS_WARNING, status_style,
)

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
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(6)

        self.placeholder = QtWidgets.QLabel(
            f"<i style='color:{TEXT_MUTED};'>Load a structure to see details</i>"
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

        # Check if this looks like a PDB code (4 chars alphanumeric)
        if len(pdb_id) == 4 and pdb_id.isalnum():
            loading = QtWidgets.QLabel(f"Loading info for {self._pdb_id}...")
            loading.setStyleSheet(status_style("muted"))
            self._add(loading)

            self._worker = _FetchWorker(self._pdb_id, self)
            self._worker.fetch_done.connect(lambda: self._populate(self._worker.result))
            self._worker.start()
        else:
            # Local file — show what we can from PyMOL
            self._build_local_info(pdb_id)

    def _build_local_info(self, name):
        """Show basic info from PyMOL for file-loaded structures."""
        header = QtWidgets.QLabel(name)
        header.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT}; padding-bottom: 6px;")
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

        self._add_separator()
        note = QtWidgets.QLabel("Detailed info available only for PDB structures")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {FONT_SIZE_SM}; padding: 4px 0;")
        self._add(note)
        self.main_layout.addStretch()

    def _clear(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @staticmethod
    def _constrain(widget):
        """Force widget to shrink to available width (prevents text overflow)."""
        sp = widget.sizePolicy()
        sp.setHorizontalPolicy(QtWidgets.QSizePolicy.Policy.Ignored)
        widget.setSizePolicy(sp)
        if isinstance(widget, QtWidgets.QLabel):
            widget.setWordWrap(True)
        return widget

    def _add(self, widget):
        self._constrain(widget)
        self.main_layout.addWidget(widget)

    def _add_header(self, text):
        label = QtWidgets.QLabel(text.lower())
        label.setStyleSheet(f"""
            font-size: {FONT_SIZE_BASE}; font-weight: 600;
            color: {TEXT}; padding: 4px 0 2px 0;
            border-left: 2px solid {ACCENT}; padding-left: 8px;
        """)
        self._add(label)

    def _add_separator(self):
        spacer = QtWidgets.QWidget()
        spacer.setFixedHeight(8)
        self._add(spacer)

    def _add_info_row(self, label, value):
        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 2, 0, 2)
        key = QtWidgets.QLabel(label)
        key.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT_MUTED};")
        key.setFixedWidth(90)
        val = QtWidgets.QLabel(value)
        val.setWordWrap(True)
        val.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT};")
        row.addWidget(key)
        row.addWidget(val, 1)
        w = QtWidgets.QWidget()
        w.setLayout(row)
        self._add(w)

    def _add_clickable(self, text, tooltip, callback):
        # Use a QLabel-based button so long text wraps instead of overflowing
        label = QtWidgets.QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"""
            padding: 6px 10px;
            font-size: {FONT_SIZE_SM}; border: 1px solid {BORDER};
            border-radius: {RADIUS}; background: {SURFACE};
        """)
        label.setCursor(Qt.CursorShape.PointingHandCursor)
        label.setToolTip(tooltip)
        label.mousePressEvent = lambda e: callback(False)
        self._add(label)

    def _add_card(self, content_widget):
        """Wrap a widget in a styled card container."""
        card = QtWidgets.QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {BORDER}; border-radius: {RADIUS};
                background: {SURFACE}; padding: 8px;
            }}
        """)
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        layout.addWidget(content_widget)
        self._add(card)

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

    # -- Overview --

    def _build_overview(self):
        d = self._data
        info = d.get("rcsb_entry_info") or {}
        exptl = (d.get("exptl") or [{}])[0]
        acc = d.get("rcsb_accession_info") or {}

        title = (d.get("struct") or {}).get("title", "")
        pdb_id = d.get("rcsb_id", "")

        header = QtWidgets.QLabel(pdb_id)
        header.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT}; padding-bottom: 2px;")
        self._add(header)

        if title:
            t = QtWidgets.QLabel(title)
            t.setWordWrap(True)
            t.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT_MUTED}; padding-bottom: 6px;")
            self._add(t)

        self._add_separator()

        method = exptl.get("method", "?")
        res = info.get("resolution_combined")
        res_str = f"{res[0]:.2f} \u00c5" if res else "N/A"
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

        self._add_separator()

        # Link to RCSB
        link_row = QtWidgets.QHBoxLayout()
        link_row.setContentsMargins(0, 0, 0, 0)
        link_row.addStretch()
        link_btn = QtWidgets.QPushButton(f"View on RCSB.org")
        link_btn.setStyleSheet(f"""
            font-size: {FONT_SIZE_SM}; padding: 6px 16px;
            border: 1px solid {BORDER}; border-radius: {RADIUS};
            background: {SURFACE};
        """)
        link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        link_btn.clicked.connect(
            lambda: webbrowser.open(f"https://www.rcsb.org/structure/{pdb_id}")
        )
        link_row.addWidget(link_btn)
        link_row.addStretch()
        link_w = QtWidgets.QWidget()
        link_w.setLayout(link_row)
        self._add(link_w)

    # -- Publications --

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

            # Card container
            card = QtWidgets.QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid {BORDER}; border-radius: {RADIUS};
                    background: {SURFACE};
                }}
            """)
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(4)

            title_label = self._constrain(QtWidgets.QLabel(f"<b>{title[:120]}{'...' if len(title) > 120 else ''}</b>"))
            title_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}; border: none; background: transparent;")
            card_layout.addWidget(title_label)

            if author_str:
                auth_label = self._constrain(QtWidgets.QLabel(author_str))
                auth_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT}; border: none; background: transparent;")
                card_layout.addWidget(auth_label)

            if journal or year:
                meta_label = self._constrain(QtWidgets.QLabel(f"{journal} ({year})"))
                meta_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT_MUTED}; border: none; background: transparent;")
                card_layout.addWidget(meta_label)

            # DOI / PubMed links
            if doi or pubmed:
                links = QtWidgets.QHBoxLayout()
                links.setContentsMargins(0, 4, 0, 0)
                links.setSpacing(6)
                link_style = f"""
                    font-size: {FONT_SIZE_SM}; padding: 3px 8px;
                    border: 1px solid {BORDER}; border-radius: {RADIUS_SM};
                    background: {BG};
                """
                if doi:
                    doi_btn = QtWidgets.QPushButton("DOI")
                    doi_btn.setStyleSheet(link_style)
                    doi_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    doi_btn.clicked.connect(
                        lambda checked, d=doi: webbrowser.open(f"https://doi.org/{d}")
                    )
                    links.addWidget(doi_btn)
                if pubmed:
                    pm_btn = QtWidgets.QPushButton("PubMed")
                    pm_btn.setStyleSheet(link_style)
                    pm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    pm_btn.clicked.connect(
                        lambda checked, p=pubmed: webbrowser.open(
                            f"https://pubmed.ncbi.nlm.nih.gov/{p}/"
                        )
                    )
                    links.addWidget(pm_btn)
                links.addStretch()
                links_w = QtWidgets.QWidget()
                links_w.setStyleSheet("border: none; background: transparent;")
                links_w.setLayout(links)
                card_layout.addWidget(links_w)

            self._add(card)

    # -- Chains --

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

            orgs = pe.get("rcsb_entity_source_organism") or []
            org = orgs[0].get("ncbi_scientific_name", "") if orgs else ""

            instances = pe.get("polymer_entity_instances") or []
            chain_ids = [inst["rcsb_id"].split(".")[-1] for inst in instances]
            chain_str = ", ".join(chain_ids)

            # Info text
            parts = []
            if seq:
                parts.append(f"{len(seq)} res")
            if weight:
                parts.append(f"{weight:.1f} kDa")
            if org:
                parts.append(org)

            # Card
            card = QtWidgets.QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid {BORDER}; border-radius: {RADIUS};
                    background: {SURFACE};
                }}
            """)
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(4)

            chain_label = self._constrain(QtWidgets.QLabel(f"<b>Chain {chain_str}</b>"))
            chain_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}; border: none; background: transparent;")
            card_layout.addWidget(chain_label)

            desc_label = self._constrain(QtWidgets.QLabel(desc))
            desc_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT}; border: none; background: transparent;")
            card_layout.addWidget(desc_label)

            if parts:
                meta = self._constrain(QtWidgets.QLabel(" \u00b7 ".join(parts)))
                meta.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT_MUTED}; border: none; background: transparent;")
                card_layout.addWidget(meta)

            # Select buttons
            btn_row = QtWidgets.QHBoxLayout()
            btn_row.setContentsMargins(0, 4, 0, 0)
            btn_row.setSpacing(6)
            for chain_id in chain_ids:
                sel_expr = f"{self._pdb_id} and chain {chain_id}"
                s_btn = QtWidgets.QPushButton(f"Select {chain_id}")
                s_btn.setStyleSheet(f"""
                    font-size: {FONT_SIZE_SM}; padding: 3px 8px;
                    border: 1px solid {BORDER}; border-radius: {RADIUS_SM};
                    background: {BG};
                """)
                s_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                s_btn.clicked.connect(
                    lambda checked, s=sel_expr: self._select_and_zoom(s)
                )
                btn_row.addWidget(s_btn)
            btn_row.addStretch()
            btn_w = QtWidgets.QWidget()
            btn_w.setStyleSheet("border: none; background: transparent;")
            btn_w.setLayout(btn_row)
            card_layout.addWidget(btn_w)

            self._add(card)

    # -- Domains & Motifs --

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
                label.setWordWrap(True)
                label.setStyleSheet(f"font-size: {FONT_SIZE_SM}; padding: 4px 0;")
                self._add(label)

    # -- Ligands --

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

            self._add_clickable(
                text, f"Select and zoom to {comp_name}",
                lambda checked, s=f"{self._pdb_id} and hetatm and not solvent": self._select_and_zoom(s)
            )

    # -- Binding Sites --

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

    # -- Secondary Structure --

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

    # -- Function (GO) --

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
            cat_label = QtWidgets.QLabel(category)
            cat_label.setStyleSheet(f"font-size: {FONT_SIZE_SM}; font-weight: 600; color: {TEXT_MUTED}; padding: 6px 0 2px 0;")
            self._add(cat_label)
            for term in terms[:8]:
                t = QtWidgets.QLabel(f"\u2022  {term}")
                t.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT}; padding-left: 8px;")
                t.setWordWrap(True)
                self._add(t)
            if len(terms) > 8:
                more = QtWidgets.QLabel(f"    +{len(terms) - 8} more")
                more.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {TEXT_MUTED}; padding-left: 8px;")
                self._add(more)

    # -- Quality --

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
            label.setStyleSheet(f"font-size: {FONT_SIZE_SM}; color: {STATUS_WARNING};")
            self._add(label)


class _FetchWorker(QtCore.QThread):
    fetch_done = QtCore.Signal()

    def __init__(self, pdb_id, parent=None):
        super().__init__(parent)
        self.pdb_id = pdb_id
        self.result = None

    def run(self):
        try:
            self.result = fetch_entry_metadata(self.pdb_id)
        except Exception as e:
            print(f"[MolKit] Inspector fetch error: {e}")
            self.result = None
        self.fetch_done.emit()


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
