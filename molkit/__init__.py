"""
MolKit - Friendly PyMOL Interface
Version: 0.1.0
"""

from pymol.Qt import QtCore, QtGui, QtWidgets

from .theme import build_qss


def _apply_dark_theme(app):
    """Apply dark stylesheet to the entire application."""
    app.setStyleSheet(build_qss())


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

    # Top corners → left/right docks so sidebars extend full height
    window.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
    window.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
    # Bottom corners → bottom dock so console bar spans between sidebars
    window.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.BottomDockWidgetArea)
    window.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.BottomDockWidgetArea)

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

        # Console dock at the bottom (between left/right sidebars)
        # Embeds PyMOL's ext_window inside a dock instead of a floating window
        from .console_bar import ConsoleBar

        console_container = QtWidgets.QWidget()
        console_layout = QtWidgets.QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(0)

        console_bar = ConsoleBar(window)
        console_layout.addWidget(console_bar)

        # Reparent ext_window into the bottom dock
        window._molkit_ext_holder = QtWidgets.QWidget()
        ext_layout = QtWidgets.QVBoxLayout(window._molkit_ext_holder)
        ext_layout.setContentsMargins(0, 0, 0, 0)
        if hasattr(window, 'ext_window'):
            ext_w = window.ext_window
            if isinstance(ext_w, QtWidgets.QMainWindow):
                # Take the central widget out of the QMainWindow shell
                central = ext_w.centralWidget()
                if central:
                    ext_layout.addWidget(central)
            else:
                ext_layout.addWidget(ext_w)
        window._molkit_ext_holder.setVisible(False)
        console_layout.addWidget(window._molkit_ext_holder)

        console_dock = QtWidgets.QDockWidget("", window)
        console_dock.setObjectName("molkit_console_dock")
        console_dock.setWidget(console_container)
        console_dock.setTitleBarWidget(QtWidgets.QWidget())  # hide title bar
        console_dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, console_dock)
        window._molkit_console_bar = console_bar

        # Hide internal GUI elements and set defaults
        try:
            cmd.set("internal_gui", 0)
            cmd.set("internal_feedback", 0)
            cmd.bg_color("black")
        except Exception:
            pass

    window._molkit_sidebar.show()
    window._molkit_sidebar.raise_()
