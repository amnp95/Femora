from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QSpinBox, QLabel, QDialogButtonBox, QColorDialog,
    QComboBox, QPushButton, QGridLayout, QMessageBox, QProgressDialog, QApplication,
    QSlider, QDialog, QDoubleSpinBox, QCheckBox, QFileDialog, QHBoxLayout, QLineEdit, 
    QRadioButton, QButtonGroup
)
from qtpy.QtCore import Qt
from femora.gui.plotter import PlotterManager
from femora.components.MeshMaker import MeshMaker
from qtpy.QtWidgets import QSizePolicy
from femora.components.Pattern.patternBase import H5DRMPattern, PatternManager
import numpy as np
import os
import csv
import tempfile
from femora.gui.tapis_integration import TapisWorker, TACCFileBrowserDialog
from femora.components.DRM.DRM import DRM

class DRMGUI(QWidget):
    """A GUI widget for managing and visualizing H5DRM load patterns and DRM points.

    This class provides an interface to load H5DRM files, apply transformations,
    and visualize DRM points, either from the H5DRM file or a separate CSV file.
    It integrates with the Femora MeshMaker and PatternManager.

    Attributes:
        meshmaker (MeshMaker): An instance of the MeshMaker for mesh-related operations.
        pattern_manager (PatternManager): Manages the creation and storage of patterns.
        h5drmFilePath (QLineEdit): Displays the path to the selected H5DRM file.
        factorSpinBox (QDoubleSpinBox): Controls the scale factor for the H5DRM pattern.
        coordScaleSpinBox (QDoubleSpinBox): Controls the coordinate scale for DRM points.
        distToleranceSpinBox (QDoubleSpinBox): Controls the distance tolerance for matching DRM points.
        matrix_inputs (list[QDoubleSpinBox]): List of input fields for the 3x3 transformation matrix.
        origin_inputs (list[QDoubleSpinBox]): List of input fields for the XYZ origin coordinates.
        file_source (str): Indicates if the H5DRM file is "local" or "remote".
        csv_file_source (str): Indicates if the CSV file is "local" or "remote".
        remote_connection_info (dict | None): Stores connection details for remote file access.
        showPointsCheckbox (QCheckBox): Controls visibility of DRM points visualization.
        pointsSourceGroup (QButtonGroup): Groups radio buttons for H5DRM or CSV point source.
        h5drmFileRadio (QRadioButton): Selects H5DRM file as the source for points.
        csvFileRadio (QRadioButton): Selects CSV file as the source for points.
        csvFilePath (QLineEdit): Displays the path to the selected CSV file for points.
        browseCsvButton (QPushButton): Button to browse for local CSV files.
        browseCsvRemoteButton (QPushButton): Button to browse for remote CSV files.
        pointSizeSpinBox (QDoubleSpinBox): Controls the size of visualized DRM points.
        pointColorButton (QPushButton): Button to choose the color for DRM points.
        pointColor (tuple[float, float, float]): The RGB color tuple for DRM points (0-1 range).
        showDRMPointsButton (QPushButton): Button to trigger DRM points visualization.
        togglePointsVisibilityButton (QPushButton): Button to toggle visibility of DRM points.
        removePointsButton (QPushButton): Button to remove DRM points from the visualization.
        addH5DRMButton (QPushButton): Button to add the H5DRM pattern to the model.
        transform_matrix (list[float]): The 3x3 transformation matrix stored as a flattened list.
        origin (list[float]): The XYZ origin translation vector.
        drm_points_actor (vtkActor | None): The VTK actor representing the visualized DRM points.
        points_visible (bool): Current visibility state of the DRM points actor.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> gui = DRMGUI()
        >>> gui.show()
        >>> # Basic initialization and display.
        >>> # Interaction would happen through the GUI elements.
    """
    def __init__(self, parent=None):
        """Initializes the DRMGUI.

        Args:
            parent (QWidget, optional): The parent widget for this GUI component.
                Defaults to None.
        """
        super().__init__(parent)

        self.meshmaker = MeshMaker.get_instance()
        self.pattern_manager = PatternManager()
        
        # Set size policy for the main widget
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # make the alignment of the layout to be top left
        layout.setAlignment(Qt.AlignTop)
        
        # Add H5DRM Pattern box FIRST
        h5drmPatternBox = QGroupBox("H5DRM Load Pattern")
        h5drmPatternBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        h5drmLayout = QGridLayout(h5drmPatternBox)
        
        # H5DRM File path
        h5drmLayout.addWidget(QLabel("H5DRM File"), 0, 0)
        self.h5drmFilePath = QLineEdit()
        self.h5drmFilePath.setReadOnly(True)
        self.h5drmFilePath.setPlaceholderText("Select H5DRM file...")
        
        fileLayout = QHBoxLayout()
        fileLayout.addWidget(self.h5drmFilePath)
        
        self.browseButton = QPushButton("Browse Local")
        self.browseButton.clicked.connect(self.browse_h5drm_file)
        fileLayout.addWidget(self.browseButton)
                
        # Add remote browse button
        self.remoteBrowseButton = QPushButton("Browse TACC")
        self.remoteBrowseButton.clicked.connect(self.browse_h5drm_remote)
        fileLayout.addWidget(self.remoteBrowseButton)
        
        h5drmLayout.addLayout(fileLayout, 0, 1)
        
        # Scale factor
        h5drmLayout.addWidget(QLabel("Scale Factor"), 1, 0)
        self.factorSpinBox = QDoubleSpinBox()
        self.factorSpinBox.setMinimum(0.01)
        self.factorSpinBox.setMaximum(10.0)
        self.factorSpinBox.setSingleStep(0.1)
        self.factorSpinBox.setValue(1.0)
        h5drmLayout.addWidget(self.factorSpinBox, 1, 1)
        
        # Coordinate scale
        h5drmLayout.addWidget(QLabel("Coordinate Scale"), 2, 0)
        self.coordScaleSpinBox = QDoubleSpinBox()
        self.coordScaleSpinBox.setMinimum(0.001)
        self.coordScaleSpinBox.setMaximum(1000.0)
        self.coordScaleSpinBox.setSingleStep(0.1)
        self.coordScaleSpinBox.setValue(1.0)
        h5drmLayout.addWidget(self.coordScaleSpinBox, 2, 1)
        
        # Distance tolerance
        h5drmLayout.addWidget(QLabel("Distance Tolerance"), 3, 0)
        self.distToleranceSpinBox = QDoubleSpinBox()
        self.distToleranceSpinBox.setMinimum(0.0001)
        self.distToleranceSpinBox.setMaximum(1.0)
        self.distToleranceSpinBox.setSingleStep(0.001)
        self.distToleranceSpinBox.setValue(0.001)
        self.distToleranceSpinBox.setDecimals(4)
        h5drmLayout.addWidget(self.distToleranceSpinBox, 3, 1)
        
        # Add transformation matrix group
        transform_group = QGroupBox("Transformation Matrix")
        transform_layout = QGridLayout()
        
        # Create matrix input fields
        self.matrix_inputs = []
        for i in range(3):
            for j in range(3):
                idx = i * 3 + j
                transform_layout.addWidget(QLabel(f"M[{i+1},{j+1}]"), i, j*2)
                input_field = QDoubleSpinBox()
                input_field.setRange(-1000, 1000)
                input_field.setDecimals(6)
                input_field.setSingleStep(0.1)
                transform_layout.addWidget(input_field, i, j*2+1)
                self.matrix_inputs.append(input_field)
        self.file_source = "local"  # "local" or "remote"
        self.csv_file_source = "local"  # "local" or "remote"
        self.remote_connection_info = None
        
        # Add identity matrix button
        identity_btn = QPushButton("Set Identity Matrix")
        identity_btn.clicked.connect(self.set_identity_matrix)
        transform_layout.addWidget(identity_btn, 3, 0, 1, 6)
        
        transform_group.setLayout(transform_layout)
        h5drmLayout.addWidget(transform_group, 4, 0, 1, 2)
        
        # Add origin group
        origin_group = QGroupBox("Origin Location")
        origin_layout = QGridLayout()
        
        # Create origin input fields
        self.origin_inputs = []
        for i, label in enumerate(["X:", "Y:", "Z:"]):
            origin_layout.addWidget(QLabel(label), 0, i*2)
            input_field = QDoubleSpinBox()
            input_field.setRange(-10000, 10000)
            input_field.setDecimals(6)
            input_field.setSingleStep(0.1)
            origin_layout.addWidget(input_field, 0, i*2+1)
            self.origin_inputs.append(input_field)
        
        # Add buttons for origin control
        origin_buttons_layout = QHBoxLayout()
        
        # Reset origin button
        reset_origin_btn = QPushButton("Reset Origin")
        reset_origin_btn.clicked.connect(self.reset_origin)
        origin_buttons_layout.addWidget(reset_origin_btn)
        
        # Auto set from mesh button - only affects origin coordinates
        auto_set_origin_btn = QPushButton("Auto Set Origin from Mesh")
        auto_set_origin_btn.clicked.connect(self.auto_set_origin_from_mesh)
        auto_set_origin_btn.setToolTip("Sets origin coordinates based on mesh center (preserves transform matrix)")
        origin_buttons_layout.addWidget(auto_set_origin_btn)
        
        origin_layout.addLayout(origin_buttons_layout, 1, 0, 1, 6)
        
        origin_group.setLayout(origin_layout)
        h5drmLayout.addWidget(origin_group, 5, 0, 1, 2)
        
        # DRM Points Visualization
        pointsGroup = QGroupBox("DRM Points Visualization")
        pointsLayout = QGridLayout(pointsGroup)
        
        # Radio buttons for point source
        self.showPointsCheckbox = QCheckBox("Show DRM points in visualization")
        pointsLayout.addWidget(self.showPointsCheckbox, 0, 0, 1, 2)
        
        sourceGroup = QGroupBox("Points Source")
        sourceLayout = QVBoxLayout(sourceGroup)
        
        self.pointsSourceGroup = QButtonGroup()
        self.h5drmFileRadio = QRadioButton("From H5DRM file (Local only)")
        self.h5drmFileRadio.setChecked(True)
        self.csvFileRadio = QRadioButton("From CSV file")
        
        self.pointsSourceGroup.addButton(self.h5drmFileRadio)
        self.pointsSourceGroup.addButton(self.csvFileRadio)
        
        sourceLayout.addWidget(self.h5drmFileRadio)
        sourceLayout.addWidget(self.csvFileRadio)
        
        # CSV file selection
        csvFileLayout = QHBoxLayout()
        self.csvFilePath = QLineEdit()
        self.csvFilePath.setReadOnly(True)
        self.csvFilePath.setEnabled(False)
        self.csvFilePath.setPlaceholderText("Select CSV file with DRM points...")
        # Ensure placeholder text is visible in dark theme
        
        # Add the missing button
        self.browseCsvButton = QPushButton("Browse Local")
        self.browseCsvButton.setEnabled(False)  
        self.browseCsvButton.clicked.connect(self.browse_csv_file)

        self.browseCsvRemoteButton = QPushButton("Browse TACC")
        self.browseCsvRemoteButton.setEnabled(False)
        self.browseCsvRemoteButton.clicked.connect(self.browse_csv_remote)

        csvFileLayout.addWidget(self.csvFilePath)
        csvFileLayout.addWidget(self.browseCsvButton)
        csvFileLayout.addWidget(self.browseCsvRemoteButton)
        
        # Connect radio buttons to enable/disable CSV controls
        self.h5drmFileRadio.toggled.connect(self.toggle_csv_controls)
        self.csvFileRadio.toggled.connect(self.toggle_csv_controls)
        
        sourceLayout.addLayout(csvFileLayout)
        pointsLayout.addWidget(sourceGroup, 1, 0, 1, 2)
        
        # Point visualization customization
        visualGroup = QGroupBox("Point Visualization")
        visualLayout = QGridLayout(visualGroup)
        
        visualLayout.addWidget(QLabel("Point Size:"), 0, 0)
        self.pointSizeSpinBox = QDoubleSpinBox()
        self.pointSizeSpinBox.setRange(1, 20)
        self.pointSizeSpinBox.setValue(5)
        self.pointSizeSpinBox.setSingleStep(1)
        visualLayout.addWidget(self.pointSizeSpinBox, 0, 1)
        
        visualLayout.addWidget(QLabel("Color:"), 1, 0)
        self.pointColorButton = QPushButton("Choose Color...")
        self.pointColorButton.clicked.connect(self.choose_point_color)
        visualLayout.addWidget(self.pointColorButton, 1, 1)
        
        # Initialize point color
        self.pointColor = (1.0, 0.0, 0.0)  # Default red
        
        pointsLayout.addWidget(visualGroup, 2, 0, 1, 2)
        
        # Add DRM points control buttons
        pointsControlGroup = QGroupBox("DRM Points Control")
        pointsControlLayout = QGridLayout(pointsControlGroup)
        
        # Show DRM Points Button
        self.showDRMPointsButton = QPushButton("Show DRM Points")
        self.showDRMPointsButton.clicked.connect(self.show_drm_points)
        pointsControlLayout.addWidget(self.showDRMPointsButton, 0, 0)
        
        # Toggle visibility button
        self.togglePointsVisibilityButton = QPushButton("Hide Points")
        self.togglePointsVisibilityButton.setEnabled(False)  # Initially disabled
        self.togglePointsVisibilityButton.clicked.connect(self.toggle_points_visibility)
        pointsControlLayout.addWidget(self.togglePointsVisibilityButton, 0, 1)
        
        # Remove points button
        self.removePointsButton = QPushButton("Remove Points")
        self.removePointsButton.setEnabled(False)  # Initially disabled
        self.removePointsButton.clicked.connect(self.remove_drm_points)
        pointsControlLayout.addWidget(self.removePointsButton, 1, 0, 1, 2)
        
        pointsLayout.addWidget(pointsControlGroup, 3, 0, 1, 2)
        
        h5drmLayout.addWidget(pointsGroup, 6, 0, 1, 2)
        
        # Add H5DRM Pattern button
        self.addH5DRMButton = QPushButton("Add H5DRM Pattern")
        self.addH5DRMButton.setStyleSheet("background-color: blue; color: white")
        self.addH5DRMButton.clicked.connect(self.add_h5drm_pattern)
        h5drmLayout.addWidget(self.addH5DRMButton, 7, 0, 1, 2)
        
        h5drmLayout.setContentsMargins(10, 10, 10, 10)
        h5drmLayout.setSpacing(10)
        
        layout.addWidget(h5drmPatternBox)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Initialize transformation matrix with identity matrix and zero origin
        self.transform_matrix = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        self.origin = [0.0, 0.0, 0.0]
        
        # Update the UI to show the initial values
        self.update_transform_ui()
        
        # Initialize DRM points visualization attributes
        self.drm_points_actor = None
        self.points_visible = True  # Track visibility state

    def update_transform_ui(self):
        """Updates the UI input fields to reflect the current transformation matrix and origin values.

        This method populates the `matrix_inputs` and `origin_inputs` with the
        values stored in `self.transform_matrix` and `self.origin` respectively.
        """
        # Update matrix inputs
        for i, value in enumerate(self.transform_matrix):
            self.matrix_inputs[i].setValue(value)
        
        # Update origin inputs
        for i, value in enumerate(self.origin):
            self.origin_inputs[i].setValue(value)

    def set_identity_matrix(self):
        """Sets the internal transformation matrix to an identity matrix.

        After setting the matrix, it calls `update_transform_ui` to reflect
        the changes in the GUI.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> # Assume some matrix values were set
            >>> gui.set_identity_matrix()
            >>> # The matrix input fields in the UI will now show identity matrix.
        """
        self.transform_matrix = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        self.update_transform_ui()

    def reset_origin(self):
        """Resets the internal origin coordinates to [0.0, 0.0, 0.0].

        It then updates the origin input fields in the UI to reflect these
        new values.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> # Assume some origin values were set
            >>> gui.reset_origin()
            >>> # The origin input fields in the UI will now show [0, 0, 0].
        """
        self.origin = [0.0, 0.0, 0.0]
        for i, value in enumerate(self.origin):
            self.origin_inputs[i].setValue(value)
    
    def auto_set_origin_from_mesh(self):
        """Sets the origin coordinates based on the assembled mesh's bounding box.

        The X and Y coordinates are set to the center of the mesh's bounding box,
        while the Z coordinate is set to the maximum Z value of the bounding box.
        The transformation matrix itself is preserved.

        Returns:
            bool: True if the origin was successfully set, False otherwise (e.g., no mesh).

        Raises:
            UserWarning: If no assembled mesh is available, a warning message is displayed.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> # In a real scenario, you'd have a mesh assembled first
            >>> # gui.meshmaker.assembler.AssembeledMesh = ... # (Mock a mesh for testing)
            >>> success = gui.auto_set_origin_from_mesh()
            >>> # print(f"Origin set from mesh: {success}")
        """
        if self.meshmaker.assembler.AssembeledMesh is None:
            QMessageBox.warning(self, "Warning", "No assembled mesh available. Please assemble a mesh first.")
            return False
        
        # Get mesh bounds
        bounds = self.meshmaker.assembler.AssembeledMesh.bounds
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        
        # Calculate center for x and y, but use zmax for z
        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2
        center_z = zmax  # As requested, use zmax for z-coordinate
        
        # Set origin only - preserve transform matrix
        self.origin = [center_x, center_y, center_z]
        
        # Update only the origin fields in UI
        for i, value in enumerate(self.origin):
            self.origin_inputs[i].setValue(value)
        
        return True
    
    def browse_h5drm_file(self):
        """Opens a file dialog to allow the user to select a local H5DRM file.

        Upon successful selection, the file path is displayed in the
        `h5drmFilePath` QLineEdit, and the file source is set to "local".
        Both `h5drmFileRadio` and `csvFileRadio` become enabled for point source selection.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> # Simulate clicking the browse button (would open a native file dialog)
            >>> # gui.browse_h5drm_file()
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select H5DRM File", "", "H5DRM Files (*.h5drm);;All Files (*)"
        )
        if file_path:
            self.h5drmFilePath.setText(file_path)
            self.file_source = "local"
            
            # Enable both point source options when using local H5DRM
            self.h5drmFileRadio.setEnabled(True)
    
    def browse_csv_file(self):
        """Opens a file dialog to allow the user to select a local CSV file with DRM points.

        Upon successful selection, the file path is displayed in the
        `csvFilePath` QLineEdit, and the CSV file source is set to "local".

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> # Simulate clicking the browse CSV button (would open a native file dialog)
            >>> # gui.browse_csv_file()
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File with DRM Points", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.csvFilePath.setText(file_path)
            self.csv_file_source = "local"
    
    def toggle_csv_controls(self):
        """Toggles the enabled state of CSV file controls based on the selected point source.

        If `csvFileRadio` is checked, the `csvFilePath` QLineEdit and
        `browseCsvButton`/`browseCsvRemoteButton` are enabled. Otherwise, they are disabled.
        If a remote H5DRM file is selected, this method ensures `csvFileRadio` is checked.
        """
        enable_csv = self.csvFileRadio.isChecked()
        self.csvFilePath.setEnabled(enable_csv)
        self.browseCsvButton.setEnabled(enable_csv)
        self.browseCsvRemoteButton.setEnabled(enable_csv)
        
        # If using remote H5DRM, force CSV mode
        if self.file_source == "remote" and not enable_csv:
            self.csvFileRadio.setChecked(True)
    
    def choose_point_color(self):
        """Opens a color dialog for the user to select a color for DRM points.

        If a valid color is selected, `self.pointColor` is updated with the
        new RGB tuple (0-1 range), and the `pointColorButton`'s background
        is updated to visually reflect the chosen color.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> # Simulate clicking the Choose Color button (would open a native color dialog)
            >>> # gui.choose_point_color()
        """
        color = QColorDialog.getColor()
        if color.isValid():
            # Convert QColor to RGB tuple (0-1 range)
            self.pointColor = (color.redF(), color.greenF(), color.blueF())
            
            # Update button background color as visual feedback
            style = f"background-color: rgb({color.red()}, {color.green()}, {color.blue()})"
            self.pointColorButton.setStyleSheet(style)
    
    def toggle_points_visibility(self):
        """Toggles the visibility of the DRM points actor in the plotter.

        If DRM points are currently visible, they are hidden, and the button text changes to "Show Points".
        If hidden, they are made visible, and the button text changes to "Hide Points".
        The plotter is rendered after the change.
        """
        if self.drm_points_actor is None:
            return
            
        plotter = PlotterManager.get_plotter()
        
        # Toggle visibility
        self.points_visible = not self.points_visible
        self.drm_points_actor.SetVisibility(self.points_visible)
        
        # Update button text based on current state
        if self.points_visible:
            self.togglePointsVisibilityButton.setText("Hide Points")
        else:
            self.togglePointsVisibilityButton.setText("Show Points")
            
        # Render the scene to reflect changes
        plotter.render()
    
    def remove_drm_points(self):
        """Removes the DRM points actor from the plotter scene.

        Disables the toggle and remove buttons and resets `self.drm_points_actor` to None.
        A confirmation message is displayed to the user.
        The plotter is rendered after removal.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> # Assume DRM points are shown
            >>> # gui.remove_drm_points()
        """
        if self.drm_points_actor == None:
            return
            
        plotter = PlotterManager.get_plotter()
        plotter.remove_actor(self.drm_points_actor)
        self.drm_points_actor = None
        
        # Disable the control buttons
        self.togglePointsVisibilityButton.setEnabled(False)
        self.removePointsButton.setEnabled(False)
        
        # Render the scene to reflect changes
        plotter.render()
        
        QMessageBox.information(self, "Points Removed", "DRM points have been removed from the visualization.")
    
    def show_drm_points(self):
        """Visualizes DRM points on the Femora plotter based on selected source and transformation.

        Points can be loaded from either a local H5DRM file (transforming by metadata
        and GUI scale factor) or a local/remote CSV file.
        The loaded points are then subjected to the transformation matrix and origin
        defined in the GUI before being displayed in the plotter.
        Existing DRM point actors are removed before adding new ones.

        Raises:
            UserWarning: If 'Show DRM points in visualization' checkbox is not checked,
                or no H5DRM/CSV file is selected, or no valid points are loaded.
            UserError: If plotter cannot be initialized, or H5DRM/CSV file reading fails,
                or points cannot be visualized.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> gui.showPointsCheckbox.setChecked(True)
            >>> # Assuming a H5DRM file is selected or CSV file is ready
            >>> # gui.show_drm_points()
            >>> # This would visualize points in the external plotter window.
        """
        if not self.showPointsCheckbox.isChecked():
            QMessageBox.warning(self, "Warning", "Please check 'Show DRM points in visualization' first.")
            return
        
        # Get current matrix and origin values from UI
        self.transform_matrix = [input_field.value() for input_field in self.matrix_inputs]
        self.origin = [input_field.value() for input_field in self.origin_inputs]
        
        # Get the plotter
        try:
            plotter = PlotterManager.get_plotter()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not get plotter: {str(e)}")
            return
        
        # Remove existing DRM points actor if any
        if self.drm_points_actor is not None:
            plotter.remove_actor(self.drm_points_actor)
            self.drm_points_actor = None
        
        points = None
        
        # Get points based on selected source
        if self.h5drmFileRadio.isChecked():
            # From H5DRM file
            h5drm_path = self.h5drmFilePath.text()
            if not h5drm_path:
                QMessageBox.warning(self, "Warning", "Please select an H5DRM file first.")
                return
            
            try:
                import h5py
                with h5py.File(h5drm_path, 'r') as h5_file:
                    # Get the points from the "xyz" dataset in the DRM_Data group
                    points = h5_file['DRM_Data']["xyz"][()]
                    points = np.array(points)
                    
                    # Get the origin from the DRM_Metadata/drmbox_x0 dataset
                    xyz0 = h5_file['DRM_Metadata']['drmbox_x0'][()]
                    xyz0 = np.array(xyz0)
                    
                    # Adjust points relative to the DRM box origin
                    points = points - xyz0
                    
                    # Apply coordinate scale from GUI
                    coord_scale = self.coordScaleSpinBox.value()
                    points = points * coord_scale
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read H5DRM file: {str(e)}")
                return
        else:
            # From CSV file
            csv_path = self.csvFilePath.text()
            if not csv_path:
                QMessageBox.warning(self, "Warning", "Please select a CSV file with DRM points.")
                return
            
            try:
                # Read points from CSV file
                points = []
                with open(csv_path, 'r') as file:
                    csv_reader = csv.reader(file)
                    header = next(csv_reader, None)  # Skip header if exists
                    
                    # Check if first row is header or data
                    if header and all(not is_number(val) for val in header):
                        # First row is header, continue with data
                        pass
                    else:
                        # First row is data, add it to points
                        try:
                            points.append([float(val) for val in header[:3]])
                        except ValueError:
                            # Not numeric data, must be header
                            pass
                    
                    # Read remaining rows
                    for row in csv_reader:
                        if len(row) >= 3:  # Ensure we have at least x,y,z coordinates
                            try:
                                x, y, z = float(row[0]), float(row[1]), float(row[2])
                                points.append([x, y, z])
                            except ValueError:
                                # Skip non-numeric rows
                                continue
                
                points = np.array(points)
                if len(points) == 0:
                    raise ValueError("No valid points found in CSV file")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read CSV file: {str(e)}")
                return
        
        if points is None or len(points) == 0:
            QMessageBox.warning(self, "Error", "No points loaded.")
            return
        
        # Always apply coordinate transformation as requested
        # Create transformation matrix
        T = np.array(self.transform_matrix).reshape(3, 3)
        
        # Apply transformation and add origin
        points_transformed = np.dot(points, T.T)
        points_transformed += np.array(self.origin)
        points = points_transformed
        
        try:
            # Create and visualize points
            point_size = self.pointSizeSpinBox.value()
            
            import pyvista as pv
            point_cloud = pv.PolyData(points)
            self.drm_points_actor = plotter.add_mesh(
                point_cloud, 
                color=self.pointColor,
                point_size=point_size,
                render_points_as_spheres=True
            )
            
            # Reset visibility state
            self.points_visible = True
            
            # Enable the control buttons
            self.togglePointsVisibilityButton.setEnabled(True)
            self.togglePointsVisibilityButton.setText("Hide Points")
            self.removePointsButton.setEnabled(True)
            
            plotter.update()
            plotter.render()
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Visualized {len(points)} DRM points"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to visualize points: {str(e)}")
    
    def add_h5drm_pattern(self):
        """Creates and adds an H5DRM load pattern to the Femora model.

        This method retrieves the file path, scale factor, coordinate scale,
        distance tolerance, transformation matrix, and origin from the GUI.
        It then uses the `PatternManager` to create an `H5DRMPattern` object.
        If the 'Show DRM points' checkbox is checked, it also triggers the
        visualization of the DRM points. The pattern is then assigned to the DRM component.

        Raises:
            UserWarning: If no H5DRM file path is provided.
            UserError: If the H5DRM pattern creation fails.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> gui = DRMGUI()
            >>> gui.show()
            >>> # Set a dummy file path (in a real scenario, this would come from QLineEdit)
            >>> gui.h5drmFilePath.setText("path/to/your/test.h5drm")
            >>> # gui.add_h5drm_pattern()
            >>> # This would create an H5DRM pattern and add it to the model.
        """
        # Check if file path is provided
        filepath = self.h5drmFilePath.text()
        if not filepath:
            QMessageBox.warning(self, "Missing File", "Please select a H5DRM file.")
            return
        
        # Get current matrix and origin values from UI
        self.transform_matrix = [input_field.value() for input_field in self.matrix_inputs]
        self.origin = [input_field.value() for input_field in self.origin_inputs]
        
        try:
            # Get parameters
            factor = self.factorSpinBox.value()
            crd_scale = self.coordScaleSpinBox.value()
            distance_tolerance = self.distToleranceSpinBox.value()
            do_transform = 1  # Always enable transformation
            
            # Create the H5DRM pattern
            pattern = self.pattern_manager.create_pattern(
                "h5drm",
                filepath=filepath,
                factor=factor,
                crd_scale=crd_scale,
                distance_tolerance=distance_tolerance,
                do_coordinate_transformation=do_transform,
                transform_matrix=self.transform_matrix,
                origin=self.origin
            )
            
            QMessageBox.information(
                self,
                "Success",
                f"H5DRM pattern created successfully with tag: {pattern.tag}"
            )
            
            # Show DRM points if checkbox is checked
            if self.showPointsCheckbox.isChecked():
                self.show_drm_points()

            DRM().set_pattern(pattern)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create H5DRM pattern: {str(e)}")
    
    def browse_h5drm_remote(self):
        """Opens a TACC file browser dialog to select a remote H5DRM file.

        If a file is selected, its path is displayed in `h5drmFilePath` prefixed with "REMOTE:",
        and `file_source` is set to "remote". It also disables the H5DRM file radio button
        and forces the selection of the CSV file radio button for point visualization,
        notifying the user about this constraint.
        """
        dialog = TACCFileBrowserDialog(self, file_type="h5drm")
        if dialog.exec_():
            remote_path = dialog.get_selected_file()
            self.remote_connection_info = dialog.get_connection_info()
            
            if remote_path:
                self.h5drmFilePath.setText(f"REMOTE: {remote_path}")
                self.file_source = "remote"
                
                # When using remote H5DRM, points source must be from CSV
                self.h5drmFileRadio.setEnabled(False)
                self.csvFileRadio.setChecked(True)
                QMessageBox.information(self, "Remote File Selected", 
                                    "When using a remote H5DRM file, points must be loaded from a CSV file.")

    def browse_csv_remote(self):
        """Opens a TACC file browser dialog to select a remote CSV file.

        If a file is selected, its path is displayed in `csvFilePath` prefixed with "REMOTE:",
        and `csv_file_source` is set to "remote".
        """
        dialog = TACCFileBrowserDialog(self, file_type="csv")
        if dialog.exec_():
            remote_path = dialog.get_selected_file()
            self.remote_connection_info = dialog.get_connection_info()
            
            if remote_path:
                self.csvFilePath.setText(f"REMOTE: {remote_path}")
                self.csv_file_source = "remote"


def is_number(s):
    """Checks if a given string can be converted to a float.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string can be converted to a float, False otherwise.

    Example:
        >>> is_number("123")
        True
        >>> is_number("3.14")
        True
        >>> is_number("hello")
        False
        >>> is_number("-5.0")
        True
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = DRMGUI()
    window.show()
    sys.exit(app.exec_())