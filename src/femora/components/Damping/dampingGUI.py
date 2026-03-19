from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QMessageBox, QHeaderView, QGridLayout,
    QFrame, QTextBrowser  
)

from qtpy.QtCore import Qt
from femora.components.Damping.dampingBase import DampingBase, DampingRegistry

class DampingManagerTab(QDialog):
    """Manages the creation, editing, and deletion of damping objects in a GUI tab.

    This dialog provides an interface to view existing damping definitions,
    create new ones of various types, and modify or remove them. It interacts
    with the `DampingRegistry` and `DampingBase` to manage the global damping
    definitions.

    Attributes:
        damping_type_combo (QComboBox): Dropdown menu to select the type of damping
            to create.
        dampings_table (QTableWidget): Table displaying all currently defined
            damping objects, including their tag, type, name, and action buttons.
        refresh_btn (QPushButton): Button to refresh the list of dampings in the table.

    Example:
        >>> import sys
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.Damping.dampingBase import RayleighDamping, ModalDamping
        >>> # Pre-populate some damping for demonstration
        >>> _ = RayleighDamping(alphaM=0.1, betaK=0.2)
        >>> _ = ModalDamping(numberofModes=2, dampingFactors="0.1,0.2")
        >>> app = QApplication(sys.argv)
        >>> manager_tab = DampingManagerTab()
        >>> manager_tab.show()
        >>> # app.exec_() # Uncomment to run the application event loop
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the DampingManagerTab.

        Sets up the UI elements including the damping type selection, the table
        to display dampings, and buttons for creation and refreshing.

        Args:
            parent: The parent widget for this dialog. Defaults to None.
        """
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Damping type selection
        type_layout = QGridLayout()
        self.damping_type_combo = QComboBox()
        self.damping_type_combo.addItems(DampingRegistry.get_available_types())
        
        create_damping_btn = QPushButton("Create New Damping")
        create_damping_btn.clicked.connect(self.open_damping_creation_dialog)
        
        type_layout.addWidget(QLabel("Damping Type:"), 0, 0)
        type_layout.addWidget(self.damping_type_combo, 0, 1, 1, 2)
        type_layout.addWidget(create_damping_btn, 1, 0, 1, 3)
        
        layout.addLayout(type_layout)
        
        # Dampings table
        self.dampings_table = QTableWidget()
        self.dampings_table.setColumnCount(5)  # Tag, Type, Name, Edit, Delete
        self.dampings_table.setHorizontalHeaderLabels(["Tag", "Type", "Name", "Edit", "Delete"])
        header = self.dampings_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.dampings_table)
        
        # Refresh dampings button
        refresh_btn = QPushButton("Refresh Dampings List")
        refresh_btn.clicked.connect(self.refresh_dampings_list)
        layout.addWidget(refresh_btn)
        
        # Initial refresh
        self.refresh_dampings_list()

    def open_damping_creation_dialog(self):
        """Opens a dialog to create a new damping object.

        The type of damping to be created is determined by the currently
        selected item in the `damping_type_combo` QComboBox. If a new damping
        is successfully created, the dampings list is refreshed.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> app = QApplication(sys.argv)
            >>> manager_tab = DampingManagerTab()
            >>> manager_tab.damping_type_combo.setCurrentText("RayleighDamping")
            >>> # manager_tab.open_damping_creation_dialog() # This would open a modal dialog
            >>> # If you programmatically want to create one without the dialog,
            >>> # you'd use DampingRegistry.create_damping directly.
        """
        damping_type = self.damping_type_combo.currentText()
        dialog = DampingCreationDialog(damping_type, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_dampings_list()

    def refresh_dampings_list(self):
        """Updates the dampings table with the current list of registered damping objects.

        This method clears the existing table content and repopulates it with
        all damping objects currently managed by `DampingBase._dampings`.
        It creates a row for each damping, including its tag, type, name,
        and "Edit" and "Delete" action buttons.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> app = QApplication(sys.argv)
            >>> manager_tab = DampingManagerTab()
            >>> # Initially, the table might be empty or have pre-existing ones
            >>> manager_tab.refresh_dampings_list()
            >>> # Create a new damping programmatically
            >>> _ = RayleighDamping(alphaM=0.1, betaK=0.2, name="test_damping")
            >>> manager_tab.refresh_dampings_list() # Table will now show the new damping
            >>> # The following would only work in an interactive session or by checking
            >>> # the table widget directly.
            >>> # manager_tab.dampings_table.rowCount()
            # 1
        """
        self.dampings_table.setRowCount(0)
        dampings = DampingBase._dampings
        
        self.dampings_table.setRowCount(len(dampings))
        # print(DampingBase.print_dampings())
        for row, (tag, damping) in enumerate(dampings.items()):
            # Tag
            tag_item = QTableWidgetItem(str(tag))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            self.dampings_table.setItem(row, 0, tag_item)
            
            # Damping Type
            type_item = QTableWidgetItem(damping.__class__.__name__)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.dampings_table.setItem(row, 1, type_item)
            
            # Name
            name_item = QTableWidgetItem(damping.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.dampings_table.setItem(row, 2, name_item)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, d=damping: self.open_damping_edit_dialog(d))
            self.dampings_table.setCellWidget(row, 3, edit_btn)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, t=tag: self.delete_damping(t))
            self.dampings_table.setCellWidget(row, 4, delete_btn)

    def open_damping_edit_dialog(self, damping: DampingBase):
        """Opens a dialog to edit an existing damping object's properties.

        If the damping's properties are successfully updated via the dialog,
        the dampings list is refreshed to reflect the changes.

        Args:
            damping: The `DampingBase` object whose properties are to be edited.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> app = QApplication(sys.argv)
            >>> manager_tab = DampingManagerTab()
            >>> existing_damping = RayleighDamping(alphaM=0.1, betaK=0.2, name="MyDamping")
            >>> # manager_tab.open_damping_edit_dialog(existing_damping) # This would open a modal dialog
            >>> # To observe the effect, you'd typically interact with the GUI.
            >>> # If you programmatically want to edit, use existing_damping.update_values.
        """
        dialog = DampingEditDialog(damping, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_dampings_list()

    def delete_damping(self, tag: int):
        """Deletes a damping object from the system after user confirmation.

        A confirmation dialog is presented to the user. If confirmed, the damping
        object corresponding to the given tag is removed using `DampingBase.remove_damping()`,
        and the dampings list in the UI is refreshed.

        Args:
            tag: The unique integer tag of the damping object to be deleted.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> app = QApplication(sys.argv)
            >>> manager_tab = DampingManagerTab()
            >>> damping_to_delete = RayleighDamping(alphaM=0.1, betaK=0.2)
            >>> # Get the tag of the newly created damping
            >>> tag = damping_to_delete.tag
            >>> manager_tab.refresh_dampings_list()
            >>> # The following would only work in an interactive session or by mocking
            >>> # QMessageBox.question is a blocking call, so for testing,
            >>> # one might mock it or interact manually.
            >>> # manager_tab.delete_damping(tag)
            >>> # Assuming confirmation, the table row count would decrease.
            >>> # manager_tab.dampings_table.rowCount()
            # 0
        """
        reply = QMessageBox.question(
            self, 'Delete Damping',
            f"Are you sure you want to delete damping with tag {tag}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            DampingBase.remove_damping(tag)
            self.refresh_dampings_list()

class DampingCreationDialog(QDialog):
    """A dialog for creating a new damping object of a specific type.

    This dialog presents input fields for the parameters required by the selected
    damping type, along with notes and references for guidance. Users can input
    values and create a new damping object, which is then registered in the system.

    Attributes:
        damping_type (str): The string identifier for the type of damping
            being created (e.g., 'rayleigh', 'modal').
        param_inputs (dict[str, QLineEdit]): A dictionary mapping parameter
            names (str) to their corresponding QLineEdit input widgets.
    """
    def __init__(self, damping_type: str, parent: QWidget = None):
        """Initializes the DampingCreationDialog.

        Sets up the UI, including parameter input fields dynamically generated
        based on the `damping_type`, and displays relevant notes and references.

        Args:
            damping_type: The string identifier for the type of damping to create.
            parent: The parent widget for this dialog. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Create {damping_type} Damping")
        self.damping_type = damping_type.lower()
        
        # Main horizontal layout to split the dialog
        main_layout = QHBoxLayout(self)
        
        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Get damping class
        damping_class = DampingRegistry._damping_types[self.damping_type]
        
        # Parameter inputs
        self.param_inputs = {}
        parameters = damping_class.get_Parameters()
        
        # Create a grid layout for input fields
        params_group = QGridLayout()
        
        # Add label and input fields to the grid layout
        for row, (param, desc) in enumerate(parameters):
            label = QLabel(param)
            input_field = QLineEdit()
            description_label = QLabel(desc)
            description_label.setWordWrap(True)
            
            params_group.addWidget(label, row, 0)
            params_group.addWidget(input_field, row, 1)
            params_group.addWidget(description_label, row, 2)
            
            self.param_inputs[param] = input_field
        
        left_layout.addLayout(params_group)
        
        # Buttons at the bottom of left side
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Damping")
        create_btn.clicked.connect(self.create_damping)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        left_layout.addLayout(btn_layout)
        
        # make the left side be top aligned and left
        left_layout.addStretch()

        # Add left widget to main layout
        main_layout.addWidget(left_widget)

        
        # Vertical line separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Right side - Notes
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
                
        # Notes content using QTextEdit
        notes_display = QTextBrowser()
        notes_display.setReadOnly(True)  # Make it read-only
        notes_display.setOpenExternalLinks(True) 
        
        # Format notes content
        infotxt = ""
        infotxt += "<b>Notes:</b><br>"

        info = damping_class.get_Notes()
        notes = info.get("Notes", None)
        if notes:
            for i, note in enumerate(notes, 1):
                infotxt += f"{i}. {note}<br><br>"
        else:
            infotxt += "No notes available for this damping type.<br>"

        ref = info.get("References", None)
        if ref:
            infotxt += "<br><b>Reference:</b><br>"
            # Convert reference to clickable link
            for i, ref in enumerate(ref, 1):
                infotxt += f"{i}. <a href='{ref}'>{ref}</a><br>"

        notes_display.setHtml(infotxt)  # Use HTML formatting

        
        right_layout.addWidget(notes_display)
        
        right_layout.addStretch()
        
        # Add right widget to main layout
        main_layout.addWidget(right_widget)
        
        # Set the layout proportions
        main_layout.setStretch(0, 3)  # Left side takes 3/5 of the width
        main_layout.setStretch(2, 2)  # Right side takes 2/5 of the width

    def create_damping(self):
        """Collects input parameters and attempts to create a new damping object.

        This method reads values from the parameter input fields, validates them,
        and uses `DampingRegistry.create_damping()` to instantiate and register
        a new damping object. On success, the dialog is accepted.
        On failure (e.g., invalid input), a warning message is displayed.

        Raises:
            ValueError: If any input parameter has an invalid format or value.
            Exception: For any other unexpected errors during damping creation.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Damping.dampingBase import DampingRegistry
            >>> app = QApplication(sys.argv)
            >>> dialog = DampingCreationDialog(damping_type="RayleighDamping")
            >>> # Simulate inputting values
            >>> dialog.param_inputs["alphaM"].setText("0.1")
            >>> dialog.param_inputs["betaK"].setText("0.2")
            >>> # dialog.create_damping() # This would attempt to create and close the dialog
            >>> # Check if a damping was created (requires DampingRegistry._dampings access)
            >>> # len(DampingRegistry._dampings) == initial_count + 1 if successful
        """
        try:
            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                value = input_field.text().strip() 
                if value == "" :
                    continue
                params[param] = value

            # Create damping
            DampingRegistry.create_damping(self.damping_type, **params)
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error",
                              f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class DampingEditDialog(QDialog):
    """A dialog for editing the properties of an existing damping object.

    This dialog pre-fills input fields with the current values of the damping
    object's parameters and allows the user to modify them. It also displays
    relevant notes and references for the damping type.

    Attributes:
        damping (DampingBase): The `DampingBase` object whose properties are being edited.
        param_inputs (dict[str, QLineEdit]): A dictionary mapping parameter
            names (str) to their corresponding QLineEdit input widgets.
    """
    def __init__(self, damping: DampingBase, parent: QWidget = None):
        """Initializes the DampingEditDialog.

        Sets up the UI with pre-filled parameter input fields based on the
        provided `damping` object, and displays its type-specific notes and references.

        Args:
            damping: The `DampingBase` object to be edited.
            parent: The parent widget for this dialog. Defaults to None.
        """
        super().__init__(parent)
        self.damping = damping
        self.setWindowTitle(f"Edit {damping.__class__.__name__} (Tag: {damping.tag})")
        
        
        # Main horizontal layout to split the dialog
        main_layout = QHBoxLayout(self)
        
        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Parameter inputs
        self.param_inputs = {}
        parameters = damping.__class__.get_Parameters()
        values = damping.get_values()
        
        # Create a grid layout for parameter inputs
        params_group = QGridLayout()
        
        # Add label and input fields to the grid layout
        for row, (param, desc) in enumerate(parameters):
            label = QLabel(param)
            input_field = QLineEdit()
            description_label = QLabel(desc)
            description_label.setWordWrap(True)
            
            # Set current value if available
            current_value = values.get(param, None)
            if current_value is not None:
                if isinstance(current_value, list):
                    input_field.setText(",".join(map(str, current_value)))
                else:
                    input_field.setText(str(current_value))
            
            params_group.addWidget(label, row, 0)
            params_group.addWidget(input_field, row, 1)
            params_group.addWidget(description_label, row, 2)
            
            self.param_inputs[param] = input_field
        
        left_layout.addLayout(params_group)
        
        # Buttons at the bottom of left side
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        left_layout.addLayout(btn_layout)
        left_layout.addStretch()
        
        # Add left widget to main layout
        main_layout.addWidget(left_widget)
        
        # Vertical line separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Right side - Notes
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
                
        # Notes content using QTextEdit
        notes_display = QTextBrowser()
        notes_display.setReadOnly(True)  # Make it read-only
        notes_display.setOpenExternalLinks(True) 
        
        # Format notes content
        infotxt = ""
        infotxt += "<b>Notes:</b><br>"

        info = damping.__class__.get_Notes()
        notes = info.get("Notes", None)
        if notes:
            for i, note in enumerate(notes, 1):
                infotxt += f"{i}. {note}<br><br>"
        else:
            infotxt += "No notes available for this damping type.<br>"

        ref = info.get("References", None)
        if ref:
            infotxt += "<br><b>Reference:</b><br>"
            # Convert reference to clickable link
            for i, ref in enumerate(ref, 1):
                infotxt += f"{i}. <a href='{ref}'>{ref}</a><br>"

        notes_display.setHtml(infotxt)  # Use HTML formatting

        
        right_layout.addWidget(notes_display)
        
        right_layout.addStretch()
        
        # Add right widget to main layout
        main_layout.addWidget(right_widget)

        # Set the layout proportions
        main_layout.setStretch(0, 3)  # Left side takes 3/5 of the width
        main_layout.setStretch(2, 2)  # Right side takes 2/5 of the width


    def save_changes(self):
        """Collects updated parameters and attempts to save changes to the damping object.

        This method reads values from the input fields, validates them, and
        uses the `damping.update_values()` method to apply the changes to the
        associated damping object. On success, the dialog is accepted.
        On failure (e.g., invalid input), a warning message is displayed.

        Raises:
            ValueError: If any input parameter has an invalid format or value.
            Exception: For any other unexpected errors during damping update.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> app = QApplication(sys.argv)
            >>> existing_damping = RayleighDamping(alphaM=0.1, betaK=0.2)
            >>> dialog = DampingEditDialog(existing_damping)
            >>> # Simulate changing a value
            >>> dialog.param_inputs["alphaM"].setText("0.15")
            >>> # dialog.save_changes() # This would attempt to save and close the dialog
            >>> # Check if value was updated
            >>> # existing_damping.alphaM == 0.15 if successful
        """
        try:
            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                value = input_field.text().strip()
                params[param] = value

            # Update damping
            self.damping.update_values(**params)            

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error",
                              f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    from femora.components.Damping.dampingBase import RayleighDamping, ModalDamping
    RayleighDamping1 = RayleighDamping(alphaM=0.1, betaK=0.2, betaKInit=0.3, betaKComm=0.4)
    RayleighDamping2 = RayleighDamping(alphaM=0.5, betaK=0.6, betaKInit=0.7, betaKComm=0.8)
    ModalDamping1 = ModalDamping(numberofModes=2, dampingFactors="0.1,0.2")
    ModalDamping2 = ModalDamping(numberofModes=3, dampingFactors="0.3,0.4,0.5")
    app = QApplication(sys.argv)
    window = DampingManagerTab()
    window.show()
    sys.exit(app.exec_())