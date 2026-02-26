from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout
)

from femora.core.element_base import Element, ElementRegistry
from femora.components.element import *
from femora.components.Material.materialBase import Material

# Import beam element GUI components
from femora.gui.components.element.beam_gui import (
    BeamElementCreationDialog, BeamElementEditDialog, is_beam_element
)


class ElementManagerTab(QWidget):
    """Manages the creation, display, editing, and deletion of finite elements.

    This tab provides a user interface for interacting with various element
    types registered in the system. It displays elements in a table and allows
    users to create new elements, modify existing ones, or remove them.

    Attributes:
        element_type_combo (QComboBox): Dropdown menu for selecting the type of
            element to create.
        elements_table (QTableWidget): Table widget that displays all
            currently registered elements with their properties.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> from femora.components.transformation.transformation import GeometricTransformation3D
        >>> from femora.components.element import ElasticBeamColumnElement
        >>>
        >>> # Setup some elements for the example
        >>> section = ElasticSection(user_name="Ex Section", E=200000, A=0.01, Iz=1e-6)
        >>> transformation = GeometricTransformation3D(
        ...     transf_type="Linear",
        ...     vecxz_x=1, vecxz_y=0, vecxz_z=-1,
        ...     d_xi=0, d_yi=0, d_zi=0,
        ...     d_xj=1, d_yj=0, d_zj=0
        ... )
        >>> ElasticIsotropicMaterial(user_name="Ex Steel", E=200e3, nu=0.3, rho=7.85e-9)
        >>> ElasticBeamColumnElement(section=section, ndof=6, transformation=transformation)
        >>>
        >>> app = QApplication(sys.argv)
        >>> manager = ElementManagerTab()
        >>> manager.show()
        >>> # app.exec() # Uncomment to run interactively
    """
    def __init__(self, parent=None):
        """Initializes the ElementManagerTab.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)

        # Main layout
        layout = QVBoxLayout(self)

        # Element type selection
        type_layout = QGridLayout()

        # Element type dropdown
        self.element_type_combo = QComboBox()
        self.element_type_combo.addItems(ElementRegistry.get_element_types())

        create_element_btn = QPushButton("Create New Element")
        create_element_btn.clicked.connect(self.open_element_creation_dialog)

        type_layout.addWidget(QLabel("Element Type:"), 0, 0)
        type_layout.addWidget(self.element_type_combo, 0, 1)
        type_layout.addWidget(create_element_btn, 1, 0, 1, 2)

        layout.addLayout(type_layout)

        # Elements table
        self.elements_table = QTableWidget()
        self.elements_table.setColumnCount(6)  # Tag, Type, Material/Section, Parameters, Edit, Delete
        self.elements_table.setHorizontalHeaderLabels(["Tag", "Type", "Material/Section", "Parameters", "Edit", "Delete"])
        header = self.elements_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # Stretch all columns
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Except for the first one

        layout.addWidget(self.elements_table)

        # Refresh elements button
        refresh_btn = QPushButton("Refresh Elements List")
        refresh_btn.clicked.connect(self.refresh_elements_list)
        layout.addWidget(refresh_btn)

        # Initial refresh
        self.refresh_elements_list()

    def open_element_creation_dialog(self):
        """Opens a dialog to create a new element of the selected type.

        The dialog presented depends on the currently selected element type
        (e.g., BeamElementCreationDialog for beam elements).
        The elements list is refreshed if an element is successfully created.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager = ElementManagerTab()
            >>> manager.element_type_combo.setCurrentText("ElasticBeamColumnElement")
            >>> # manager.open_element_creation_dialog() # Would open a dialog
        """
        element_type = self.element_type_combo.currentText()

        # Check if it's a beam element
        if is_beam_element(element_type):
            dialog = BeamElementCreationDialog(element_type, self)
        else:
            dialog = ElementCreationDialog(element_type, self)

        # Only refresh if an element was actually created
        if dialog.exec() == QDialog.Accepted and hasattr(dialog, 'created_element'):
            self.refresh_elements_list()

    def refresh_elements_list(self):
        """Updates the elements table with the current list of registered elements.

        This method clears the existing table content and repopulates it with
        the latest information from the `ElementRegistry`, including tag, type,
        material/section, parameters, and action buttons.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
            >>> from femora.components.section.section_opensees import ElasticSection
            >>> from femora.components.transformation.transformation import GeometricTransformation3D
            >>> from femora.components.element import ElasticBeamColumnElement
            >>>
            >>> section = ElasticSection(user_name="Ex Section", E=200000, A=0.01, Iz=1e-6)
            >>> transformation = GeometricTransformation3D(
            ...     transf_type="Linear", vecxz_x=1, vecxz_y=0, vecxz_z=-1,
            ...     d_xi=0, d_yi=0, d_zi=0, d_xj=1, d_yj=0, d_zj=0
            ... )
            >>> ElasticIsotropicMaterial(user_name="Ex Steel", E=200e3, nu=0.3, rho=7.85e-9)
            >>> ElasticBeamColumnElement(section=section, ndof=6, transformation=transformation)
            >>>
            >>> app = QApplication(sys.argv)
            >>> manager = ElementManagerTab()
            >>> manager.refresh_elements_list()
            >>> # manager.elements_table.rowCount() should be > 0
        """
        # Clear existing rows
        self.elements_table.setRowCount(0)

        # Get all elements
        elements = Element.get_all_elements()

        # Set row count
        self.elements_table.setRowCount(len(elements))

        # Populate table
        for row, (tag, element) in enumerate(elements.items()):
            # Tag
            tag_item = QTableWidgetItem(str(tag))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            self.elements_table.setItem(row, 0, tag_item)

            # Element Type
            type_item = QTableWidgetItem(element.element_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.elements_table.setItem(row, 1, type_item)

            # Material/Section info
            if is_beam_element(element.element_type):
                # Show section info for beam elements
                section_info = f"Section: {element._section.user_name}"
                material_item = QTableWidgetItem(section_info)
            else:
                # Show material info for regular elements
                material = element.get_material()
                material_item = QTableWidgetItem(material.user_name if material else "No Material")

            material_item.setFlags(material_item.flags() & ~Qt.ItemIsEditable)
            self.elements_table.setItem(row, 2, material_item)

            # Parameters
            params_str = ", ".join([f"{k}: {v}" for k, v in element.get_values(element.get_parameters()).items()])
            params_item = QTableWidgetItem(params_str)
            params_item.setFlags(params_item.flags() & ~Qt.ItemIsEditable)
            self.elements_table.setItem(row, 3, params_item)

            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, elem=element: self.open_element_edit_dialog(elem))
            self.elements_table.setCellWidget(row, 4, edit_btn)

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, tag=tag: self.delete_element(tag))
            self.elements_table.setCellWidget(row, 5, delete_btn)

    def open_element_edit_dialog(self, element: Element):
        """Opens a dialog to edit an existing element.

        The dialog displayed (e.g., BeamElementEditDialog) depends on the
        type of the element being edited. The elements list is refreshed if
        changes are successfully saved.

        Args:
            element (Element): The element object to be edited.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
            >>> from femora.components.section.section_opensees import ElasticSection
            >>> from femora.components.transformation.transformation import GeometricTransformation3D
            >>> from femora.components.element import ElasticBeamColumnElement
            >>>
            >>> section = ElasticSection(user_name="Ex Section", E=200000, A=0.01, Iz=1e-6)
            >>> transformation = GeometricTransformation3D(
            ...     transf_type="Linear", vecxz_x=1, vecxz_y=0, vecxz_z=-1,
            ...     d_xi=0, d_yi=0, d_zi=0, d_xj=1, d_yj=0, d_zj=0
            ... )
            >>> material = ElasticIsotropicMaterial(user_name="Ex Steel", E=200e3, nu=0.3, rho=7.85e-9)
            >>> element = ElasticBeamColumnElement(section=section, ndof=6, transformation=transformation)
            >>>
            >>> app = QApplication(sys.argv)
            >>> manager = ElementManagerTab()
            >>> # manager.open_element_edit_dialog(element) # Would open an edit dialog
        """
        # Check if it's a beam element
        print(element.element_type)
        if is_beam_element(element.element_type):
            dialog = BeamElementEditDialog(element, self)
        else:
            dialog = ElementEditDialog(element, self)

        if dialog.exec() == QDialog.Accepted:
            self.refresh_elements_list()

    def delete_element(self, tag: int):
        """Deletes an element from the system after user confirmation.

        A confirmation dialog is shown to the user before proceeding with
        the deletion. If confirmed, the element is removed from the
        `ElementRegistry` and the elements list is refreshed.

        Args:
            tag (int): The unique integer tag of the element to delete.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
            >>> from femora.components.section.section_opensees import ElasticSection
            >>> from femora.components.transformation.transformation import GeometricTransformation3D
            >>> from femora.components.element import ElasticBeamColumnElement
            >>> from femora.core.element_base import Element
            >>>
            >>> section = ElasticSection(user_name="Ex Section", E=200000, A=0.01, Iz=1e-6)
            >>> transformation = GeometricTransformation3D(
            ...     transf_type="Linear", vecxz_x=1, vecxz_y=0, vecxz_z=-1,
            ...     d_xi=0, d_yi=0, d_zi=0, d_xj=1, d_yj=0, d_zj=0
            ... )
            >>> material = ElasticIsotropicMaterial(user_name="Ex Steel", E=200e3, nu=0.3, rho=7.85e-9)
            >>> element = ElasticBeamColumnElement(section=section, ndof=6, transformation=transformation)
            >>>
            >>> app = QApplication(sys.argv)
            >>> manager = ElementManagerTab()
            >>> manager.refresh_elements_list()
            >>> # initial count
            >>> initial_count = Element.get_all_elements().get(element.tag) is not None
            >>> # manager.delete_element(element.tag) # Would open a confirmation dialog
            >>> # if confirmed, Element.get_all_elements().get(element.tag) would be None
        """
        # Confirm deletion
        reply = QMessageBox.question(self, 'Delete Element',
                                     f"Are you sure you want to delete element with tag {tag}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            Element.delete_element(tag)
            self.refresh_elements_list()


class ElementCreationDialog(QDialog):
    """A dialog for creating new finite elements.

    This dialog dynamically generates input fields based on the parameters
    required by the selected element type. It allows users to assign a material,
    specify degrees of freedom (DOF), and input element-specific parameters
    before creating the element.

    Attributes:
        element_type (str): The string identifier for the type of element to create.
        element_class (type[Element]): The actual Python class for the selected
            element type, retrieved from the `ElementRegistry`.
        param_inputs (dict[str, QLineEdit]): A dictionary mapping parameter names
            (str) to their respective QLineEdit input widgets.
        material_combo (QComboBox): Dropdown menu for selecting a material to
            assign to the new element.
        materials (list[Material]): A list of all available material objects
            loaded from the system.
        dof_combo (QComboBox): Dropdown menu for selecting the number of degrees
            of freedom (DOF) for the element.
        created_element (Element): The element instance created by the dialog,
            available after `create_element` is called successfully and the
            dialog accepts.

    Example:
        >>> from qtpy.QtWidgets import QApplication, QDialog
        >>> import sys
        >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
        >>> from femora.components.element import TrussElement
        >>>
        >>> app = QApplication(sys.argv)
        >>> # Ensure some materials are registered for selection
        >>> ElasticIsotropicMaterial(user_name="Steel", E=200e3, nu=0.3, rho=7.85e-9)
        >>> # Create a dialog for TrussElement
        >>> dialog = ElementCreationDialog("TrussElement")
        >>> # dialog.exec() # Uncomment to open the dialog
        >>> if dialog.result() == QDialog.Accepted:
        ...     print(f"Created element: {dialog.created_element.tag}")
    """
    def __init__(self, element_type: str, parent: QWidget = None):
        """Initializes the ElementCreationDialog.

        Args:
            element_type: The string identifier for the type of element to create.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle(f"Create {element_type} Element")
        self.element_type = element_type

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Get the element class
        self.element_class = ElementRegistry._element_types[element_type]

        # Parameter inputs
        self.param_inputs = {}
        parameters = self.element_class.get_parameters()

        # Create a grid layout for input fields
        grid_layout = QGridLayout()

        # Material selection
        self.material_combo = QComboBox()
        self.materials = list(Material.get_all_materials().values())
        self.material_combo.addItem("No Material")
        for material in self.materials:
            self.material_combo.addItem(f"{material.user_name} (Category: {material.material_type} Type: {material.material_name})")
        form_layout.addRow("Assign Material:", self.material_combo)

        # dof selection
        self.dof_combo = QComboBox()
        dofs = self.element_class.get_possible_dofs()
        self.dof_combo.addItems(dofs)
        form_layout.addRow("Assign DOF:", self.dof_combo)

        # Add label and input fields to the grid layout
        row = 0
        description = self.element_class.get_description()
        for param,desc in zip(parameters,description):
            input_field = QLineEdit()

            # Add the label and input field to the grid
            grid_layout.addWidget(QLabel(param), row, 0)  # Label in column 0
            grid_layout.addWidget(input_field, row, 1)  # Input field in column 1
            grid_layout.addWidget(QLabel(desc), row, 2)  # Description in column 2

            self.param_inputs[param] = input_field
            row += 1

        # Add the grid layout to the form
        form_layout.addRow(grid_layout)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Element")
        create_btn.clicked.connect(self.create_element)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def create_element(self) -> Element:
        """Creates a new element based on the input values in the dialog.

        Validates the input parameters, material, and DOF, then creates
        the element using the `ElementRegistry`. On successful creation,
        the dialog accepts and the `created_element` attribute is set.

        Returns:
            Element: The newly created element instance.

        Raises:
            ValueError: If any input is invalid or a compatible material
                is not selected.
            Exception: For any other unexpected errors during element creation.

        Example:
            >>> from qtpy.QtWidgets import QApplication, QDialog
            >>> import sys
            >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
            >>> from femora.components.element import TrussElement
            >>>
            >>> app = QApplication(sys.argv)
            >>> material = ElasticIsotropicMaterial(user_name="Steel for Truss", E=200e3, nu=0.3, rho=7.85e-9)
            >>> dialog = ElementCreationDialog("TrussElement")
            >>>
            >>> # Simulate user input
            >>> dialog.material_combo.setCurrentText("Steel for Truss (Category: Isotropic Material Type: ElasticIsotropicMaterial)")
            >>> dialog.dof_combo.setCurrentText("2")
            >>> # If TrussElement expects a 'length' parameter:
            >>> if 'length' in dialog.param_inputs:
            ...     dialog.param_inputs['length'].setText("10.0")
            >>>
            >>> # Try creating the element
            >>> # dialog.create_element()
            >>> # if dialog.result() == QDialog.Accepted:
            >>> #     print(f"Element created: {dialog.created_element.tag}")
        """
        try:
            # Assign material if selected
            material_index = self.material_combo.currentIndex()
            if material_index > 0:
                material = self.materials[material_index - 1]
                if not self.element_class._is_material_compatible(material):
                    raise ValueError("Selected material is not compatible with element type")
            else:
                raise ValueError("Please select a material for the element")

            # Assign DOF if selected
            dof = self.dof_combo.currentText()
            if dof:
                dof = int(dof)
            else:
                raise ValueError("Invalid number of DOFs returned")

            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                value = input_field.text().strip()
                if value:
                    params[param] = value

            params = self.element_class.validate_element_parameters(**params)
            # Create element
            self.created_element = ElementRegistry.create_element(
                element_type=self.element_type,
                ndof=dof,
                material=material,
                **params
            )
            self.accept()

            # Return the created element
            return self.created_element

        except ValueError as e:
            QMessageBox.warning(self, "Input Error",
                                f"Invalid input: {str(e)}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class ElementEditDialog(QDialog):
    """A dialog for editing existing finite elements.

    This dialog allows users to modify the material, degrees of freedom (DOF),
    and element-specific parameters of an already created element. It pre-populates
    fields with the element's current values to facilitate editing.

    Attributes:
        element (Element): The element instance being edited.
        material_combo (QComboBox): Dropdown menu for selecting a material to
            assign to the element.
        materials (list[Material]): A list of all available material objects
            loaded from the system.
        dof_combo (QComboBox): Dropdown menu for selecting the number of degrees
            of freedom (DOF) for the element.
        param_inputs (dict[str, QLineEdit]): A dictionary mapping parameter names
            (str) to their respective QLineEdit input widgets.

    Example:
        >>> from qtpy.QtWidgets import QApplication, QDialog
        >>> import sys
        >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> from femora.components.transformation.transformation import GeometricTransformation3D
        >>> from femora.components.element import ElasticBeamColumnElement
        >>>
        >>> app = QApplication(sys.argv)
        >>> # Setup an element to edit
        >>> material_old = ElasticIsotropicMaterial(user_name="Old Steel", E=200e3, nu=0.3, rho=7.85e-9)
        >>> material_new = ElasticIsotropicMaterial(user_name="New Aluminum", E=70e3, nu=0.33, rho=2.7e-9)
        >>> section = ElasticSection(user_name="Ex Section", E=200000, A=0.01, Iz=1e-6)
        >>> transformation = GeometricTransformation3D(
        ...     transf_type="Linear", vecxz_x=1, vecxz_y=0, vecxz_z=-1,
        ...     d_xi=0, d_yi=0, d_zi=0, d_xj=1, d_yj=0, d_zj=0
        ... )
        >>> element_to_edit = ElasticBeamColumnElement(
        ...     section=section, ndof=6, transformation=transformation, material=material_old
        ... )
        >>>
        >>> dialog = ElementEditDialog(element_to_edit)
        >>> # dialog.exec() # Uncomment to open the dialog
        >>> if dialog.result() == QDialog.Accepted:
        ...     print(f"Element {element_to_edit.tag} updated.")
    """
    def __init__(self, element: Element, parent: QWidget = None):
        """Initializes the ElementEditDialog.

        Args:
            element: The `Element` object to be edited.
            parent (QWidget, optional): The parent widget. Defaults to None.

        Raises:
            ValueError: If the current element's DOF is not found in the
                possible DOFs.
        """
        super().__init__(parent)
        self.element = element
        self.setWindowTitle(f"Edit {element.element_type} Element (Tag: {element.tag})")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Material selection
        self.material_combo = QComboBox()
        self.materials = list(Material.get_all_materials().values())
        self.material_combo.addItem("No Material")

        current_material = element.get_material()
        selected_index = 0
        for i, material in enumerate(self.materials):
            self.material_combo.addItem(f"{material.user_name} (Category: {material.material_type} Type: {material.material_name})")
            if current_material and current_material.user_name == material.user_name:
                selected_index = i + 1

        self.material_combo.setCurrentIndex(selected_index)
        form_layout.addRow("Assign Material:", self.material_combo)

        # dof selection
        self.dof_combo = QComboBox()
        dofs = self.element.get_possible_dofs()
        self.dof_combo.addItems(dofs)
        if str(self.element._ndof) in dofs:
            self.dof_combo.setCurrentText(str(self.element._ndof))
        else:
            raise ValueError("Invalid number of DOFs returned")
        form_layout.addRow("Assign DOF:", self.dof_combo)

        # Parameters
        self.param_inputs = {}
        parameters = self.element.__class__.get_parameters()
        descriptions = self.element.__class__.get_description()
        current_values = self.element.get_values(parameters)

        # Create a grid layout for input fields
        grid_layout = QGridLayout()

        row = 0
        for param, desc in zip(parameters, descriptions):
            input_field = QLineEdit()
            if param in current_values and current_values[param] is not None:
                input_field.setText(str(current_values[param]))

            # Add the label and input field to the grid
            grid_layout.addWidget(QLabel(param), row, 0)  # Label in column 0
            grid_layout.addWidget(input_field, row, 1)  # Input field in column 1
            grid_layout.addWidget(QLabel(desc), row, 2)  # Description in column 2

            self.param_inputs[param] = input_field
            row += 1

        # Add the grid layout to the form
        form_layout.addRow(grid_layout)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_changes(self):
        """Saves the changes made to the element based on the dialog's input.

        Validates the new material, DOF, and element-specific parameters,
        then updates the `element` object. On successful update, a confirmation
        message is shown and the dialog accepts.

        Raises:
            ValueError: If any input is invalid or a compatible material
                is not selected.
            Exception: For any other unexpected errors during saving changes.

        Example:
            >>> from qtpy.QtWidgets import QApplication, QDialog
            >>> import sys
            >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
            >>> from femora.components.section.section_opensees import ElasticSection
            >>> from femora.components.transformation.transformation import GeometricTransformation3D
            >>> from femora.components.element import ElasticBeamColumnElement
            >>>
            >>> app = QApplication(sys.argv)
            >>> material_old = ElasticIsotropicMaterial(user_name="Old Steel", E=200e3, nu=0.3, rho=7.85e-9)
            >>> material_new = ElasticIsotropicMaterial(user_name="New Aluminum", E=70e3, nu=0.33, rho=2.7e-9)
            >>> section = ElasticSection(user_name="Ex Section", E=200000, A=0.01, Iz=1e-6)
            >>> transformation = GeometricTransformation3D(
            ...     transf_type="Linear", vecxz_x=1, vecxz_y=0, vecxz_z=-1,
            ...     d_xi=0, d_yi=0, d_zi=0, d_xj=1, d_yj=0, d_zj=0
            ... )
            >>> element_to_edit = ElasticBeamColumnElement(
            ...     section=section, ndof=6, transformation=transformation, material=material_old
            ... )
            >>>
            >>> dialog = ElementEditDialog(element_to_edit)
            >>>
            >>> # Simulate user input for changes
            >>> dialog.material_combo.setCurrentText("New Aluminum (Category: Isotropic Material Type: ElasticIsotropicMaterial)")
            >>> dialog.dof_combo.setCurrentText("3")
            >>> # if BeamElement has a 'length' parameter that could be edited:
            >>> # if 'length' in dialog.param_inputs:
            >>> #     dialog.param_inputs['length'].setText("12.0")
            >>>
            >>> # Try saving changes
            >>> # dialog.save_changes()
            >>> # if dialog.result() == QDialog.Accepted:
            >>> #     print(f"Element {element_to_edit.tag} material updated to {element_to_edit.get_material().user_name}.")
        """
        try:
            # Assign material if selected
            material_index = self.material_combo.currentIndex()
            if material_index > 0:
                material = self.materials[material_index - 1]
                if not self.element.__class__._is_material_compatible(material):
                    raise ValueError("Selected material is not compatible with element type")
                self.element.assign_material(material)

            # Update DOF
            dof = int(self.dof_combo.currentText())
            self.element._ndof = dof

            # Collect and validate parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                value = input_field.text().strip()
                if value:
                    params[param] = value

            if params:
                validated_params = self.element.__class__.validate_element_parameters(**params)
                self.element.update_values(validated_params)

            QMessageBox.information(self, "Success", f"Element '{self.element.tag}' updated successfully!")
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    import sys
    from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial, ElasticUniaxialMaterial
    from femora.components.section.section_opensees import ElasticSection
    from femora.components.transformation.transformation import GeometricTransformation3D
    from femora.components.element import ElasticBeamColumnElement


    # Create test data
    section = ElasticSection(user_name="Test Section", E=200000, A=0.01, Iz=1e-6)
    transformation = GeometricTransformation3D(
        transf_type="Linear",
        vecxz_x=1, vecxz_y=0, vecxz_z=-1,
        d_xi=0, d_yi=0, d_zi=0,
        d_xj=1, d_yj=0, d_zj=0
    )
    # Create the Qt Application
    app = QApplication(sys.argv)

    ElasticIsotropicMaterial(user_name="Steel", E=200e3, nu=0.3, rho=7.85e-9)
    ElasticIsotropicMaterial(user_name="Concrete", E=30e3, nu=0.2, rho=24e-9)
    ElasticIsotropicMaterial(user_name="Aluminum", E=70e3, nu=0.33, rho=2.7e-9)
    ElasticUniaxialMaterial(user_name="Steel2", E=200e3, eta=0.1)
    ElasticBeamColumnElement(section=section, ndof=6, transformation=transformation)
    # Create and show the ElementManagerTab directly
    element_manager_tab = ElementManagerTab()
    element_manager_tab.show()

    sys.exit(app.exec())