# MolKit

A friendly visual sidebar for PyMOL -- no command-line syntax required.

## What It Does

MolKit is a PyMOL plugin that replaces the CLI-heavy workflow with a point-and-click sidebar:

- **Search & Load** -- find PDB structures by ID or keyword via the RCSB API
- **Representations** -- switch between cartoon, sticks, surface, spheres, and more
- **Coloring** -- color by element, chain, B-factor, or pick a custom color
- **Selection Builder** -- build atom selections visually instead of writing `select` commands
- **Measurements** -- distance, angle, dihedral, and hydrogen-bond overlays
- **Inspector** -- view RCSB metadata (publications, chains, domains, ligands) in a right-side panel
- **Export** -- save screenshots, ray-traced images, or PyMOL sessions

Zero external dependencies. Everything runs on Python's `urllib` and the PySide6/PyQt bundled with PyMOL.

## Prerequisites

| Requirement | Minimum |
|---|---|
| Python | 3.9+ |
| C++ compiler | C++17 (gcc 8+, clang 10+, Xcode CLT) |
| CMake | 3.13+ |
| pip | latest recommended |

System libraries: OpenGL, GLEW, GLUT (freeglut), libpng, freetype, glm.
Optional: libxml2, msgpack-c.

### macOS (Homebrew)

```bash
brew install cmake glew glm freeglut libpng freetype libxml2 msgpack-cxx
```

### Linux (apt)

```bash
sudo apt install build-essential cmake libglew-dev libglm-dev freeglut3-dev \
  libpng-dev libfreetype-dev libxml2-dev libmsgpack-dev
```

## Quick Start

```bash
# Clone with the PyMOL submodule
git clone --recursive https://github.com/user/molkit.git
cd molkit

# Init submodule and symlink the plugin into PyMOL's startup directory
bash scripts/setup-dev.sh

# Install system deps (see Prerequisites above), then build PyMOL
cd pymol-open-source
pip install .

# Run
pymol
```

MolKit opens automatically in the left sidebar on launch. You can also toggle it from the Plugin menu.

## Project Structure

```
molkit/                  Plugin source code (Python / PySide6)
  __init__.py            Plugin entry point, auto-opens sidebar
  sidebar.py             Main sidebar dock widget
  inspector.py           Right-side RCSB metadata panel
  rcsb_client.py         RCSB PDB API client (urllib)
  tabs.py                Tab container for sidebar sections
  sections/              One module per sidebar section
    loader.py              Search & load structures
    structure.py           Representation controls
    view.py                Camera / viewport tools
    colors.py              Coloring tools
    selection.py           Visual selection builder
    measurements.py        Distance, angle, dihedral, H-bonds
    export.py              Screenshot, ray-trace, session save
pymol-open-source/       PyMOL source (git submodule, Schrodinger)
scripts/
  setup-dev.sh           Symlink plugin into PyMOL for development
docs/                    Design plans and references
```

## Development

The `setup-dev.sh` script creates a symlink from `pymol-open-source/data/startup/molkit` back to the top-level `molkit/` directory. This means you edit files in `molkit/` and restart PyMOL to see your changes -- no copy step needed.

```bash
# Typical workflow
vim molkit/sections/colors.py   # edit
pymol                           # restart to test
```

If you rebuild PyMOL (`pip install .` inside `pymol-open-source/`), the symlink survives because it lives in `data/startup/`, which is copied into the installed package. Re-run `setup-dev.sh` if it breaks.
