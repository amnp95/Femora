from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenuBar, QFileDialog, QMessageBox, QProgressDialog,QApplication
from qtpy.QtCore import Qt


class ToolbarManager:
    """Manages the creation and interaction of the application's menubar and toolbar actions.

    This class centralizes the setup of menus (File, View, Theme, Tools)
    and their associated actions, connecting them to the main window's
    functionality.

    Attributes:
        main_window (MainWindow): Reference to the main application window instance.
        menubar (QMenuBar): The QMenuBar object of the main window.

    Example:
        >>> from qtpy.QtWidgets import QMainWindow, QApplication, QMenuBar
        >>> # Assume ToolbarManager is imported or defined in the current scope.
        >>> class MockMainWindow(QMainWindow):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self._menu_bar = QMenuBar(self)
        ...         self.setMenuBar(self._menu_bar)
        ...         self.increase_font_size = lambda: None
        ...         self.decrease_font_size = lambda: None
        ...         self.switch_theme = lambda theme_name: None
        ...         self.drm_manager = type('DRMManager', (object,), {
        ...             'create_sv_wave': lambda: None,
        ...             'create_surface_wave': lambda: None
        ...         })()
        ...         self.meshMaker = type('MeshMaker', (object,), {
        ...             'export_to_tcl': lambda filename, progress_callback: True,
        ...             'export_to_vtk': lambda filename: True
        ...         })()
        ...
        ...     def menuBar(self):
        ...         return self._menu_bar
        ...
        >>> app = QApplication([])
        >>> main_window = MockMainWindow()
        >>> manager = ToolbarManager(main_window)
        >>> # After initialization, all menus are set up
        >>> # Check if top-level menus exist
        >>> menu_titles = [action.text() for action in manager.menubar.actions()]
        >>> print(sorted(menu_titles))
        ['File', 'Theme', 'Tools', 'View']
        >>> app.quit()
    """
    def __init__(self, main_window: 'MainWindow'):
        """Initializes the ToolbarManager.

        Args:
            main_window: The main application window instance. This is used
                to access its menubar and connect actions to its methods.
        """
        self.main_window = main_window
        self.menubar = main_window.menuBar()
        self.setup_menus()

    def setup_menus(self):
        """Sets up all primary menus in the menubar.

        This method orchestrates the creation of the File, View, Theme,
        and Tools menus by calling their respective creation methods.

        Example:
            >>> from qtpy.QtWidgets import QMainWindow, QApplication, QMenuBar
            >>> class MockMainWindow(QMainWindow):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self._menu_bar = QMenuBar(self)
            ...         self.setMenuBar(self._menu_bar)
            ...         self.increase_font_size = lambda: None
            ...         self.decrease_font_size = lambda: None
            ...         self.switch_theme = lambda theme_name: None
            ...         self.drm_manager = type('DRMManager', (object,), {
            ...             'create_sv_wave': lambda: None,
            ...             'create_surface_wave': lambda: None
            ...         })()
            ...         self.meshMaker = type('MeshMaker', (object,), {
            ...             'export_to_tcl': lambda filename, progress_callback: True,
            ...             'export_to_vtk': lambda filename: True
            ...         })()
            ...
            ...     def menuBar(self):
            ...         return self._menu_bar
            ...
            >>> app = QApplication([])
            >>> main_window = MockMainWindow()
            >>> manager = ToolbarManager(main_window)
            >>> manager.menubar.clear() # Clear existing menus for explicit setup
            >>> manager.setup_menus()
            >>> menu_titles = [action.text() for action in manager.menubar.actions()]
            >>> print(sorted(menu_titles))
            ['File', 'Theme', 'Tools', 'View']
            >>> app.quit()
        """
        self.create_file_menu()
        self.create_view_menu()
        self.create_theme_menu()
        self.create_tools_menu()

    def create_file_menu(self):
        """Creates the 'File' menu and its associated actions.

        This includes actions for exporting data to TCL and VTK formats.

        Example:
            >>> from qtpy.QtWidgets import QMainWindow, QApplication, QMenuBar
            >>> class MockMainWindow(QMainWindow):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self._menu_bar = QMenuBar(self)
            ...         self.setMenuBar(self._menu_bar)
            ...         # Mock methods that would be connected to actions
            ...         self.export_to_tcl = lambda: None
            ...         self.export_to_vtk = lambda: None
            ...     def menuBar(self):
            ...         return self._menu_bar
            ...
            >>> app = QApplication([])
            >>> main_window = MockMainWindow()
            >>> manager = ToolbarManager(main_window)
            >>> manager.create_file_menu()
            >>> file_menu_action = manager.menubar.actions()[0]
            >>> print(file_menu_action.text())
            File
            >>> export_menu_action = file_menu_action.menu().actions()[0]
            >>> print(export_menu_action.text())
            Export
            >>> app.quit()
        """
        file_menu = self.menubar.addMenu("File")
        export_menu = file_menu.addMenu("Export")

        export_tcl_action = QAction("Export TCL", self.main_window)
        export_tcl_action.triggered.connect(self.export_to_tcl)
        export_menu.addAction(export_tcl_action)

        export_vtk_action = QAction("Export VTK", self.main_window)
        export_vtk_action.triggered.connect(self.export_to_vtk)
        export_menu.addAction(export_vtk_action)
        

    def export_to_tcl(self):
        """Handles the 'Export TCL' action, prompting the user for a filename
        and then exporting the current mesh to a TCL file.

        Shows a progress dialog during export and informs the user about
        success or failure.

        Raises:
            Exception: If any error occurs during the file dialog or export process.

        Example:
            >>> from qtpy.QtWidgets import QMainWindow, QApplication, QMenuBar
            >>> # This example cannot fully simulate QFileDialog interaction,
            >>> # but shows the setup and expected behavior.
            >>> class MockMainWindow(QMainWindow):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self.setMenuBar(QMenuBar())
            ...         self.meshMaker = type('MeshMaker', (object,), {
            ...             'export_to_tcl': lambda filename, progress_callback: (print(f"Mock exporting TCL to {filename} with progress."), True)[1],
            ...         })()
            ...     def menuBar(self):
            ...         return QMenuBar() # Simplified mock for menuBar
            ...
            >>> app = QApplication([])
            >>> main_window = MockMainWindow()
            >>> manager = ToolbarManager(main_window)
            >>> # To trigger the functionality, you would normally click the menu item.
            >>> # manager.export_to_tcl() # This would open a file dialog.
            >>> app.quit()
        """
        try:
            # Get file path from user
            filename, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Export TCL File",
                "",
                "TCL Files (*.tcl);;All Files (*)"
            )
            
            if filename:
                from femora.gui.progress_gui import get_progress_callback_gui

                progress_callback = get_progress_callback_gui("Exporting")

                success = self.main_window.meshMaker.export_to_tcl(filename, progress_callback)

                if success:
                    QMessageBox.information(
                        self.main_window,
                        "Success",
                        "File exported successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "Export Failed",
                        "Failed to export the file. Please check the console for details."
                    )
                    
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Error",
                f"An error occurred while exporting: {str(e)}"
            )

    def export_to_vtk(self):
        """Handles the 'Export VTK' action, prompting the user for a filename
        and then exporting the current mesh to a VTK file.

        Informs the user about success or failure of the export.

        Raises:
            Exception: If any error occurs during the file dialog or export process.

        Example:
            >>> from qtpy.QtWidgets import QMainWindow, QApplication, QMenuBar
            >>> # This example cannot fully simulate QFileDialog interaction,
            >>> # but shows the setup and expected behavior.
            >>> class MockMainWindow(QMainWindow):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self.setMenuBar(QMenuBar())
            ...         self.meshMaker = type('MeshMaker', (object,), {
            ...             'export_to_vtk': lambda filename: (print(f"Mock exporting VTK to {filename}"), True)[1]
            ...         })()
            ...     def menuBar(self):
            ...         return QMenuBar()
            ...
            >>> app = QApplication([])
            >>> main_window = MockMainWindow()
            >>> manager = ToolbarManager(main_window)
            >>> # To trigger the functionality, you would normally click the menu item.
            >>> # manager.export_to_vtk() # This would open a file dialog.
            >>> app.quit()
        """
        try:
            # Get file path from user
            filename, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Export VTK File",
                "",
                "VTK Files (*.vtk);;All Files (*)"
            )
            
            if filename:
                # Export the file
                success = self.main_window.meshMaker.export_to_vtk(filename)
                
                if success:
                    QMessageBox.information(
                        self.main_window,
                        "Success",
                        "File exported successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "Export Failed",
                        "Failed to export the file. Please check the console for details."
                    )
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Error",
                f"An error occurred while exporting: {str(e)}"
            )

    def create_view_menu(self):
        """Creates the 'View' menu and its associated actions.

        This includes actions for increasing and decreasing the application's
        font size.

        Example:
            >>> from qtpy.QtWidgets import QMainWindow, QApplication, QMenuBar
            >>> class MockMainWindow(QMainWindow):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self._menu_bar = QMenuBar(self)
            ...         self.setMenuBar(self._menu_bar)
            ...         # Mock methods that would be connected to actions
            ...         self.increase_font_size = lambda: None
            ...         self.decrease_font_size = lambda: None
            ...     def menuBar(self):
            ...         return self._menu_bar
            ...
            >>> app = QApplication([])
            >>> main_window = MockMainWindow()
            >>> manager = ToolbarManager(main_window)
            >>> manager.create_view_menu()
            >>> # Find the 'View' menu (its index depends on other menus added)
            >>> view_menu_action = next(a for a in manager.menubar.actions() if a.text() == "View")
            >>> print(view_menu_action.text())
            View
            >>> app.quit()
        """
        view_menu = self.menubar.addMenu("View")
        
        increase_size_action = QAction("Increase Size", self.main_window)
        increase_size_action.setShortcut("Ctrl+=")
        increase_size_action.triggered.connect(self.main_window.increase_font_size)
        view_menu.addAction(increase_size_action)

        decrease_size_action = QAction("Decrease Size", self.main_window)
        decrease_size_action.setShortcut("Ctrl+-")
        decrease_size_action.triggered.connect(self.main_window.decrease_font_size)
        view_menu.addAction(decrease_size_action)

    def create_theme_menu(self):
        """Creates the 'Theme' menu and its associated actions.

        This allows users to switch between different application themes
        like Dark, Light, and SimCenter.

        Example:
            >>> from qtpy.QtWidgets import QMainWindow, QApplication, QMenuBar
            >>> class MockMainWindow(QMainWindow):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self._menu_bar = QMenuBar(self)
            ...         self.setMenuBar(self._menu_bar)
            ...         # Mock method for theme switching
            ...         self.switch_theme = lambda theme_name: None
            ...     def menuBar(self):
            ...         return self._menu_bar
            ...
            >>> app = QApplication([])
            >>> main_window = MockMainWindow()
            >>> manager = ToolbarManager(main_window)
            >>> manager.create_theme_menu()
            >>> # Find the 'Theme' menu
            >>> theme_menu_action = next(a for a in manager.menubar.actions() if a.text() == "Theme")
            >>> print(theme_menu_action.text())
            Theme
            >>> app.quit()
        """
        theme_menu = self.menubar.addMenu("Theme")
        
        dark_theme_action = QAction("Dark Theme", self.main_window)
        dark_theme_action.triggered.connect(lambda: self.main_window.switch_theme("Dark"))
        theme_menu.addAction(dark_theme_action)
        
        light_theme_action = QAction("Light Theme", self.main_window)
        light_theme_action.triggered.connect(lambda: self.main_window.switch_theme("Light"))
        theme_menu.addAction(light_theme_action)

        brown_theme_action = QAction("SimCenter Theme", self.main_window)
        brown_theme_action.triggered.connect(lambda: self.main_window.switch_theme("SimCenter"))
        theme_menu.addAction(brown_theme_action)

    def create_tools_menu(self):
        """Creates the 'Tools' menu, specifically the 'DRM Generator' submenu.

        This submenu contains actions related to generating different types
        of DRM waves, such as SV Wave and Surface Wave.

        Example:
            >>> from qtpy.QtWidgets import QMainWindow, QApplication, QMenuBar
            >>> class MockMainWindow(QMainWindow):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self._menu_bar = QMenuBar(self)
            ...         self.setMenuBar(self._menu_bar)
            ...         self.drm_manager = type('DRMManager', (object,), {
            ...             'create_sv_wave': lambda: None,
            ...             'create_surface_wave': lambda: None
            ...         })()
            ...     def menuBar(self):
            ...         return self._menu_bar
            ...
            >>> app = QApplication([])
            >>> main_window = MockMainWindow()
            >>> manager = ToolbarManager(main_window)
            >>> manager.create_tools_menu()
            >>> # Find the 'Tools' menu
            >>> tools_menu_action = next(a for a in manager.menubar.actions() if a.text() == "Tools")
            >>> print(tools_menu_action.text())
            Tools
            >>> app.quit()
        """
        tools_menu = self.menubar.addMenu("Tools")
        drm_menu = tools_menu.addMenu("DRM Generator")

        sv_wave_action = QAction("SV Wave", self.main_window)
        sv_wave_action.triggered.connect(self.main_window.drm_manager.create_sv_wave)
        drm_menu.addAction(sv_wave_action)

        surface_wave_action = QAction("Surface Wave", self.main_window)
        surface_wave_action.triggered.connect(self.main_window.drm_manager.create_surface_wave)
        drm_menu.addAction(surface_wave_action)