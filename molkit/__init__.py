"""
MolKit - Friendly PyMOL Interface
Version: 0.1.0
"""

from pymol.Qt import QtCore, QtGui, QtWidgets


_DARK_QSS = """
QWidget {
    background-color: #1e1e1e;
    color: #d0d0d0;
    font-size: 13px;
}
QMainWindow { background-color: #1e1e1e; }
QDockWidget { background-color: #1e1e1e; color: #d0d0d0; }
QDockWidget::title {
    background-color: #262626; color: #d0d0d0;
    padding: 6px; border-bottom: 1px solid #3c3c3c;
}
QMenuBar { background-color: #262626; color: #d0d0d0; }
QMenuBar::item:selected { background-color: #385e94; }
QMenu { background-color: #262626; color: #d0d0d0; border: 1px solid #3c3c3c; }
QMenu::item:selected { background-color: #385e94; }
QPushButton {
    background-color: #303030; color: #d0d0d0;
    border: 1px solid #4a4a4a; border-radius: 4px;
    padding: 4px 10px;
}
QPushButton:hover { background-color: #3a3a3a; border-color: #5690d2; }
QPushButton:pressed { background-color: #2a2a2a; }
QPushButton:disabled { color: #646464; background-color: #262626; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #161616; color: #d0d0d0;
    border: 1px solid #4a4a4a; border-radius: 3px; padding: 3px 6px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #5690d2;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #262626; color: #d0d0d0;
    selection-background-color: #385e94;
}
QCheckBox { color: #d0d0d0; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px; border: 1px solid #4a4a4a;
    border-radius: 3px; background-color: #161616;
}
QCheckBox::indicator:checked { background-color: #5690d2; border-color: #5690d2; }
QScrollArea { border: none; }
QScrollBar:vertical {
    background: #1e1e1e; width: 8px; border: none;
}
QScrollBar::handle:vertical {
    background: #4a4a4a; border-radius: 4px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #5a5a5a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #1e1e1e; height: 8px; border: none;
}
QScrollBar::handle:horizontal {
    background: #4a4a4a; border-radius: 4px; min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #5a5a5a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QTabBar::tab {
    background-color: #262626; color: #a0a0a0;
    border: 1px solid #3c3c3c; padding: 5px 12px;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
}
QTabBar::tab:selected { background-color: #1e1e1e; color: #d0d0d0; border-bottom-color: #1e1e1e; }
QTabBar::tab:hover { color: #e0e0e0; }
QLabel { background-color: transparent; }
QToolTip { background-color: #282828; color: #d0d0d0; border: 1px solid #4a4a4a; }
QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #3c3c3c; }
QGroupBox { border: 1px solid #3c3c3c; border-radius: 4px; margin-top: 8px; padding-top: 8px; }
QGroupBox::title { color: #d0d0d0; }
"""


def _apply_dark_theme(app):
    """Apply dark stylesheet to the entire application."""
    app.setStyleSheet(_DARK_QSS)


def _get_main_window():
    """Find the PyMOL QMainWindow instance."""
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, QtWidgets.QMainWindow):
            return w
    return None


def __init_plugin__(app=None):
    from pymol import plugins
    plugins.addmenuitemqt('MolKit', open_molkit)

    # Apply dark theme
    _apply_dark_theme(QtWidgets.QApplication.instance())

    # Auto-open on startup (slight delay to let PyMOL finish init)
    QtCore.QTimer.singleShot(500, open_molkit)


def open_molkit():
    from pymol.Qt import QtCore
    from pymol import cmd

    Qt = QtCore.Qt

    window = _get_main_window()
    if window is None:
        return

    # Give top corners to left/right docks so they extend full height
    window.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
    window.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

    if not hasattr(window, '_molkit_sidebar'):
        # Tab bar as a top dock (squeezed between left/right panels)
        from .tabs import ModelTabBar

        tab_bar = ModelTabBar(cmd, window)
        tab_dock = QtWidgets.QDockWidget("", window)
        tab_dock.setObjectName("molkit_model_tabs")
        tab_dock.setWidget(tab_bar)
        tab_dock.setTitleBarWidget(QtWidgets.QWidget())  # hide title bar
        tab_dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        window.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, tab_dock)
        window._molkit_tab_bar = tab_bar

        # Sidebar
        from .sidebar import MolKitSidebar

        window._molkit_sidebar = MolKitSidebar(window)
        window.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea,
            window._molkit_sidebar,
        )

        # Connect sidebar to the tab bar
        window._molkit_sidebar.widget_inner.set_tab_bar(tab_bar)

        # Inspector panel on the right
        from .inspector import InspectorDock

        window._molkit_inspector = InspectorDock(cmd, window)
        window.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            window._molkit_inspector,
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

    window._molkit_sidebar.show()
    window._molkit_sidebar.raise_()
