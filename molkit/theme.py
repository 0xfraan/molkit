"""
MolKit Theme — modern developer-tool aesthetic.

Zinc palette, Inter font, 6px radius, 8px grid spacing.
All design tokens live here. No file should hardcode colors or font sizes.
"""

# ── Colors (Zinc palette) ──────────────────────────────────────────────
BG = "#09090B"              # zinc-950
SURFACE = "#18181B"          # zinc-900
HOVER = "#27272A"            # zinc-800
BORDER = "#3F3F46"           # zinc-700
DISABLED = "#52525B"         # zinc-600
TEXT_MUTED = "#A1A1AA"       # zinc-400
TEXT = "#FAFAFA"             # zinc-50

PRESSED = "#111113"
CHECKED = "#3F3F46"
ACCENT = "#818CF8"           # indigo-400 (section accent bar)

STATUS_SUCCESS = "#4ADE80"   # green-400
STATUS_ERROR = "#F87171"     # red-400
STATUS_WARNING = "#FBBF24"   # amber-400

# ── Typography ──────────────────────────────────────────────────────────
FONT_FAMILY = "'Inter', 'SF Pro Display', -apple-system, 'Segoe UI', sans-serif"
FONT_SIZE_SM = "12px"
FONT_SIZE_BASE = "13px"
FONT_SIZE_LG = "18px"

# ── Geometry ────────────────────────────────────────────────────────────
RADIUS = "6px"
RADIUS_SM = "4px"


def status_style(kind: str) -> str:
    """Return an inline QSS snippet for a status label.

    Usage:  label.setStyleSheet(status_style("success"))
    Valid kinds: "success", "error", "warning", "muted"
    """
    color = {
        "success": STATUS_SUCCESS,
        "error": STATUS_ERROR,
        "warning": STATUS_WARNING,
        "muted": TEXT_MUTED,
    }.get(kind, TEXT_MUTED)
    return f"color: {color}; font-size: {FONT_SIZE_SM};"


def build_qss() -> str:
    """Build the full application QSS string from theme tokens."""
    return f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_BASE};
}}
QMainWindow {{ background-color: {BG}; }}
QDockWidget {{ background-color: {BG}; color: {TEXT}; }}
QDockWidget::title {{
    background-color: {SURFACE}; color: {TEXT};
    padding: 6px; border-bottom: 1px solid {BORDER};
}}
QMenuBar {{ background-color: {SURFACE}; color: {TEXT}; }}
QMenuBar::item:selected {{ background-color: {HOVER}; border-radius: {RADIUS_SM}; }}
QMenu {{
    background-color: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: {RADIUS};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px; border-radius: {RADIUS_SM};
}}
QMenu::item:selected {{ background-color: {HOVER}; }}
QPushButton {{
    background-color: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: {RADIUS};
    padding: 6px 12px;
    font-size: {FONT_SIZE_BASE};
}}
QPushButton:hover {{ background-color: {HOVER}; border-color: {DISABLED}; }}
QPushButton:pressed {{ background-color: {PRESSED}; }}
QPushButton:disabled {{ color: {DISABLED}; background-color: {SURFACE}; }}
QPushButton:checked {{ background-color: {CHECKED}; border-color: {TEXT_MUTED}; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {PRESSED}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: {RADIUS};
    padding: 5px 8px;
    font-size: {FONT_SIZE_BASE};
    selection-background-color: {CHECKED};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none; padding-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: {RADIUS};
    selection-background-color: {HOVER};
    padding: 4px;
}}
QCheckBox {{ color: {TEXT}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {BORDER};
    border-radius: {RADIUS_SM}; background-color: {PRESSED};
}}
QCheckBox::indicator:hover {{ border-color: {DISABLED}; }}
QCheckBox::indicator:checked {{
    background-color: {ACCENT}; border-color: {ACCENT};
}}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{
    background: transparent; width: 6px; border: none;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 3px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {DISABLED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 6px; border: none;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 3px; min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{ background: {DISABLED}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QTabBar::tab {{
    background-color: {SURFACE}; color: {TEXT_MUTED};
    border: 1px solid {BORDER}; padding: 6px 14px;
    border-top-left-radius: {RADIUS}; border-top-right-radius: {RADIUS};
    font-size: {FONT_SIZE_BASE};
}}
QTabBar::tab:selected {{
    background-color: {BG}; color: {TEXT};
    border-bottom-color: {BG};
}}
QTabBar::tab:hover {{ color: {TEXT}; }}
QLabel {{ background-color: transparent; }}
QToolTip {{
    background-color: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: {RADIUS_SM};
    padding: 4px 8px;
}}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {BORDER}; }}
QGroupBox {{
    border: 1px solid {BORDER}; border-radius: {RADIUS};
    margin-top: 8px; padding-top: 12px;
}}
QGroupBox::title {{ color: {TEXT}; }}
"""
