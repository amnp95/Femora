from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout,
    QCheckBox, QGroupBox, QDoubleSpinBox, QRadioButton, QSpinBox
)

from femora.utils.validator import DoubleValidator, IntValidator
from femora.components.Analysis.convergenceTests import (
    Test, TestManager, 
    NormUnbalanceTest, NormDispIncrTest,
    EnergyIncrTest, RelativeNormUnbalanceTest,
    RelativeNormDispIncrTest, RelativeTotalNormDispIncrTest,
    RelativeEnergyIncrTest, FixedNumIterTest,
    NormDispAndUnbalanceTest, NormDispOrUnbalanceTest
)

class TestManagerTab(QDialog):
    """Manages the creation, editing, and deletion of convergence tests.

    This dialog provides a user interface for interacting with the TestManager
    backend, allowing users to define various types of convergence criteria
    for numerical analyses. It displays available test types, their descriptions,
    and a table of currently configured tests.

    Attributes:
        test_manager (TestManager): An instance of the test manager to
            handle backend test operations.
        test_type_combo (QComboBox): Dropdown for selecting the type of test
            to create.
        info_label (QLabel): Displays a description of the currently selected
            test type.
        tests_table (QTableWidget): Table displaying all configured convergence
            tests.
        checkboxes (list[QCheckBox]): List of checkboxes in the `tests_table`
            for selecting individual tests.
        edit_btn (QPushButton): Button to edit the selected test.
        delete_selected_btn (QPushButton): Button to delete the selected test.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> window = TestManagerTab()
        >>> window.show()
        >>> sys.exit(app.exec_())
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the TestManagerTab dialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        
        # Setup dialog properties
        self.setWindowTitle("Convergence Test Manager")
        self.resize(800, 500)
        
        # Get the test manager instance
        self.test_manager = TestManager()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Test type selection
        type_layout = QGridLayout()
        
        # Test type dropdown
        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems(self.test_manager.get_available_types())
        
        create_test_btn = QPushButton("Create New Test")
        create_test_btn.clicked.connect(self.open_test_creation_dialog)
        
        type_layout.addWidget(QLabel("Test Type:"), 0, 0)
        type_layout.addWidget(self.test_type_combo, 0, 1)
        type_layout.addWidget(create_test_btn, 1, 0, 1, 2)
        
        layout.addLayout(type_layout)
        
        # Info box for test description
        info_group = QGroupBox("Test Description")
        info_layout = QVBoxLayout(info_group)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)
        
        # Update info label when test type changes
        self.test_type_combo.currentTextChanged.connect(self.update_info_text)
        # Initialize with the first test type
        self.update_info_text(self.test_type_combo.currentText())
        
        # Tests table
        self.tests_table = QTableWidget()
        self.tests_table.setColumnCount(4)  # Select, Tag, Type, Parameters
        self.tests_table.setHorizontalHeaderLabels(["Select", "Tag", "Type", "Parameters"])
        self.tests_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tests_table.setSelectionMode(QTableWidget.SingleSelection)
        header = self.tests_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tests_table)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected_test)
        
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.clicked.connect(self.delete_selected_test)
        
        refresh_btn = QPushButton("Refresh Tests List")
        refresh_btn.clicked.connect(self.refresh_tests_list)
        
        buttons_layout.addWidget(self.edit_btn)
        buttons_layout.addWidget(self.delete_selected_btn)
        buttons_layout.addWidget(refresh_btn)
        
        layout.addLayout(buttons_layout)
        
        # Initial refresh
        self.refresh_tests_list()
        
        # Disable edit/delete buttons initially
        self.update_button_state()

    def update_info_text(self, test_type: str):
        """Updates the info text label based on the selected test type.

        Args:
            test_type: The name of the selected test type from the combo box.
        """
        descriptions = {
            "normunbalance": "Checks the norm of the right-hand side (unbalanced forces) vector against a tolerance. "
                            "Useful for checking overall system equilibrium, but sensitive to large penalty constraint forces.",
            
            "normdispincr": "Checks the norm of the displacement increment vector against a tolerance. "
                           "Measures displacement change and useful for tracking solution convergence.",
            
            "energyincr": "Checks the energy increment (0.5 * x^T * b) against a tolerance. "
                         "Provides energy-based convergence assessment, useful for problems with energy-critical behaviors.",
            
            "relativenormunbalance": "Compares current unbalance norm to initial unbalance norm. "
                                    "Requires at least two iterations and can be sensitive to initial conditions.",
            
            "relativenormdispincr": "Compares current displacement increment norm to initial norm. "
                                   "Tracks relative changes in displacement.",
            
            "relativetotalnormdispincr": "Uses ratio of current norm to total norm (sum of norms since last convergence). "
                                        "Tracks cumulative displacement changes and provides more comprehensive tracking.",
            
            "relativeenergyincr": "Compares energy increment relative to first iteration. "
                                 "Provides energy-based relative convergence assessment.",
            
            "fixednumiter": "Runs a fixed number of iterations with no convergence check. "
                           "Useful for specific analytical requirements.",
            
            "normdispandunbalance": "Simultaneously checks displacement increment and unbalanced force norms. "
                                   "Requires BOTH displacement and unbalance norms to converge.",
            
            "normdisporunbalance": "Convergence achieved if EITHER displacement OR unbalance norm criterion is met. "
                                  "More flexible than the AND condition."
        }
        
        test_type = test_type.lower()
        if test_type in descriptions:
            self.info_label.setText(descriptions[test_type])
        else:
            self.info_label.setText("No description available for this test type.")

    def refresh_tests_list(self):
        """Refreshes the table displaying all currently configured convergence tests.

        Populates the `tests_table` with data from the `test_manager`, including
        test tags, types, and parameters. It also manages the selection checkboxes
        and updates the state of the action buttons.
        """
        self.tests_table.setRowCount(0)
        tests = self.test_manager.get_all_tests()
        
        self.tests_table.setRowCount(len(tests))
        self.checkboxes = []  # Changed from radio_buttons to checkboxes
        
        # Hide vertical header (row indices)
        self.tests_table.verticalHeader().setVisible(False)
        
        for row, (tag, test) in enumerate(tests.items()):
            # Select checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("QCheckBox::indicator { width: 15px; height: 15px; }")
            # Connect checkboxes to a common slot to ensure mutual exclusivity
            checkbox.toggled.connect(lambda checked, btn=checkbox: self.on_checkbox_toggled(checked, btn))
            self.checkboxes.append(checkbox)
            checkbox_cell = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_cell)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.tests_table.setCellWidget(row, 0, checkbox_cell)
            
            # Tag
            tag_item = QTableWidgetItem(str(tag))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            self.tests_table.setItem(row, 1, tag_item)
            
            # Test Type
            type_item = QTableWidgetItem(test.test_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.tests_table.setItem(row, 2, type_item)
            
            # Parameters
            params = test.get_values()
            params_str = ", ".join([f"{k}: {v}" for k, v in params.items()]) if params else "None"
            params_item = QTableWidgetItem(params_str)
            params_item.setFlags(params_item.flags() & ~Qt.ItemIsEditable)
            self.tests_table.setItem(row, 3, params_item)
        
        self.update_button_state()
        
    def on_checkbox_toggled(self, checked: bool, btn: QCheckBox):
        """Handles the toggling of checkboxes in the tests table to ensure mutual exclusivity.

        When a checkbox is checked, all other checkboxes in the table are
        unchecked. This ensures only one test can be selected at a time
        for editing or deletion.

        Args:
            checked: True if the checkbox is checked, False otherwise.
            btn: The QCheckBox instance that triggered the event.
        """
        if checked:
            # Uncheck all other checkboxes
            for checkbox in self.checkboxes:
                if checkbox != btn and checkbox.isChecked():
                    checkbox.setChecked(False)
        self.update_button_state()

    def update_button_state(self):
        """Enables or disables the edit and delete buttons based on test selection.

        The buttons are enabled if at least one test checkbox is checked,
        otherwise they are disabled.
        """
        enable_buttons = any(cb.isChecked() for cb in self.checkboxes) if hasattr(self, 'checkboxes') else False
        self.edit_btn.setEnabled(enable_buttons)
        self.delete_selected_btn.setEnabled(enable_buttons)

    def get_selected_test_tag(self) -> int | None:
        """Retrieves the tag of the currently selected test in the table.

        Returns:
            int | None: The integer tag of the selected test, or None if no
                test is selected.
        """
        for row, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                tag_item = self.tests_table.item(row, 1)
                return int(tag_item.text())
        return None

    def open_test_creation_dialog(self):
        """Opens a specialized dialog for creating a new convergence test.

        The type of dialog opened depends on the currently selected test type
        in the `test_type_combo` dropdown. If the dialog is accepted, the
        tests list is refreshed.
        """
        test_type = self.test_type_combo.currentText().lower()
        
        dialog = None
        
        if test_type == "normunbalance":
            dialog = NormUnbalanceTestDialog(self)
        elif test_type == "normdispincr":
            dialog = NormDispIncrTestDialog(self)
        elif test_type == "energyincr":
            dialog = EnergyIncrTestDialog(self)
        elif test_type == "relativenormunbalance":
            dialog = RelativeNormUnbalanceTestDialog(self)
        elif test_type == "relativenormdispincr":
            dialog = RelativeNormDispIncrTestDialog(self)
        elif test_type == "relativetotalnormdispincr":
            dialog = RelativeTotalNormDispIncrTestDialog(self)
        elif test_type == "relativeenergyincr":
            dialog = RelativeEnergyIncrTestDialog(self)
        elif test_type == "fixednumiter":
            dialog = FixedNumIterTestDialog(self)
        elif test_type == "normdispandunbalance":
            dialog = NormDispAndUnbalanceTestDialog(self)
        elif test_type == "normdisporunbalance":
            dialog = NormDispOrUnbalanceTestDialog(self)
        else:
            QMessageBox.warning(self, "Error", f"No creation dialog available for test type: {test_type}")
            return
        
        if dialog.exec() == QDialog.Accepted:
            self.refresh_tests_list()

    def edit_selected_test(self):
        """Opens a specialized dialog for editing the parameters of the selected test.

        The type of dialog opened depends on the type of the selected test.
        If the dialog is accepted, the tests list is refreshed.
        """
        tag = self.get_selected_test_tag()
        if tag is None:
            QMessageBox.warning(self, "Warning", "Please select a test to edit")
            return
        
        try:
            test = self.test_manager.get_test(tag)
            
            dialog = None
            test_type = test.test_type.lower()
            
            if test_type == "normunbalance":
                dialog = NormUnbalanceTestEditDialog(test, self)
            elif test_type == "normdispincr":
                dialog = NormDispIncrTestEditDialog(test, self)
            elif test_type == "energyincr":
                dialog = EnergyIncrTestEditDialog(test, self)
            elif test_type == "relativenormunbalance":
                dialog = RelativeNormUnbalanceTestEditDialog(test, self)
            elif test_type == "relativenormdispincr":
                dialog = RelativeNormDispIncrTestEditDialog(test, self)
            elif test_type == "relativetotalnormdispincr":
                dialog = RelativeTotalNormDispIncrTestEditDialog(test, self)
            elif test_type == "relativeenergyincr":
                dialog = RelativeEnergyIncrTestEditDialog(test, self)
            elif test_type == "fixednumiter":
                dialog = FixedNumIterTestEditDialog(test, self)
            elif test_type == "normdispandunbalance":
                dialog = NormDispAndUnbalanceTestEditDialog(test, self)
            elif test_type == "normdisporunbalance":
                dialog = NormDispOrUnbalanceTestEditDialog(test, self)
            else:
                QMessageBox.warning(self, "Error", f"No edit dialog available for test type: {test_type}")
                return
            
            if dialog.exec() == QDialog.Accepted:
                self.refresh_tests_list()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_selected_test(self):
        """Deletes the test currently selected in the table.

        A warning message is displayed if no test is selected.
        """
        tag = self.get_selected_test_tag()
        if tag is None:
            QMessageBox.warning(self, "Warning", "Please select a test to delete")
            return
        
        self.delete_test(tag)

    def delete_test(self, tag: int):
        """Deletes a specific convergence test from the test manager.

        A confirmation dialog is presented to the user before proceeding with
        the deletion. The tests list is refreshed after deletion.

        Args:
            tag: The unique integer tag of the test to be deleted.
        """
        reply = QMessageBox.question(
            self, 'Delete Test',
            f"Are you sure you want to delete test with tag {tag}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.test_manager.remove_test(tag)
            self.refresh_tests_list()

#------------------------------------------------------
# Base Test Dialog Classes
#------------------------------------------------------

class BaseTestDialog(QDialog):
    """Base dialog for creating and editing convergence tests with common fields.

    This abstract base class provides the foundational structure and shared
    UI elements for all specific test creation and editing dialogs, including
    a parameters group box and standard Save/Cancel buttons.

    Attributes:
        test_manager (TestManager): An instance of the test manager for
            interacting with backend test logic.
        layout (QVBoxLayout): The main vertical layout of the dialog.
        params_group (QGroupBox): Group box to contain test-specific parameters.
        params_layout (QFormLayout): Form layout within `params_group` for
            arranging parameter input widgets.
        btn_layout (QHBoxLayout): Horizontal layout for the Save and Cancel buttons.
        save_btn (QPushButton): Button to trigger the saving of test parameters.
        cancel_btn (QPushButton): Button to close the dialog without saving.
    """
    def __init__(self, parent: QWidget = None, title: str = "Test Dialog"):
        """Initializes the BaseTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
            title: The title to display in the dialog's window bar.
                Defaults to "Test Dialog".
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.test_manager = TestManager()
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Parameters group
        self.params_group = QGroupBox("Parameters")
        self.params_layout = QFormLayout(self.params_group)
        self.layout.addWidget(self.params_group)
        
        # Buttons
        self.btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_test)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.btn_layout.addWidget(self.save_btn)
        self.btn_layout.addWidget(self.cancel_btn)
        
        # Add button layout at the end after subclass adds its fields
    
    def add_button_layout(self):
        """Adds the standard button layout (Save/Cancel) to the main dialog layout.

        This method should be called by subclasses after all test-specific
        parameter fields have been added to ensure buttons appear at the bottom.
        """
        self.layout.addLayout(self.btn_layout)
    
    def save_test(self):
        """Placeholder method for saving test parameters.

        This method must be implemented by subclasses to define how the
        specific test's parameters are gathered and saved or updated.
        """
        pass


class BaseNormTestDialog(BaseTestDialog):
    """Base dialog for tests that utilize common norm-based convergence parameters.

    This class extends `BaseTestDialog` by adding standard input fields for
    tolerance, maximum iterations, print flag, and norm type. It is designed
    for convergence tests that evaluate a norm against a specified tolerance.

    Attributes:
        tol_spin (QDoubleSpinBox): Input field for the convergence tolerance.
        max_iter_spin (QSpinBox): Input field for the maximum number of
            iterations allowed.
        print_flag_combo (QComboBox): Dropdown for selecting the print verbosity
            level.
        norm_type_combo (QComboBox): Dropdown for selecting the type of norm
            (e.g., Max-norm, 1-norm, 2-norm).
    """
    def __init__(self, parent: QWidget = None, title: str = "Norm Test Dialog"):
        """Initializes the BaseNormTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
            title: The title to display in the dialog's window bar.
                Defaults to "Norm Test Dialog".
        """
        super().__init__(parent, title)
        
        # Tolerance parameter
        self.tol_spin = QDoubleSpinBox()
        self.tol_spin.setDecimals(6)
        self.tol_spin.setRange(1e-12, 1.0)
        self.tol_spin.setValue(1e-6)
        self.params_layout.addRow("Tolerance:", self.tol_spin)
        
        # Max iterations parameter
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(1, 1000)
        self.max_iter_spin.setValue(25)
        self.params_layout.addRow("Max Iterations:", self.max_iter_spin)
        
        # Print flag parameter
        self.print_flag_combo = QComboBox()
        self.print_flag_combo.addItems([
            "0: Print nothing",
            "1: Print norm information each iteration",
            "2: Print norms and iterations at successful test",
            "4: Print norms, displacement vector, and residual vector",
            "5: Print error message but return successful test"
        ])
        self.params_layout.addRow("Print Flag:", self.print_flag_combo)
        
        # Norm type parameter
        self.norm_type_combo = QComboBox()
        self.norm_type_combo.addItems([
            "0: Max-norm",
            "1: 1-norm",
            "2: 2-norm (default)"
        ])
        self.norm_type_combo.setCurrentIndex(2)  # Set default to 2-norm
        self.params_layout.addRow("Norm Type:", self.norm_type_combo)
        
        # Add button layout
        self.add_button_layout()
    
    def get_params(self) -> dict:
        """Retrieves the common norm-based parameters from the dialog's input fields.

        Returns:
            dict: A dictionary containing the 'tol', 'max_iter', 'print_flag',
                and 'norm_type' values.
        """
        tol = self.tol_spin.value()
        max_iter = self.max_iter_spin.value()
        print_flag = int(self.print_flag_combo.currentText().split(":")[0])
        norm_type = int(self.norm_type_combo.currentText().split(":")[0])
        
        return {
            "tol": tol,
            "max_iter": max_iter,
            "print_flag": print_flag,
            "norm_type": norm_type
        }


class BaseEnergyTestDialog(BaseTestDialog):
    """Base dialog for tests that utilize energy-based convergence parameters.

    This class extends `BaseTestDialog` by adding standard input fields for
    tolerance, maximum iterations, and a print flag, tailored for energy-based
    convergence criteria.

    Attributes:
        tol_spin (QDoubleSpinBox): Input field for the energy convergence tolerance.
        max_iter_spin (QSpinBox): Input field for the maximum number of
            iterations allowed.
        print_flag_combo (QComboBox): Dropdown for selecting the print verbosity
            level.
    """
    def __init__(self, parent: QWidget = None, title: str = "Energy Test Dialog"):
        """Initializes the BaseEnergyTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
            title: The title to display in the dialog's window bar.
                Defaults to "Energy Test Dialog".
        """
        super().__init__(parent, title)
        
        # Tolerance parameter
        self.tol_spin = QDoubleSpinBox()
        self.tol_spin.setDecimals(6)
        self.tol_spin.setRange(1e-12, 1.0)
        self.tol_spin.setValue(1e-6)
        self.params_layout.addRow("Tolerance:", self.tol_spin)
        
        # Max iterations parameter
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(1, 1000)
        self.max_iter_spin.setValue(25)
        self.params_layout.addRow("Max Iterations:", self.max_iter_spin)
        
        # Print flag parameter
        self.print_flag_combo = QComboBox()
        self.print_flag_combo.addItems([
            "0: Print nothing",
            "1: Print norm information each iteration",
            "2: Print norms and iterations at successful test",
            "4: Print norms, displacement vector, and residual vector",
            "5: Print error message but return successful test"
        ])
        self.params_layout.addRow("Print Flag:", self.print_flag_combo)
        
        # Add button layout
        self.add_button_layout()
    
    def get_params(self) -> dict:
        """Retrieves the common energy-based parameters from the dialog's input fields.

        Returns:
            dict: A dictionary containing the 'tol', 'max_iter', and 'print_flag' values.
        """
        tol = self.tol_spin.value()
        max_iter = self.max_iter_spin.value()
        print_flag = int(self.print_flag_combo.currentText().split(":")[0])
        
        return {
            "tol": tol,
            "max_iter": max_iter,
            "print_flag": print_flag
        }


class BaseCombinedNormTestDialog(BaseTestDialog):
    """Base dialog for convergence tests that involve two separate tolerances.

    This class extends `BaseTestDialog` to provide input fields for
    displacement tolerance, residual tolerance, maximum iterations, print flag,
    norm type, and maximum error increase. It's suitable for tests
    that evaluate multiple convergence criteria simultaneously.

    Attributes:
        tol_incr_spin (QDoubleSpinBox): Input for the displacement increment
            tolerance.
        tol_r_spin (QDoubleSpinBox): Input for the residual (unbalanced force)
            tolerance.
        max_iter_spin (QSpinBox): Input for the maximum number of iterations.
        print_flag_combo (QComboBox): Dropdown for selecting print verbosity.
        norm_type_combo (QComboBox): Dropdown for selecting the type of norm.
        max_incr_spin (QSpinBox): Input for the maximum allowed error increase.
    """
    def __init__(self, parent: QWidget = None, title: str = "Combined Norm Test Dialog"):
        """Initializes the BaseCombinedNormTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
            title: The title to display in the dialog's window bar.
                Defaults to "Combined Norm Test Dialog".
        """
        super().__init__(parent, title)
        
        # Displacement tolerance parameter
        self.tol_incr_spin = QDoubleSpinBox()
        self.tol_incr_spin.setDecimals(6)
        self.tol_incr_spin.setRange(1e-12, 1.0)
        self.tol_incr_spin.setValue(1e-6)
        self.params_layout.addRow("Displacement Tolerance:", self.tol_incr_spin)
        
        # Residual tolerance parameter
        self.tol_r_spin = QDoubleSpinBox()
        self.tol_r_spin.setDecimals(6)
        self.tol_r_spin.setRange(1e-12, 1.0)
        self.tol_r_spin.setValue(1e-6)
        self.params_layout.addRow("Residual Tolerance:", self.tol_r_spin)
        
        # Max iterations parameter
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(1, 1000)
        self.max_iter_spin.setValue(25)
        self.params_layout.addRow("Max Iterations:", self.max_iter_spin)
        
        # Print flag parameter
        self.print_flag_combo = QComboBox()
        self.print_flag_combo.addItems([
            "0: Print nothing",
            "1: Print norm information each iteration",
            "2: Print norms and iterations at successful test",
            "4: Print norms, displacement vector, and residual vector",
            "5: Print error message but return successful test"
        ])
        self.params_layout.addRow("Print Flag:", self.print_flag_combo)
        
        # Norm type parameter
        self.norm_type_combo = QComboBox()
        self.norm_type_combo.addItems([
            "0: Max-norm",
            "1: 1-norm",
            "2: 2-norm (default)"
        ])
        self.norm_type_combo.setCurrentIndex(2)  # Set default to 2-norm
        self.params_layout.addRow("Norm Type:", self.norm_type_combo)
        
        # Max increment parameter
        self.max_incr_spin = QSpinBox()
        self.max_incr_spin.setRange(-1, 1000)
        self.max_incr_spin.setValue(-1)
        self.params_layout.addRow("Max Error Increase (-1 for default):", self.max_incr_spin)
        
        # Add button layout
        self.add_button_layout()
    
    def get_params(self) -> dict:
        """Retrieves the common combined norm parameters from the dialog's input fields.

        Returns:
            dict: A dictionary containing 'tol_incr', 'tol_r', 'max_iter',
                'print_flag', 'norm_type', and 'max_incr' values.
        """
        tol_incr = self.tol_incr_spin.value()
        tol_r = self.tol_r_spin.value()
        max_iter = self.max_iter_spin.value()
        print_flag = int(self.print_flag_combo.currentText().split(":")[0])
        norm_type = int(self.norm_type_combo.currentText().split(":")[0])
        max_incr = self.max_incr_spin.value()
        
        return {
            "tol_incr": tol_incr,
            "tol_r": tol_r,
            "max_iter": max_iter,
            "print_flag": print_flag,
            "norm_type": norm_type,
            "max_incr": max_incr
        }


#------------------------------------------------------
# Test Dialog Classes - Creation
#------------------------------------------------------

class NormUnbalanceTestDialog(BaseNormTestDialog):
    """Dialog for creating a Norm Unbalance convergence test.

    This dialog provides a specialized interface for defining the parameters
    of a `NormUnbalanceTest`, including tolerance, max iterations, print flag,
    and norm type.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            NormUnbalance test.
        test (NormUnbalanceTest): The created `NormUnbalanceTest` instance
            after successful saving.

    Example:
        >>> from qtpy.QtWidgets import QApplication, QDialog
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> dialog = NormUnbalanceTestDialog()
        >>> if dialog.exec() == QDialog.Accepted:
        ...     print("Norm Unbalance Test Created (Tag:", dialog.test.tag, ")")
        >>> app.quit()
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the NormUnbalanceTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Norm Unbalance Test")
        
        # Additional info
        info = QLabel("The NormUnbalance test checks the norm of the right-hand side (unbalanced forces) vector "
                     "against a tolerance. Useful for checking overall system equilibrium.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new NormUnbalanceTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "normunbalance",
                tol=params["tol"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"],
                norm_type=params["norm_type"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class NormDispIncrTestDialog(BaseNormTestDialog):
    """Dialog for creating a Norm Displacement Increment convergence test.

    This dialog provides a specialized interface for defining the parameters
    of a `NormDispIncrTest`, including tolerance, max iterations, print flag,
    and norm type.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            NormDispIncr test.
        test (NormDispIncrTest): The created `NormDispIncrTest` instance
            after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the NormDispIncrTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Norm Displacement Increment Test")
        
        # Additional info
        info = QLabel("The NormDispIncr test checks the norm of the displacement increment vector "
                     "against a tolerance. Useful for tracking solution convergence.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new NormDispIncrTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "normdispincr",
                tol=params["tol"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"],
                norm_type=params["norm_type"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class EnergyIncrTestDialog(BaseEnergyTestDialog):
    """Dialog for creating an Energy Increment convergence test.

    This dialog provides a specialized interface for defining the parameters
    of an `EnergyIncrTest`, including tolerance, max iterations, and print flag.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            EnergyIncr test.
        test (EnergyIncrTest): The created `EnergyIncrTest` instance
            after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the EnergyIncrTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Energy Increment Test")
        
        # Additional info
        info = QLabel("The EnergyIncr test checks the energy increment (0.5 * x^T * b) against a tolerance. "
                     "Useful for problems with energy-critical behaviors.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new EnergyIncrTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "energyincr",
                tol=params["tol"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class RelativeNormUnbalanceTestDialog(BaseNormTestDialog):
    """Dialog for creating a Relative Norm Unbalance convergence test.

    This dialog provides a specialized interface for defining the parameters
    of a `RelativeNormUnbalanceTest`, including tolerance, max iterations,
    print flag, and norm type.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            RelativeNormUnbalance test.
        test (RelativeNormUnbalanceTest): The created `RelativeNormUnbalanceTest`
            instance after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the RelativeNormUnbalanceTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Relative Norm Unbalance Test")
        
        # Additional info
        info = QLabel("The RelativeNormUnbalance test compares current unbalance to initial unbalance. "
                     "Requires at least two iterations and can be sensitive to initial conditions.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new RelativeNormUnbalanceTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "relativenormunbalance",
                tol=params["tol"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"],
                norm_type=params["norm_type"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class RelativeNormDispIncrTestDialog(BaseNormTestDialog):
    """Dialog for creating a Relative Norm Displacement Increment convergence test.

    This dialog provides a specialized interface for defining the parameters
    of a `RelativeNormDispIncrTest`, including tolerance, max iterations,
    print flag, and norm type.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            RelativeNormDispIncr test.
        test (RelativeNormDispIncrTest): The created `RelativeNormDispIncrTest`
            instance after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the RelativeNormDispIncrTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Relative Norm Displacement Increment Test")
        
        # Additional info
        info = QLabel("The RelativeNormDispIncr test compares current displacement increment to initial. "
                     "Tracks relative changes in displacement.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new RelativeNormDispIncrTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "relativenormdispincr",
                tol=params["tol"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"],
                norm_type=params["norm_type"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class RelativeTotalNormDispIncrTestDialog(BaseNormTestDialog):
    """Dialog for creating a Relative Total Norm Displacement Increment convergence test.

    This dialog provides a specialized interface for defining the parameters
    of a `RelativeTotalNormDispIncrTest`, including tolerance, max iterations,
    print flag, and norm type.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            RelativeTotalNormDispIncr test.
        test (RelativeTotalNormDispIncrTest): The created
            `RelativeTotalNormDispIncrTest` instance after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the RelativeTotalNormDispIncrTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Relative Total Norm Displacement Increment Test")
        
        # Additional info
        info = QLabel("The RelativeTotalNormDispIncr test uses ratio of current norm to total norm "
                     "(sum of norms since last convergence). Tracks cumulative displacement changes.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new RelativeTotalNormDispIncrTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "relativetotalnormdispincr",
                tol=params["tol"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"],
                norm_type=params["norm_type"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class RelativeEnergyIncrTestDialog(BaseEnergyTestDialog):
    """Dialog for creating a Relative Energy Increment convergence test.

    This dialog provides a specialized interface for defining the parameters
    of a `RelativeEnergyIncrTest`, including tolerance, max iterations,
    and print flag.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            RelativeEnergyIncr test.
        test (RelativeEnergyIncrTest): The created `RelativeEnergyIncrTest`
            instance after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the RelativeEnergyIncrTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Relative Energy Increment Test")
        
        # Additional info
        info = QLabel("The RelativeEnergyIncr test compares energy increment relative to first iteration. "
                     "Provides energy-based relative convergence assessment.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new RelativeEnergyIncrTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "relativeenergyincr",
                tol=params["tol"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class FixedNumIterTestDialog(BaseTestDialog):
    """Dialog for creating a Fixed Number of Iterations convergence test.

    This dialog allows users to specify the exact number of iterations
    for a `FixedNumIterTest`, which runs without convergence checks.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            FixedNumIter test.
        num_iter_spin (QSpinBox): Input field for the fixed number of iterations.
        test (FixedNumIterTest): The created `FixedNumIterTest` instance
            after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the FixedNumIterTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Fixed Number of Iterations Test")
        
        # Additional info
        info = QLabel("The FixedNumIter test runs a fixed number of iterations with no convergence check. "
                     "Useful for specific analytical requirements.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
        
        # Number of iterations parameter
        self.num_iter_spin = QSpinBox()
        self.num_iter_spin.setRange(1, 1000)
        self.num_iter_spin.setValue(10)
        self.params_layout.addRow("Number of Iterations:", self.num_iter_spin)
        
        # Add button layout
        self.add_button_layout()
    
    def save_test(self):
        """Creates and registers a new FixedNumIterTest with the `TestManager`.

        Retrieves the number of iterations from the dialog's input field and
        uses it to instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            # Create test
            self.test = self.test_manager.create_test(
                "fixednumiter",
                num_iter=self.num_iter_spin.value()
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class NormDispAndUnbalanceTestDialog(BaseCombinedNormTestDialog):
    """Dialog for creating a Norm Displacement AND Unbalance convergence test.

    This dialog provides a specialized interface for defining the parameters
    of a `NormDispAndUnbalanceTest`, which checks both displacement increment
    and unbalanced force norms.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            NormDispAndUnbalance test.
        test (NormDispAndUnbalanceTest): The created `NormDispAndUnbalanceTest`
            instance after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the NormDispAndUnbalanceTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Norm Displacement AND Unbalance Test")
        
        # Additional info
        info = QLabel("The NormDispAndUnbalance test simultaneously checks displacement increment and unbalanced force norms. "
                      "Requires BOTH displacement and unbalance norms to converge.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new NormDispAndUnbalanceTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "normdispandunbalance",
                tol_incr=params["tol_incr"],
                tol_r=params["tol_r"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"],
                norm_type=params["norm_type"],
                max_incr=params["max_incr"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class NormDispOrUnbalanceTestDialog(BaseCombinedNormTestDialog):
    """Dialog for creating a Norm Displacement OR Unbalance convergence test.

    This dialog provides a specialized interface for defining the parameters
    of a `NormDispOrUnbalanceTest`, which checks either displacement increment
    or unbalanced force norms for convergence.

    Attributes:
        info (QLabel): A label displaying a descriptive summary of the
            NormDispOrUnbalance test.
        test (NormDispOrUnbalanceTest): The created `NormDispOrUnbalanceTest`
            instance after successful saving.
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the NormDispOrUnbalanceTestDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Create Norm Displacement OR Unbalance Test")
        
        # Additional info
        info = QLabel("The NormDispOrUnbalance test checks displacement increment or unbalanced force norms. "
                      "Convergence achieved if EITHER displacement OR unbalance norm criterion is met.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Creates and registers a new NormDispOrUnbalanceTest with the `TestManager`.

        Retrieves parameters from the dialog's input fields and uses them to
        instantiate and save a new test.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test creation or parameter retrieval.
        """
        try:
            params = self.get_params()
            
            # Create test
            self.test = self.test_manager.create_test(
                "normdisporunbalance",
                tol_incr=params["tol_incr"],
                tol_r=params["tol_r"],
                max_iter=params["max_iter"],
                print_flag=params["print_flag"],
                norm_type=params["norm_type"],
                max_incr=params["max_incr"]
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


#------------------------------------------------------
# Test Dialog Classes - Editing Existing Tests
#------------------------------------------------------

class NormUnbalanceTestEditDialog(BaseNormTestDialog):
    """Dialog for editing an existing Norm Unbalance convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `NormUnbalanceTest` and allows the user to modify and save them.

    Attributes:
        test (NormUnbalanceTest): The existing `NormUnbalanceTest` instance
            being edited.
        info (QLabel): A label displaying a descriptive summary of the
            NormUnbalance test.
    """
    def __init__(self, test: NormUnbalanceTest, parent: QWidget = None):
        """Initializes the NormUnbalanceTestEditDialog.

        Args:
            test: The `NormUnbalanceTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Norm Unbalance Test")
        self.test = test
        
        # Fill in existing values
        self.tol_spin.setValue(test.tol)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        self.norm_type_combo.setCurrentIndex(min(test.norm_type, self.norm_type_combo.count()-1))
        
        # Additional info
        info = QLabel("The NormUnbalance test checks the norm of the right-hand side (unbalanced forces) vector "
                     "against a tolerance. Useful for checking overall system equilibrium.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing NormUnbalanceTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol = params["tol"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            self.test.norm_type = params["norm_type"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class NormDispIncrTestEditDialog(BaseNormTestDialog):
    """Dialog for editing an existing Norm Displacement Increment convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `NormDispIncrTest` and allows the user to modify and save them.

    Attributes:
        test (NormDispIncrTest): The existing `NormDispIncrTest` instance
            being edited.
        info (QLabel): A label displaying a descriptive summary of the
            NormDispIncr test.
    """
    def __init__(self, test: NormDispIncrTest, parent: QWidget = None):
        """Initializes the NormDispIncrTestEditDialog.

        Args:
            test: The `NormDispIncrTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Norm Displacement Increment Test")
        self.test = test
        
        # Fill in existing values
        self.tol_spin.setValue(test.tol)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        self.norm_type_combo.setCurrentIndex(min(test.norm_type, self.norm_type_combo.count()-1))
        
        # Additional info
        info = QLabel("The NormDispIncr test checks the norm of the displacement increment vector "
                     "against a tolerance. Useful for tracking solution convergence.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing NormDispIncrTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol = params["tol"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            self.test.norm_type = params["norm_type"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class EnergyIncrTestEditDialog(BaseEnergyTestDialog):
    """Dialog for editing an existing Energy Increment convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `EnergyIncrTest` and allows the user to modify and save them.

    Attributes:
        test (EnergyIncrTest): The existing `EnergyIncrTest` instance
            being edited.
        info (QLabel): A label displaying a descriptive summary of the
            EnergyIncr test.
    """
    def __init__(self, test: EnergyIncrTest, parent: QWidget = None):
        """Initializes the EnergyIncrTestEditDialog.

        Args:
            test: The `EnergyIncrTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Energy Increment Test")
        self.test = test
        
        # Fill in existing values
        self.tol_spin.setValue(test.tol)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        
        # Additional info
        info = QLabel("The EnergyIncr test checks the energy increment (0.5 * x^T * b) against a tolerance. "
                     "Useful for problems with energy-critical behaviors.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing EnergyIncrTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol = params["tol"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class RelativeNormUnbalanceTestEditDialog(BaseNormTestDialog):
    """Dialog for editing an existing Relative Norm Unbalance convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `RelativeNormUnbalanceTest` and allows the user to modify and save them.

    Attributes:
        test (RelativeNormUnbalanceTest): The existing `RelativeNormUnbalanceTest`
            instance being edited.
        info (QLabel): A label displaying a descriptive summary of the
            RelativeNormUnbalance test.
    """
    def __init__(self, test: RelativeNormUnbalanceTest, parent: QWidget = None):
        """Initializes the RelativeNormUnbalanceTestEditDialog.

        Args:
            test: The `RelativeNormUnbalanceTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Relative Norm Unbalance Test")
        self.test = test
        
        # Fill in existing values
        self.tol_spin.setValue(test.tol)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        self.norm_type_combo.setCurrentIndex(min(test.norm_type, self.norm_type_combo.count()-1))
        
        # Additional info
        info = QLabel("The RelativeNormUnbalance test compares current unbalance to initial unbalance. "
                     "Requires at least two iterations and can be sensitive to initial conditions.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing RelativeNormUnbalanceTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol = params["tol"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            self.test.norm_type = params["norm_type"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class RelativeNormDispIncrTestEditDialog(BaseNormTestDialog):
    """Dialog for editing an existing Relative Norm Displacement Increment convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `RelativeNormDispIncrTest` and allows the user to modify and save them.

    Attributes:
        test (RelativeNormDispIncrTest): The existing `RelativeNormDispIncrTest`
            instance being edited.
        info (QLabel): A label displaying a descriptive summary of the
            RelativeNormDispIncr test.
    """
    def __init__(self, test: RelativeNormDispIncrTest, parent: QWidget = None):
        """Initializes the RelativeNormDispIncrTestEditDialog.

        Args:
            test: The `RelativeNormDispIncrTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Relative Norm Displacement Increment Test")
        self.test = test
        
        # Fill in existing values
        self.tol_spin.setValue(test.tol)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        self.norm_type_combo.setCurrentIndex(min(test.norm_type, self.norm_type_combo.count()-1))
        
        # Additional info
        info = QLabel("The RelativeNormDispIncr test compares current displacement increment to initial. "
                     "Tracks relative changes in displacement.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing RelativeNormDispIncrTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol = params["tol"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            self.test.norm_type = params["norm_type"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class RelativeTotalNormDispIncrTestEditDialog(BaseNormTestDialog):
    """Dialog for editing an existing Relative Total Norm Displacement Increment convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `RelativeTotalNormDispIncrTest` and allows the user to modify and save them.

    Attributes:
        test (RelativeTotalNormDispIncrTest): The existing
            `RelativeTotalNormDispIncrTest` instance being edited.
        info (QLabel): A label displaying a descriptive summary of the
            RelativeTotalNormDispIncr test.
    """
    def __init__(self, test: RelativeTotalNormDispIncrTest, parent: QWidget = None):
        """Initializes the RelativeTotalNormDispIncrTestEditDialog.

        Args:
            test: The `RelativeTotalNormDispIncrTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Relative Total Norm Displacement Increment Test")
        self.test = test
        
        # Fill in existing values
        self.tol_spin.setValue(test.tol)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        self.norm_type_combo.setCurrentIndex(min(test.norm_type, self.norm_type_combo.count()-1))
        
        # Additional info
        info = QLabel("The RelativeTotalNormDispIncr test uses ratio of current norm to total norm "
                     "(sum of norms since last convergence). Tracks cumulative displacement changes.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing RelativeTotalNormDispIncrTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol = params["tol"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            self.test.norm_type = params["norm_type"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class RelativeEnergyIncrTestEditDialog(BaseEnergyTestDialog):
    """Dialog for editing an existing Relative Energy Increment convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `RelativeEnergyIncrTest` and allows the user to modify and save them.

    Attributes:
        test (RelativeEnergyIncrTest): The existing `RelativeEnergyIncrTest`
            instance being edited.
        info (QLabel): A label displaying a descriptive summary of the
            RelativeEnergyIncr test.
    """
    def __init__(self, test: RelativeEnergyIncrTest, parent: QWidget = None):
        """Initializes the RelativeEnergyIncrTestEditDialog.

        Args:
            test: The `RelativeEnergyIncrTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Relative Energy Increment Test")
        self.test = test
        
        # Fill in existing values
        self.tol_spin.setValue(test.tol)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        
        # Additional info
        info = QLabel("The RelativeEnergyIncr test compares energy increment relative to first iteration. "
                     "Provides energy-based relative convergence assessment.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing RelativeEnergyIncrTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol = params["tol"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class FixedNumIterTestEditDialog(BaseTestDialog):
    """Dialog for editing an existing Fixed Number of Iterations convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `FixedNumIterTest` and allows the user to modify and save them.

    Attributes:
        test (FixedNumIterTest): The existing `FixedNumIterTest` instance
            being edited.
        info (QLabel): A label displaying a descriptive summary of the
            FixedNumIter test.
        num_iter_spin (QSpinBox): Input field for the fixed number of iterations.
    """
    def __init__(self, test: FixedNumIterTest, parent: QWidget = None):
        """Initializes the FixedNumIterTestEditDialog.

        Args:
            test: The `FixedNumIterTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Fixed Number of Iterations Test")
        self.test = test
        
        # Number of iterations parameter
        self.num_iter_spin = QSpinBox()
        self.num_iter_spin.setRange(1, 1000)
        self.num_iter_spin.setValue(test.num_iter)
        self.params_layout.addRow("Number of Iterations:", self.num_iter_spin)
        
        # Additional info
        info = QLabel("The FixedNumIter test runs a fixed number of iterations with no convergence check. "
                     "Useful for specific analytical requirements.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
        
        # Add button layout
        self.add_button_layout()
    
    def save_test(self):
        """Updates the parameters of the existing FixedNumIterTest.

        Retrieves the updated number of iterations from the dialog's input field
        and applies it to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            # Update test parameters
            self.test.num_iter = self.num_iter_spin.value()
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class NormDispAndUnbalanceTestEditDialog(BaseCombinedNormTestDialog):
    """Dialog for editing an existing Norm Displacement AND Unbalance convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `NormDispAndUnbalanceTest` and allows the user to modify and save them.

    Attributes:
        test (NormDispAndUnbalanceTest): The existing `NormDispAndUnbalanceTest`
            instance being edited.
        info (QLabel): A label displaying a descriptive summary of the
            NormDispAndUnbalance test.
    """
    def __init__(self, test: NormDispAndUnbalanceTest, parent: QWidget = None):
        """Initializes the NormDispAndUnbalanceTestEditDialog.

        Args:
            test: The `NormDispAndUnbalanceTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Norm Displacement AND Unbalance Test")
        self.test = test
        
        # Fill in existing values
        self.tol_incr_spin.setValue(test.tol_incr)
        self.tol_r_spin.setValue(test.tol_r)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        self.norm_type_combo.setCurrentIndex(min(test.norm_type, self.norm_type_combo.count()-1))
        self.max_incr_spin.setValue(test.max_incr)
        
        # Additional info
        info = QLabel("The NormDispAndUnbalance test simultaneously checks displacement increment and unbalanced force norms. "
                      "Requires BOTH displacement and unbalance norms to converge.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing NormDispAndUnbalanceTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol_incr = params["tol_incr"]
            self.test.tol_r = params["tol_r"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            self.test.norm_type = params["norm_type"]
            self.test.max_incr = params["max_incr"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class NormDispOrUnbalanceTestEditDialog(BaseCombinedNormTestDialog):
    """Dialog for editing an existing Norm Displacement OR Unbalance convergence test.

    This dialog pre-populates its fields with the parameters of an existing
    `NormDispOrUnbalanceTest` and allows the user to modify and save them.

    Attributes:
        test (NormDispOrUnbalanceTest): The existing `NormDispOrUnbalanceTest`
            instance being edited.
        info (QLabel): A label displaying a descriptive summary of the
            NormDispOrUnbalance test.
    """
    def __init__(self, test: NormDispOrUnbalanceTest, parent: QWidget = None):
        """Initializes the NormDispOrUnbalanceTestEditDialog.

        Args:
            test: The `NormDispOrUnbalanceTest` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent, "Edit Norm Displacement OR Unbalance Test")
        self.test = test
        
        # Fill in existing values
        self.tol_incr_spin.setValue(test.tol_incr)
        self.tol_r_spin.setValue(test.tol_r)
        self.max_iter_spin.setValue(test.max_iter)
        self.print_flag_combo.setCurrentIndex(min(test.print_flag, self.print_flag_combo.count()-1))
        self.norm_type_combo.setCurrentIndex(min(test.norm_type, self.norm_type_combo.count()-1))
        self.max_incr_spin.setValue(test.max_incr)
        
        # Additional info
        info = QLabel("The NormDispOrUnbalance test checks displacement increment or unbalanced force norms. "
                      "Convergence achieved if EITHER displacement OR unbalance norm criterion is met.")
        info.setWordWrap(True)
        self.layout.insertWidget(1, info)
    
    def save_test(self):
        """Updates the parameters of the existing NormDispOrUnbalanceTest.

        Retrieves updated parameters from the dialog's input fields and
        applies them to the `test` instance.

        Returns:
            None: The dialog accepts (closes with `QDialog.Accepted`) on success.

        Raises:
            Exception: If an error occurs during test parameter update or retrieval.
        """
        try:
            params = self.get_params()
            
            # Update test parameters
            self.test.tol_incr = params["tol_incr"]
            self.test.tol_r = params["tol_r"]
            self.test.max_iter = params["max_iter"]
            self.test.print_flag = params["print_flag"]
            self.test.norm_type = params["norm_type"]
            self.test.max_incr = params["max_incr"]
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = TestManagerTab()
    window.show()
    sys.exit(app.exec_())
    
    sys.exit(app.exec_())