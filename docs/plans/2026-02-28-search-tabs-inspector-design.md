# MatiMac v0.2 — Search, Tabs, Inspector

## Features

### 1. PDB Search Engine
- Typed text search (min 3 chars, 500ms debounce) -> RCSB Search API full_text
- Results enriched with metadata via GraphQL batch (title, organism, resolution, method)
- 4-char exact codes still do instant fetch
- Results shown as cards with key info + [Load] button

### 2. Model Tabs
- QTabBar above viewport, each loaded model = one tab
- Active tab = only that model visible (cmd.disable all, cmd.enable active)
- Each tab saves/restores camera view (get_view/set_view)
- [+] tab opens loader
- [x] closes/deletes model
- "Show all" checkbox for overlay mode

### 3. Molecule Inspector (right panel)
Rich info panel fetched from RCSB GraphQL on structure load. Sections:

- **Overview**: title, method, resolution, organism, weight, atoms, deposit date
- **Publications**: primary citation + related papers with DOI/PubMed links, authors
- **Chains**: each with description, residue count, organism — clickable [Select] [Zoom]
- **Domains & Motifs**: Pfam, CATH, SCOP, InterPro, ECOD — with residue ranges, clickable
- **Ligands**: non-polymer entities with formula, weight — clickable
- **Binding Sites**: residues involved, which ligand — clickable
- **Secondary Structure**: helix/sheet counts and positions — clickable
- **Function (GO)**: grouped by molecular function / biological process / cellular component
- **Quality**: validation metrics (clashes, outliers, RSCC) — collapsed by default

All [Select] buttons do cmd.select + highlight. All [Zoom] buttons do cmd.zoom.

### GraphQL query
Single query per loaded structure fetches everything:
- entry.struct (title)
- entry.exptl (method)
- entry.rcsb_entry_info (resolution, weight, atom count)
- entry.citation (all papers with DOI, PubMed, authors, journal, year)
- entry.polymer_entities (chains, organism, sequence, annotations, features, domains)
- entry.nonpolymer_entities (ligands, formula)
- Annotations: GO, Pfam, CATH, SCOP, SCOP2, ECOD, InterPro
- Features: binding sites, secondary structure, ligand interactions

## Layout
```
+----------+------------------------+--------------+
| Sidebar  |  [1ATP x] [4HHB x] [+]|  Inspector   |
| (actions)|                        |  (info)      |
|          |     3D Viewport        |              |
|          |                        |  Overview    |
|          |                        |  Papers      |
|          |                        |  Chains      |
|          |                        |  Domains     |
|          |                        |  Ligands     |
|          |                        |  ...         |
+----------+------------------------+--------------+
```
