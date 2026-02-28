# Repo Restructure: molkit → molkit

## Problem

All plugin code (~2700 lines) lives inside the `pymol-open-source` submodule at `data/startup/molkit/`. The submodule points to Schrödinger's upstream repo, so our commits only exist locally. Anyone cloning the repo gets an empty project.

## Solution

Extract plugin code to top-level `molkit/` directory, rename everything from molkit to molkit, keep PyMOL as a clean submodule, and use a symlink for development.

## Target Structure

```
molkit/                          (GitHub repo, renamed from molkit)
├── molkit/                      plugin source (single source of truth)
│   ├── __init__.py
│   ├── sidebar.py
│   ├── inspector.py
│   ├── rcsb_client.py
│   ├── tabs.py
│   └── sections/
│       ├── __init__.py
│       ├── loader.py
│       ├── structure.py
│       ├── view.py
│       ├── colors.py
│       ├── selection.py
│       ├── measurements.py
│       └── export.py
├── pymol-open-source/           submodule (clean Schrödinger upstream)
├── docs/
│   ├── plans/                   design & implementation docs
│   └── pymol-user-map.md        PyMOL command reference
├── scripts/
│   └── setup-dev.sh             creates symlink into submodule for dev
├── AGENTS.md                    AI agent context (architecture, conventions)
├── README.md                    project overview + build-from-source instructions
├── .gitignore
└── .gitmodules
```

## Key Decisions

- **Plugin as top-level dir**: `molkit/` is the source of truth, tracked in git
- **Submodule stays clean**: no custom commits in pymol-open-source
- **Symlink for dev**: `scripts/setup-dev.sh` creates `pymol-open-source/data/startup/molkit → ../../molkit`
- **Rename**: molkit → molkit everywhere (code, docs, strings, GH repo)
- **README.md**: project description + how to build PyMOL from source + how to install/run the plugin
- **AGENTS.md**: architecture overview, tech stack, conventions, file map for AI agents
- **Cleanup**: remove .worktrees/, .cif files, __pycache__; move PYMOL_USER_MAP.md to docs/

## Scope

1. Extract plugin code from submodule to `molkit/`
2. Rename molkit → molkit in all files
3. Reset submodule to clean upstream state
4. Create `scripts/setup-dev.sh`
5. Create `README.md` with build-from-source instructions
6. Create `AGENTS.md` with project context for AI agents
7. Move `PYMOL_USER_MAP.md` → `docs/pymol-user-map.md`
8. Clean up .worktrees/, .cif files
9. Rename GitHub repo from molkit to molkit
