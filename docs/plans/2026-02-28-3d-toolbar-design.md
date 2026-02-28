# MolKit 3D Toolbar & Viewport Tools - Design

## Overview

Hybrydowy toolbar z narzędziami do bezpośredniej interakcji w viewporcie 3D PyMOL. Sidebar zostaje dla złożonych ustawień, toolbar umożliwia szybką interakcję w przestrzeni 3D.

**Podejście:** Qt overlay (toolbar + selection overlays) + PyMOL CGO (gizmo, wizualizacja selekcji).

## Architecture

```
┌──────┬──┬──────────────────────────┐
│ Side │TB│                          │
│ bar  │  │     3D Viewport          │
│      │  │        (OpenGL)          │
│      │  │                          │
│      │  │              [Gizmo CGO] │
│      │  │                          │
└──────┴──┴──────────────────────────┘
         ↑
    QToolBar (vertical, ~40px)
```

- **Toolbar**: `QToolBar` pionowy, dokowany między sidebarem a viewportem
- **Tool actions**: `QActionGroup` (exclusive - jedno narzędzie aktywne naraz)
- **Sub-panel**: mały panel pod ikonami narzędzi z opcjami aktywnego narzędzia
- **Event handling**: `QObject.installEventFilter()` na GL widgecie PyMOL do przechwytywania myszki gdy narzędzie jest aktywne

## Tool 1: Select

Trzy tryby zaznaczania, przełączane w sub-panelu:

### Click mode
- Klik na atom → zaznacza residue
- Shift+klik → dodaje do selekcji
- Bazuje na natywnym PyMOL picking

### Box mode
- Drag w viewporcie → `QRubberBand` rysuje prostokąt
- Release → konwertuj screen coords na atomy (projekcja 2D pozycji atomów)
- `cmd.select("sele", ...)` z odpowiednim wyrażeniem

### Lasso mode
- Custom QPainter na przezroczystym overlay widgecie nad GL widgetem
- Rysuj ścieżkę myszki, zamknij polygon
- Point-in-polygon test na 2D projekcjach atomów

### Wizualizacja selekcji
- `cmd.show("spheres", "sele")` + `cmd.set("sphere_transparency", 0.6, "sele")`
- Wyróżniający kolor (np. żółty)
- Czyść starą wizualizację przy zmianie selekcji

## Tool 2: Brush (Paint)

Malowanie kolorem bezpośrednio po cząsteczce.

### Sub-panel
- Granulacja: `[Atom] [Residue] [Chain]` - 3 przyciski, jeden aktywny
- Paleta: ~12 predefiniowanych kolorów + custom color picker
- Podgląd aktualnego koloru

### Działanie
- Klik na atom → identyfikuj przez PyMOL picking callback
- W zależności od granulacji:
  - **Atom**: `cmd.color(color, f"id {atom_id}")`
  - **Residue**: `cmd.color(color, f"resi {resi} and chain {chain}")`
  - **Chain**: `cmd.color(color, f"chain {chain}")`
- Drag → ciągłe malowanie (każdy nowy atom pod kursorem)
- Kursor: custom Qt cursor z kolorem

## Tool 3: Gizmo (Camera Orbit)

CGO 3D object w scenie PyMOL do precyzyjnej kontroli kamery.

### Wygląd
- 3 kolorowe pierścienie (osie obrotu):
  - Czerwony → obrót wokół X
  - Zielony → obrót wokół Y
  - Niebieski → obrót wokół Z
- 3 strzałki do przesuwania pivot pointu
- Rysowane jako CGO objects

### Działanie
- Klik+drag na pierścieniu → `cmd.turn("x/y/z", angle)`
- Klik+drag na strzałce → `cmd.move("x/y/z", distance)`
- Klik na środkowy punkt → reset orientacji (`cmd.orient()`)

### Technicznie
- CGO object renderowany w stałej pozycji ekranowej
- Event filter sprawdza hit testing na gizmo area

## Tool 4: Measure

Pomiary bezpośrednio w viewporcie, bazujące na natywnych PyMOL measurement objects.

### Sub-panel
- Tryb: `[Distance] [Angle] [Dihedral]`
- Lista pomiarów z przyciskiem usuwania
- "Clear all" button

### Działanie
- Distance: klik 2 atomy → `cmd.distance("dist_N", "pk1", "pk2")` → linia + etykieta Å
- Angle: klik 3 atomy → `cmd.angle("ang_N", "pk1", "pk2", "pk3")`
- Dihedral: klik 4 atomy → `cmd.dihedral("dih_N", "pk1", "pk2", "pk3", "pk4")`
- Wizualne markery na klikniętych atomach (tymczasowe sfery)

## Technical Implementation Notes

### Event Filter Pattern
```python
class ToolEventFilter(QtCore.QObject):
    def eventFilter(self, obj, event):
        if self.active_tool and event.type() in (MousePress, MouseMove, MouseRelease):
            return self.active_tool.handle_event(event)
        return False

# Install on PyMOL GL widget
gl_widget = pymol_window.findChild(QOpenGLWidget)
gl_widget.installEventFilter(tool_filter)
```

### Atom Picking from Screen Coords
- PyMOL's `cmd.get_model("all")` → iterate atoms → project 3D→2D via `cmd.get_view()` matrix
- Alternatively: use PyMOL's built-in picking (mouse mode 1) and intercept results

### CGO Gizmo
```python
from pymol.cgo import *
gizmo = [
    COLOR, 1.0, 0.0, 0.0,  # Red X ring
    # ... ring geometry
    COLOR, 0.0, 1.0, 0.0,  # Green Y ring
    # ... ring geometry
    COLOR, 0.0, 0.0, 1.0,  # Blue Z ring
    # ... ring geometry
]
cmd.load_cgo(gizmo, "gizmo_obj")
```

## File Structure

```
sections/
├── toolbar.py          # QToolBar + tool switching logic
├── tools/
│   ├── __init__.py
│   ├── base.py         # BaseTool abstract class
│   ├── select_tool.py  # Select (click/box/lasso)
│   ├── brush_tool.py   # Brush (paint colors)
│   ├── gizmo_tool.py   # Camera orbit gizmo (CGO)
│   └── measure_tool.py # Distance/angle/dihedral
└── event_filter.py     # GL widget event interception
```

## Dependencies
- PySide6 (already used)
- PyMOL CGO API (built-in)
- PyMOL cmd API (already used)
