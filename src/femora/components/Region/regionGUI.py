from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QMessageBox, QHeaderView, QGridLayout,
    QFrame, QTextBrowser, QCheckBox
)
from qtpy.QtCore import Qt
from femora.components.Damping.dampingBase import DampingBase
from femora.components.Region.regionBase import RegionBase, GlobalRegion, ElementRegion, NodeRegion

class DampingSelectorWidget(QWidget):
    """A widget for selecting a damping object from available dampings.

    This widget provides a combo box to choose an existing damping and
    a button to open a damping manager dialog for creation and editing.

    Attributes:
        damping_combo (QComboBox): The combo box displaying available damping objects.
        create_damping_btn (QPushButton): Button to open the damping manager dialog.
    """

    def __init__(self, parent=None):
        """Initializes the DampingSelectorWidget.

        Args:
            parent: The parent widget, if any.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.damping_combo = QComboBox()
        self.refresh_dampings()

        self.create_damping_btn = QPushButton("Manage Dampings")
        self.create_damping_btn.clicked.connect(self.open_damping_dialog)

        layout.addWidget(QLabel("Damping:"))
        layout.addWidget(self.damping_combo, stretch=1)
        layout.addWidget(self.create_damping_btn)

    def refresh_dampings(self):
        """Refreshes the list of damping objects in the combo box.

        It clears the current items and re-populates them with all
        registered damping objects from `DampingBase._dampings`.

        Example:
            >>> selector = DampingSelectorWidget()
            >>> # Assume some dampings exist
            >>> selector.refresh_dampings()
            >>> print(selector.damping_combo.count() > 1)
            True
        """
        self.damping_combo.clear()
        self.damping_combo.addItem("None", None)
        for tag, damping in DampingBase._dampings.items():
            self.damping_combo.addItem(f"{damping.name} (Tag: {tag}, Type: {damping.get_Type()})", damping)

    def open_damping_dialog(self):
        """Opens the DampingManagerTab dialog to manage damping objects.

        After the dialog is closed, the damping list in the combo box is refreshed.

        Example:
            >>> selector = DampingSelectorWidget()
            >>> # Simulate clicking the button
            >>> selector.create_damping_btn.click() # This would open a dialog
            >>> # The dialog would then be interacted with and closed.
        """
        from femora.components.Damping.dampingGUI import DampingManagerTab
        dialog = DampingManagerTab(self)
        dialog.exec()
        self.refresh_dampings()

    def get_selected_damping(self):
        """Returns the currently selected damping object from the combo box.

        Returns:
            DampingBase or None: The selected damping object, or None if "None" is selected.

        Example:
            >>> selector = DampingSelectorWidget()
            >>> # Assuming "None" is the default or first item
            >>> print(selector.get_selected_damping() is None)
            True
        """
        return self.damping_combo.currentData()

    def set_selected_damping(self, damping):
        """Sets the currently selected damping in the combo box.

        If the specified damping is not found, the selection defaults to the first item (None).

        Args:
            damping: The damping object to set as selected.

        Example:
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> selector = DampingSelectorWidget()
            >>> my_damping = RayleighDamping(alphaM=0.1, betaK=0.2)
            >>> selector.refresh_dampings() # Ensure dampings are loaded
            >>> selector.set_selected_damping(my_damping)
            >>> print(selector.get_selected_damping() == my_damping)
            True
        """
        index = self.damping_combo.findData(damping)
        self.damping_combo.setCurrentIndex(max(index, 0))

class RegionManagerTab(QDialog):
    """A dialog for managing regions within the Femora project.

    This dialog allows users to create, edit, view information about,
    and delete different types of regions (ElementRegion, NodeRegion).

    Attributes:
        region_type_combo (QComboBox): Dropdown to select the type of region to create.
        regions_table (QTableWidget): Table displaying all registered regions.
    """

    def __init__(self, parent=None):
        """Initializes the RegionManagerTab.

        Args:
            parent: The parent widget, if any.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> manager_tab = RegionManagerTab()
            >>> manager_tab.setWindowTitle("Region Manager")
            >>> manager_tab.show()
            >>> # To properly test, one would interact with the UI.
            >>> # manager_tab.exec()
            >>> app.quit() # In a real app, exec() would block.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Region type selection
        type_layout = QGridLayout()
        self.region_type_combo = QComboBox()
        self.region_type_combo.addItems(["ElementRegion", "NodeRegion"])

        create_region_btn = QPushButton("Create New Region")
        create_region_btn.clicked.connect(self.open_region_creation_dialog)

        type_layout.addWidget(QLabel("Region Type:"), 0, 0)
        type_layout.addWidget(self.region_type_combo, 0, 1, 1, 2)
        type_layout.addWidget(create_region_btn, 1, 0, 1, 3)

        layout.addLayout(type_layout)

        # Regions table
        self.regions_table = QTableWidget()
        self.regions_table.setColumnCount(7)  # Tag, Type, Name, Damping, Edit, Delete
        self.regions_table.setHorizontalHeaderLabels(["Tag", "Type", "Name", "Damping", "Edit", "info" ,"Delete"])
        header = self.regions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # dont show the index column
        self.regions_table.verticalHeader().setVisible(False)

        layout.addWidget(self.regions_table)

        # Refresh regions button
        refresh_btn = QPushButton("Refresh Regions List")
        refresh_btn.clicked.connect(self.refresh_regions_list)
        layout.addWidget(refresh_btn)

        # Initial refresh
        self.refresh_regions_list()

    def refresh_regions_list(self):
        """Refreshes the table with the current list of registered regions.

        It clears the table and populates it with details of all regions
        managed by `RegionBase`, including buttons for editing, viewing info,
        and deleting.

        Example:
            >>> from femora.components.Region.regionBase import GlobalRegion, ElementRegion
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> GlobalRegion(damping=RayleighDamping(alphaM=0.1, betaK=0.2)) # Ensure global exists
            >>> element_region = ElementRegion(elements=[1,2], damping=None)
            >>> manager_tab = RegionManagerTab()
            >>> manager_tab.refresh_regions_list()
            >>> print(manager_tab.regions_table.rowCount() >= 2)
            True
            >>> # Cleanup for testing purposes
            >>> RegionBase.remove_region(element_region.tag)
        """
        self.regions_table.setRowCount(0)
        regions = RegionBase.get_all_regions()

        self.regions_table.setRowCount(len(regions))
        for row, (tag, region) in enumerate(regions.items()):
            # Tag
            tag_item = QTableWidgetItem(str(tag))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            self.regions_table.setItem(row, 0, tag_item)

            # Region Type
            type_item = QTableWidgetItem(region.get_type())
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.regions_table.setItem(row, 1, type_item)

            # Name
            name_item = QTableWidgetItem(region.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.regions_table.setItem(row, 2, name_item)

            # Damping
            damping_text = region.damping.name if region.damping else "None"
            damping_item = QTableWidgetItem(damping_text)
            damping_item.setFlags(damping_item.flags() & ~Qt.ItemIsEditable)
            self.regions_table.setItem(row, 3, damping_item)

            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, r=region: self.open_region_edit_dialog(r))
            self.regions_table.setCellWidget(row, 4, edit_btn)

            # Delete button (disabled for global region)
            delete_btn = QPushButton("Delete")
            delete_btn.setEnabled(tag != 0)
            delete_btn.clicked.connect(lambda checked, t=tag: self.delete_region(t))
            self.regions_table.setCellWidget(row, 6, delete_btn)

            # info button
            info_btn = QPushButton("Info")
            info_btn.clicked.connect(lambda checked, r=region: self.show_region_info(r))
            self.regions_table.setCellWidget(row, 5, info_btn)

    def open_region_creation_dialog(self):
        """Opens a dialog for creating a new region of the selected type.

        If a new region is successfully created, the regions list is refreshed.

        Example:
            >>> manager_tab = RegionManagerTab()
            >>> manager_tab.region_type_combo.setCurrentText("ElementRegion")
            >>> # Simulate clicking the create button. In a real scenario, this would open
            >>> # the dialog and await user interaction.
            >>> manager_tab.open_region_creation_dialog()
            >>> # After closing the dialog (e.g., accepting it), the list would refresh.
        """
        region_type = self.region_type_combo.currentText()
        dialog = RegionCreationDialog(region_type, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_regions_list()

    def open_region_edit_dialog(self, region):
        """Opens a dialog for editing an existing region.

        If changes are successfully saved, the regions list is refreshed.

        Args:
            region (RegionBase): The region object to be edited.

        Example:
            >>> from femora.components.Region.regionBase import NodeRegion
            >>> from femora.components.Damping.dampingBase import ModalDamping
            >>> node_region = NodeRegion(nodes=[10, 20], damping=ModalDamping(numberofModes=1))
            >>> manager_tab = RegionManagerTab()
            >>> # Simulate opening the edit dialog for the created region.
            >>> manager_tab.open_region_edit_dialog(node_region)
            >>> # Cleanup for testing purposes
            >>> RegionBase.remove_region(node_region.tag)
        """
        dialog = RegionEditDialog(region, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_regions_list()

    def show_region_info(self, region):
        """Displays detailed information about a selected region in a message box.

        Args:
            region (RegionBase): The region object for which to show information.

        Example:
            >>> from femora.components.Region.regionBase import GlobalRegion
            >>> global_region = GlobalRegion()
            >>> manager_tab = RegionManagerTab()
            >>> manager_tab.show_region_info(global_region) # This will open a QMessageBox
        """
        QMessageBox.information(self, f"{region.get_type()} Info", str(region))

    def delete_region(self, tag):
        """Deletes a region after user confirmation.

        The global region (tag 0) cannot be deleted. If deletion is confirmed,
        the regions list is refreshed.

        Args:
            tag (int): The unique tag of the region to be deleted.

        Example:
            >>> from femora.components.Region.regionBase import ElementRegion
            >>> element_region = ElementRegion(elements=[5, 6])
            >>> manager_tab = RegionManagerTab()
            >>> # To actually delete, a QMessageBox interaction is needed.
            >>> # This example only sets up the call.
            >>> # manager_tab.delete_region(element_region.tag)
            >>> # Manually remove for test cleanup:
            >>> RegionBase.remove_region(element_region.tag)
        """
        reply = QMessageBox.question(
            self, 'Delete Region',
            f"Are you sure you want to delete region with tag {tag}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            RegionBase.remove_region(tag)
            self.refresh_regions_list()

class RegionCreationDialog(QDialog):
    """A dialog for creating a new region of a specified type.

    This dialog dynamically generates input fields based on the parameters
    required by the selected region type and allows assigning a damping.

    Attributes:
        region_type (str): The string name of the region type to create.
        region_class (type): The actual class object for the region type.
        param_inputs (dict): A dictionary mapping parameter names to their QWidget input fields.
        damping_selector (DampingSelectorWidget): Widget for selecting a damping for the new region.
    """

    def __init__(self, region_type: str, parent=None):
        """Initializes the RegionCreationDialog.

        Args:
            region_type: The string name of the region class to be created (e.g., "ElementRegion").
            parent: The parent widget, if any.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> dialog = RegionCreationDialog("ElementRegion")
            >>> dialog.setWindowTitle("Create New Element Region")
            >>> # dialog.exec() # In a real app, exec() would block for user input.
            >>> app.quit() # Cleanup
        """
        super().__init__(parent)
        self.setWindowTitle(f"Create {region_type}")
        self.region_type = region_type

        # Main horizontal layout
        main_layout = QHBoxLayout(self)

        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Get region class
        self.region_class = globals()[region_type]

        # Parameter inputs
        self.param_inputs = {}
        parameters = self.region_class.get_Parameters()

        # Create a grid layout for parameters
        params_group = QGridLayout()
        row = 0

        # Add damping selector
        self.damping_selector = DampingSelectorWidget()
        params_group.addWidget(QLabel("Damping:"), row, 0, 1, 3)
        row += 1
        params_group.addWidget(self.damping_selector, row, 0, 1, 3)
        row += 1

        # Add other parameters
        for param, input_type in parameters.items():
            if input_type == "checkbox":
                input_field = QCheckBox()
                params_group.addWidget(QLabel(param), row, 0)
                params_group.addWidget(input_field, row, 1, 1, 2)
            else:  # lineEdit
                input_field = QLineEdit()
                params_group.addWidget(QLabel(param), row, 0)
                params_group.addWidget(input_field, row, 1, 1, 2)

            self.param_inputs[param] = input_field
            row += 1

        left_layout.addLayout(params_group)

        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Region")
        create_btn.clicked.connect(self.create_region)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
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

        notes_display = QTextBrowser()
        notes_display.setHtml(f"<b>Notes:</b><br>")
        info = self.region_class.getNotes()
        for i, note in enumerate(info["Notes"]):
            notes_display.append(f"<b>{i+1}</b>) {note}")
        notes_display.append(f"<br><b>References:</b>")
        for i, ref in enumerate(info["References"]):
            notes_display.append(f"<b>{i+1}</b>) {ref}")

        right_layout.addWidget(notes_display)
        right_layout.addStretch()

        main_layout.addWidget(right_widget)

        # Set layout proportions
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def create_region(self):
        """Creates a new region instance based on the input fields.

        It parses the values from the input fields, converts them to the
        appropriate types, and attempts to instantiate a new region object.
        If successful, the dialog is accepted. Handles various input types
        like checkboxes, comma-separated integers for lists, and text.

        Raises:
            ValueError: If there's an issue parsing input values (e.g., non-integer in a list).
            Exception: For other errors during region instantiation.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> app = QApplication(sys.argv)
            >>> dialog = RegionCreationDialog("ElementRegion")
            >>> # Simulate user input
            >>> dialog.param_inputs['elements'].setText('10,20,30')
            >>> dialog.param_inputs['element_only'].setChecked(True)
            >>> dialog.create_region() # Attempt to create the region
            >>> # If accepted, a new region would be created and dialog closed.
            >>> app.quit() # Cleanup
        """
        try:
            params = {}
            for param, input_field in self.param_inputs.items():
                if isinstance(input_field, QCheckBox):
                    value = input_field.isChecked()
                else:
                    text = input_field.text().strip()
                    if not text:
                        continue
                    if param in ['elements', 'nodes']:
                        value = [int(x) for x in text.split(',')]
                    elif param in ['element_range', 'node_range']:
                        value = [int(x) for x in text.split(',')][:2]
                    else:
                        value = text
                params[param] = value

            damping = self.damping_selector.get_selected_damping()
            region = self.region_class(damping=damping, **params)
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class RegionEditDialog(QDialog):
    """A dialog for editing an existing region's properties.

    This dialog pre-populates input fields with the current values of the
    given region and allows the user to modify them, including its damping.

    Attributes:
        region (RegionBase): The region instance being edited.
        param_inputs (dict): A dictionary mapping parameter names to their QWidget input fields.
        damping_selector (DampingSelectorWidget): Widget for selecting a damping for the region.
    """

    def __init__(self, region: RegionBase, parent=None):
        """Initializes the RegionEditDialog.

        Args:
            region: The `RegionBase` object to be edited.
            parent: The parent widget, if any.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Region.regionBase import NodeRegion
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> app = QApplication(sys.argv)
            >>> my_damping = RayleighDamping(alphaM=0.01, betaK=0.02)
            >>> RegionBase._dampings[my_damping.tag] = my_damping # Manually add for example
            >>> node_region = NodeRegion(nodes=[100, 200], damping=my_damping)
            >>> dialog = RegionEditDialog(node_region)
            >>> dialog.setWindowTitle(f"Edit Node Region (Tag: {node_region.tag})")
            >>> # dialog.exec() # In a real app, exec() would block for user input.
            >>> app.quit() # Cleanup
            >>> RegionBase.remove_region(node_region.tag)
            >>> del RegionBase._dampings[my_damping.tag]
        """
        super().__init__(parent)
        self.region = region
        self.setWindowTitle(f"Edit {region.get_type()} (Tag: {region.tag})")

        # Main horizontal layout
        main_layout = QHBoxLayout(self)

        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Parameter inputs
        self.param_inputs = {}
        parameters = region.__class__.get_Parameters()

        # Create a grid layout for parameters
        params_group = QGridLayout()
        row = 0

        # Add damping selector
        self.damping_selector = DampingSelectorWidget()
        self.damping_selector.set_selected_damping(region.damping)
        params_group.addWidget(QLabel("Damping:"), row, 0, 1, 3)
        row += 1
        params_group.addWidget(self.damping_selector, row, 0, 1, 3)
        row += 1

        # Add other parameters
        for param, input_type in parameters.items():
            if input_type == "checkbox":
                input_field = QCheckBox()
                input_field.setChecked(getattr(region, param, False))
                params_group.addWidget(QLabel(param), row, 0)
                params_group.addWidget(input_field, row, 1, 1, 2)
            else:  # lineEdit
                input_field = QLineEdit()
                value = getattr(region, param, [])
                if value:
                    input_field.setText(','.join(map(str, value)))
                params_group.addWidget(QLabel(param), row, 0)
                params_group.addWidget(input_field, row, 1, 1, 2)

            self.param_inputs[param] = input_field
            row += 1

        left_layout.addLayout(params_group)

        # Buttons
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

        notes_display = QTextBrowser()
        notes_display.setHtml(f"<b>Notes:</b><br>")
        info = region.getNotes()
        for i, note in enumerate(info["Notes"]):
            notes_display.append(f"<b>{i+1}</b>) {note}")
        notes_display.append(f"<br><b>References:</b>")
        for i, ref in enumerate(info["References"]):
            notes_display.append(f"<b>{i+1}</b>) {ref}")
        right_layout.addWidget(notes_display)
        right_layout.addStretch()

        main_layout.addWidget(right_widget)

        # Set layout proportions
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def save_changes(self):
        """Saves the modifications made in the dialog to the associated region object.

        Updates the region's damping and other parameters based on the current
        values in the input fields. If successful, the dialog is accepted.

        Raises:
            ValueError: If there's an issue parsing input values (e.g., non-integer in a list).
            Exception: For other errors during attribute assignment.

        Example:
            >>> import sys
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.Region.regionBase import ElementRegion
            >>> from femora.components.Damping.dampingBase import RayleighDamping
            >>> app = QApplication(sys.argv)
            >>> # Setup a region for editing
            >>> initial_damping = RayleighDamping(alphaM=0.05, betaK=0.1)
            >>> RegionBase._dampings[initial_damping.tag] = initial_damping
            >>> region_to_edit = ElementRegion(elements=[1,2], damping=initial_damping)
            >>>
            >>> dialog = RegionEditDialog(region_to_edit)
            >>> # Simulate changing the 'elements' parameter and setting a new damping
            >>> new_damping = RayleighDamping(alphaM=0.15, betaK=0.2)
            >>> RegionBase._dampings[new_damping.tag] = new_damping # Ensure new damping is available
            >>> dialog.damping_selector.set_selected_damping(new_damping)
            >>> dialog.param_inputs['elements'].setText('1,2,3,4')
            >>>
            >>> dialog.save_changes() # Attempt to save
            >>> print(region_to_edit.elements == [1,2,3,4])
            True
            >>> print(region_to_edit.damping == new_damping)
            True
            >>>
            >>> app.quit() # Cleanup
            >>> RegionBase.remove_region(region_to_edit.tag)
            >>> del RegionBase._dampings[initial_damping.tag]
            >>> del RegionBase._dampings[new_damping.tag]
        """
        try:
            # Update damping
            self.region.damping = self.damping_selector.get_selected_damping()

            # Update other parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                if isinstance(input_field, QCheckBox):
                    setattr(self.region, param, input_field.isChecked())
                else:
                    text = input_field.text().strip()
                    if text:
                        if param in ['elements', 'nodes']:
                            value = [int(x) for x in text.split(',')]
                        elif param in ['element_range', 'node_range']:
                            value = [int(x) for x in text.split(',')][:2]
                        else:
                            value = text
                        setattr(self.region, param, value)

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    from femora.components.Damping.dampingBase import RayleighDamping, ModalDamping

    # Create some sample dampings
    RayleighDamping1 = RayleighDamping(alphaM=0.1, betaK=0.2, betaKInit=0.3, betaKComm=0.4)
    RayleighDamping2 = RayleighDamping(alphaM=0.5, betaK=0.6, betaKInit=0.7, betaKComm=0.8)
    ModalDamping1 = ModalDamping(numberofModes=2, dampingFactors="0.1,0.2")

    # Initialize global region
    global_region = GlobalRegion(damping=RayleighDamping1)

    # Create some sample regions
    element_region = ElementRegion(damping=ModalDamping1, elements=[1, 2, 3], element_only=True)
    node_region = NodeRegion(damping=RayleighDamping2, nodes=[1, 2, 3, 4])

    # Create and show the application
    app = QApplication(sys.argv)
    window = RegionManagerTab()
    window.show()
    sys.exit(app.exec_())