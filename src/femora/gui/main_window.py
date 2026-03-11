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
    """The main application window for the Femora GUI.

    This class implements the singleton pattern to ensure only one instance
    of the main window exists. It orchestrates the overall layout, including
    the left panel, plotter, and interactive console, and manages themes
    and font settings.

    Attributes:
        _instance (MainWindow): The singleton instance of the MainWindow class.
        font_size (int): The current font size used in the application.
        current_theme (str): The name of the currently active theme (e.g., "SimCenter", "Dark").
        drm_manager (DRMManager): Manages Digital Reconstruction Models.
        dark_palette (QPalette): The QPalette for the dark theme.
        light_palette (QPalette): The QPalette for the light theme.
        brown_palette (QPalette): The QPalette for the brown theme.
        simcenter_palette (QPalette): The QPalette for the SimCenter theme.
        meshMaker (MeshMaker): The singleton instance of the MeshMaker.
        main_splitter (QSplitter): The main horizontal splitter dividing the UI.
        left_panel (LeftPanel): The left-hand panel containing various controls.
        right_panel (QSplitter): The vertical splitter on the right, holding plotter and console.
        plotter (pyvistaqt.BackgroundPlotter): The 3D plotting widget for visualization.
        plotter_widget (QWidget): The QWidget wrapper for the PyVistaQt plotter.
        console (InteractiveConsole): The interactive Python console.
        toolbar_manager (ToolbarManager): Manages the application's toolbar.

    Example:
        >>> from femora.gui.main_window import MainWindow
        >>> app_window = MainWindow()
        >>> app_window.setWindowTitle("Femora New Title")
        >>> print(app_window.windowTitle())
        Femora New Title
    """
    _instance = None  # Class variable to store the single instance

    def __new__(cls, *args, **kwargs):
        """Creates a new instance of MainWindow, enforcing the singleton pattern.

        This method ensures that only one instance of the `MainWindow` class
        can be created throughout the application's lifecycle. Subsequent
        calls to the constructor will return the existing instance.
        """
        if not cls._instance:
            cls._instance = super(MainWindow, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Retrieves the singleton instance of MainWindow.

        Returns:
            MainWindow: The single instance of the MainWindow class.

        Raises:
            RuntimeError: If the instance has not been created yet by
                calling the constructor first.

        Example:
            >>> from femora.gui.main_window import MainWindow
            >>> # This will create the instance if it doesn't exist
            >>> main_window_instance = MainWindow()
            >>> # This will return the same existing instance
            >>> retrieved_instance = MainWindow.get_instance()
            >>> assert main_window_instance is retrieved_instance
        """
        if cls._instance is None:
            raise RuntimeError("MainWindow instance has not been created yet. "
                             "Create an instance first before calling get_instance().")
        return cls._instance

    def __init__(self):
        """Initializes the MainWindow.

        This constructor sets up the core application components, including
        the theme, DRM manager, MeshMaker, and the UI elements. It ensures
        that initialization only occurs once due to the singleton pattern.

        Args:
            None: This constructor takes no direct arguments as it's part
                of a singleton pattern and relies on internal state setup.
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
        """Initializes the user interface components and layout.

        Sets up the window title, size, main layout, panels, plotter,
        console, and configures splitters. It also applies the current
        theme and shows the window maximized.

        Example:
            >>> from femora.gui.main_window import MainWindow
            >>> app_window = MainWindow() # Automatically calls init_ui if not already initialized
            >>> print(app_window.windowTitle())
            Femora
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
        """Retrieves the PyVistaQt plotter instance from the main window.

        This class method provides convenient access to the 3D visualization
        plotter used throughout the application.

        Returns:
            pyvistaqt.BackgroundPlotter: The plotter instance.

        Raises:
            RuntimeError: If the MainWindow instance or the plotter has not
                been created or initialized yet.

        Example:
            >>> from femora.gui.main_window import MainWindow
            >>> import pyvista as pv
            >>> main_window = MainWindow() # Ensure instance is created and UI is initialized
            >>> plotter = MainWindow.get_plotter()
            >>> # You can now interact with the plotter, e.g.,
            >>> # plotter.add_mesh(pv.Sphere())
            >>> assert isinstance(plotter, pyvistaqt.BackgroundPlotter)
        """
        instance = cls.get_instance()
        if not hasattr(instance, 'plotter'):
            raise RuntimeError("Plotter has not been initialized yet.")
        return instance.plotter


    def setup_main_layout(self):
        """Sets up the main widget and horizontal splitter for the application.

        This method creates the central widget, applies a horizontal box layout,
        and initializes the main splitter that will divide the left and right
        panels of the GUI.
        """
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)

    def setup_panels(self):
        """Configures and adds the left and right panels to the main splitter.

        This method initializes the `LeftPanel` and a vertical splitter for
        the right side, then adds them to the `main_splitter`.
        """
        self.left_panel = LeftPanel()
        self.right_panel = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)

    def setup_plotter(self):
        """Initializes and configures the PyVistaQt 3D plotter.

        Creates a `pyvistaqt.BackgroundPlotter`, wraps it in a QWidget,
        sets its minimum height, and adds it to the right-hand panel.
        It also registers this plotter with the `PlotterManager`.
        """
        self.plotter = pyvistaqt.BackgroundPlotter(show=False)
        self.plotter_widget = self.plotter.app_window
        self.plotter_widget.setMinimumHeight(400)
        self.right_panel.addWidget(self.plotter_widget)

        # Set the global plotter
        PlotterManager.set_plotter(self.plotter)

    def setup_console(self):
        """Initializes the interactive Python console.

        Creates an `InteractiveConsole` instance, sets its minimum height,
        and adds it to the right-hand panel. It also pushes essential
        objects like the plotter, PyVista, and MeshMaker into the console's
        namespace for direct interaction.
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

        Configures the `main_splitter` to allocate space between the left
        and right panels, and the `right_panel` splitter to allocate space
        between the plotter and the console.
        """
        self.main_splitter.setSizes([300, 1100])  # Left panel : Right panel ratio
        self.right_panel.setSizes([600, 200])     # Plotter : Console ratio


    def update_font_and_resize(self):
        """Updates the application's font and reapplies the current theme.

        This method is typically called after a font size change to ensure
        the UI elements and console reflect the new font settings and the
        theme is consistently applied.
        """
        font = QFont('Segoe UI', self.font_size)
        QApplication.setFont(font)
        self.apply_theme()
        self.update()


    def create_palettes(self):
        """Initializes various QPalette objects for different application themes.

        Creates distinct color palettes for "Dark", "Light", "Brown", and
        "SimCenter" themes, defining colors for various UI elements like
        windows, text, buttons, and highlights. These palettes are then
        used by `apply_theme` and `switch_theme`.

        Example:
            >>> from femora.gui.main_window import MainWindow
            >>> app_window = MainWindow() # Palettes are created during init
            >>> assert isinstance(app_window.dark_palette, QPalette)
            >>> assert isinstance(app_window.simcenter_palette, QPalette)
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
        """Switches the application's visual theme based on the provided name.

        Applies the appropriate QPalette, console style, and plotter background
        color corresponding to the specified theme. Ensures the 'Fusion'
        style is set for QApplication.

        Args:
            theme: The name of the theme to apply. Valid options are
                "Dark", "SimCenter", "Brown", or "Light".

        Example:
            >>> from femora.gui.main_window import MainWindow
            >>> app_window = MainWindow()
            >>> app_window.switch_theme("Dark")
            >>> assert app_window.current_theme == "Dark"
            >>> # The application's palette and plotter background would change
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
        """Applies the currently selected theme to the application.

        This method sets the QApplication's style to 'Fusion', applies the
        appropriate QPalette, console styling, and plotter background color
        based on `self.current_theme`. It also updates button stylesheets
        specifically for the "SimCenter" theme.

        Example:
            >>> from femora.gui.main_window import MainWindow
            >>> app_window = MainWindow()
            >>> app_window.current_theme = "SimCenter"
            >>> app_window.apply_theme()
            >>> # The UI elements now reflect the SimCenter theme,
            >>> # including specific button styling.
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
        """Increases the application's font size by one point.

        Updates `self.font_size`, informs the console to adjust its font size,
        and triggers a full UI font and theme refresh.
        """
        self.font_size += 1
        self.console.change_font_size(1)
        self.update_font_and_resize()
    
    def decrease_font_size(self):
        """Decreases the application's font size by one point, if above minimum.

        If `self.font_size` is greater than 6, it decreases the font size,
        informs the console to adjust, and triggers a full UI font and theme refresh.
        """
        if self.font_size > 6:
            self.font_size -= 1
            self.console.change_font_size(-1)
            self.update_font_and_resize()