from qtpy.QtGui import QAction, QPalette, QColor, QFont
from qtpy.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter, QStyleFactory)
from qtpy.QtCore import Qt

import pyvistaqt
import pyvista as pv
from femora.components.MeshMaker import MeshMaker
from femora.gui.left_panel import LeftPanel
from femora.gui.console import InteractiveConsole
from femora.components.drm_creators.drm_manager import DRMManager
from femora.gui.plotter import PlotterManager
from femora.gui.toolbar import ToolbarManager
from femora.gui.progress_gui import ProgressGUI


class MainWindow(QMainWindow):
    """The main application window for Femora, implementing a singleton pattern.

    This class provides the primary user interface for the Femora application,
    including the main layout, panels, 3D plotter, and an interactive console.
    It ensures that only one instance of the main window exists at any given time.

    Attributes:
        _instance (MainWindow): The singleton instance of the MainWindow.
        font_size (int): The current font size used in the application.
        current_theme (str): The name of the currently active theme ("SimCenter", "Dark", "Light", "Brown").
        drm_manager (DRMManager): Manages Digital Reconstruction of Morphology components.
        meshMaker (MeshMaker): The singleton instance of the MeshMaker component.
        plotter (pyvistaqt.BackgroundPlotter): The 3D visualization plotter for Femora.
        plotter_widget (QWidget): The Qt widget embedding the PyVista plotter.
        console (InteractiveConsole): The interactive Python console.
        left_panel (LeftPanel): The left-hand panel containing various UI controls.
        right_panel (QSplitter): The right-hand splitter containing the plotter and console.
        main_splitter (QSplitter): The main horizontal splitter separating left and right panels.
        dark_palette (QPalette): The color palette for the "Dark" theme.
        light_palette (QPalette): The color palette for the "Light" theme.
        brown_palette (QPalette): The color palette for the "Brown" theme.
        simcenter_palette (QPalette): The color palette for the "SimCenter" theme.

    Example:
        >>> import sys
        >>> from qtpy.QtWidgets import QApplication
        >>> app = QApplication(sys.argv)
        >>> main_window = MainWindow()
        >>> main_window.show()
        >>> # To retrieve the same instance later:
        >>> another_window = MainWindow.get_instance()
        >>> print(main_window is another_window)
        True
        >>> app.quit() # Clean up the QApplication
    """
    _instance = None  # Class variable to store the single instance

    def __new__(cls, *args, **kwargs):
        """Implements the singleton pattern for MainWindow.

        Ensures that only a single instance of the MainWindow class can be created.
        Subsequent calls to the constructor will return the existing instance.
        """
        if not cls._instance:
            cls._instance = super(MainWindow, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Returns the singleton instance of MainWindow.

        This class method allows access to the unique MainWindow instance
        without needing to call its constructor directly.

        Returns:
            MainWindow: The single instance of the MainWindow class.

        Raises:
            RuntimeError: If the MainWindow instance has not been created yet
                by calling the constructor at least once.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> main_window = MainWindow()
            >>> retrieved_window = MainWindow.get_instance()
            >>> print(main_window is retrieved_window)
            True
            >>> try:
            ...     # Simulate calling get_instance before creation
            ...     temp_instance = MainWindow._instance # Store original
            ...     MainWindow._instance = None # Temporarily clear
            ...     MainWindow.get_instance() # This should raise an error
            ... except RuntimeError as e:
            ...     print(e)
            ... finally:
            ...     MainWindow._instance = temp_instance # Restore original
            MainWindow instance has not been created yet...
            >>> app.quit() # Clean up the QApplication
        """
        if cls._instance is None:
            raise RuntimeError("MainWindow instance has not been created yet. "
                             "Create an instance first before calling get_instance().")
        return cls._instance

    def __init__(self):
        """Initializes the MainWindow instance.

        This constructor sets up the initial state of the main window,
        including default font size, theme, and managers. It also ensures
        that the QApplication is running.

        If an instance of MainWindow already exists, this method will
        return without re-initializing the UI components, upholding
        the singleton pattern's initialization behavior.
        """
        # Ensure parent class constructor is called first
        super().__init__()

        # Check if already initialized to prevent re-initialization
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # Ensure Qt event loop is running (if necessary)
        app = QApplication.instance()
        if not app:
            app = QApplication([])

        self.font_size = 10
        self.current_theme = "SimCenter"
        self.drm_manager = DRMManager(self)
        self.create_palettes()
        self.meshMaker = MeshMaker.get_instance()
        self.init_ui()

    def init_ui(self):
        """Initializes the user interface components and layout for the main window.

        This method sets up the window title, size, main layout, various panels
        (left panel, plotter, console), splitters, and the toolbar. It also applies
        the default theme and shows the window maximized.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> main_window = MainWindow()
            >>> main_window.init_ui() # Typically called automatically by __init__
            >>> # The UI would be visible and arranged.
            >>> app.quit() # Clean up the QApplication
        """
        self.setWindowTitle("Femora")
        self.resize(1400, 800)
        
        self.setup_main_layout()
        self.setup_panels()
        self.setup_plotter()
        self.setup_console()
        self.setup_splitters()
        self.toolbar_manager = ToolbarManager(self)
        self.apply_theme()
        ProgressGUI.show("Progress")
        self.showMaximized()

    @classmethod
    def get_plotter(cls):
        """Returns the PyVistaQt plotter instance associated with the MainWindow.

        This provides a convenient way to access the 3D visualization plotter
        from anywhere in the application.

        Returns:
            pyvistaqt.BackgroundPlotter: The plotter instance used for 3D visualization.

        Raises:
            RuntimeError: If the MainWindow instance has not been created yet
                or if the plotter itself has not been initialized within the MainWindow.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> main_window = MainWindow()
            >>> plotter = MainWindow.get_plotter()
            >>> # Now 'plotter' can be used for PyVista operations, e.g.:
            >>> # plotter.add_mesh(pyvista.Sphere())
            >>> print(isinstance(plotter, pyvistaqt.BackgroundPlotter))
            True
            >>> app.quit() # Clean up the QApplication
        """
        instance = cls.get_instance()
        if not hasattr(instance, 'plotter'):
            raise RuntimeError("Plotter has not been initialized yet.")
        return instance.plotter


    def setup_main_layout(self):
        """Sets up the central widget and the main horizontal splitter.

        This creates the fundamental structure for arranging the main UI
        elements into left and right sections.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> main_window.setup_main_layout()
            >>> # The main_splitter attribute would now be initialized.
            >>> print(isinstance(main_window.centralWidget(), QWidget))
            True
            >>> app.quit() # Clean up the QApplication
        """
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)

    def setup_panels(self):
        """Initializes and arranges the left and right panels within the main splitter.

        The left panel (`LeftPanel`) is added to the left side, and a vertical
        splitter (`right_panel`) is created for the right side, which will
        later contain the plotter and console.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> main_window.setup_main_layout()
            >>> main_window.setup_panels()
            >>> # main_window.left_panel and main_window.right_panel would be initialized.
            >>> print(isinstance(main_window.left_panel, LeftPanel))
            True
            >>> app.quit() # Clean up the QApplication
        """
        self.left_panel = LeftPanel()
        self.right_panel = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)

    def setup_plotter(self):
        """Initializes the PyVistaQt plotter and integrates it into the UI.

        A `pyvistaqt.BackgroundPlotter` is created, its widget is added to
        the right panel, and the plotter instance is registered with the
        `PlotterManager`.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> main_window.setup_main_layout()
            >>> main_window.setup_panels()
            >>> main_window.setup_plotter()
            >>> # The plotter attribute would be initialized and added to the UI.
            >>> print(isinstance(main_window.plotter, pyvistaqt.BackgroundPlotter))
            True
            >>> app.quit() # Clean up the QApplication
        """
        self.plotter = pyvistaqt.BackgroundPlotter(show=False)
        self.plotter_widget = self.plotter.app_window
        self.plotter_widget.setMinimumHeight(400)
        self.right_panel.addWidget(self.plotter_widget)

        # Set the global plotter
        PlotterManager.set_plotter(self.plotter)

    def setup_console(self):
        """Initializes the interactive console and integrates it into the UI.

        An `InteractiveConsole` is created and added to the right panel,
        below the plotter. It also makes key objects like the plotter and
        meshMaker available in the console's namespace for interactive use.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> main_window.setup_main_layout()
            >>> main_window.setup_panels()
            >>> main_window.setup_plotter()
            >>> main_window.setup_console()
            >>> # The console attribute would be initialized and added to the UI.
            >>> print(isinstance(main_window.console, InteractiveConsole))
            True
            >>> app.quit() # Clean up the QApplication
        """
        self.console = InteractiveConsole()
        self.console.setMinimumHeight(200)
        self.right_panel.addWidget(self.console)
        
        # Make plotter available in console namespace
        self.console.kernel_manager.kernel.shell.push({
            'plotter': self.plotter,
            'pv': pv,
            'meshMaker': self.meshMaker,
        })

    def setup_splitters(self):
        """Sets the initial sizes and proportions for the main and right splitters.

        This ensures a balanced layout of the main UI components,
        specifically the left panel, the plotter, and the console.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> main_window.setup_main_layout()
            >>> main_window.setup_panels()
            >>> main_window.setup_plotter()
            >>> main_window.setup_console()
            >>> main_window.setup_splitters()
            >>> # Splitter sizes would be applied.
            >>> print(main_window.main_splitter.sizes()[0] == 300)
            True
            >>> app.quit() # Clean up the QApplication
        """
        self.main_splitter.setSizes([300, 1100])  # Left panel : Right panel ratio
        self.right_panel.setSizes([600, 200])     # Plotter : Console ratio


    def update_font_and_resize(self):
        """Updates the application's global font and triggers a UI resize and theme reapplication.

        This method is called when the font size changes to ensure all UI elements
        are rendered with the new font settings and the theme is reapplied
        to maintain visual consistency.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> original_font_size = main_window.font_size
            >>> main_window.font_size = 12
            >>> main_window.update_font_and_resize()
            >>> # The application font and theme would be updated.
            >>> print(QApplication.font().pointSize() >= original_font_size)
            True
            >>> app.quit() # Clean up the QApplication
        """
        font = QFont('Segoe UI', self.font_size)
        QApplication.setFont(font)
        self.apply_theme()
        self.update()


    def create_palettes(self):
        """Creates and configures various color palettes for different application themes.

        This method initializes `QPalette` objects for "Dark", "Light", "Brown",
        and "SimCenter" themes, defining their respective color schemes for
        various UI elements. These palettes are stored as attributes of the
        MainWindow instance.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> main_window.create_palettes()
            >>> # Palettes like main_window.dark_palette would be initialized.
            >>> print(isinstance(main_window.dark_palette, QPalette))
            True
            >>> app.quit() # Clean up the QApplication
        """
        # Dark Palette
        self.dark_palette = QPalette()
        self.dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.WindowText, Qt.white)
        self.dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        self.dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        self.dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        self.dark_palette.setColor(QPalette.Text, Qt.white)
        self.dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ButtonText, Qt.white)
        self.dark_palette.setColor(QPalette.BrightText, Qt.red)
        self.dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        self.dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        self.dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.dark_palette.setColor(QPalette.PlaceholderText, QColor(160, 160, 160))

        # Light Palette (system default)
        self.light_palette = QApplication.style().standardPalette()
        # change background color to white
        self.light_palette.setColor(QPalette.Window, QColor(237, 241, 247))
        self.light_palette.setColor(QPalette.WindowText, Qt.black)
        self.light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        self.light_palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
        self.light_palette.setColor(QPalette.ToolTipBase, Qt.black)
        self.light_palette.setColor(QPalette.ToolTipText, Qt.white)
        self.light_palette.setColor(QPalette.Text, Qt.black)
        self.light_palette.setColor(QPalette.Button, QColor(214, 204, 227))
        self.light_palette.setColor(QPalette.ButtonText, Qt.black)
        self.light_palette.setColor(QPalette.BrightText, Qt.red)
        self.light_palette.setColor(QPalette.Link, QColor(0, 122, 204))
        self.light_palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
        self.light_palette.setColor(QPalette.HighlightedText, Qt.white)
        self.light_palette.setColor(QPalette.PlaceholderText, QColor(128, 128, 128))

        self.brown_palette = QApplication.style().standardPalette()
        self.brown_palette.setColor(QPalette.Window, QColor(255, 244, 242))
        self.brown_palette.setColor(QPalette.Button, QColor(237, 213, 217))

        # SimCenter Palette (based on QSS colors)
        self.simcenter_palette = QPalette()
        self.simcenter_palette.setColor(QPalette.Window, QColor(240, 240, 240))  # #F0F0F0
        self.simcenter_palette.setColor(QPalette.WindowText, QColor(66, 66, 66))  # #424242
        self.simcenter_palette.setColor(QPalette.Base, QColor(255, 255, 255))  # white
        self.simcenter_palette.setColor(QPalette.AlternateBase, QColor(250, 250, 250))  # #FAFAFA
        self.simcenter_palette.setColor(QPalette.ToolTipBase, QColor(38, 50, 56))  # #263238
        self.simcenter_palette.setColor(QPalette.ToolTipText, Qt.white)
        self.simcenter_palette.setColor(QPalette.Text, QColor(66, 66, 66))  # #424242
        self.simcenter_palette.setColor(QPalette.Button, QColor(176, 190, 197))  # #B0BEC5
        self.simcenter_palette.setColor(QPalette.ButtonText, QColor(38, 50, 56))  # #263238
        self.simcenter_palette.setColor(QPalette.BrightText, QColor(244, 67, 54))  # #F44336
        self.simcenter_palette.setColor(QPalette.Link, QColor(25, 118, 210))  # #1976D2
        self.simcenter_palette.setColor(QPalette.Highlight, QColor(100, 181, 246))  # #64B5F6
        self.simcenter_palette.setColor(QPalette.HighlightedText, QColor(25, 118, 210))  # #1976D2
        self.simcenter_palette.setColor(QPalette.PlaceholderText, QColor(158, 158, 158))  # #9E9E9E

        

    def switch_theme(self, theme: str):
        """Switches the application's visual theme.

        Applies the specified theme by setting the global QApplication palette,
        adjusting console styles, and changing the PyVista plotter background.
        The `Fusion` style is explicitly applied to ensure consistent rendering.

        Args:
            theme: The name of the theme to apply. Valid options are "Dark",
                "SimCenter", "Light", or "Brown".

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> main_window.create_palettes() # Ensure palettes are created
            >>> main_window.switch_theme("Dark")
            >>> print(main_window.current_theme)
            Dark
            >>> main_window.switch_theme("SimCenter")
            >>> print(main_window.current_theme)
            SimCenter
            >>> app.quit() # Clean up the QApplication
        """
        if theme == "Dark":
            QApplication.setPalette(self.dark_palette)
            self.console.set_default_style(colors='linux')
            self.console.syntax_style = 'monokai'
            self.plotter.set_background('#52576eff')
            self.current_theme = "Dark"
        elif theme == "SimCenter":
            QApplication.setPalette(self.simcenter_palette)
            self.console.set_default_style(colors='lightbg')
            self.console.syntax_style = 'default'
            self.plotter.set_background('white')
            self.current_theme = "SimCenter"
        else:
            if theme == "Brown":
                QApplication.setPalette(self.brown_palette)
            if theme == "Light":
                QApplication.setPalette(self.light_palette)
            self.console.set_default_style(colors='lightbg')
            self.console.syntax_style = 'default'
            self.plotter.set_background('white')
            self.current_theme = "Light"
        
        # Ensure Fusion style is applied
        QApplication.setStyle(QStyleFactory.create('Fusion'))



    def apply_theme(self):
        """Applies the currently selected theme to the application UI.

        This method sets the QApplication style to `Fusion`, applies the
        appropriate `QPalette` based on `self.current_theme`, adjusts the
        console's styling, and sets the PyVista plotter's background color.
        It also applies specific QSS (Qt Style Sheet) rules for the "SimCenter"
        theme and updates the console font.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> main_window.create_palettes()
            >>> main_window.current_theme = "Dark"
            >>> main_window.apply_theme()
            >>> # The UI would reflect the "Dark" theme settings.
            >>> print(main_window.current_theme)
            Dark
            >>> app.quit() # Clean up the QApplication
        """
        # Use Fusion style
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        # Apply the current theme's palette
        if self.current_theme == "Dark":
            QApplication.setPalette(self.dark_palette)
            self.console.set_default_style(colors='linux')
            self.console.syntax_style = 'monokai'
            self.plotter.set_background('#52576eff')
        elif self.current_theme == "SimCenter":
            QApplication.setPalette(self.simcenter_palette)
            self.console.set_default_style(colors='lightbg')
            self.console.syntax_style = 'default'
            self.plotter.set_background('white')
            QApplication.instance().setStyleSheet("""
                QPushButton {
                    background-color: #64B5F6;
                    color: white;
                    border-radius: 6px;
                    padding: 6px 12px;         /* vertical and horizontal padding */
                    min-height: 28px;          /* prevent buttons from collapsing */
                }
                QPushButton:hover {
                    background-color: #42A5F5;
                }
                QPushButton:pressed {
                    background-color: #1E88E5;
                }
            """)
        else:
            QApplication.setPalette(self.light_palette)
            self.plotter.set_background('#52576eff')
            # self.console.set_default_style(colors='lightbg')
            # self.console.syntax_style = 'default'
            # self.plotter.set_background('white')
        
        # Update font
        console_font = QFont('Menlo', self.font_size)
        self.console.font = console_font
    
    def increase_font_size(self):
        """Increases the global font size of the application.

        Increments `self.font_size` by 1, updates the console's font size,
        and triggers a UI refresh to apply the changes.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> original_size = main_window.font_size
            >>> main_window.increase_font_size()
            >>> print(main_window.font_size == original_size + 1)
            True
            >>> app.quit() # Clean up the QApplication
        """
        self.font_size += 1
        self.console.change_font_size(1)
        self.update_font_and_resize()
    
    def decrease_font_size(self):
        """Decreases the global font size of the application.

        Decrements `self.font_size` by 1, if it's greater than 6,
        updates the console's font size, and triggers a UI refresh
        to apply the changes.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication([])
            >>> main_window = MainWindow()
            >>> original_size = main_window.font_size
            >>> # Set a font size above 6 to test decrement
            >>> main_window.font_size = 10
            >>> main_window.decrease_font_size()
            >>> print(main_window.font_size == 9)
            True
            >>> # Test when font_size is 6 or less
            >>> main_window.font_size = 6
            >>> main_window.decrease_font_size()
            >>> print(main_window.font_size == 6)
            True
            >>> app.quit() # Clean up the QApplication
        """
        if self.font_size > 6:
            self.font_size -= 1
            self.console.change_font_size(-1)
            self.update_font_and_resize()