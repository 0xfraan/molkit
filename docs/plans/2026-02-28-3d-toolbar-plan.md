# 3D Toolbar & Viewport Tools Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a vertical toolbar with Select, Brush, Gizmo, and Measure tools for direct 3D viewport interaction in MatiMac.

**Architecture:** Qt overlay toolbar positioned over the left edge of the PyMOL GL widget. Each tool is a self-contained class implementing a `BaseTool` interface. A `ToolManager` installs an event filter on the GL widget and routes mouse events to the active tool. Selection visualization uses PyMOL representations (spheres). Gizmo uses PyMOL CGO objects. Brush uses PyMOL `cmd.color()`. Measurements use native PyMOL `cmd.distance()`/`cmd.angle()`/`cmd.dihedral()`.

**Tech Stack:** PySide6 (Qt), PyMOL `cmd` API, PyMOL CGO (compiled graphics objects)

**Key Technical Details:**
- GL widget: `PyMOLGLWidget` at `window.pymolwidget`, set as central widget via `setCentralWidget()`
- Coordinate conversion: `widget._event_x_y_mod(ev)` returns `(x, y, modifiers)` in OpenGL coords (Y flipped)
- Picking: after click, `cmd.identify("pk1", mode=1)` returns `[(obj_name, atom_id), ...]`
- Select by indices: `cmd.select_list(name, object, id_list, mode='id')`
- View matrix: `cmd.get_view()` returns 18 floats (rotation 0-8, camera origin 9-11, model origin 12-14, clip 15-16, ortho 17)
- Event filter: `widget.installEventFilter(filter_obj)` — return `True` to consume event, `False` to pass through

**File Structure:**
```
pymol-open-source/data/startup/matimac/
├── __init__.py              (modify: add toolbar init)
├── sidebar.py               (no changes)
├── toolbar.py               (create: toolbar widget + tool manager)
├── tools/
│   ├── __init__.py          (create: exports)
│   ├── base.py              (create: BaseTool ABC)
│   ├── select_tool.py       (create: click/box/lasso selection)
│   ├── brush_tool.py        (create: paint colors)
│   ├── gizmo_tool.py        (create: camera orbit CGO gizmo)
│   └── measure_tool.py      (create: distance/angle/dihedral)
└── sections/                (existing, no changes)
```

---

### Task 1: BaseTool abstract class and tools package

**Files:**
- Create: `pymol-open-source/data/startup/matimac/tools/__init__.py`
- Create: `pymol-open-source/data/startup/matimac/tools/base.py`

**Step 1: Create the tools package**

Create `tools/__init__.py`:
```python
from .base import BaseTool
```

**Step 2: Create BaseTool ABC**

Create `tools/base.py`:
```python
from abc import ABC, abstractmethod
from pymol.Qt import QtWidgets, QtCore

Qt = QtCore.Qt


class BaseTool(ABC):
    """Base class for all viewport tools."""

    name: str = ""
    icon: str = ""  # Unicode icon for toolbar button

    def __init__(self, cmd, gl_widget):
        self.cmd = cmd
        self.gl_widget = gl_widget
        self._sub_panel = None

    def activate(self):
        """Called when this tool becomes the active tool."""
        pass

    def deactivate(self):
        """Called when switching away from this tool."""
        pass

    @abstractmethod
    def mouse_press(self, x, y, modifiers, button):
        """Handle mouse press in GL widget. Return True to consume event."""
        return False

    @abstractmethod
    def mouse_move(self, x, y, modifiers, buttons):
        """Handle mouse move in GL widget. Return True to consume event."""
        return False

    @abstractmethod
    def mouse_release(self, x, y, modifiers, button):
        """Handle mouse release in GL widget. Return True to consume event."""
        return False

    def get_sub_panel(self):
        """Return a QWidget with tool-specific options, or None."""
        return self._sub_panel
```

**Step 3: Verify file structure**

Run: `ls pymol-open-source/data/startup/matimac/tools/`
Expected: `__init__.py  base.py`

**Step 4: Commit**

```bash
git add pymol-open-source/data/startup/matimac/tools/__init__.py \
        pymol-open-source/data/startup/matimac/tools/base.py
git commit -m "feat: add BaseTool ABC for viewport tools"
```

---

### Task 2: ToolManager with event filter

**Files:**
- Create: `pymol-open-source/data/startup/matimac/toolbar.py`

**Step 1: Create ToolManager class**

This class installs an event filter on the GL widget and routes events to the active tool.

Create `toolbar.py`:
```python
from pymol.Qt import QtWidgets, QtCore, QtGui

Qt = QtCore.Qt


class ToolManager(QtCore.QObject):
    """Routes GL widget mouse events to the active tool."""

    tool_changed = QtCore.Signal(str)  # emits tool name

    def __init__(self, cmd, gl_widget, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self.gl_widget = gl_widget
        self._tools = {}
        self._active_tool = None
        gl_widget.installEventFilter(self)

    def register_tool(self, tool):
        self._tools[tool.name] = tool

    def set_active_tool(self, name):
        if self._active_tool:
            self._active_tool.deactivate()
        self._active_tool = self._tools.get(name)
        if self._active_tool:
            self._active_tool.activate()
        self.tool_changed.emit(name)

    @property
    def active_tool(self):
        return self._active_tool

    def eventFilter(self, obj, event):
        if obj is not self.gl_widget or self._active_tool is None:
            return False

        t = event.type()

        if t == QtCore.QEvent.Type.MouseButtonPress:
            pos = event.position() if hasattr(event, "position") else event.pos()
            mods = event.modifiers()
            return self._active_tool.mouse_press(
                pos.x(), pos.y(), mods, event.button()
            )

        if t == QtCore.QEvent.Type.MouseMove:
            pos = event.position() if hasattr(event, "position") else event.pos()
            mods = event.modifiers()
            return self._active_tool.mouse_move(
                pos.x(), pos.y(), mods, event.buttons()
            )

        if t == QtCore.QEvent.Type.MouseButtonRelease:
            pos = event.position() if hasattr(event, "position") else event.pos()
            mods = event.modifiers()
            return self._active_tool.mouse_release(
                pos.x(), pos.y(), mods, event.button()
            )

        return False
```

**Step 2: Verify**

Run: `python3 -c "import ast; ast.parse(open('pymol-open-source/data/startup/matimac/toolbar.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add pymol-open-source/data/startup/matimac/toolbar.py
git commit -m "feat: add ToolManager with GL widget event filter"
```

---

### Task 3: Toolbar overlay widget

**Files:**
- Modify: `pymol-open-source/data/startup/matimac/toolbar.py`

**Step 1: Add ToolbarWidget class to toolbar.py**

This is a transparent QWidget overlaid on the left edge of the GL widget. It shows tool buttons vertically.

Append to `toolbar.py`:

```python
class ToolbarWidget(QtWidgets.QWidget):
    """Vertical toolbar overlaid on the left edge of the GL widget."""

    def __init__(self, tool_manager, gl_widget, parent=None):
        super().__init__(parent or gl_widget)
        self.tool_manager = tool_manager
        self.gl_widget = gl_widget
        self.setFixedWidth(44)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(2)

        self._buttons = {}
        self._sub_panel_container = None

        # Style
        self.setStyleSheet("""
            ToolbarWidget {
                background: rgba(40, 40, 40, 200);
                border-right: 1px solid rgba(80, 80, 80, 150);
            }
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def add_tool_button(self, tool):
        btn = QtWidgets.QPushButton(tool.icon)
        btn.setFixedSize(36, 36)
        btn.setCheckable(True)
        btn.setToolTip(tool.name)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                border: 1px solid transparent;
                border-radius: 4px;
                background: transparent;
                color: white;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 30);
            }
            QPushButton:checked {
                background: rgba(100, 150, 255, 120);
                border: 1px solid rgba(100, 150, 255, 200);
            }
        """)
        btn.clicked.connect(lambda checked, n=tool.name: self._on_tool_clicked(n))
        self._layout.addWidget(btn)
        self._buttons[tool.name] = btn

    def finish_layout(self):
        """Call after adding all tool buttons."""
        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setStyleSheet("color: rgba(255,255,255,40);")
        self._layout.addWidget(sep)

        # Sub-panel container (shows options for active tool)
        self._sub_panel_container = QtWidgets.QVBoxLayout()
        self._layout.addLayout(self._sub_panel_container)

        self._layout.addStretch()

    def _on_tool_clicked(self, name):
        # Uncheck all other buttons
        for n, btn in self._buttons.items():
            btn.setChecked(n == name)

        self.tool_manager.set_active_tool(name)

        # Swap sub-panel
        self._clear_sub_panel()
        tool = self.tool_manager.active_tool
        if tool:
            panel = tool.get_sub_panel()
            if panel:
                self._sub_panel_container.addWidget(panel)
                panel.show()

    def _clear_sub_panel(self):
        if self._sub_panel_container:
            while self._sub_panel_container.count():
                item = self._sub_panel_container.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()
                    w.setParent(None)

    def reposition(self):
        """Position toolbar on the left edge of the GL widget."""
        self.move(0, 0)
        self.setFixedHeight(self.gl_widget.height())

    def showEvent(self, event):
        super().showEvent(event)
        self.reposition()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reposition()
```

**Step 2: Make toolbar reposition when GL widget resizes**

Add a `ResizeWatcher` helper at the top of the class section in `toolbar.py`:

```python
class _ResizeWatcher(QtCore.QObject):
    """Watches a widget for resize events and calls a callback."""

    def __init__(self, widget, callback, parent=None):
        super().__init__(parent)
        self._callback = callback
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.Resize:
            self._callback()
        return False
```

In `ToolbarWidget.__init__`, after setting up the layout, add:
```python
        self._resize_watcher = _ResizeWatcher(gl_widget, self.reposition, self)
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('pymol-open-source/data/startup/matimac/toolbar.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pymol-open-source/data/startup/matimac/toolbar.py
git commit -m "feat: add ToolbarWidget overlay for GL viewport"
```

---

### Task 4: Select Tool - click mode

**Files:**
- Create: `pymol-open-source/data/startup/matimac/tools/select_tool.py`

**Step 1: Create SelectTool with click mode**

```python
from pymol.Qt import QtWidgets, QtCore, QtGui

from .base import BaseTool

Qt = QtCore.Qt

# Selection visualization object name
_SEL_VIZ = "_matimac_sel_viz"


class SelectTool(BaseTool):
    name = "Select"
    icon = "\u25ce"  # ◎

    def __init__(self, cmd, gl_widget):
        super().__init__(cmd, gl_widget)
        self._mode = "click"  # click | box | lasso
        self._dragging = False
        self._drag_start = None
        self._lasso_points = []
        self._rubber_band = None
        self._lasso_overlay = None
        self._build_sub_panel()

    def _build_sub_panel(self):
        self._sub_panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self._sub_panel)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(2)

        for mode, icon, tip in [
            ("click", "\u2716", "Click select"),       # ✖
            ("box", "\u25a1", "Box select"),            # □
            ("lasso", "\u270d", "Lasso select"),        # ✍
        ]:
            btn = QtWidgets.QPushButton(icon)
            btn.setFixedSize(36, 36)
            btn.setCheckable(True)
            btn.setToolTip(tip)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px; border: 1px solid transparent;
                    border-radius: 4px; background: transparent; color: white;
                }
                QPushButton:hover { background: rgba(255,255,255,30); }
                QPushButton:checked { background: rgba(100,150,255,80); }
            """)
            btn.clicked.connect(lambda _, m=mode: self._set_mode(m))
            layout.addWidget(btn)
            if mode == "click":
                btn.setChecked(True)
            setattr(self, f"_btn_{mode}", btn)

    def _set_mode(self, mode):
        self._mode = mode
        for m in ("click", "box", "lasso"):
            getattr(self, f"_btn_{m}").setChecked(m == mode)

    def activate(self):
        pass

    def deactivate(self):
        self._cleanup_overlays()

    # --- Click mode ---

    def mouse_press(self, x, y, modifiers, button):
        if button != Qt.MouseButton.LeftButton:
            return False

        if self._mode == "click":
            return self._click_press(x, y, modifiers)
        elif self._mode == "box":
            return self._box_press(x, y, modifiers)
        elif self._mode == "lasso":
            return self._lasso_press(x, y, modifiers)
        return False

    def mouse_move(self, x, y, modifiers, buttons):
        if not (buttons & Qt.MouseButton.LeftButton):
            return False

        if self._mode == "box":
            return self._box_move(x, y)
        elif self._mode == "lasso":
            return self._lasso_move(x, y)
        return False

    def mouse_release(self, x, y, modifiers, button):
        if button != Qt.MouseButton.LeftButton:
            return False

        if self._mode == "box":
            return self._box_release(x, y, modifiers)
        elif self._mode == "lasso":
            return self._lasso_release(x, y, modifiers)
        return False

    def _click_press(self, x, y, modifiers):
        """Click on atom to select its residue."""
        # Let PyMOL handle the pick, then read pk1
        # We return False so PyMOL processes the click normally
        # Then use a short timer to read the pick result
        QtCore.QTimer.singleShot(50, lambda: self._process_click(modifiers))
        return False

    def _process_click(self, modifiers):
        """Process click after PyMOL has done its picking."""
        try:
            atoms = self.cmd.identify("pk1", mode=1)
            if not atoms:
                return
            obj_name, atom_id = atoms[0]

            # Get residue info for this atom
            resi_info = {}
            self.cmd.iterate(
                f"id {atom_id} and {obj_name}",
                "resi_info.update(resi=resi, chain=chain)",
                space={"resi_info": resi_info},
            )

            if not resi_info:
                return

            resi = resi_info["resi"]
            chain = resi_info["chain"]
            sel_expr = f"resi {resi} and chain {chain} and {obj_name}"

            shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
            if shift:
                # Add to existing selection
                try:
                    n = self.cmd.count_atoms("sele")
                    if n > 0:
                        self.cmd.select("sele", f"sele or ({sel_expr})")
                    else:
                        self.cmd.select("sele", sel_expr)
                except Exception:
                    self.cmd.select("sele", sel_expr)
            else:
                self.cmd.select("sele", sel_expr)

            self.cmd.unpick()
            self._update_selection_viz()
        except Exception:
            pass

    def _update_selection_viz(self):
        """Show selection as transparent yellow spheres."""
        try:
            self.cmd.delete(_SEL_VIZ)
        except Exception:
            pass
        try:
            n = self.cmd.count_atoms("sele")
            if n > 0:
                self.cmd.create(_SEL_VIZ, "sele")
                self.cmd.show("spheres", _SEL_VIZ)
                self.cmd.hide("everything", _SEL_VIZ)
                self.cmd.show("spheres", _SEL_VIZ)
                self.cmd.set("sphere_transparency", 0.6, _SEL_VIZ)
                self.cmd.set("sphere_scale", 0.5, _SEL_VIZ)
                self.cmd.color("yellow", _SEL_VIZ)
                self.cmd.disable(_SEL_VIZ)
                self.cmd.enable(_SEL_VIZ)
        except Exception:
            pass

    def _cleanup_overlays(self):
        if self._rubber_band:
            self._rubber_band.hide()
            self._rubber_band = None
        if self._lasso_overlay:
            self._lasso_overlay.hide()
            self._lasso_overlay = None

    # --- Box mode (placeholder, implemented in Task 5) ---

    def _box_press(self, x, y, modifiers):
        self._drag_start = (x, y)
        self._dragging = True
        if not self._rubber_band:
            self._rubber_band = QtWidgets.QRubberBand(
                QtWidgets.QRubberBand.Shape.Rectangle, self.gl_widget
            )
        self._rubber_band.setGeometry(int(x), int(y), 0, 0)
        self._rubber_band.show()
        return True

    def _box_move(self, x, y):
        if not self._dragging or not self._drag_start:
            return False
        sx, sy = self._drag_start
        rect = QtCore.QRect(
            int(min(sx, x)), int(min(sy, y)),
            int(abs(x - sx)), int(abs(y - sy))
        )
        self._rubber_band.setGeometry(rect)
        return True

    def _box_release(self, x, y, modifiers):
        if not self._dragging:
            return False
        self._dragging = False
        self._rubber_band.hide()

        sx, sy = self._drag_start
        rect = (min(sx, x), min(sy, y), max(sx, x), max(sy, y))
        self._select_atoms_in_rect(rect, modifiers)
        self._drag_start = None
        return True

    # --- Lasso mode (placeholder, implemented in Task 6) ---

    def _lasso_press(self, x, y, modifiers):
        self._lasso_points = [(x, y)]
        self._dragging = True
        if not self._lasso_overlay:
            self._lasso_overlay = _LassoOverlay(self.gl_widget)
        self._lasso_overlay.points = self._lasso_points
        self._lasso_overlay.setGeometry(self.gl_widget.rect())
        self._lasso_overlay.show()
        return True

    def _lasso_move(self, x, y):
        if not self._dragging:
            return False
        self._lasso_points.append((x, y))
        self._lasso_overlay.points = self._lasso_points
        self._lasso_overlay.update()
        return True

    def _lasso_release(self, x, y, modifiers):
        if not self._dragging:
            return False
        self._dragging = False
        self._lasso_overlay.hide()
        self._select_atoms_in_polygon(self._lasso_points, modifiers)
        self._lasso_points = []
        return True

    # --- Spatial selection helpers ---

    def _get_atom_screen_positions(self):
        """Project all atom 3D positions to 2D screen coordinates.

        Returns list of (screen_x, screen_y, obj_name, atom_id).
        Uses the current view matrix from cmd.get_view().
        """
        view = self.cmd.get_view()
        # Rotation matrix (3x3, row-major)
        rot = [
            [view[0], view[1], view[2]],
            [view[3], view[4], view[5]],
            [view[6], view[7], view[8]],
        ]
        # Camera-space translation
        tx, ty, tz = view[9], view[10], view[11]
        # Model-space origin
        ox, oy, oz = view[12], view[13], view[14]

        w = self.gl_widget.width()
        h = self.gl_widget.height()

        results = []
        atom_data = []
        self.cmd.iterate_state(
            -1,
            "all",
            "atom_data.append((model, ID, x, y, z))",
            space={"atom_data": atom_data},
        )

        for obj_name, atom_id, ax, ay, az in atom_data:
            # Translate to origin
            dx, dy, dz = ax - ox, ay - oy, az - oz
            # Rotate to camera space
            cx = rot[0][0] * dx + rot[0][1] * dy + rot[0][2] * dz
            cy = rot[1][0] * dx + rot[1][1] * dy + rot[1][2] * dz
            cz = rot[2][0] * dx + rot[2][1] * dy + rot[2][2] * dz
            # Apply camera translation
            cx += tx
            cy += ty
            cz += tz

            # Perspective / orthographic projection
            if abs(cz) < 0.001:
                continue
            # PyMOL uses a specific projection; approximate with simple perspective
            fov = abs(view[11])
            if fov < 0.001:
                fov = 1.0
            scale = min(w, h) / (2.0 * fov) * abs(tz)
            sx = w / 2.0 + cx * scale / (-cz) if cz != 0 else w / 2.0
            sy = h / 2.0 - cy * scale / (-cz) if cz != 0 else h / 2.0

            results.append((sx, sy, obj_name, atom_id))

        return results

    def _select_atoms_in_rect(self, rect, modifiers):
        """Select atoms whose screen projection falls inside rect."""
        x1, y1, x2, y2 = rect
        positions = self._get_atom_screen_positions()

        atom_ids_by_obj = {}
        for sx, sy, obj_name, atom_id in positions:
            if x1 <= sx <= x2 and y1 <= sy <= y2:
                atom_ids_by_obj.setdefault(obj_name, []).append(atom_id)

        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        self._apply_spatial_selection(atom_ids_by_obj, shift)

    def _select_atoms_in_polygon(self, polygon, modifiers):
        """Select atoms whose screen projection falls inside polygon."""
        if len(polygon) < 3:
            return

        positions = self._get_atom_screen_positions()

        atom_ids_by_obj = {}
        for sx, sy, obj_name, atom_id in positions:
            if self._point_in_polygon(sx, sy, polygon):
                atom_ids_by_obj.setdefault(obj_name, []).append(atom_id)

        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        self._apply_spatial_selection(atom_ids_by_obj, shift)

    def _apply_spatial_selection(self, atom_ids_by_obj, extend):
        """Apply selection from spatial queries (box/lasso)."""
        if not atom_ids_by_obj:
            return

        parts = []
        for obj_name, ids in atom_ids_by_obj.items():
            id_str = "+".join(str(i) for i in ids)
            parts.append(f"(id {id_str} and {obj_name})")
        expr = " or ".join(parts)

        if extend:
            try:
                n = self.cmd.count_atoms("sele")
                if n > 0:
                    expr = f"sele or ({expr})"
            except Exception:
                pass

        self.cmd.select("sele", expr)
        self._update_selection_viz()

    @staticmethod
    def _point_in_polygon(px, py, polygon):
        """Ray-casting point-in-polygon test."""
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > py) != (yj > py)) and (
                px < (xj - xi) * (py - yi) / (yj - yi) + xi
            ):
                inside = not inside
            j = i
        return inside


class _LassoOverlay(QtWidgets.QWidget):
    """Transparent overlay that draws the lasso path."""

    def __init__(self, parent):
        super().__init__(parent)
        self.points = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        if len(self.points) < 2:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor(100, 150, 255, 200), 2)
        painter.setPen(pen)
        brush = QtGui.QBrush(QtGui.QColor(100, 150, 255, 40))
        painter.setBrush(brush)

        path = QtGui.QPainterPath()
        path.moveTo(self.points[0][0], self.points[0][1])
        for px, py in self.points[1:]:
            path.lineTo(px, py)
        path.closeSubpath()
        painter.drawPath(path)
        painter.end()
```

**Step 2: Update tools `__init__.py`**

```python
from .base import BaseTool
from .select_tool import SelectTool
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('pymol-open-source/data/startup/matimac/tools/select_tool.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pymol-open-source/data/startup/matimac/tools/select_tool.py \
        pymol-open-source/data/startup/matimac/tools/__init__.py
git commit -m "feat: add SelectTool with click/box/lasso modes and selection viz"
```

---

### Task 5: Brush Tool

**Files:**
- Create: `pymol-open-source/data/startup/matimac/tools/brush_tool.py`
- Modify: `pymol-open-source/data/startup/matimac/tools/__init__.py`

**Step 1: Create BrushTool**

```python
from pymol.Qt import QtWidgets, QtCore, QtGui

from .base import BaseTool

Qt = QtCore.Qt

BRUSH_COLORS = [
    ("Red", "red"),
    ("Blue", "blue"),
    ("Green", "green"),
    ("Yellow", "yellow"),
    ("Orange", "orange"),
    ("Cyan", "cyan"),
    ("Magenta", "magenta"),
    ("White", "white"),
    ("Salmon", "salmon"),
    ("Forest", "forest"),
    ("Slate", "slate"),
    ("Deep Teal", "deepteal"),
]


class BrushTool(BaseTool):
    name = "Brush"
    icon = "\U0001f58c"  # 🖌

    def __init__(self, cmd, gl_widget):
        super().__init__(cmd, gl_widget)
        self._granularity = "residue"  # atom | residue | chain
        self._color = "red"
        self._painting = False
        self._last_painted = None  # avoid repainting same target
        self._build_sub_panel()

    def _build_sub_panel(self):
        self._sub_panel = QtWidgets.QWidget()
        self._sub_panel.setStyleSheet("color: white; font-size: 10px;")
        layout = QtWidgets.QVBoxLayout(self._sub_panel)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # Granularity buttons
        self._gran_btns = {}
        for gran, label in [("atom", "A"), ("residue", "R"), ("chain", "C")]:
            btn = QtWidgets.QPushButton(label)
            btn.setFixedSize(36, 24)
            btn.setCheckable(True)
            btn.setToolTip(f"Paint per {gran}")
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 11px; font-weight: bold;
                    border: 1px solid transparent; border-radius: 3px;
                    background: transparent; color: white;
                }
                QPushButton:hover { background: rgba(255,255,255,30); }
                QPushButton:checked { background: rgba(100,150,255,80); }
            """)
            btn.clicked.connect(lambda _, g=gran: self._set_granularity(g))
            layout.addWidget(btn)
            self._gran_btns[gran] = btn
        self._gran_btns["residue"].setChecked(True)

        # Color swatches (small grid)
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setStyleSheet("color: rgba(255,255,255,40);")
        layout.addWidget(sep)

        for name, color in BRUSH_COLORS:
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(36, 16)
            btn.setToolTip(name)
            try:
                rgb = cmd.get_color_tuple(color)
                r, g, b = int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
                btn.setStyleSheet(
                    f"background-color: rgb({r},{g},{b}); border: 1px solid gray; border-radius: 2px;"
                )
            except Exception:
                btn.setText(name[:2])
            btn.clicked.connect(lambda _, c=color: self._set_color(c))
            layout.addWidget(btn)

    def _set_granularity(self, gran):
        self._granularity = gran
        for g, btn in self._gran_btns.items():
            btn.setChecked(g == gran)

    def _set_color(self, color):
        self._color = color

    def activate(self):
        self._painting = False

    def deactivate(self):
        self._painting = False

    def mouse_press(self, x, y, modifiers, button):
        if button != Qt.MouseButton.LeftButton:
            return False
        self._painting = True
        self._last_painted = None
        self._paint_at(x, y)
        return True

    def mouse_move(self, x, y, modifiers, buttons):
        if not self._painting:
            return False
        self._paint_at(x, y)
        return True

    def mouse_release(self, x, y, modifiers, button):
        if button != Qt.MouseButton.LeftButton:
            return False
        self._painting = False
        self._last_painted = None
        return True

    def _paint_at(self, x, y):
        """Color the atom/residue/chain under cursor position."""
        # Use PyMOL picking: simulate a click and read pk1
        # We need to use the GL widget's coordinate system
        try:
            fb_scale = getattr(self.gl_widget, "fb_scale", 1.0)
            gl_x = int(fb_scale * x)
            gl_y = int(fb_scale * (self.gl_widget.height() - y))

            # Use PyMOL's internal picking
            self.gl_widget.pymol.button(0, 0, gl_x, gl_y, 0)  # press
            self.gl_widget.pymol.button(0, 1, gl_x, gl_y, 0)  # release

            atoms = self.cmd.identify("pk1", mode=1)
            if not atoms:
                return

            obj_name, atom_id = atoms[0]

            # Get atom info
            info = {}
            self.cmd.iterate(
                f"id {atom_id} and {obj_name}",
                "info.update(resi=resi, chain=chain, name=name)",
                space={"info": info},
            )
            if not info:
                return

            # Build selection expression based on granularity
            if self._granularity == "atom":
                target = f"id {atom_id} and {obj_name}"
                cache_key = (obj_name, atom_id)
            elif self._granularity == "residue":
                target = f"resi {info['resi']} and chain {info['chain']} and {obj_name}"
                cache_key = (obj_name, info["resi"], info["chain"])
            else:  # chain
                target = f"chain {info['chain']} and {obj_name}"
                cache_key = (obj_name, info["chain"])

            # Skip if same as last painted
            if cache_key == self._last_painted:
                return
            self._last_painted = cache_key

            self.cmd.color(self._color, target)
            self.cmd.unpick()
        except Exception:
            pass
```

**Step 2: Update tools `__init__.py`**

Add import:
```python
from .brush_tool import BrushTool
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('pymol-open-source/data/startup/matimac/tools/brush_tool.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pymol-open-source/data/startup/matimac/tools/brush_tool.py \
        pymol-open-source/data/startup/matimac/tools/__init__.py
git commit -m "feat: add BrushTool with atom/residue/chain paint modes"
```

---

### Task 6: Gizmo Tool (CGO camera orbit)

**Files:**
- Create: `pymol-open-source/data/startup/matimac/tools/gizmo_tool.py`
- Modify: `pymol-open-source/data/startup/matimac/tools/__init__.py`

**Step 1: Create GizmoTool**

```python
import math

from pymol.Qt import QtCore
from pymol import cgo

from .base import BaseTool

Qt = QtCore.Qt

_GIZMO_OBJ = "_matimac_gizmo"
_RING_SEGMENTS = 48
_RING_RADIUS = 2.0
_ARROW_LENGTH = 2.5
_ARROW_RADIUS = 0.06


def _make_ring(axis, color, radius=_RING_RADIUS, segments=_RING_SEGMENTS):
    """Generate CGO for a circle around the given axis."""
    obj = [cgo.COLOR, *color, cgo.BEGIN, cgo.LINE_STRIP]
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        c = math.cos(angle) * radius
        s = math.sin(angle) * radius
        if axis == "x":
            obj.extend([cgo.VERTEX, 0, c, s])
        elif axis == "y":
            obj.extend([cgo.VERTEX, c, 0, s])
        else:
            obj.extend([cgo.VERTEX, c, s, 0])
    obj.append(cgo.END)
    return obj


def _make_arrow(axis, color, length=_ARROW_LENGTH):
    """Generate CGO for an arrow along the given axis."""
    obj = [cgo.COLOR, *color]
    obj.extend([cgo.CYLINDER])
    if axis == "x":
        obj.extend([0, 0, 0, length, 0, 0])
    elif axis == "y":
        obj.extend([0, 0, 0, 0, length, 0])
    else:
        obj.extend([0, 0, 0, 0, 0, length])
    obj.extend([_ARROW_RADIUS, *color, *color])
    return obj


def _build_gizmo_cgo():
    """Build the full gizmo CGO object."""
    obj = []
    obj.extend(_make_ring("x", [1.0, 0.2, 0.2]))   # Red ring - X rotation
    obj.extend(_make_ring("y", [0.2, 1.0, 0.2]))   # Green ring - Y rotation
    obj.extend(_make_ring("z", [0.3, 0.3, 1.0]))   # Blue ring - Z rotation
    obj.extend(_make_arrow("x", [1.0, 0.2, 0.2]))  # Red arrow - X
    obj.extend(_make_arrow("y", [0.2, 1.0, 0.2]))  # Green arrow - Y
    obj.extend(_make_arrow("z", [0.3, 0.3, 1.0]))  # Blue arrow - Z
    # Center sphere
    obj.extend([cgo.COLOR, 0.8, 0.8, 0.8, cgo.SPHERE, 0, 0, 0, 0.15])
    return obj


class GizmoTool(BaseTool):
    name = "Gizmo"
    icon = "\u2725"  # ✥

    def __init__(self, cmd, gl_widget):
        super().__init__(cmd, gl_widget)
        self._dragging = False
        self._drag_start = None
        self._drag_axis = None  # "x", "y", "z", or None

    def activate(self):
        """Show the gizmo CGO object."""
        self._show_gizmo()

    def deactivate(self):
        """Hide the gizmo."""
        try:
            self.cmd.delete(_GIZMO_OBJ)
        except Exception:
            pass

    def _show_gizmo(self):
        """Create/update the gizmo at the current view origin."""
        try:
            self.cmd.delete(_GIZMO_OBJ)
        except Exception:
            pass

        gizmo_cgo = _build_gizmo_cgo()
        self.cmd.load_cgo(gizmo_cgo, _GIZMO_OBJ)

        # Position gizmo at the model origin (center of rotation)
        view = self.cmd.get_view()
        ox, oy, oz = view[12], view[13], view[14]
        self.cmd.translate([ox, oy, oz], _GIZMO_OBJ)

    def mouse_press(self, x, y, modifiers, button):
        if button != Qt.MouseButton.LeftButton:
            return False

        # Determine which axis the click is closest to
        self._drag_axis = self._detect_axis(x, y)
        if self._drag_axis is None:
            return False  # Click wasn't on gizmo, pass through

        self._dragging = True
        self._drag_start = (x, y)
        return True

    def mouse_move(self, x, y, modifiers, buttons):
        if not self._dragging or self._drag_axis is None:
            return False

        dx = x - self._drag_start[0]
        dy = y - self._drag_start[1]
        self._drag_start = (x, y)

        # Convert pixel delta to rotation angle
        sensitivity = 0.5  # degrees per pixel
        if self._drag_axis == "x":
            self.cmd.turn("x", dy * sensitivity)
        elif self._drag_axis == "y":
            self.cmd.turn("y", -dx * sensitivity)
        elif self._drag_axis == "z":
            self.cmd.turn("z", dx * sensitivity)

        return True

    def mouse_release(self, x, y, modifiers, button):
        if not self._dragging:
            return False
        self._dragging = False
        self._drag_axis = None
        self._drag_start = None
        # Refresh gizmo position after rotation
        self._show_gizmo()
        return True

    def _detect_axis(self, x, y):
        """Detect which gizmo axis the click is on.

        Uses a simple heuristic: divide the viewport into zones.
        Center area = gizmo. Then determine axis by click angle
        from center.
        """
        w = self.gl_widget.width()
        h = self.gl_widget.height()
        cx, cy = w / 2, h / 2

        # Distance from center
        dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        gizmo_screen_radius = min(w, h) * 0.15  # ~15% of viewport

        if dist > gizmo_screen_radius * 1.5:
            return None  # Too far from center

        if dist < gizmo_screen_radius * 0.2:
            # Click on center sphere - reset orientation
            try:
                self.cmd.orient()
                self._show_gizmo()
            except Exception:
                pass
            return None

        # Determine axis by angle from center
        angle = math.degrees(math.atan2(cy - y, x - cx)) % 360

        # Rough mapping: 0°/180° = Y axis, 90°/270° = X axis
        # Within 30° of horizontal = Y rotation
        # Within 30° of vertical = X rotation
        # Otherwise = Z rotation
        if angle % 180 < 30 or angle % 180 > 150:
            return "y"
        elif 60 < angle % 180 < 120:
            return "x"
        else:
            return "z"
```

**Step 2: Update tools `__init__.py`**

Add import:
```python
from .gizmo_tool import GizmoTool
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('pymol-open-source/data/startup/matimac/tools/gizmo_tool.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pymol-open-source/data/startup/matimac/tools/gizmo_tool.py \
        pymol-open-source/data/startup/matimac/tools/__init__.py
git commit -m "feat: add GizmoTool with CGO rings/arrows for camera orbit"
```

---

### Task 7: Measure Tool

**Files:**
- Create: `pymol-open-source/data/startup/matimac/tools/measure_tool.py`
- Modify: `pymol-open-source/data/startup/matimac/tools/__init__.py`

**Step 1: Create MeasureTool**

```python
from pymol.Qt import QtWidgets, QtCore

from .base import BaseTool

Qt = QtCore.Qt

_PICK_MARKER = "_matimac_pick_marker"


class MeasureTool(BaseTool):
    name = "Measure"
    icon = "\U0001f4cf"  # 📏

    def __init__(self, cmd, gl_widget):
        super().__init__(cmd, gl_widget)
        self._mode = "distance"  # distance | angle | dihedral
        self._picks = []  # list of (obj_name, atom_id) tuples
        self._measurement_count = 0
        self._build_sub_panel()

    def _build_sub_panel(self):
        self._sub_panel = QtWidgets.QWidget()
        self._sub_panel.setStyleSheet("color: white; font-size: 10px;")
        layout = QtWidgets.QVBoxLayout(self._sub_panel)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(2)

        self._mode_btns = {}
        for mode, icon, tip, n_atoms in [
            ("distance", "\u2194", "Distance (2 atoms)", 2),   # ↔
            ("angle", "\u2220", "Angle (3 atoms)", 3),         # ∠
            ("dihedral", "\u29a1", "Dihedral (4 atoms)", 4),   # ⦡
        ]:
            btn = QtWidgets.QPushButton(icon)
            btn.setFixedSize(36, 36)
            btn.setCheckable(True)
            btn.setToolTip(tip)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 18px; border: 1px solid transparent;
                    border-radius: 4px; background: transparent; color: white;
                }
                QPushButton:hover { background: rgba(255,255,255,30); }
                QPushButton:checked { background: rgba(100,150,255,80); }
            """)
            btn.clicked.connect(lambda _, m=mode: self._set_mode(m))
            layout.addWidget(btn)
            self._mode_btns[mode] = btn
        self._mode_btns["distance"].setChecked(True)

        # Status label
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setStyleSheet("color: rgba(255,255,255,40);")
        layout.addWidget(sep)

        self._status = QtWidgets.QLabel("Click atoms...")
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color: rgba(255,255,255,150); font-size: 9px;")
        layout.addWidget(self._status)

        # Clear button
        clear_btn = QtWidgets.QPushButton("\u2715")  # ✕
        clear_btn.setFixedSize(36, 24)
        clear_btn.setToolTip("Clear all measurements")
        clear_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; border: 1px solid transparent;
                border-radius: 3px; background: transparent; color: #ff6666;
            }
            QPushButton:hover { background: rgba(255,100,100,40); }
        """)
        clear_btn.clicked.connect(self._clear_all)
        layout.addWidget(clear_btn)

    def _set_mode(self, mode):
        self._mode = mode
        self._picks = []
        self._clear_markers()
        for m, btn in self._mode_btns.items():
            btn.setChecked(m == mode)
        needed = {"distance": 2, "angle": 3, "dihedral": 4}[mode]
        self._status.setText(f"Click {needed} atoms...")

    def _required_picks(self):
        return {"distance": 2, "angle": 3, "dihedral": 4}[self._mode]

    def activate(self):
        self._picks = []
        self._update_status()

    def deactivate(self):
        self._picks = []
        self._clear_markers()

    def mouse_press(self, x, y, modifiers, button):
        if button != Qt.MouseButton.LeftButton:
            return False
        # Let PyMOL do the picking, then read result
        QtCore.QTimer.singleShot(50, self._process_pick)
        return False  # Don't consume - let PyMOL pick

    def mouse_move(self, x, y, modifiers, buttons):
        return False

    def mouse_release(self, x, y, modifiers, button):
        return False

    def _process_pick(self):
        try:
            atoms = self.cmd.identify("pk1", mode=1)
            if not atoms:
                return

            obj_name, atom_id = atoms[0]

            # Avoid duplicate picks
            if self._picks and self._picks[-1] == (obj_name, atom_id):
                return

            self._picks.append((obj_name, atom_id))

            # Show marker sphere on picked atom
            marker_name = f"{_PICK_MARKER}_{len(self._picks)}"
            self.cmd.select(marker_name, f"id {atom_id} and {obj_name}")
            self.cmd.show("spheres", marker_name)
            self.cmd.set("sphere_scale", 0.3, marker_name)
            self.cmd.color("orange", marker_name)

            self.cmd.unpick()
            self._update_status()

            # Check if we have enough picks
            if len(self._picks) >= self._required_picks():
                self._create_measurement()
                self._clear_markers()
                self._picks = []
                self._update_status()

        except Exception:
            pass

    def _create_measurement(self):
        self._measurement_count += 1

        # Build selection strings for each pick
        sels = []
        for i, (obj_name, atom_id) in enumerate(self._picks):
            sel_name = f"_mm_pk{i}"
            self.cmd.select(sel_name, f"id {atom_id} and {obj_name}")
            sels.append(sel_name)

        try:
            if self._mode == "distance":
                name = f"dist_{self._measurement_count}"
                self.cmd.distance(name, sels[0], sels[1])
                d = self.cmd.get_distance(sels[0], sels[1])
                self._status.setText(f"{d:.2f} A")
            elif self._mode == "angle":
                name = f"angle_{self._measurement_count}"
                self.cmd.angle(name, sels[0], sels[1], sels[2])
                a = self.cmd.get_angle(sels[0], sels[1], sels[2])
                self._status.setText(f"{a:.1f}\u00b0")
            elif self._mode == "dihedral":
                name = f"dihe_{self._measurement_count}"
                self.cmd.dihedral(name, sels[0], sels[1], sels[2], sels[3])
                d = self.cmd.get_dihedral(sels[0], sels[1], sels[2], sels[3])
                self._status.setText(f"{d:.1f}\u00b0")

            # Style the measurement
            self.cmd.set("dash_color", "white", name)
            self.cmd.set("dash_gap", 0.2, name)
            self.cmd.set("label_color", "white", name)
        except Exception as e:
            self._status.setText(f"Error: {e}")
        finally:
            # Clean up temp selections
            for sel_name in sels:
                try:
                    self.cmd.delete(sel_name)
                except Exception:
                    pass

    def _update_status(self):
        needed = self._required_picks()
        have = len(self._picks)
        remaining = needed - have
        if remaining > 0:
            self._status.setText(f"Pick {remaining} more atom{'s' if remaining > 1 else ''}...")
        else:
            self._status.setText("Click atoms...")

    def _clear_markers(self):
        for i in range(1, 5):
            try:
                self.cmd.delete(f"{_PICK_MARKER}_{i}")
            except Exception:
                pass

    def _clear_all(self):
        self._clear_markers()
        self._picks = []
        for i in range(1, self._measurement_count + 1):
            for prefix in ("dist_", "angle_", "dihe_"):
                try:
                    self.cmd.delete(f"{prefix}{i}")
                except Exception:
                    pass
        self._measurement_count = 0
        self._update_status()
```

**Step 2: Update tools `__init__.py`**

Add import:
```python
from .measure_tool import MeasureTool
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('pymol-open-source/data/startup/matimac/tools/measure_tool.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pymol-open-source/data/startup/matimac/tools/measure_tool.py \
        pymol-open-source/data/startup/matimac/tools/__init__.py
git commit -m "feat: add MeasureTool with distance/angle/dihedral modes"
```

---

### Task 8: Wire everything together in `__init__.py`

**Files:**
- Modify: `pymol-open-source/data/startup/matimac/__init__.py`
- Modify: `pymol-open-source/data/startup/matimac/tools/__init__.py` (final exports)

**Step 1: Finalize tools `__init__.py`**

```python
from .base import BaseTool
from .select_tool import SelectTool
from .brush_tool import BrushTool
from .gizmo_tool import GizmoTool
from .measure_tool import MeasureTool
```

**Step 2: Update `__init__.py` to create toolbar on startup**

Modify `open_matimac()` in `__init__.py`:

```python
def open_matimac():
    from pymol.Qt import QtCore
    from pymol import cmd

    Qt = QtCore.Qt

    window = _get_main_window()
    if window is None:
        return

    if not hasattr(window, '_matimac_sidebar'):
        from .sidebar import MatiMacSidebar

        window._matimac_sidebar = MatiMacSidebar(window)
        window.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea,
            window._matimac_sidebar,
        )

        # Hide the default external GUI (CLI)
        if hasattr(window, 'ext_window'):
            window.ext_window.hide()

        # Hide internal GUI elements and set defaults
        try:
            cmd.set("internal_gui", 0)
            cmd.set("internal_feedback", 0)
            cmd.bg_color("black")
        except Exception:
            pass

        # --- Create toolbar ---
        _init_toolbar(window, cmd)

    window._matimac_sidebar.show()
    window._matimac_sidebar.raise_()


def _init_toolbar(window, cmd):
    """Create the 3D viewport toolbar with tools."""
    from .toolbar import ToolManager, ToolbarWidget
    from .tools import SelectTool, BrushTool, GizmoTool, MeasureTool

    gl_widget = getattr(window, 'pymolwidget', None)
    if gl_widget is None:
        return

    # Create tool manager
    manager = ToolManager(cmd, gl_widget, parent=window)

    # Create tools
    tools = [
        SelectTool(cmd, gl_widget),
        BrushTool(cmd, gl_widget),
        GizmoTool(cmd, gl_widget),
        MeasureTool(cmd, gl_widget),
    ]
    for tool in tools:
        manager.register_tool(tool)

    # Create toolbar widget
    toolbar = ToolbarWidget(manager, gl_widget, parent=gl_widget)
    for tool in tools:
        toolbar.add_tool_button(tool)
    toolbar.finish_layout()
    toolbar.show()

    # Store references
    window._matimac_toolbar = toolbar
    window._matimac_tool_manager = manager
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('pymol-open-source/data/startup/matimac/__init__.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pymol-open-source/data/startup/matimac/__init__.py \
        pymol-open-source/data/startup/matimac/tools/__init__.py
git commit -m "feat: wire toolbar and tools into MatiMac plugin startup"
```

---

### Task 9: Manual integration test

**Files:** None (testing only)

**Step 1: Launch PyMOL with MatiMac**

Run: `cd pymol-open-source && python setup.py install && pymol`

Or if using development mode:
Run: `pymol`

**Step 2: Verify toolbar appears**

Expected:
- MatiMac sidebar on the left (as before)
- Vertical toolbar overlaid on the left edge of the 3D viewport
- 4 tool buttons visible: ◎ (Select), 🖌 (Brush), ✥ (Gizmo), 📏 (Measure)

**Step 3: Test Select tool**

1. Load a structure: use sidebar Loader → "1HHO"
2. Click Select tool (◎) in toolbar
3. Click on an atom → residue should get selected, yellow transparent spheres appear
4. Shift+click another atom → adds to selection
5. Switch to "box" sub-mode → drag rectangle → atoms inside get selected
6. Switch to "lasso" sub-mode → draw lasso → atoms inside get selected

**Step 4: Test Brush tool**

1. Click Brush tool (🖌) in toolbar
2. Select a color from the sub-panel
3. Click/drag on the molecule → residues change color
4. Switch granularity to "A" (atom) → individual atoms change color
5. Switch to "C" (chain) → entire chain changes color

**Step 5: Test Gizmo tool**

1. Click Gizmo tool (✥)
2. CGO gizmo should appear (3 colored rings + arrows)
3. Drag on the gizmo → camera rotates along the corresponding axis
4. Click center sphere → orientation resets

**Step 6: Test Measure tool**

1. Click Measure tool (📏)
2. Click two atoms → distance line + label appears in viewport
3. Switch to angle mode → click 3 atoms → angle shown
4. Click clear button → all measurements removed

**Step 7: Commit any fixes from testing**

```bash
git add -A
git commit -m "fix: adjustments from manual integration testing"
```
