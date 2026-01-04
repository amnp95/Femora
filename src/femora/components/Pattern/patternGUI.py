from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout, 
    QStackedWidget, QScrollArea, QTextEdit
)

from femora.components.Pattern.patternBase import Pattern, PatternManager
from femora.components.TimeSeries.timeSeriesBase import TimeSeries, TimeSeriesManager
from femora.utils.validator import DoubleValidator, IntValidator

class PatternManagerTab(QDialog):
    """Manages the creation, editing, and deletion of dynamic patterns.

    This dialog provides a user interface to interact with `Pattern` objects,
    displaying them in a table and allowing various operations like creating
    new patterns of different types (e.g., Uniform Excitation, H5DRM) or
    modifying existing ones.

    Attributes:
        pattern_manager (PatternManager): The singleton manager for Pattern objects.
        time_series_manager (TimeSeriesManager): The singleton manager for TimeSeries objects.
        pattern_type_combo (QComboBox): Dropdown for selecting the type of pattern to create.
        patterns_table (QTableWidget): Table displaying all registered patterns.
    
    Example:
        >>> import sys
        >>> from qtpy.QtWidgets import QApplication
        >>> app = QApplication(sys.argv)
        >>> manager_tab = PatternManagerTab()
        >>> manager_tab.show()
        >>> # app.exec_() # Uncomment to run the Qt event loop
    """
    def __init__(self, parent=None):
        """Initializes the PatternManagerTab dialog.

        Args:
            parent (QWidget, optional): The parent widget of this dialog.
                Defaults to None.
        """
        super().__init__(parent)
        
        # Setup dialog properties
        self.setWindowTitle("Pattern Manager")
        self.resize(800, 600)
        
        # Get the pattern manager instance
        self.pattern_manager = PatternManager()
        self.time_series_manager = TimeSeriesManager()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Pattern type selection
        type_layout = QGridLayout()
        
        # Pattern type dropdown
        self.pattern_type_combo = QComboBox()
        self.pattern_type_combo.addItems(self.pattern_manager.get_available_types())
        
        create_pattern_btn = QPushButton("Create New Pattern")
        create_pattern_btn.clicked.connect(self.open_pattern_creation_dialog)
        
        type_layout.addWidget(QLabel("Pattern Type:"), 0, 0)
        type_layout.addWidget(self.pattern_type_combo, 0, 1)
        type_layout.addWidget(create_pattern_btn, 1, 0, 1, 2)
        
        layout.addLayout(type_layout)
        
        # Patterns table
        self.patterns_table = QTableWidget()
        self.patterns_table.setColumnCount(5)  # Tag, Type, Parameters, Edit, Delete
        self.patterns_table.setHorizontalHeaderLabels(["Tag", "Type", "Parameters", "Edit", "Delete"])
        header = self.patterns_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # Stretch all columns
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Except for the first one
        
        layout.addWidget(self.patterns_table)
        
        # Refresh patterns button
        refresh_btn = QPushButton("Refresh Patterns List")
        refresh_btn.clicked.connect(self.refresh_patterns_list)
        layout.addWidget(refresh_btn)
        
        # Initial refresh
        self.refresh_patterns_list()

    def open_pattern_creation_dialog(self):
        """Opens a specific dialog to create a new pattern based on the selected type.

        If a creation dialog is available for the selected pattern type, it is
        opened. Upon successful creation, the patterns list is refreshed.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> manager_tab = PatternManagerTab()
            >>> manager_tab.pattern_type_combo.setCurrentText("UniformExcitation")
            >>> manager_tab.open_pattern_creation_dialog()
            >>> # This would open the UniformExcitationCreationDialog
        """
        pattern_type = self.pattern_type_combo.currentText()
        
        if pattern_type.lower() == "uniformexcitation":
            dialog = UniformExcitationCreationDialog(self)
        elif pattern_type.lower() == "h5drm":
            dialog = H5DRMCreationDialog(self)
        else:
            QMessageBox.warning(self, "Error", f"No creation dialog available for pattern type: {pattern_type}")
            return
        
        if dialog.exec() == QDialog.Accepted:
            self.refresh_patterns_list()

    def refresh_patterns_list(self):
        """Updates the patterns table with the current list of patterns from the manager.

        This method clears the existing table content and repopulates it with
        all patterns currently managed by the `PatternManager`, including their
        tag, type, parameters, and action buttons.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> app = QApplication(sys.argv)
            >>> PatternManager().create_pattern("UniformExcitation", dof=1, time_series=None)
            >>> manager_tab = PatternManagerTab()
            >>> manager_tab.refresh_patterns_list()
            >>> print(manager_tab.patterns_table.rowCount() > 0)
            True
        """
        self.patterns_table.setRowCount(0)
        patterns = Pattern.get_all_patterns()
        
        self.patterns_table.setRowCount(len(patterns))
        
        for row, (tag, pattern) in enumerate(patterns.items()):
            # Tag
            tag_item = QTableWidgetItem(str(tag))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            self.patterns_table.setItem(row, 0, tag_item)
            
            # Pattern Type
            type_item = QTableWidgetItem(pattern.pattern_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.patterns_table.setItem(row, 1, type_item)
            
            # Parameters
            params_dict = pattern.get_values()
            if pattern.pattern_type == "UniformExcitation":
                params_str = f"DOF: {params_dict['dof']}, TimeSeries: {params_dict['time_series'].tag}"
                if params_dict.get('vel0', 0.0) != 0.0:
                    params_str += f", Velocity: {params_dict['vel0']}"
                if params_dict.get('factor', 1.0) != 1.0:
                    params_str += f", Factor: {params_dict['factor']}"
            elif pattern.pattern_type == "H5DRM":
                params_str = f"File: {params_dict['filepath']}, Factor: {params_dict['factor']}"
            else:
                params_str = str(params_dict)
                
            params_item = QTableWidgetItem(params_str)
            params_item.setFlags(params_item.flags() & ~Qt.ItemIsEditable)
            self.patterns_table.setItem(row, 2, params_item)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, p=pattern: self.open_pattern_edit_dialog(p))
            self.patterns_table.setCellWidget(row, 3, edit_btn)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, t=tag: self.delete_pattern(t))
            self.patterns_table.setCellWidget(row, 4, delete_btn)

    def open_pattern_edit_dialog(self, pattern: Pattern):
        """Opens a specific dialog to edit an existing pattern.

        The appropriate edit dialog (e.g., `UniformExcitationEditDialog`, `H5DRMEditDialog`)
        is opened based on the `pattern_type` of the provided `pattern` object.
        Upon successful editing, the patterns list is refreshed.

        Args:
            pattern (Pattern): The `Pattern` object to be edited.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries
            >>> app = QApplication(sys.argv)
            >>> ts = ConstantTimeSeries(factor=1.0)
            >>> pm = PatternManager()
            >>> existing_pattern = pm.create_pattern("UniformExcitation", dof=1, time_series=ts)
            >>> manager_tab = PatternManagerTab()
            >>> manager_tab.open_pattern_edit_dialog(existing_pattern)
            >>> # This would open the UniformExcitationEditDialog for the pattern
        """
        if pattern.pattern_type == "UniformExcitation":
            dialog = UniformExcitationEditDialog(pattern, self)
        elif pattern.pattern_type == "H5DRM":
            dialog = H5DRMEditDialog(pattern, self)
        else:
            QMessageBox.warning(self, "Error", f"No edit dialog available for pattern type: {pattern.pattern_type}")
            return
        
        if dialog.exec() == QDialog.Accepted:
            self.refresh_patterns_list()

    def delete_pattern(self, tag: int):
        """Deletes a pattern from the system after user confirmation.

        A confirmation dialog is presented to the user before the pattern
        with the given tag is permanently removed. The patterns list is
        refreshed after deletion.

        Args:
            tag (int): The unique integer tag of the pattern to be deleted.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries
            >>> app = QApplication(sys.argv)
            >>> ts = ConstantTimeSeries(factor=1.0)
            >>> pm = PatternManager()
            >>> pattern_to_delete = pm.create_pattern("UniformExcitation", dof=1, time_series=ts)
            >>> manager_tab = PatternManagerTab()
            >>> # To avoid blocking, this example would typically be part of a test suite
            >>> # where QMessageBox can be mocked or automatically accepted.
            >>> # For interactive use: manager_tab.delete_pattern(pattern_to_delete.tag)
        """
        reply = QMessageBox.question(
            self, 'Delete Pattern',
            f"Are you sure you want to delete pattern with tag {tag}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.pattern_manager.remove_pattern(tag)
            self.refresh_patterns_list()


class UniformExcitationCreationDialog(QDialog):
    """Dialog for creating a new Uniform Excitation Pattern.

    This dialog allows users to define the properties for a new uniform
    excitation pattern, including the DOF direction, associated time series,
    initial velocity, and a scaling factor.

    Attributes:
        pattern_manager (PatternManager): The singleton manager for Pattern objects.
        time_series_manager (TimeSeriesManager): The singleton manager for TimeSeries objects.
        int_validator (IntValidator): Validator for integer input fields.
        double_validator (DoubleValidator): Validator for float input fields.
        dof_input (QLineEdit): Input field for the DOF direction.
        time_series_combo (QComboBox): Dropdown for selecting an existing time series.
        vel0_input (QLineEdit): Input field for the initial velocity.
        factor_input (QLineEdit): Input field for the scaling factor.

    Example:
        >>> import sys
        >>> from qtpy.QtWidgets import QApplication
        >>> app = QApplication(sys.argv)
        >>> create_dialog = UniformExcitationCreationDialog()
        >>> create_dialog.show()
        >>> # app.exec_() # Uncomment to run the Qt event loop
    """
    def __init__(self, parent=None):
        """Initializes the UniformExcitationCreationDialog.

        Args:
            parent (QWidget, optional): The parent widget of this dialog.
                Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Create Uniform Excitation Pattern")
        self.pattern_manager = PatternManager()
        self.time_series_manager = TimeSeriesManager()
        self.int_validator = IntValidator()
        self.double_validator = DoubleValidator()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Input form
        form_layout = QFormLayout()
        
        # DOF Direction
        self.dof_input = QLineEdit()
        self.dof_input.setValidator(self.int_validator)
        form_layout.addRow("DOF Direction:", self.dof_input)
        
        # TimeSeries selection
        self.time_series_combo = QComboBox()
        self.update_time_series_list()
        form_layout.addRow("Time Series:", self.time_series_combo)
        
        # Time series management buttons
        ts_layout = QHBoxLayout()
        refresh_ts_btn = QPushButton("Refresh")
        refresh_ts_btn.clicked.connect(self.update_time_series_list)
        create_ts_btn = QPushButton("Create New")
        create_ts_btn.clicked.connect(self.open_time_series_dialog)
        
        ts_layout.addWidget(refresh_ts_btn)
        ts_layout.addWidget(create_ts_btn)
        form_layout.addRow("", ts_layout)
        
        # Initial velocity
        self.vel0_input = QLineEdit("0.0")
        self.vel0_input.setValidator(self.double_validator)
        form_layout.addRow("Initial Velocity (optional):", self.vel0_input)
        
        # Factor
        self.factor_input = QLineEdit("1.0")
        self.factor_input.setValidator(self.double_validator)
        form_layout.addRow("Factor (optional):", self.factor_input)
        
        layout.addLayout(form_layout)
        
        # Add notes
        notes_section = QTextEdit()
        notes_section.setReadOnly(True)
        notes_section.setPlainText(
            "Notes:\n"
            "- The DOF direction specifies the degrees of freedom affected by the motion\n"
            "- For standard models: 1=X, 2=Y, 3=Z\n"
            "- The responses obtained from the nodes are RELATIVE values\n"
            "- Time Series defines the acceleration history\n"
            "- Initial velocity allows setting a non-zero starting velocity\n"
            "- Factor allows scaling the input motion"
        )
        layout.addWidget(notes_section)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_pattern)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def update_time_series_list(self):
        """Updates the time series dropdown with all available time series.

        This method clears the `time_series_combo` and repopulates it with
        the current list of `TimeSeries` objects from the `TimeSeriesManager`,
        displaying their type and tag.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries
            >>> app = QApplication(sys.argv)
            >>> ts = ConstantTimeSeries(factor=1.0)
            >>> dialog = UniformExcitationCreationDialog()
            >>> dialog.update_time_series_list()
            >>> print(dialog.time_series_combo.count() > 0)
            True
        """
        self.time_series_combo.clear()
        time_series_dict = TimeSeries.get_all_time_series()
        
        for tag, ts in time_series_dict.items():
            self.time_series_combo.addItem(f"{ts.series_type} (Tag: {tag})", ts)

    def open_time_series_dialog(self):
        """Opens the TimeSeriesManagerTab dialog to create or manage time series.

        Upon `TimeSeriesManagerTab` being accepted, the `time_series_combo`
        in this dialog is refreshed to reflect any changes.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> dialog = UniformExcitationCreationDialog()
            >>> # This would typically be triggered by clicking a button.
            >>> # dialog.open_time_series_dialog()
            >>> # This would open the TimeSeriesManagerTab
        """
        from femora.components.TimeSeries.timeSeriesGUI import TimeSeriesManagerTab
        dialog = TimeSeriesManagerTab(self)
        if dialog.exec() == QDialog.Accepted:
            self.update_time_series_list()

    def create_pattern(self):
        """Validates input fields and creates a new Uniform Excitation Pattern.

        Collects the DOF direction, selected time series, initial velocity,
        and scaling factor from the input fields. If all inputs are valid,
        a new `UniformExcitation` pattern is created via the `PatternManager`
        and the dialog is accepted.

        Raises:
            ValueError: If input values cannot be converted to the expected types.
            Exception: For any other errors during pattern creation.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries, TimeSeriesManager
            >>> app = QApplication(sys.argv)
            >>> ts_manager = TimeSeriesManager()
            >>> # Ensure a time series exists for selection
            >>> ts = ts_manager.create_time_series("ConstantTimeSeries", factor=10.0)
            >>> dialog = UniformExcitationCreationDialog()
            >>> dialog.dof_input.setText("1")
            >>> dialog.update_time_series_list() # Populate combo box
            >>> # Select the created time series
            >>> for i in range(dialog.time_series_combo.count()):
            >>>     if dialog.time_series_combo.itemData(i).tag == ts.tag:
            >>>         dialog.time_series_combo.setCurrentIndex(i)
            >>>         break
            >>> dialog.vel0_input.setText("0.5")
            >>> dialog.factor_input.setText("1.2")
            >>> # Assuming inputs are valid, calling create_pattern would attempt creation.
            >>> # dialog.create_pattern()
        """
        try:
            # Validate and collect parameters
            dof = int(self.dof_input.text())
            
            # Get selected time series
            time_series = self.time_series_combo.currentData()
            if time_series is None:
                QMessageBox.warning(self, "Error", "Please select a time series")
                return
            
            # Get optional parameters
            vel0 = float(self.vel0_input.text() or "0.0")
            factor = float(self.factor_input.text() or "1.0")
            
            # Create pattern
            pattern = self.pattern_manager.create_pattern(
                "UniformExcitation",
                dof=dof,
                time_series=time_series,
                vel0=vel0,
                factor=factor
            )
            
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class UniformExcitationEditDialog(QDialog):
    """Dialog for editing an existing Uniform Excitation Pattern.

    This dialog allows users to modify the properties of an existing uniform
    excitation pattern, including the DOF direction, associated time series,
    initial velocity, and a scaling factor. The dialog pre-populates its
    fields with the current values of the `pattern` object passed during
    initialization.

    Attributes:
        pattern (Pattern): The `UniformExcitation` pattern instance being edited.
        pattern_manager (PatternManager): The singleton manager for Pattern objects.
        time_series_manager (TimeSeriesManager): The singleton manager for TimeSeries objects.
        int_validator (IntValidator): Validator for integer input fields.
        double_validator (DoubleValidator): Validator for float input fields.
        dof_input (QLineEdit): Input field for the DOF direction.
        time_series_combo (QComboBox): Dropdown for selecting an existing time series.
        vel0_input (QLineEdit): Input field for the initial velocity.
        factor_input (QLineEdit): Input field for the scaling factor.

    Example:
        >>> import sys
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.Pattern.patternBase import PatternManager
        >>> from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries
        >>> app = QApplication(sys.argv)
        >>> ts = ConstantTimeSeries(factor=5.0)
        >>> pm = PatternManager()
        >>> existing_pattern = pm.create_pattern("UniformExcitation", dof=2, time_series=ts)
        >>> edit_dialog = UniformExcitationEditDialog(existing_pattern)
        >>> edit_dialog.show()
        >>> # app.exec_() # Uncomment to run the Qt event loop
    """
    def __init__(self, pattern: Pattern, parent=None):
        """Initializes the UniformExcitationEditDialog.

        Args:
            pattern (Pattern): The `UniformExcitation` pattern instance to be edited.
            parent (QWidget, optional): The parent widget of this dialog.
                Defaults to None.
        """
        super().__init__(parent)
        self.pattern = pattern
        self.setWindowTitle(f"Edit Uniform Excitation Pattern (Tag: {pattern.tag})")
        self.pattern_manager = PatternManager()
        self.time_series_manager = TimeSeriesManager()
        self.int_validator = IntValidator()
        self.double_validator = DoubleValidator()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Input form
        form_layout = QFormLayout()
        
        # DOF Direction
        self.dof_input = QLineEdit(str(pattern.dof))
        self.dof_input.setValidator(self.int_validator)
        form_layout.addRow("DOF Direction:", self.dof_input)
        
        # TimeSeries selection
        self.time_series_combo = QComboBox()
        self.update_time_series_list()
        # Set current time series
        for i in range(self.time_series_combo.count()):
            ts = self.time_series_combo.itemData(i)
            if ts and ts.tag == pattern.time_series.tag:
                self.time_series_combo.setCurrentIndex(i)
                break
        form_layout.addRow("Time Series:", self.time_series_combo)
        
        # Time series management buttons
        ts_layout = QHBoxLayout()
        refresh_ts_btn = QPushButton("Refresh")
        refresh_ts_btn.clicked.connect(self.update_time_series_list)
        create_ts_btn = QPushButton("Create New")
        create_ts_btn.clicked.connect(self.open_time_series_dialog)
        
        ts_layout.addWidget(refresh_ts_btn)
        ts_layout.addWidget(create_ts_btn)
        form_layout.addRow("", ts_layout)
        
        # Initial velocity
        self.vel0_input = QLineEdit(str(pattern.vel0))
        self.vel0_input.setValidator(self.double_validator)
        form_layout.addRow("Initial Velocity:", self.vel0_input)
        
        # Factor
        self.factor_input = QLineEdit(str(pattern.factor))
        self.factor_input.setValidator(self.double_validator)
        form_layout.addRow("Factor:", self.factor_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_pattern)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def update_time_series_list(self):
        """Updates the time series dropdown with all available time series.

        This method clears the `time_series_combo` and repopulates it with
        the current list of `TimeSeries` objects from the `TimeSeriesManager`,
        displaying their type and tag. It also attempts to re-select the
        currently associated time series if it still exists.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries
            >>> app = QApplication(sys.argv)
            >>> ts_old = ConstantTimeSeries(factor=5.0)
            >>> ts_new = ConstantTimeSeries(factor=10.0)
            >>> pm = PatternManager()
            >>> existing_pattern = pm.create_pattern("UniformExcitation", dof=2, time_series=ts_old)
            >>> edit_dialog = UniformExcitationEditDialog(existing_pattern)
            >>> edit_dialog.update_time_series_list()
            >>> print(edit_dialog.time_series_combo.count() > 0)
            True
        """
        current_ts_tag = None
        if self.time_series_combo.currentData():
            current_ts_tag = self.time_series_combo.currentData().tag
        
        self.time_series_combo.clear()
        time_series_dict = TimeSeries.get_all_time_series()
        
        current_index = 0
        for i, (tag, ts) in enumerate(time_series_dict.items()):
            self.time_series_combo.addItem(f"{ts.series_type} (Tag: {tag})", ts)
            if tag == current_ts_tag:
                current_index = i
        
        if self.time_series_combo.count() > 0:
            self.time_series_combo.setCurrentIndex(current_index)

    def open_time_series_dialog(self):
        """Opens the TimeSeriesManagerTab dialog to create or manage time series.

        Upon `TimeSeriesManagerTab` being accepted, the `time_series_combo`
        in this dialog is refreshed to reflect any changes.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries
            >>> app = QApplication(sys.argv)
            >>> ts = ConstantTimeSeries(factor=5.0)
            >>> pm = PatternManager()
            >>> existing_pattern = pm.create_pattern("UniformExcitation", dof=2, time_series=ts)
            >>> dialog = UniformExcitationEditDialog(existing_pattern)
            >>> # This would typically be triggered by clicking a button.
            >>> # dialog.open_time_series_dialog()
            >>> # This would open the TimeSeriesManagerTab
        """
        from femora.components.TimeSeries.timeSeriesGUI import TimeSeriesManagerTab
        dialog = TimeSeriesManagerTab(self)
        if dialog.exec() == QDialog.Accepted:
            self.update_time_series_list()

    def save_pattern(self):
        """Validates input fields and saves changes to the existing Pattern.

        Collects the DOF direction, selected time series, initial velocity,
        and scaling factor from the input fields. If all inputs are valid,
        the `pattern` object's values are updated using its `update_values`
        method, and the dialog is accepted.

        Raises:
            ValueError: If input values cannot be converted to the expected types.
            Exception: For any other errors during pattern update.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries, TimeSeriesManager
            >>> app = QApplication(sys.argv)
            >>> ts_manager = TimeSeriesManager()
            >>> ts = ts_manager.create_time_series("ConstantTimeSeries", factor=10.0)
            >>> pm = PatternManager()
            >>> existing_pattern = pm.create_pattern("UniformExcitation", dof=1, time_series=ts)
            >>> dialog = UniformExcitationEditDialog(existing_pattern)
            >>> dialog.dof_input.setText("2") # Change DOF
            >>> # Assuming other inputs are valid, calling save_pattern would attempt update.
            >>> # dialog.save_pattern()
            >>> # print(existing_pattern.dof) # Would print 2 if save successful
        """
        try:
            # Validate and collect parameters
            dof = int(self.dof_input.text())
            
            # Get selected time series
            time_series = self.time_series_combo.currentData()
            if time_series is None:
                QMessageBox.warning(self, "Error", "Please select a time series")
                return
            
            # Get optional parameters
            vel0 = float(self.vel0_input.text() or "0.0")
            factor = float(self.factor_input.text() or "1.0")
            
            # Update pattern
            self.pattern.update_values(
                dof=dof,
                time_series=time_series,
                vel0=vel0,
                factor=factor
            )
            
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class H5DRMCreationDialog(QDialog):
    """Dialog for creating a new H5DRM Pattern.

    This dialog allows users to define the properties for a new H5DRM
    pattern, which typically involves an HDF5-based DRM dataset. It includes
    options for scaling, coordinate transformation, and origin definition.

    Attributes:
        pattern_manager (PatternManager): The singleton manager for Pattern objects.
        double_validator (DoubleValidator): Validator for float input fields.
        int_validator (IntValidator): Validator for integer input fields.
        filepath_input (QLineEdit): Input field for the H5DRM dataset file path.
        factor_input (QLineEdit): Input field for the scaling factor.
        crd_scale_input (QLineEdit): Input field for coordinate scaling.
        distance_tolerance_input (QLineEdit): Input field for distance tolerance.
        do_transform_combo (QComboBox): Dropdown for selecting coordinate transformation option.
        transform_inputs (list[QLineEdit]): List of 9 QLineEdit widgets for the 3x3 transformation matrix.
        origin_inputs (list[QLineEdit]): List of 3 QLineEdit widgets for the X, Y, Z origin coordinates.

    Example:
        >>> import sys
        >>> from qtpy.QtWidgets import QApplication
        >>> app = QApplication(sys.argv)
        >>> create_dialog = H5DRMCreationDialog()
        >>> create_dialog.show()
        >>> # app.exec_() # Uncomment to run the Qt event loop
    """
    def __init__(self, parent=None):
        """Initializes the H5DRMCreationDialog.

        Args:
            parent (QWidget, optional): The parent widget of this dialog.
                Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Create H5DRM Pattern")
        self.pattern_manager = PatternManager()
        self.double_validator = DoubleValidator()
        self.int_validator = IntValidator()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Input form within a scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # File path
        self.filepath_input = QLineEdit()
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.filepath_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        form_layout.addRow("H5DRM Dataset:", file_layout)
        
        # Factor
        self.factor_input = QLineEdit("1.0")
        self.factor_input.setValidator(self.double_validator)
        form_layout.addRow("Factor:", self.factor_input)
        
        # Coordinate scale
        self.crd_scale_input = QLineEdit("1.0")
        self.crd_scale_input.setValidator(self.double_validator)
        form_layout.addRow("Coordinate Scale:", self.crd_scale_input)
        
        # Distance tolerance
        self.distance_tolerance_input = QLineEdit("0.001")
        self.distance_tolerance_input.setValidator(self.double_validator)
        form_layout.addRow("Distance Tolerance:", self.distance_tolerance_input)
        
        # Coordinate transformation
        self.do_transform_combo = QComboBox()
        self.do_transform_combo.addItems(["0 - No Transformation", "1 - Apply Transformation"])
        form_layout.addRow("Apply Transformation:", self.do_transform_combo)
        
        # Transformation matrix
        form_layout.addRow(QLabel("Transformation Matrix:"))
        
        # Create a grid layout for the transformation matrix
        matrix_layout = QGridLayout()
        self.transform_inputs = []
        for i in range(3):
            for j in range(3):
                input_field = QLineEdit("0.0")
                if i == j:
                    input_field.setText("1.0")  # Identity matrix by default
                input_field.setValidator(self.double_validator)
                matrix_layout.addWidget(input_field, i, j)
                self.transform_inputs.append(input_field)
        
        form_layout.addRow(matrix_layout)
        
        # Origin
        form_layout.addRow(QLabel("Origin Location:"))
        origin_layout = QHBoxLayout()
        self.origin_inputs = []
        for label in ["X:", "Y:", "Z:"]:
            origin_layout.addWidget(QLabel(label))
            input_field = QLineEdit("0.0")
            input_field.setValidator(self.double_validator)
            origin_layout.addWidget(input_field)
            self.origin_inputs.append(input_field)
        
        form_layout.addRow(origin_layout)
        
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        # Add notes
        notes_section = QTextEdit()
        notes_section.setReadOnly(True)
        notes_section.setPlainText(
            "Notes:\n"
            "- Factor: Scale DRM dataset displacements and accelerations\n"
            "- Coordinate Scale: Scale coordinates for unit conversion\n"
            "- Distance Tolerance: For DRM point to FE mesh matching\n"
            "- Transformation Matrix: Applied to dataset coordinates\n"
            "- Origin: Location after transformation"
        )
        layout.addWidget(notes_section)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_pattern)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def browse_file(self):
        """Opens a file dialog to allow the user to select an H5DRM dataset file.

        The selected file path is then set as the text in the `filepath_input`
        QLineEdit.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> dialog = H5DRMCreationDialog()
            >>> # Simulate clicking the browse button (this would open a file dialog)
            >>> # dialog.browse_file()
            >>> # After selecting a file, dialog.filepath_input.text() would contain the path.
        """
        from qtpy.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select H5DRM Dataset", "", "H5DRM Files (*.h5drm);;All Files (*)"
        )
        if filename:
            self.filepath_input.setText(filename)

    def create_pattern(self):
        """Validates input fields and creates a new H5DRM Pattern.

        Collects the file path, various scaling and tolerance parameters,
        coordinate transformation settings, and origin from the input fields.
        If all inputs are valid, a new `H5DRM` pattern is created via the
        `PatternManager` and the dialog is accepted.

        Raises:
            ValueError: If input values cannot be converted to the expected types
                or if a file path is not provided.
            Exception: For any other errors during pattern creation.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> app = QApplication(sys.argv)
            >>> dialog = H5DRMCreationDialog()
            >>> # Set dummy values for a test scenario
            >>> dialog.filepath_input.setText("/path/to/dummy.h5drm")
            >>> dialog.factor_input.setText("1.0")
            >>> dialog.crd_scale_input.setText("1.0")
            >>> dialog.distance_tolerance_input.setText("0.001")
            >>> dialog.do_transform_combo.setCurrentIndex(0) # No Transformation
            >>> # dialog.create_pattern() # Would attempt creation
        """
        try:
            # Validate and collect parameters
            filepath = self.filepath_input.text().strip()
            if not filepath:
                QMessageBox.warning(self, "Error", "Please provide a file path")
                return
            
            factor = float(self.factor_input.text())
            crd_scale = float(self.crd_scale_input.text())
            distance_tolerance = float(self.distance_tolerance_input.text())
            
            do_transform = int(self.do_transform_combo.currentText().split(" ")[0])
            
            # Get transformation matrix
            transform_matrix = []
            for input_field in self.transform_inputs:
                transform_matrix.append(float(input_field.text()))
            
            # Get origin
            origin = []
            for input_field in self.origin_inputs:
                origin.append(float(input_field.text()))
            
            # Create pattern
            pattern = self.pattern_manager.create_pattern(
                "H5DRM",
                filepath=filepath,
                factor=factor,
                crd_scale=crd_scale,
                distance_tolerance=distance_tolerance,
                do_coordinate_transformation=do_transform,
                transform_matrix=transform_matrix,
                origin=origin
            )
            
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class H5DRMEditDialog(QDialog):
    """Dialog for editing an existing H5DRM Pattern.

    This dialog allows users to modify the properties of an existing H5DRM
    pattern. It pre-populates its fields with the current values of the
    `pattern` object passed during initialization, enabling changes to
    scaling, coordinate transformation, and origin definition.

    Attributes:
        pattern (Pattern): The `H5DRM` pattern instance being edited.
        pattern_manager (PatternManager): The singleton manager for Pattern objects.
        double_validator (DoubleValidator): Validator for float input fields.
        int_validator (IntValidator): Validator for integer input fields.
        filepath_input (QLineEdit): Input field for the H5DRM dataset file path.
        factor_input (QLineEdit): Input field for the scaling factor.
        crd_scale_input (QLineEdit): Input field for coordinate scaling.
        distance_tolerance_input (QLineEdit): Input field for distance tolerance.
        do_transform_combo (QComboBox): Dropdown for selecting coordinate transformation option.
        transform_inputs (list[QLineEdit]): List of 9 QLineEdit widgets for the 3x3 transformation matrix.
        origin_inputs (list[QLineEdit]): List of 3 QLineEdit widgets for the X, Y, Z origin coordinates.

    Example:
        >>> import sys
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.Pattern.patternBase import PatternManager
        >>> app = QApplication(sys.argv)
        >>> pm = PatternManager()
        >>> # Create a dummy H5DRM pattern for editing
        >>> existing_pattern = pm.create_pattern("H5DRM", filepath="test.h5drm", factor=1.0)
        >>> edit_dialog = H5DRMEditDialog(existing_pattern)
        >>> edit_dialog.show()
        >>> # app.exec_() # Uncomment to run the Qt event loop
    """
    def __init__(self, pattern: Pattern, parent=None):
        """Initializes the H5DRMEditDialog.

        Args:
            pattern (Pattern): The `H5DRM` pattern instance to be edited.
            parent (QWidget, optional): The parent widget of this dialog.
                Defaults to None.
        """
        super().__init__(parent)
        self.pattern = pattern
        self.setWindowTitle(f"Edit H5DRM Pattern (Tag: {pattern.tag})")
        self.pattern_manager = PatternManager()
        self.double_validator = DoubleValidator()
        self.int_validator = IntValidator()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Input form within a scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # File path
        self.filepath_input = QLineEdit(pattern.filepath)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.filepath_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        form_layout.addRow("H5DRM Dataset:", file_layout)
        
        # Factor
        self.factor_input = QLineEdit(str(pattern.factor))
        self.factor_input.setValidator(self.double_validator)
        form_layout.addRow("Factor:", self.factor_input)
        
        # Coordinate scale
        self.crd_scale_input = QLineEdit(str(pattern.crd_scale))
        self.crd_scale_input.setValidator(self.double_validator)
        form_layout.addRow("Coordinate Scale:", self.crd_scale_input)
        
        # Distance tolerance
        self.distance_tolerance_input = QLineEdit(str(pattern.distance_tolerance))
        self.distance_tolerance_input.setValidator(self.double_validator)
        form_layout.addRow("Distance Tolerance:", self.distance_tolerance_input)
        
        # Coordinate transformation
        self.do_transform_combo = QComboBox()
        self.do_transform_combo.addItems(["0 - No Transformation", "1 - Apply Transformation"])
        self.do_transform_combo.setCurrentIndex(pattern.do_coordinate_transformation)
        form_layout.addRow("Apply Transformation:", self.do_transform_combo)
        
        # Transformation matrix
        form_layout.addRow(QLabel("Transformation Matrix:"))
        
        # Create a grid layout for the transformation matrix
        matrix_layout = QGridLayout()
        self.transform_inputs = []
        for i in range(3):
            for j in range(3):
                input_field = QLineEdit(str(pattern.transform_matrix[i*3 + j]))
                input_field.setValidator(self.double_validator)
                matrix_layout.addWidget(input_field, i, j)
                self.transform_inputs.append(input_field)
        
        form_layout.addRow(matrix_layout)
        
        # Origin
        form_layout.addRow(QLabel("Origin Location:"))
        origin_layout = QHBoxLayout()
        self.origin_inputs = []
        for idx, label in enumerate(["X:", "Y:", "Z:"]):
            origin_layout.addWidget(QLabel(label))
            input_field = QLineEdit(str(pattern.origin[idx]))
            input_field.setValidator(self.double_validator)
            origin_layout.addWidget(input_field)
            self.origin_inputs.append(input_field)
        
        form_layout.addRow(origin_layout)
        
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_pattern)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def browse_file(self):
        """Opens a file dialog to allow the user to select an H5DRM dataset file.

        The selected file path is then set as the text in the `filepath_input`
        QLineEdit.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> app = QApplication(sys.argv)
            >>> pm = PatternManager()
            >>> existing_pattern = pm.create_pattern("H5DRM", filepath="test.h5drm", factor=1.0)
            >>> dialog = H5DRMEditDialog(existing_pattern)
            >>> # Simulate clicking the browse button (this would open a file dialog)
            >>> # dialog.browse_file()
            >>> # After selecting a file, dialog.filepath_input.text() would contain the path.
        """
        from qtpy.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select H5DRM Dataset", "", "H5DRM Files (*.h5drm);;All Files (*)"
        )
        if filename:
            self.filepath_input.setText(filename)

    def save_pattern(self):
        """Validates input fields and saves changes to the existing H5DRM Pattern.

        Collects the file path, various scaling and tolerance parameters,
        coordinate transformation settings, and origin from the input fields.
        If all inputs are valid, the `pattern` object's values are updated
        using its `update_values` method, and the dialog is accepted.

        Raises:
            ValueError: If input values cannot be converted to the expected types
                or if a file path is not provided.
            Exception: For any other errors during pattern update.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Pattern.patternBase import PatternManager
            >>> app = QApplication(sys.argv)
            >>> pm = PatternManager()
            >>> existing_pattern = pm.create_pattern("H5DRM", filepath="old_path.h5drm", factor=1.0)
            >>> dialog = H5DRMEditDialog(existing_pattern)
            >>> dialog.filepath_input.setText("new_path.h5drm") # Change file path
            >>> dialog.factor_input.setText("1.5") # Change factor
            >>> # dialog.save_pattern() # Would attempt update
            >>> # print(existing_pattern.filepath) # Would print "new_path.h5drm" if save successful
        """
        try:
            # Validate and collect parameters
            filepath = self.filepath_input.text().strip()
            if not filepath:
                QMessageBox.warning(self, "Error", "Please provide a file path")
                return
            
            factor = float(self.factor_input.text())
            crd_scale = float(self.crd_scale_input.text())
            distance_tolerance = float(self.distance_tolerance_input.text())
            
            do_transform = int(self.do_transform_combo.currentText().split(" ")[0])
            
            # Get transformation matrix
            transform_matrix = []
            for input_field in self.transform_inputs:
                transform_matrix.append(float(input_field.text()))
            
            # Get origin
            origin = []
            for input_field in self.origin_inputs:
                origin.append(float(input_field.text()))
            
            # Update pattern
            self.pattern.update_values(
                filepath=filepath,
                factor=factor,
                crd_scale=crd_scale,
                distance_tolerance=distance_tolerance,
                do_coordinate_transformation=do_transform,
                transform_matrix=transform_matrix,
                origin=origin
            )
            
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    import sys
    
    # Create sample time series for testing
    from femora.components.TimeSeries.timeSeriesBase import (
        ConstantTimeSeries, LinearTimeSeries, TrigTimeSeries
    )
    
    const_ts = ConstantTimeSeries(factor=1.0)
    linear_ts = LinearTimeSeries(factor=2.0)
    trig_ts = TrigTimeSeries(tStart=0.0, tEnd=10.0, period=1.0, factor=1.0, shift=0.0)
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    window = PatternManagerTab()
    window.show()
    sys.exit(app.exec_())