from PySide6.QtWidgets import (QLabel, QLineEdit, QComboBox, QPushButton,
                           QGridLayout, QWidget, QDialog, QVBoxLayout,
                           QHBoxLayout, QDialogButtonBox)
import numpy as np
import pyvista as pv
from .baseGrid import BaseGridTab
from femora.utils.validator import DoubleValidator, IntValidator

class SpacingSettingsDialog(QDialog):
    """A dialog for configuring spacing methods along a specific direction.

    This dialog allows users to select from various spacing methods (Linear, Geometric,
    Log, Power, Custom) and set their parameters such as start, end, number of elements,
    and method-specific parameters like growth rate or base.

    Attributes:
        layout (QVBoxLayout): The main vertical layout of the dialog.
        method_combo (QComboBox): Dropdown to select the spacing method.
        start (QLineEdit): Input field for the starting value of the spacing.
        end (QLineEdit): Input field for the ending value of the spacing.
        num_elements (QLineEdit): Input field for the number of elements.
        param1 (QLineEdit): Input field for method-specific parameter (e.g., base, growth rate).
        param1_label (QLabel): Label for the method-specific parameter.

    Example:
        >>> from PySide6.QtWidgets import QApplication
        >>> app = QApplication([])
        >>> dialog = SpacingSettingsDialog(direction="X")
        >>> dialog.setWindowTitle("Test Spacing Settings")
        >>> # In a real application, you'd typically show with dialog.exec_()
        >>> # For testing, we just check its properties
        >>> print(dialog.method_combo.count())
        5
        >>> app.quit()
    """
    def __init__(self, parent: QWidget = None, direction: str = "X"):
        """Initializes the SpacingSettingsDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
            direction: The string identifier for the direction this dialog configures
                (e.g., "X", "Y", "Z"). Used in the window title.
        """
        super().__init__(parent)
        self.setWindowTitle(f"{direction} Direction Spacing Settings")
        self.layout = QVBoxLayout(self)

        # Method selection
        method_layout = QHBoxLayout()
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            'Linear', 'Geometric', 'Log', 'Power', 'Custom'
        ])
        method_layout.addWidget(QLabel("Method:"))
        method_layout.addWidget(self.method_combo)
        self.layout.addLayout(method_layout)

        # Parameters
        params_layout = QGridLayout()
        self.start = QLineEdit()
        self.end = QLineEdit()
        self.num_elements = QLineEdit()
        self.param1 = QLineEdit()
        self.param1_label = QLabel("Base:")

        params_layout.addWidget(QLabel("Start:"), 0, 0)
        params_layout.addWidget(self.start, 0, 1)
        params_layout.addWidget(QLabel("End:"), 1, 0)
        params_layout.addWidget(self.end, 1, 1)
        params_layout.addWidget(QLabel("Elements:"), 2, 0)
        params_layout.addWidget(self.num_elements, 2, 1)
        params_layout.addWidget(self.param1_label, 3, 0)
        params_layout.addWidget(self.param1, 3, 1)

        self.layout.addLayout(params_layout)

        # Add validators
        double_validator = DoubleValidator()
        int_validator = IntValidator()

        if double_validator:
            self.start.setValidator(double_validator)
            self.end.setValidator(double_validator)
            self.param1.setValidator(double_validator)
        if int_validator:
            self.num_elements.setValidator(int_validator)

        # Connect method change to UI update
        self.method_combo.currentTextChanged.connect(self.update_fields)

        # Add OK/Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        self.update_fields()

    def update_fields(self):
        """Updates the visibility and labels of parameter fields based on the selected spacing method.

        This method is connected to the `method_combo`'s `currentTextChanged` signal
        and dynamically adjusts the UI to show relevant input fields for the
        chosen spacing algorithm.
        """
        method = self.method_combo.currentText()
        self.param1.hide()
        self.param1_label.hide()

        if method == 'Geometric':
            self.param1.show()
            self.param1_label.show()
            self.param1_label.setText("Growth Rate:")
        elif method == 'Log':
            self.param1.show()
            self.param1_label.show()
            self.param1_label.setText("Base:")

class DirectionModule(QWidget):
    """A compact widget displaying the current spacing method and providing an edit button.

    This widget represents the spacing configuration for a single direction (e.g., X, Y, or Z)
    within a grid generation interface. It allows users to view the selected method
    and open a detailed settings dialog to modify it.

    Attributes:
        direction (str): The string identifier for the direction this module represents (e.g., "X").
        parent (QWidget): The parent widget of this module.
        method_label (QLabel): A label displaying the currently selected spacing method.
        edit_button (QPushButton): A button to open the `SpacingSettingsDialog`.
        current_settings (dict): A dictionary storing the current spacing parameters
            for this direction.

    Example:
        >>> from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
        >>> app = QApplication([])
        >>> window = QWidget()
        >>> layout = QVBoxLayout(window)
        >>> x_module = DirectionModule("X", window)
        >>> layout.addWidget(x_module)
        >>> print(x_module.direction)
        X
        >>> print(x_module.method_label.text())
        Linear
        >>> app.quit()
    """
    def __init__(self, direction: str, parent: QWidget = None):
        """Initializes the DirectionModule.

        Args:
            direction: The string identifier for the direction (e.g., "X", "Y", "Z").
            parent: The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.direction = direction
        self.parent = parent

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.method_label = QLabel("Linear")
        self.edit_button = QPushButton("Settings")
        self.edit_button.clicked.connect(self.show_settings)

        layout.addWidget(QLabel(f"{direction}:"))
        layout.addWidget(self.method_label)
        layout.addWidget(self.edit_button)

        # Store current settings
        self.current_settings = {
            'method': 'Linear',
            'start': '0',
            'end': '1',
            'num_elements': '10',
            'param1': '10'
        }

    def show_settings(self):
        """Opens the spacing settings dialog and applies changes upon acceptance.

        This method creates and displays a `SpacingSettingsDialog` pre-filled
        with the current spacing parameters for this direction. If the dialog
        is accepted, the `current_settings` of this module are updated,
        and the `method_label` is refreshed.

        Example:
            >>> from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
            >>> app = QApplication([])
            >>> window = QWidget()
            >>> layout = QVBoxLayout(window)
            >>> x_module = DirectionModule("X", window)
            >>> layout.addWidget(x_module)
            >>> # Programmatically open the settings dialog
            >>> # In a real app, this would be an interaction. We just call the method.
            >>> x_module.show_settings()
            >>> app.quit()
        """
        dialog = SpacingSettingsDialog(self.parent, self.direction)

        # Set current values
        dialog.method_combo.setCurrentText(self.current_settings['method'])
        dialog.start.setText(self.current_settings['start'])
        dialog.end.setText(self.current_settings['end'])
        dialog.num_elements.setText(self.current_settings['num_elements'])
        dialog.param1.setText(self.current_settings['param1'])

        if dialog.exec_() == QDialog.Accepted:
            # Store new settings
            self.current_settings.update({
                'method': dialog.method_combo.currentText(),
                'start': dialog.start.text(),
                'end': dialog.end.text(),
                'num_elements': dialog.num_elements.text(),
                'param1': dialog.param1.text()
            })
            self.method_label.setText(self.current_settings['method'])

    def get_spacing_array(self) -> np.ndarray | None:
        """Generates a 1D NumPy array representing the spacing for the current direction.

        The array is generated based on the `current_settings` stored in this module,
        using the selected method (Linear, Geometric, Log, Power, Custom) and its
        corresponding parameters.

        Returns:
            numpy.ndarray: A 1D NumPy array of float values representing the spacing points.
            None: If the number of elements is zero, start equals end, or if an
                internal `ValueError` occurs during numerical array generation due
                to invalid or unparseable input values from `current_settings`.

        Example:
            >>> import numpy as np
            >>> from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
            >>> app = QApplication([])
            >>> window = QWidget()
            >>> layout = QVBoxLayout(window)
            >>> x_module = DirectionModule("X", window)
            >>> # Set some example settings for linear spacing
            >>> x_module.current_settings = {
            ...     'method': 'Linear', 'start': '0', 'end': '10', 'num_elements': '5', 'param1': '10'
            ... }
            >>> spacing = x_module.get_spacing_array()
            >>> print(spacing)
            [ 0.   2.5  5.   7.5 10. ]
            >>> # Example of invalid input leading to None
            >>> x_module.current_settings['start'] = 'invalid_text'
            >>> spacing_invalid = x_module.get_spacing_array()
            >>> print(spacing_invalid is None)
            True
            >>> app.quit()
        """
        try:
            start = float(self.current_settings['start'] or 0)
            end = float(self.current_settings['end'] or 0)
            num = int(self.current_settings['num_elements'] or 0)

            if any(v == 0 for v in [num]) or start == end:
                return None

            method = self.current_settings['method']

            if method == 'Linear':
                return np.linspace(start, end, num)
            elif method == 'Geometric':
                # The 'growth' parameter from UI is not directly used by np.geomspace in this current implementation.
                # np.geomspace automatically determines the ratio based on start, end, and num.
                return np.geomspace(start, end, num)
            elif method == 'Log':
                base = float(self.current_settings['param1'] or 10)
                return np.logspace(start, end, num, base=base)
            elif method == 'Power':
                # Generates a power-law distribution
                return np.power(np.linspace(start**(1/2), end**(1/2), num), 2)
            elif method == 'Custom':
                # Currently behaves like linear spacing, can be extended for custom logic.
                return np.linspace(start, end, num)

        except ValueError:
            return None

class RectangularGridTab(BaseGridTab):
    """A tab within the main application for configuring and generating a rectangular grid.

    This tab provides user interfaces for defining the spacing along the X, Y, and Z
    directions using `DirectionModule` widgets. It allows users to define a 3D
    rectangular grid based on these directional spacings, typically as part of a
    larger grid generation workflow.

    Attributes:
        x_module (DirectionModule): The module for configuring spacing along the X-direction.
        y_module (DirectionModule): The module for configuring spacing along the Y-direction.
        z_module (DirectionModule): The module for configuring spacing along the Z-direction.

    Example:
        >>> from PySide6.QtWidgets import QApplication, QMainWindow
        >>> app = QApplication([])
        >>> # Assuming BaseGridTab is a QWidget or QFrame
        >>> class MockBaseGridTab(QWidget):
        ...     def __init__(self, parent=None):
        ...         super().__init__(parent)
        ...         self.form_layout = QGridLayout(self)
        ...     def get_data(self):
        ...         return {'base_data': True}
        >>> main_window = QMainWindow()
        >>> grid_tab = RectangularGridTab(parent=main_window)
        >>> # In a real app, this would be added to a QTabWidget.
        >>> # We can simulate its setup here.
        >>> grid_tab.setup_specific_fields()
        >>> print(grid_tab.x_module.direction)
        X
        >>> app.quit()
    """
    def setup_specific_fields(self):
        """Sets up the UI elements specific to a rectangular grid.

        This method initializes and adds `DirectionModule` widgets for X, Y, and Z
        axes to the form layout. It is called during the initialization of the tab.
        """
        # Create direction modules
        self.x_module = DirectionModule("X", self)
        self.y_module = DirectionModule("Y", self)
        self.z_module = DirectionModule("Z", self)

        # Add modules to layout
        self.form_layout.addWidget(self.x_module, 1, 0, 1, 2)
        self.form_layout.addWidget(self.y_module, 2, 0, 1, 2)
        self.form_layout.addWidget(self.z_module, 3, 0, 1, 2)

    def create_grid(self) -> pv.StructuredGrid | None:
        """Creates a PyVista `StructuredGrid` based on the configured directional spacings.

        This method retrieves the spacing arrays from the X, Y, and Z `DirectionModule`s,
        uses them to generate a 3D meshgrid, and then constructs a `pyvista.StructuredGrid`.

        Returns:
            pyvista.StructuredGrid: A 3D structured grid if all spacing arrays are valid
                and successfully generated.
            None: If any of the spacing arrays are invalid, could not be generated, or
                if an internal `ValueError` occurs during grid creation due to invalid input.

        Example:
            >>> from PySide6.QtWidgets import QApplication, QWidget
            >>> app = QApplication([])
            >>> class MockBaseGridTab(QWidget):
            ...     def __init__(self, parent=None):
            ...         super().__init__(parent)
            ...         self.form_layout = QGridLayout(self)
            ...     def get_data(self):
            ...         return {'base_data': True}
            >>> grid_tab = RectangularGridTab(parent=QWidget())
            >>> grid_tab.setup_specific_fields()
            >>> # Simulate settings (these would typically be set via UI interaction)
            >>> grid_tab.x_module.current_settings = {'method': 'Linear', 'start': '0', 'end': '1', 'num_elements': '2', 'param1': '0'}
            >>> grid_tab.y_module.current_settings = {'method': 'Linear', 'start': '0', 'end': '1', 'num_elements': '2', 'param1': '0'}
            >>> grid_tab.z_module.current_settings = {'method': 'Linear', 'start': '0', 'end': '1', 'num_elements': '2', 'param1': '0'}
            >>> grid = grid_tab.create_grid()
            >>> print(grid.dimensions)
            (2, 2, 2)
            >>> app.quit()
        """
        try:
            # Get spacing arrays for each direction
            x_spacing = self.x_module.get_spacing_array()
            y_spacing = self.y_module.get_spacing_array()
            z_spacing = self.z_module.get_spacing_array()

            if any(spacing is None for spacing in [x_spacing, y_spacing, z_spacing]):
                return None

            X, Y, Z = np.meshgrid(x_spacing, y_spacing, z_spacing, indexing='ij')
            grid = pv.StructuredGrid(X, Y, Z)
            return grid

        except ValueError:
            return None

    def get_data(self) -> dict:
        """Retrieves the current grid configuration data, including directional settings.

        This method extends the data from the base grid tab with specific
        settings for the X, Y, and Z spacing modules.

        Returns:
            dict: A dictionary containing the grid type and the current settings
                for each direction (x_settings, y_settings, z_settings).

        Example:
            >>> from PySide6.QtWidgets import QApplication, QWidget
            >>> app = QApplication([])
            >>> class MockBaseGridTab(QWidget):
            ...     def __init__(self, parent=None):
            ...         super().__init__(parent)
            ...         self.form_layout = QGridLayout(self)
            ...     def get_data(self):
            ...         return {'base_data': True}
            >>> grid_tab = RectangularGridTab(parent=QWidget())
            >>> grid_tab.setup_specific_fields()
            >>> data = grid_tab.get_data()
            >>> print(data['type'])
            rectangular
            >>> print('x_settings' in data)
            True
            >>> app.quit()
        """
        data = super().get_data()
        data.update({
            'type': 'rectangular',
            'x_settings': self.x_module.current_settings,
            'y_settings': self.y_module.current_settings,
            'z_settings': self.z_module.current_settings
        })
        return data