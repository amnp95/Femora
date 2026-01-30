from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout, QMenu,
    QSizePolicy, QProgressDialog, QApplication, QSpinBox, QDoubleSpinBox
)
from femora.components.Constraint.mpConstraint import (
    mpConstraint, equalDOF, rigidLink, rigidDiaphragm, mpConstraintManager
)
import time

class MPConstraintManagerTab(QDialog):
    """Manages the creation, viewing, editing, and deletion of multipoint constraints (MPCs).

    This dialog provides a comprehensive interface to interact with Femora's
    `mpConstraintManager`, displaying constraints in a paginated table and
    allowing various operations.

    Attributes:
        constraint_type_combo (QComboBox): Dropdown to select the type of
            constraint to create (e.g., equalDOF, rigidLink).
        status_label (QLabel): Displays status information, such as total
            number of constraints and current page.
        constraints_table (QTableWidget): Table displaying the list of
            multipoint constraints.
        page_size_combo (QComboBox): Dropdown to select the number of items
            to display per page.
        page_spinbox (QSpinBox): Navigates directly to a specific page number.
        page_label (QLabel): Shows the total number of pages.
        current_page (int): The currently displayed page number.
        total_pages (int): The total number of pages available for constraints.
        page_size (int): The number of constraints displayed per page.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> from femora.components.Constraint.mpConstraint import mpConstraintManager
        >>> app = QApplication(sys.argv)
        >>> mp_manager = mpConstraintManager()
        >>> mp_manager.create_equal_dof(master_node=1, slave_nodes=[2, 3], dofs=[1, 2, 3])
        >>> manager_tab = MPConstraintManagerTab()
        >>> manager_tab.show()
        >>> # app.exec() # Uncomment to run the Qt event loop
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the MPConstraintManagerTab dialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        
        # Configure dialog size and properties
        self.setWindowTitle("MP Constraints Manager")
        self.resize(800, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Constraint type selection
        type_layout = QGridLayout()
        
        # Constraint type dropdown
        self.constraint_type_combo = QComboBox()
        self.constraint_type_combo.addItems(["equalDOF", "rigidLink", "rigidDiaphragm", "laminarBoundary"])
        
        create_constraint_btn = QPushButton("Create New Constraint")
        create_constraint_btn.clicked.connect(self.open_constraint_creation_dialog)
        
        type_layout.addWidget(QLabel("Constraint Type:"), 0, 0)
        type_layout.addWidget(self.constraint_type_combo, 0, 1)
        type_layout.addWidget(create_constraint_btn, 1, 0, 1, 2)
        
        layout.addLayout(type_layout)
        
        # Status information showing total constraints
        self.status_label = QLabel("Loading constraints...")
        layout.addWidget(self.status_label)
        
        # Constraints table
        self.constraints_table = QTableWidget()
        self.constraints_table.setColumnCount(5)  # Tag, Type, Master, Slaves, Parameters
        self.constraints_table.setHorizontalHeaderLabels(["Tag", "Type", "Master", "Slaves", "Parameters"])
        
        # Configure table appearance
        self.constraints_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.constraints_table.setMinimumWidth(750)
        self.constraints_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set horizontal header properties
        header = self.constraints_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Set default column widths
        self.constraints_table.setColumnWidth(0, 60)   # Tag column
        self.constraints_table.setColumnWidth(1, 120)  # Type column
        self.constraints_table.setColumnWidth(2, 100)  # Master column
        self.constraints_table.setColumnWidth(3, 200)  # Slaves column
        
        # Configure double-click and context menu
        self.constraints_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.constraints_table.customContextMenuRequested.connect(self.show_context_menu)
        self.constraints_table.cellDoubleClicked.connect(self.handle_double_click)
        
        layout.addWidget(self.constraints_table)
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        
        # Page size selection
        pagination_layout.addWidget(QLabel("Items per page:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["100", "500", "1000", "All"])
        self.page_size_combo.setCurrentText("100")
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        pagination_layout.addWidget(self.page_size_combo)
        
        # Page navigation with spinbox
        pagination_layout.addStretch()
        pagination_layout.addWidget(QLabel("Go to page:"))
        
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)  # Will be updated with total pages
        self.page_spinbox.setValue(1)
        self.page_spinbox.valueChanged.connect(self.go_to_page)
        pagination_layout.addWidget(self.page_spinbox)
        
        self.page_label = QLabel("of 1")
        pagination_layout.addWidget(self.page_label)
        
        layout.addLayout(pagination_layout)
        
        button_layout = QVBoxLayout()
        # Refresh button
        refresh_btn = QPushButton("Refresh Constraints List")
        refresh_btn.clicked.connect(self.refresh_constraints_list)
        
        # Add Clear All button
        button_layout.addWidget(refresh_btn)
        # Clear All button with warning color styling
        clear_all_btn = QPushButton("Clear All Constraints")
        clear_all_btn.clicked.connect(self.clear_all_constraints)
        button_layout.addWidget(clear_all_btn)
        
        layout.addLayout(button_layout)
        
        # Pagination state
        self.current_page = 1
        self.total_pages = 1
        self.page_size = 100
        
        # Initial refresh
        self.refresh_constraints_list()

    def change_page_size(self, size_text: str):
        """Changes the number of items displayed per page.

        Resets the current page to 1 and refreshes the constraint list.
        If `size_text` is "All", the page size is set to the total number
        of constraints.

        Args:
            size_text: The string representing the desired page size (e.g., "100", "All").
        """
        if size_text == "All":
            self.page_size = len(mpConstraint._constraints)
        else:
            try:
                self.page_size = int(size_text)
            except ValueError:
                self.page_size = 100
        
        # Reset to first page and refresh
        self.current_page = 1
        self.refresh_constraints_list()

    def open_constraint_creation_dialog(self):
        """Opens a dialog to create a new multipoint constraint.

        The type of constraint dialog opened depends on the selection in
        `self.constraint_type_combo`. If the dialog is accepted, the
        constraint list is refreshed.

        Example:
            To open the dialog programmatically:
            >>> manager_tab = MPConstraintManagerTab()
            >>> manager_tab.constraint_type_combo.setCurrentText("equalDOF")
            >>> manager_tab.open_constraint_creation_dialog()
        """
        constraint_type = self.constraint_type_combo.currentText()
        
        if constraint_type == "laminarBoundary":
            dialog = MPLaminarBoundaryDialog(self)
        else:
            dialog = MPConstraintCreationDialog(constraint_type, self)
        
        if dialog.exec() == QDialog.Accepted:
            self.refresh_constraints_list()

    def refresh_constraints_list(self):
        """Updates the constraints table with current data for the current page.

        This method fetches all currently defined multipoint constraints,
        calculates pagination details, and populates the table with
        constraints relevant to the `current_page` and `page_size`.
        A progress dialog is shown for large constraint sets to maintain UI responsiveness.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> from femora.components.Constraint.mpConstraint import mpConstraintManager
            >>> app = QApplication(sys.argv)
            >>> mp_manager = mpConstraintManager()
            >>> mp_manager.create_equal_dof(master_node=1, slave_nodes=[2, 3], dofs=[1, 2, 3])
            >>> manager_tab = MPConstraintManagerTab()
            >>> manager_tab.refresh_constraints_list()
            >>> # This will populate the table.
        """
        # Show progress dialog for large constraint sets
        count = len(mpConstraint._constraints)
        
        if count > 1000:
            progress = QProgressDialog("Loading constraints...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()
        
        # Calculate total pages
        if self.page_size > 0:
            self.total_pages = max(1, (count + self.page_size - 1) // self.page_size)
        else:
            self.total_pages = 1
        
        # Ensure current page is valid
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        # Update page label
        self.page_label.setText(f"of {self.total_pages}")
        
        # Update page spinbox without triggering the valueChanged signal
        self.page_spinbox.blockSignals(True)
        self.page_spinbox.setMaximum(self.total_pages)
        self.page_spinbox.setValue(self.current_page)
        self.page_spinbox.blockSignals(False)
        
        # Clear the table
        self.constraints_table.setRowCount(0)
        
        # Get all constraints as a list for pagination
        all_constraints = list(mpConstraint._constraints.values())
        
        # Calculate start and end indices for the current page
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(all_constraints))
        
        # Get constraints for the current page
        page_constraints = all_constraints[start_idx:end_idx]
        
        # Set row count for the current page
        self.constraints_table.setRowCount(len(page_constraints))
        
        # Update progress to 20%
        if count > 1000:
            progress.setValue(20)
            QApplication.processEvents()
        
        # Process constraints in batches of 100 to maintain UI responsiveness
        batch_size = 100
        for batch_start in range(0, len(page_constraints), batch_size):
            batch_end = min(batch_start + batch_size, len(page_constraints))
            batch = page_constraints[batch_start:batch_end]
            
            for row, constraint in enumerate(batch, batch_start):
                # Tag
                tag_item = QTableWidgetItem(str(constraint.tag))
                tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
                tag_item.setData(Qt.UserRole, constraint.tag)  # Store tag for reference
                self.constraints_table.setItem(row, 0, tag_item)
                
                # Type
                type_item = QTableWidgetItem(constraint.__class__.__name__)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.constraints_table.setItem(row, 1, type_item)
                
                # Master Node
                master_item = QTableWidgetItem(str(constraint.master_node))
                master_item.setFlags(master_item.flags() & ~Qt.ItemIsEditable)
                self.constraints_table.setItem(row, 2, master_item)
                
                # Slave Nodes
                slaves_str = ", ".join(map(str, constraint.slave_nodes))
                slaves_item = QTableWidgetItem(slaves_str)
                slaves_item.setFlags(slaves_item.flags() & ~Qt.ItemIsEditable)
                self.constraints_table.setItem(row, 3, slaves_item)
                
                # Parameters
                params = ""
                if isinstance(constraint, equalDOF):
                    params = f"DOFs: {', '.join(map(str, constraint.dofs))}"
                elif isinstance(constraint, rigidLink):
                    params = f"Type: {constraint.type}"
                elif isinstance(constraint, rigidDiaphragm):
                    params = f"Direction: {constraint.direction}"
                params_item = QTableWidgetItem(params)
                params_item.setFlags(params_item.flags() & ~Qt.ItemIsEditable)
                self.constraints_table.setItem(row, 4, params_item)
            
            # Update progress for each batch
            if count > 1000:
                progress_value = 20 + int(80 * (batch_end / len(page_constraints)))
                progress.setValue(progress_value)
                QApplication.processEvents()
                
                if progress.wasCanceled():
                    progress.close()
                    return  # Exit the function early to avoid partial updates
        
        # Update status label with explicit page information
        self.status_label.setText(f"Total Constraints: {count} | Showing {len(page_constraints)} constraints | Currently on Page {self.current_page} of {self.total_pages}")
        
        # Close progress dialog if it was shown
        if count > 1000:
            progress.setValue(100)
            progress.close()

    def go_to_page(self, page: int):
        """Navigates to the specified page number in the constraints table.

        The method updates `self.current_page` and then refreshes the
        constraints list to display the items on the new page.

        Args:
            page: The target page number to navigate to. Must be between 1
                and `self.total_pages`.
        """
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self.refresh_constraints_list()

    def handle_double_click(self, row: int, column: int):
        """Handles a double-click event on a table cell to open an edit dialog.

        When a cell is double-clicked, this method retrieves the tag of the
        constraint in the clicked row and opens an `MPConstraintEditDialog`
        for that constraint.

        Args:
            row: The row index of the double-clicked cell.
            column: The column index of the double-clicked cell.
        """
        tag_item = self.constraints_table.item(row, 0)
        if tag_item:
            tag = tag_item.data(Qt.UserRole)
            constraint = mpConstraint._constraints.get(tag)
            if constraint:
                self.open_constraint_edit_dialog(constraint)

    def show_context_menu(self, position: Qt.QPoint):
        """Shows a context menu when a table cell is right-clicked.

        The context menu offers "Edit Constraint" and "Delete Constraint"
        options for the constraint in the right-clicked row.

        Args:
            position: The position of the mouse click in table coordinates.
        """
        # Get the row under the mouse
        row = self.constraints_table.rowAt(position.y())
        if row < 0:
            return
        
        # Get the constraint tag
        tag_item = self.constraints_table.item(row, 0)
        if not tag_item:
            return
        
        tag = tag_item.data(Qt.UserRole)
        
        # Create context menu
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Constraint")
        delete_action = menu.addAction("Delete Constraint")
        
        # Connect actions
        action = menu.exec_(self.constraints_table.mapToGlobal(position))
        if action == edit_action:
            constraint = mpConstraint._constraints.get(tag)
            if constraint:
                self.open_constraint_edit_dialog(constraint)
        elif action == delete_action:
            self.delete_constraint(tag)

    def open_constraint_edit_dialog(self, constraint: mpConstraint):
        """Opens a dialog to edit an existing multipoint constraint.

        If the edit dialog is accepted, the constraint list is refreshed
        to reflect the changes.

        Args:
            constraint: The `mpConstraint` object to be edited.
        """
        dialog = MPConstraintEditDialog(constraint, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_constraints_list()

    def delete_constraint(self, tag: int):
        """Deletes a multipoint constraint from the system by its tag.

        A confirmation dialog is shown before proceeding with the deletion.
        If confirmed, the constraint is removed, and the list is refreshed.

        Args:
            tag: The unique integer tag of the constraint to delete.
        """
        reply = QMessageBox.question(
            self, 'Delete Constraint',
            f"Delete constraint with tag {tag}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            mpConstraintManager().remove_constraint(tag)
            self.refresh_constraints_list()
            
    def clear_all_constraints(self):
        """Deletes all multipoint constraints from the system.

        A confirmation dialog is shown before clearing all constraints.
        For a large number of constraints, a progress dialog is displayed
        during the clearing process. The constraint list is refreshed
        after completion.
        """
        count = len(mpConstraint._constraints)
        
        if count == 0:
            QMessageBox.information(self, "No Constraints", "There are no constraints to clear.")
            return
            
        reply = QMessageBox.question(
            self, 'Clear All Constraints',
            f"Delete all {count} constraints? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Show progress dialog for large numbers of constraints
            if count > 100:
                progress = QProgressDialog("Deleting all constraints...", "Cancel", 0, 100, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setValue(0)
                progress.show()
                QApplication.processEvents()
            
            # Clear the constraints dictionary directly
            mpConstraint._constraints.clear()
            
            # Close progress dialog if it was shown
            if count > 100:
                progress.setValue(100)
                progress.close()
                
            self.refresh_constraints_list()
            QMessageBox.information(self, "Success", f"Successfully cleared {count} constraints.")


# New Laminar Boundary Dialog
class MPLaminarBoundaryDialog(QDialog):
    """Dialog for creating laminar boundary multipoint constraints.

    Laminar boundary constraints connect nodes that share the same coordinate
    in a specified direction within a given tolerance, creating `equalDOF`
    constraints along planar boundaries.

    Attributes:
        manager (mpConstraintManager): The manager responsible for creating constraints.
        dofs_input (QLineEdit): Input field for degrees of freedom (DOFs)
            to constrain.
        direction_combo (QComboBox): Dropdown to select the direction
            perpendicular to the laminar boundary (1 for X, 2 for Y, 3 for Z).
        tolerance_spin (QDoubleSpinBox): Input for the tolerance used to
            find nodes within the same plane.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> dialog = MPLaminarBoundaryDialog()
        >>> dialog.dofs_input.setText("1 2")
        >>> dialog.direction_combo.setCurrentIndex(2) # Z-direction
        >>> dialog.tolerance_spin.setValue(0.005)
        >>> # dialog.exec() # Uncomment to run the dialog
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the MPLaminarBoundaryDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Create Laminar Boundary Constraint")
        self.manager = mpConstraintManager()
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # DOFs (degrees of freedom)
        self.dofs_input = QLineEdit("1 2")
        self.dofs_input.setPlaceholderText("Enter DOFs (e.g., 1 2 3)")
        form_layout.addRow("DOFs (space separated):", self.dofs_input)
        
        # Direction
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["1 (X)", "2 (Y)", "3 (Z)"])
        self.direction_combo.setCurrentIndex(2)  # Default to Z direction (3)
        form_layout.addRow("Perpendicular Direction:", self.direction_combo)
        
        # Tolerance
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(1e-6, 1.0)
        self.tolerance_spin.setValue(0.01)
        self.tolerance_spin.setSingleStep(0.001)
        self.tolerance_spin.setDecimals(4)
        form_layout.addRow("Tolerance:", self.tolerance_spin)
        
        # Description
        description = QLabel(
            "Laminar boundary will connect nodes on the boundary of the mesh that have\n"
            "the same coordinate in the specified direction within the given tolerance.\n"
            "This creates Equal DOF constraints along planar boundaries."
        )
        description.setWordWrap(True)
        form_layout.addRow(description)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_laminar_boundary)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def create_laminar_boundary(self):
        """Creates laminar boundary constraints based on user input.

        This method retrieves the specified DOFs, direction, and tolerance
        from the dialog's input fields. It then uses the `mpConstraintManager`
        to generate `equalDOF` constraints connecting nodes within the given
        planar tolerance. A progress dialog is shown during the operation.

        Raises:
            ValueError: If the input DOFs or direction are invalid.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> dialog = MPLaminarBoundaryDialog()
            >>> dialog.dofs_input.setText("1 2")
            >>> dialog.direction_combo.setCurrentIndex(2) # Z-direction
            >>> dialog.tolerance_spin.setValue(0.005)
            >>> # Simulating the click of the create button
            >>> dialog.create_laminar_boundary()
            >>> # If successful, dialog.accept() is called.
        """
        try:
            # Get direction (1, 2, or 3)
            direction_text = self.direction_combo.currentText()
            direction = int(direction_text[0])  # Extract the first character and convert to int
            
            # Get DOFs
            dofs = list(map(int, self.dofs_input.text().split()))
            
            # Get tolerance
            tolerance = self.tolerance_spin.value()
            
            # Show progress dialog since this operation can be time-consuming
            progress = QProgressDialog("Creating laminar boundary constraints...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            
            # Create laminar boundary constraints
            try:
                # Create the constraints
                self.manager.create_laminar_boundary(dofs=dofs, direction=direction, tol=tolerance)
                progress.setValue(100)
                QMessageBox.information(self, "Success", "Laminar boundary constraints created successfully.")
                self.accept()
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", f"Error creating laminar boundary: {str(e)}")
                return
        
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")


# Keep the original dialog classes without changes
class MPConstraintCreationDialog(QDialog):
    """Dialog for creating new multipoint constraints of a specific type.

    This dialog dynamically adjusts its input fields based on the `constraint_type`
    provided during initialization, supporting `equalDOF`, `rigidLink`, and
    `rigidDiaphragm` constraints.

    Attributes:
        constraint_type (str): The type of constraint being created
            (e.g., "equalDOF", "rigidLink").
        manager (mpConstraintManager): The manager responsible for creating constraints.
        master_input (QLineEdit): Input field for the master node ID.
        slaves_input (QLineEdit): Input field for comma-separated slave node IDs.
        type_specific_widget (QWidget): A container widget for type-specific inputs.
        dofs_input (QLineEdit, optional): Input field for DOFs, visible for
            "equalDOF" constraints.
        type_combo (QComboBox, optional): Dropdown for link type, visible for
            "rigidLink" constraints.
        direction_input (QLineEdit, optional): Input field for direction, visible
            for "rigidDiaphragm" constraints.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> dialog = MPConstraintCreationDialog("equalDOF")
        >>> dialog.master_input.setText("100")
        >>> dialog.slaves_input.setText("101,102")
        >>> dialog.dofs_input.setText("1 2 3")
        >>> # dialog.exec() # Uncomment to run the dialog
    """

    def __init__(self, constraint_type: str, parent: QWidget = None):
        """Initializes the MPConstraintCreationDialog.

        Args:
            constraint_type: The type of multipoint constraint to create.
                Valid values include "equalDOF", "rigidLink", "rigidDiaphragm".
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Create {constraint_type} Constraint")
        self.constraint_type = constraint_type
        self.manager = mpConstraintManager()
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Common fields
        self.master_input = QLineEdit()
        self.slaves_input = QLineEdit()
        
        form_layout.addRow("Master Node:", self.master_input)
        form_layout.addRow("Slave Nodes (comma separated):", self.slaves_input)
        
        # Type-specific fields
        self.type_specific_widget = QWidget()
        type_layout = QFormLayout(self.type_specific_widget)
        
        if constraint_type == "equalDOF":
            self.dofs_input = QLineEdit()
            type_layout.addRow("DOFs (space separated):", self.dofs_input)
        elif constraint_type == "rigidLink":
            self.type_combo = QComboBox()
            self.type_combo.addItems(["bar", "beam"])
            type_layout.addRow("Link Type:", self.type_combo)
        elif constraint_type == "rigidDiaphragm":
            self.direction_input = QLineEdit()
            type_layout.addRow("Direction:", self.direction_input)
        
        form_layout.addRow(self.type_specific_widget)
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_constraint)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def create_constraint(self):
        """Creates a new multipoint constraint based on the dialog's input.

        This method parses the master node, slave nodes, and type-specific
        parameters from the input fields. It then uses the `mpConstraintManager`
        to create and add the new constraint to the system.

        Raises:
            ValueError: If any input field contains invalid data (e.g., non-integer node IDs).
        """
        try:
            master = int(self.master_input.text())
            slaves = [int(n.strip()) for n in self.slaves_input.text().split(",")]
            
            args = [master, slaves]
            
            if self.constraint_type == "equalDOF":
                dofs = list(map(int, self.dofs_input.text().split()))
                args.append(dofs)
            elif self.constraint_type == "rigidLink":
                args.insert(0, self.type_combo.currentText())
            elif self.constraint_type == "rigidDiaphragm":
                args.insert(0, int(self.direction_input.text()))
            
            self.manager.create_constraint(self.constraint_type, *args)
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")


class MPConstraintEditDialog(QDialog):
    """Dialog for editing an existing multipoint constraint.

    This dialog pre-populates its input fields with the current values of
    a given `mpConstraint` object and allows the user to modify them.
    Changes are saved by re-creating the constraint with the new parameters.

    Attributes:
        constraint (mpConstraint): The `mpConstraint` object being edited.
        manager (mpConstraintManager): The manager responsible for modifying constraints.
        master_input (QLineEdit): Input field for the master node ID.
        slaves_input (QLineEdit): Input field for comma-separated slave node IDs.
        dofs_input (QLineEdit, optional): Input field for DOFs, visible if the
            constraint is an `equalDOF` type.
        type_combo (QComboBox, optional): Dropdown for link type, visible if the
            constraint is a `rigidLink` type.
        direction_input (QLineEdit, optional): Input field for direction, visible
            if the constraint is a `rigidDiaphragm` type.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> from femora.components.Constraint.mpConstraint import mpConstraintManager
        >>> app = QApplication(sys.argv)
        >>> mp_manager = mpConstraintManager()
        >>> constraint = mp_manager.create_equal_dof(master_node=1, slave_nodes=[2, 3], dofs=[1, 2, 3])
        >>> dialog = MPConstraintEditDialog(constraint)
        >>> dialog.master_input.setText("10")
        >>> dialog.slaves_input.setText("20,30,40")
        >>> dialog.dofs_input.setText("1 2")
        >>> # dialog.exec() # Uncomment to run the dialog
    """

    def __init__(self, constraint: mpConstraint, parent: QWidget = None):
        """Initializes the MPConstraintEditDialog.

        Args:
            constraint: The `mpConstraint` object to be edited.
            parent: The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        self.constraint = constraint
        self.manager = mpConstraintManager()
        self.setWindowTitle(f"Edit {type(constraint).__name__} Constraint")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Master Node
        self.master_input = QLineEdit(str(constraint.master_node))
        form_layout.addRow("Master Node:", self.master_input)
        
        # Slave Nodes
        self.slaves_input = QLineEdit(", ".join(map(str, constraint.slave_nodes)))
        form_layout.addRow("Slave Nodes:", self.slaves_input)
        
        # Type-specific fields
        if isinstance(constraint, equalDOF):
            self.dofs_input = QLineEdit(" ".join(map(str, constraint.dofs)))
            form_layout.addRow("DOFs:", self.dofs_input)
        elif isinstance(constraint, rigidLink):
            self.type_combo = QComboBox()
            self.type_combo.addItems(["bar", "beam"])
            self.type_combo.setCurrentText(constraint.type)
            form_layout.addRow("Type:", self.type_combo)
        elif isinstance(constraint, rigidDiaphragm):
            self.direction_input = QLineEdit(str(constraint.direction))
            form_layout.addRow("Direction:", self.direction_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)

    def save_changes(self):
        """Saves the changes made to the constraint.

        This method first removes the original constraint and then re-creates
        it with the new parameters entered in the dialog's input fields.

        Raises:
            ValueError: If any input field contains invalid data (e.g., non-integer node IDs).
        """
        try:
            # Update common properties
            new_master = int(self.master_input.text())
            new_slaves = [int(n.strip()) for n in self.slaves_input.text().split(",")]
            
            # Recreate constraint with new parameters
            self.manager.remove_constraint(self.constraint.tag)
            
            args = [new_master, new_slaves]
            if isinstance(self.constraint, equalDOF):
                new_dofs = list(map(int, self.dofs_input.text().split()))
                args.append(new_dofs)
            elif isinstance(self.constraint, rigidLink):
                args.insert(0, self.type_combo.currentText())
            elif isinstance(self.constraint, rigidDiaphragm):
                args.insert(0, int(self.direction_input.text()))
            
            self.manager.create_constraint(type(self.constraint).__name__, *args)
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")

if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    import sys
    
    # Create some sample constraints for testing
    mp_manager = mpConstraintManager()
    
    # Create equalDOF constraints
    mp_manager.create_equal_dof(master_node=1, slave_nodes=[2, 3], dofs=[1, 2, 3])
    mp_manager.create_equal_dof(master_node=5, slave_nodes=[6], dofs=[4, 5, 6])
    
    # Create rigidLink constraints
    mp_manager.create_rigid_link(type_str="bar", master_node=10, slave_nodes=[11, 12, 13])
    mp_manager.create_rigid_link(type_str="beam", master_node=20, slave_nodes=[21, 22])
    
    # Create rigidDiaphragm constraints
    mp_manager.create_rigid_diaphragm(direction=3, master_node=30, slave_nodes=[31, 32, 33, 34])
    mp_manager.create_rigid_diaphragm(direction=2, master_node=40, slave_nodes=[41, 42, 43])
    
    # Start the application
    app = QApplication(sys.argv)
    manager_tab = MPConstraintManagerTab()
    manager_tab.show()
    sys.exit(app.exec())