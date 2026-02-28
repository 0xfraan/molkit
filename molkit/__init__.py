"""
MolKit - Friendly PyMOL Interface
Version: 0.1.0
"""

from pymol.Qt import QtCore, QtWidgets


def _get_main_window():
    """Find the PyMOL QMainWindow instance."""
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, QtWidgets.QMainWindow):
            return w
    return None


def __init_plugin__(app=None):
    from pymol import plugins
    plugins.addmenuitemqt('MolKit', open_molkit)

    # Auto-open on startup (slight delay to let PyMOL finish init)
    QtCore.QTimer.singleShot(500, open_molkit)


def open_molkit():
    from pymol.Qt import QtCore
    from pymol import cmd

    Qt = QtCore.Qt

    window = _get_main_window()
    if window is None:
        return

    if not hasattr(window, '_molkit_sidebar'):
        from .sidebar import MolKitSidebar

        window._molkit_sidebar = MolKitSidebar(window)
        window.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea,
            window._molkit_sidebar,
        )

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
