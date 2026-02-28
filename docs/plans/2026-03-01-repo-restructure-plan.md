# Repo Restructure: molkit → molkit

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the repo so plugin code lives at top level as `molkit/`, submodule is clean, and the project has proper README, AGENTS.md, and build instructions.

**Architecture:** Extract plugin files from inside the PyMOL submodule to `molkit/` at repo root. Keep `pymol-open-source` as a clean submodule pointing to Schrödinger's upstream. Use a symlink script for development. Rename all references from molkit to molkit.

**Tech Stack:** Git, Bash, Python (rename only), GitHub CLI (`gh`)

---

### Task 1: Extract plugin code from submodule

**Files:**
- Copy from: `pymol-open-source/data/startup/molkit/` (all .py files, not __pycache__)
- Create: `molkit/` directory at repo root

**Step 1: Copy plugin files out of submodule**

```bash
mkdir -p molkit/sections
cp pymol-open-source/data/startup/molkit/__init__.py molkit/
cp pymol-open-source/data/startup/molkit/sidebar.py molkit/
cp pymol-open-source/data/startup/molkit/inspector.py molkit/
cp pymol-open-source/data/startup/molkit/rcsb_client.py molkit/
cp pymol-open-source/data/startup/molkit/tabs.py molkit/
cp pymol-open-source/data/startup/molkit/sections/__init__.py molkit/sections/
cp pymol-open-source/data/startup/molkit/sections/loader.py molkit/sections/
cp pymol-open-source/data/startup/molkit/sections/structure.py molkit/sections/
cp pymol-open-source/data/startup/molkit/sections/view.py molkit/sections/
cp pymol-open-source/data/startup/molkit/sections/colors.py molkit/sections/
cp pymol-open-source/data/startup/molkit/sections/selection.py molkit/sections/
cp pymol-open-source/data/startup/molkit/sections/measurements.py molkit/sections/
cp pymol-open-source/data/startup/molkit/sections/export.py molkit/sections/
```

**Step 2: Verify all files copied**

```bash
find molkit -type f -name "*.py" | sort
```

Expected: 13 Python files (same count as source).

**Step 3: Commit**

```bash
git add molkit/
git commit -m "feat: extract plugin code to top-level molkit/ directory"
```

---

### Task 2: Rename molkit → molkit in all Python files

**Files:**
- Modify: all 13 files in `molkit/`

**Renames to apply (Python code):**

| Pattern | Replacement | Files |
|---------|-------------|-------|
| `MolKit - Friendly PyMOL Interface` | `MolKit - Friendly PyMOL Interface` | `__init__.py` |
| `MolKit` (menu item string) | `MolKit` | `__init__.py` |
| `open_molkit` | `open_molkit` | `__init__.py` |
| `_molkit_sidebar` | `_molkit_sidebar` | `__init__.py`, `sidebar.py` |
| `_molkit_inspector` | `_molkit_inspector` | `__init__.py`, `sidebar.py` |
| `MolKitSidebar` | `MolKitSidebar` | `__init__.py`, `sidebar.py` |
| `MolKitSidebarWidget` | `MolKitSidebarWidget` | `sidebar.py` |
| `molkit_sidebar` (objectName) | `molkit_sidebar` | `sidebar.py` |
| `molkit_inspector` (objectName) | `molkit_inspector` | `inspector.py` |
| `[MolKit]` (log prefix) | `[MolKit]` | `inspector.py` |
| `molkit_custom` (color name) | `molkit_custom` | `sections/colors.py` |
| `_molkit_grid` (object name) | `_molkit_grid` | `sections/view.py` |

**Step 1: Apply renames in each file**

Use find-and-replace in each file. Case-sensitive replacements:
- `MolKit` → `MolKit` (class names, strings)
- `molkit` → `molkit` (variables, object names)

**Step 2: Verify no molkit references remain**

```bash
grep -ri "molkit" molkit/
```

Expected: no output.

**Step 3: Commit**

```bash
git add molkit/
git commit -m "refactor: rename molkit to molkit in all plugin code"
```

---

### Task 3: Reset submodule to clean upstream

**Step 1: Reset submodule to upstream HEAD**

```bash
cd pymol-open-source
git checkout master
git clean -fd data/startup/molkit/
cd ..
```

This removes the `data/startup/molkit/` directory from the submodule since it only existed in our local commits.

**Step 2: Update submodule reference**

```bash
git add pymol-open-source
git commit -m "chore: reset pymol-open-source submodule to clean upstream"
```

---

### Task 4: Create setup-dev.sh script

**Files:**
- Create: `scripts/setup-dev.sh`

**Step 1: Write the script**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

PLUGIN_SRC="$ROOT_DIR/molkit"
PLUGIN_DST="$ROOT_DIR/pymol-open-source/data/startup/molkit"

# Init submodule if needed
if [ ! -f "$ROOT_DIR/pymol-open-source/setup.py" ]; then
    echo "Initializing pymol-open-source submodule..."
    git -C "$ROOT_DIR" submodule update --init --recursive
fi

# Create symlink
if [ -L "$PLUGIN_DST" ]; then
    echo "Symlink already exists: $PLUGIN_DST"
elif [ -d "$PLUGIN_DST" ]; then
    echo "ERROR: $PLUGIN_DST exists as a directory. Remove it first."
    exit 1
else
    ln -s "$PLUGIN_SRC" "$PLUGIN_DST"
    echo "Created symlink: $PLUGIN_DST -> $PLUGIN_SRC"
fi

echo ""
echo "Done! Build PyMOL with:"
echo "  cd pymol-open-source && pip install ."
echo ""
echo "Then run:"
echo "  pymol"
```

**Step 2: Make executable**

```bash
chmod +x scripts/setup-dev.sh
```

**Step 3: Commit**

```bash
git add scripts/
git commit -m "feat: add setup-dev.sh script for symlink-based development"
```

---

### Task 5: Create README.md

**Files:**
- Create: `README.md`

**Step 1: Write README**

Content should include:
- Project name and one-line description
- Screenshot placeholder
- What it does (bullet points: search PDB, visual representations, coloring, measurements, inspector, export)
- Prerequisites (Python 3.9+, C++17 compiler, CMake 3.13+, system deps)
- Quick start (clone with submodules, run setup-dev.sh, build PyMOL, run)
- macOS-specific install commands (brew install glew glm freeglut libpng freetype libxml2 msgpack-cxx)
- Development section (how the symlink works, edit molkit/, restart PyMOL)
- Project structure tree

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with build-from-source instructions"
```

---

### Task 6: Create AGENTS.md

**Files:**
- Create: `AGENTS.md`

**Step 1: Write AGENTS.md**

Content should include:
- **Project overview**: MolKit is a PyMOL plugin (PySide6/Qt6) that replaces PyMOL's CLI-heavy interface with a visual sidebar
- **Tech stack**: Python 3.9+, PySide6 (bundled with PyMOL), zero external deps, RCSB Search + GraphQL APIs via stdlib urllib
- **Architecture**: Plugin entry point (`__init__.py`) → registers menu item + auto-opens sidebar → sidebar has collapsible accordion sections → inspector dock on right shows RCSB metadata
- **Key files map**: list each file in `molkit/` with one-line description
- **PyMOL API**: all viewport operations go through `from pymol import cmd` — key methods: `cmd.fetch()`, `cmd.load()`, `cmd.show()`, `cmd.hide()`, `cmd.color()`, `cmd.select()`, `cmd.set()`
- **Qt patterns**: signals/slots for inter-widget communication, QThread workers for async API calls, 2-3s QTimer for state sync with PyMOL
- **Conventions**: no external dependencies, relative imports within plugin, sections are independent modules, all UI strings in English
- **Development**: run `scripts/setup-dev.sh` then `cd pymol-open-source && pip install . && pymol`
- **Testing**: currently manual (launch PyMOL, load structure, test UI)

**Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add AGENTS.md with project context for AI agents"
```

---

### Task 7: Clean up and reorganize docs

**Files:**
- Move: `PYMOL_USER_MAP.md` → `docs/pymol-user-map.md`
- Modify: `docs/plans/*.md` — rename molkit → molkit references
- Update: `.gitignore` — add `__pycache__/`, `*.pyc`, `*.egg-info/`

**Step 1: Move PYMOL_USER_MAP.md**

```bash
git mv PYMOL_USER_MAP.md docs/pymol-user-map.md
```

**Step 2: Update .gitignore**

```
.worktrees
*.cif
__pycache__/
*.pyc
*.egg-info/
```

**Step 3: Rename molkit → molkit in docs/plans/**

Apply find-and-replace across all markdown files in `docs/plans/`:
- `molkit` → `molkit`
- `MolKit` → `MolKit`

**Step 4: Commit**

```bash
git add .
git commit -m "chore: reorganize docs and update .gitignore"
```

---

### Task 8: Clean up worktrees and stale files

**Step 1: Remove worktrees**

```bash
git worktree remove .worktrees/3d-toolbar --force 2>/dev/null || true
git worktree remove .worktrees/search-tabs-inspector --force 2>/dev/null || true
rm -rf .worktrees
```

**Step 2: Remove .cif files from working directory**

```bash
rm -f *.cif
```

**Step 3: Verify clean state**

```bash
git status
```

Expected: clean working tree, no untracked files except possibly pymol-open-source submodule changes.

**Step 4: Commit if needed**

If any tracked files were removed:
```bash
git add -A
git commit -m "chore: clean up worktrees and stale files"
```

---

### Task 9: Rename GitHub repo and push

**Step 1: Rename repo on GitHub**

```bash
gh repo rename molkit
```

**Step 2: Update local remote**

```bash
git remote set-url origin https://github.com/0xfraan/molkit.git
```

**Step 3: Force push clean history**

```bash
git push --force origin main
```

**Step 4: Verify on GitHub**

```bash
gh repo view --web
```

---
