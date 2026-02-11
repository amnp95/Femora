"""
Beam Element GUI Components for FEMORA
Handles creation and editing of beam-column elements with sections and transformations
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox,
    QMessageBox, QGroupBox, QWidget
)
from qtpy.QtCore import Qt

from femora.core.element_base import ElementRegistry
from femora.components.section.section_base import Section, SectionManager
from femora.components.transformation.transformation import GeometricTransformation, GeometricTransformationManager
from femora.components.transformation.transformation_gui import TransformationWidget3D


def setup_section_dropdown(combo_box: QComboBox, placeholder_text: str = "Select Section"):
    """Populates a QComboBox with available section objects.

    This function clears the given QComboBox and adds a placeholder item,
    followed by all sections retrieved from the `Section` registry. Each
    section is displayed using its `user_name` and `section_name`.

    Args:
        combo_box: The QComboBox widget to populate.
        placeholder_text: The text for the initial, non-selectable item
            in the dropdown.
    
    Example:
        >>> from qtpy.QtWidgets import QApplication, QComboBox
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> app = QApplication([])
        >>> combo = QComboBox()
        >>> # Assume ElasticSection is registered with 'get_all_sections'
        >>> ElasticSection(tag=1, user_name="Concrete Rect", E=30e9, G=12e9, A=0.1, Iy=1e-3, Iz=2e-3, J=3e-3)
        >>> setup_section_dropdown(combo)
        >>> print(combo.itemText(0))
        Select Section
        >>> print(combo.itemText(1)) # Assuming 'Concrete Rect' is the first added section
        Concrete Rect (ElasticSection)
        >>> app.quit()
    """
    combo_box.clear()
    combo_box.addItem(placeholder_text)
    
    sections = Section.get_all_sections()
    for section in sections.values():
        display_text = f"{section.user_name} ({section.section_name})"
        combo_box.addItem(display_text, section)


def validate_section_selection(combo_box: QComboBox, field_name: str = "Section") -> tuple[bool, Section | None, str]:
    """Validates the selection in a QComboBox assumed to contain section objects.

    Checks if a valid section has been selected from the dropdown (i.e., not
    the placeholder item and the data associated with the item is a `Section` object).

    Args:
        combo_box: The QComboBox widget containing section selections.
        field_name: The name of the field, used in error messages.

    Returns:
        A tuple containing:
        - bool: True if a valid section is selected, False otherwise.
        - Section | None: The selected Section object, or None if invalid.
        - str: An empty string if valid, or an error message if invalid.
    
    Example:
        >>> from qtpy.QtWidgets import QApplication, QComboBox
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> app = QApplication([])
        >>> combo = QComboBox()
        >>> combo.addItem("Select Section") # Placeholder
        >>> # Add a valid section
        >>> section1 = ElasticSection(tag=1, user_name="Rect Section", E=200e9, A=0.01, Iz=1e-6)
        >>> combo.addItem("Rect Section", section1)
        >>> # Test invalid selection (placeholder)
        >>> combo.setCurrentIndex(0)
        >>> is_valid, sec, msg = validate_section_selection(combo)
        >>> print(is_valid)
        False
        >>> # Test valid selection
        >>> combo.setCurrentIndex(1)
        >>> is_valid, sec, msg = validate_section_selection(combo)
        >>> print(is_valid)
        True
        >>> print(sec.user_name)
        Rect Section
        >>> app.quit()
    """
    if combo_box.currentIndex() == 0:
        return False, None, f"Please select a {field_name.lower()}."
    
    section = combo_box.currentData()
    if section is None:
        return False, None, f"Invalid {field_name.lower()} selection."
    
    return True, section, ""


class BeamElementCreationDialog(QDialog):
    """A dialog window for creating new beam-column elements in FEMORA.

    This dialog allows users to define parameters such as degrees of freedom,
    cross-section, geometric transformation, and other element-specific properties
    before instantiating a new beam-column element.

    Attributes:
        element_type (str): The string identifier for the type of element being created.
        created_element (object | None): The instantiated element object after successful creation,
            or None if the creation was cancelled or failed.
        element_class (type): The actual Python class corresponding to `element_type`.
        dof_combo (QComboBox): Dropdown for selecting the degrees of freedom (e.g., 3D or 6D).
        section_combo (QComboBox): Dropdown for selecting the cross-section.
        transformation_widget (TransformationWidget3D): Widget for defining the geometric transformation.
        param_inputs (dict[str, QLineEdit | QCheckBox]): Dictionary mapping parameter names to their
            corresponding input widgets (QLineEdit or QCheckBox).
    
    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> from femora.components.element import ElasticBeamColumnElement # Required for setup
        >>>
        >>> app = QApplication(sys.argv)
        >>>
        >>> # Ensure a section is registered for selection in the dialog
        >>> ElasticSection(tag=100, user_name="Default Rect", E=200e9, A=0.1, Iz=1e-6)
        >>>
        >>> dialog = BeamElementCreationDialog("ElasticBeamColumn")
        >>> dialog.exec_() # Show the dialog for user interaction
        >>>
        >>> if dialog.created_element:
        >>>     print(f"Element created: {dialog.created_element.element_type} with tag {dialog.created_element.tag}")
        >>> else:
        >>>     print("Element creation cancelled or failed.")
        >>>
        >>> app.quit()
    """
    
    def __init__(self, element_type: str, parent: QWidget | None = None):
        """Initializes the BeamElementCreationDialog.

        Args:
            element_type: The string identifier for the type of beam element
                to be created (e.g., "ElasticBeamColumn").
            parent: The parent widget for this dialog, defaults to None.
        """
        super().__init__(parent)
        self.element_type = element_type
        self.setWindowTitle(f"Create {element_type} Element")
        self.created_element = None
        
        # Get element class
        self.element_class = ElementRegistry._element_types[element_type]
        
        self.setup_ui()
    
    def setup_ui(self):
        """Sets up the user interface for the element creation dialog.

        This method initializes and arranges all widgets, including the DOF
        selector, section dropdown, transformation widget, element parameters
        group, and action buttons.
        """
        layout = QVBoxLayout(self)
        
        # Form layout for main inputs
        form_layout = QFormLayout()
        
        # DOF selection
        self.dof_combo = QComboBox()
        if hasattr(self.element_class, 'get_possible_dofs'):
            dofs = self.element_class.get_possible_dofs()
            if not dofs:
                dofs = ["3", "6"]
        else:
            dofs = ["3", "6"]  # Default for beam elements
        self.dof_combo.addItems(dofs)
        form_layout.addRow("Degrees of Freedom:", self.dof_combo)
        
        # Section selection
        self.section_combo = QComboBox()
        setup_section_dropdown(self.section_combo)
        form_layout.addRow("Section:", self.section_combo)
        
        layout.addLayout(form_layout)
        
        # Transformation widget (3D)
        self.transformation_widget = TransformationWidget3D()
        layout.addWidget(QLabel("Geometric Transformation:"))
        layout.addWidget(self.transformation_widget)
        
        # Parameters group
        self.setup_parameters_group(layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Element")
        create_btn.clicked.connect(self.create_element)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def setup_parameters_group(self, main_layout: QVBoxLayout):
        """Sets up the group box for element-specific parameters.

        This method dynamically creates input fields (QLineEdit or QCheckBox)
        for each parameter defined by the `element_class.get_parameters()` method,
        along with their descriptions, and adds them to a QGroupBox.

        Args:
            main_layout: The main QVBoxLayout of the dialog to which the
                parameters group box will be added.
        """
        params_group = QGroupBox("Element Parameters")
        params_layout = QGridLayout(params_group)
        
        self.param_inputs = {}
        parameters = self.element_class.get_parameters()
        descriptions = self.element_class.get_description()
        
        for row, (param, desc) in enumerate(zip(parameters, descriptions)):
            param_label = QLabel(param + ":")
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            desc_label.setWordWrap(True)
            
            if param == "cMass":
                # Special handling for boolean cMass parameter
                param_input = QCheckBox("Use consistent mass matrix")
            else:
                param_input = QLineEdit()
                param_input.setPlaceholderText(f"Enter {param}")
            
            params_layout.addWidget(param_label, row, 0)
            params_layout.addWidget(param_input, row, 1)
            params_layout.addWidget(desc_label, row, 2)
            
            self.param_inputs[param] = param_input
        
        main_layout.addWidget(params_group)
    
    def create_element(self):
        """Creates the beam element based on the user inputs in the dialog.

        This method validates all user inputs (DOF, section, transformation,
        and element-specific parameters), then uses the `ElementRegistry`
        to instantiate the element. Upon successful creation, an information
        message is displayed, and the dialog is accepted.
        If any input is invalid or an error occurs during element creation,
        a warning or critical error message is displayed.

        Raises:
            ValueError: If any input field contains invalid data that cannot
                be processed (e.g., non-numeric where a number is expected).
            Exception: For any other unexpected errors during the element
                creation process.
        """
        try:
            # Validate DOF
            dof = int(self.dof_combo.currentText())
            
            # Validate section
            is_valid, section, error_msg = validate_section_selection(self.section_combo)
            if not is_valid:
                QMessageBox.warning(self, "Input Error", error_msg)
                return
            
            # Get transformation from widget
            transformation = self.transformation_widget.get_transformation()
            if transformation is None:
                QMessageBox.warning(self, "Input Error", "Please provide a valid geometric transformation.")
                return
            
            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                if param == "cMass":
                    params[param] = input_field.isChecked()
                else:
                    value = input_field.text().strip()
                    if value:
                        params[param] = value
            
            # Validate parameters
            if params:
                params = self.element_class.validate_element_parameters(**params)
            
            # Create element
            self.created_element = ElementRegistry.create_element(
                element_type=self.element_type,
                ndof=dof,
                section=section,
                transformation=transformation,
                **params
            )
            
            QMessageBox.information(self, "Success", 
                                  f"{self.element_type} element created successfully!")
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create element: {str(e)}")


class BeamElementEditDialog(QDialog):
    """A dialog window for editing existing beam-column elements in FEMORA.

    This dialog pre-populates its input fields with the current values of
    an existing element and allows users to modify its degrees of freedom,
    cross-section, geometric transformation, and other element-specific properties.

    Attributes:
        element (object): The existing element object to be edited. Expected to be
            an instance of a class registered in `ElementRegistry`, with attributes
            like `element_type`, `tag`, `_ndof`, `_section`, `_transformation`,
            and methods like `get_values`, `update_values`, etc.
        dof_combo (QComboBox): Dropdown for selecting the degrees of freedom (e.g., 3D or 6D).
        section_combo (QComboBox): Dropdown for selecting the cross-section.
        transformation_widget (TransformationWidget3D): Widget for defining the geometric transformation.
        param_inputs (dict[str, QLineEdit | QCheckBox]): Dictionary mapping parameter names to their
            corresponding input widgets (QLineEdit or QCheckBox).
    
    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> from femora.components.transformation.transformation import GeometricTransformation3D
        >>> from femora.components.element import ElasticBeamColumnElement
        >>>
        >>> app = QApplication(sys.argv)
        >>>
        >>> # Create a dummy element for editing
        >>> section_orig = ElasticSection(tag=1, user_name="Original Section", E=200e9, A=0.01, Iz=1e-6)
        >>> transf_orig = GeometricTransformation3D(transf_type="Linear", vecxz_x=1, vecxz_y=0, vecxz_z=0)
        >>> dummy_element = ElasticBeamColumnElement(ndof=6, section=section_orig, transformation=transf_orig, tag=99)
        >>>
        >>> # Ensure another section exists for selection in the dialog
        >>> ElasticSection(tag=2, user_name="New Rect Section", E=210e9, A=0.015, Iz=1.5e-6)
        >>>
        >>> dialog = BeamElementEditDialog(dummy_element)
        >>> dialog.exec_() # Show the dialog for user interaction
        >>>
        >>> if dialog.result() == QDialog.Accepted:
        >>>     print(f"Element {dummy_element.tag} updated. New section: {dummy_element._section.user_name}")
        >>> else:
        >>>     print("Element editing cancelled.")
        >>>
        >>> app.quit()
    """
    
    def __init__(self, element: object, parent: QWidget | None = None):
        """Initializes the BeamElementEditDialog.

        Args:
            element: The existing element object to be edited. It is expected
                to have attributes like `element_type`, `tag`, `_ndof`,
                `_section`, `_transformation`, and methods like `get_values`,
                `update_values`, `__class__.get_parameters()`, etc.
            parent: The parent widget for this dialog, defaults to None.
        """
        super().__init__(parent)
        self.element = element
        self.setWindowTitle(f"Edit {element.element_type} Element (Tag: {element.tag})")
        
        self.setup_ui()
        self.load_current_values()
    
    def setup_ui(self):
        """Sets up the user interface for the element editing dialog.

        This method initializes and arranges all widgets, including the DOF
        selector, section dropdown, transformation widget, element parameters
        group, and action buttons for saving or canceling changes.
        """
        layout = QVBoxLayout(self)
        
        # Form layout for main inputs
        form_layout = QFormLayout()
        
        # DOF selection
        self.dof_combo = QComboBox()
        if hasattr(self.element.__class__, 'get_possible_dofs'):
            dofs = self.element.__class__.get_possible_dofs()
            if not dofs:
                dofs = ["3", "6"]
        else:
            dofs = ["3", "6"]
        self.dof_combo.addItems(dofs)
        form_layout.addRow("Degrees of Freedom:", self.dof_combo)
        
        # Section selection
        self.section_combo = QComboBox()
        setup_section_dropdown(self.section_combo)
        form_layout.addRow("Section:", self.section_combo)
        
        layout.addLayout(form_layout)
        
        # Transformation widget
        self.transformation_widget = TransformationWidget3D()
        layout.addWidget(QLabel("Geometric Transformation:"))
        layout.addWidget(self.transformation_widget)
        
        # Parameters group
        self.setup_parameters_group(layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def setup_parameters_group(self, main_layout: QVBoxLayout):
        """Sets up the group box for element-specific parameters.

        This method dynamically creates input fields (QLineEdit or QCheckBox)
        for each parameter defined by the `element.__class__.get_parameters()` method,
        along with their descriptions, and adds them to a QGroupBox.

        Args:
            main_layout: The main QVBoxLayout of the dialog to which the
                parameters group box will be added.
        """
        params_group = QGroupBox("Element Parameters")
        params_layout = QGridLayout(params_group)
        
        self.param_inputs = {}
        parameters = self.element.__class__.get_parameters()
        descriptions = self.element.__class__.get_description()
        
        for row, (param, desc) in enumerate(zip(parameters, descriptions)):
            param_label = QLabel(param + ":")
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            desc_label.setWordWrap(True)
            
            if param == "cMass":
                param_input = QCheckBox("Use consistent mass matrix")
            else:
                param_input = QLineEdit()
                param_input.setPlaceholderText(f"Enter {param}")
            
            params_layout.addWidget(param_label, row, 0)
            params_layout.addWidget(param_input, row, 1)
            params_layout.addWidget(desc_label, row, 2)
            
            self.param_inputs[param] = param_input
        
        main_layout.addWidget(params_group)
    
    def load_current_values(self):
        """Loads the current values of the `element` into the dialog's input fields.

        This method populates the DOF combo box, sets the current section in
        the section dropdown, loads the transformation data into the
        `TransformationWidget3D`, and fills in all element-specific parameter
        input fields (QLineEdit or QCheckBox) with the element's existing values.
        """
        # Set DOF
        self.dof_combo.setCurrentText(str(self.element._ndof))
        
        # Set section
        current_section = self.element._section
        for i in range(self.section_combo.count()):
            section = self.section_combo.itemData(i)
            if section and section.tag == current_section.tag:
                self.section_combo.setCurrentIndex(i)
                break
        
        # Set transformation in widget
        current_transformation = self.element._transformation
        self.transformation_widget.load_transformation(current_transformation)
        
        # Set parameters
        current_values = self.element.get_values(self.element.__class__.get_parameters())
        for param, input_field in self.param_inputs.items():
            if param in current_values:
                value = current_values[param]
                if param == "cMass":
                    input_field.setChecked(bool(value))
                else:
                    input_field.setText(str(value))
    
    def save_changes(self):
        """Saves the modified values from the dialog's input fields back to the element.

        This method validates all user inputs (DOF, section, transformation,
        and element-specific parameters). If valid, it updates the `element`'s
        properties using its `update_values` method and adjusts the degrees
        of freedom if changed. Upon successful update, an information message
        is displayed, and the dialog is accepted.
        If any input is invalid or an error occurs during the update process,
        a warning or critical error message is displayed.

        Raises:
            ValueError: If any input field contains invalid data that cannot
                be processed (e.g., non-numeric where a number is expected).
            Exception: For any other unexpected errors during the element
                update process.
        """
        try:
            # Validate section
            is_valid, section, error_msg = validate_section_selection(self.section_combo)
            if not is_valid:
                QMessageBox.warning(self, "Input Error", error_msg)
                return
            
            # Get transformation from widget
            transformation = self.transformation_widget.get_transformation()
            if transformation is None:
                QMessageBox.warning(self, "Input Error", "Please provide a valid geometric transformation.")
                return
            
            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                if param == "cMass":
                    params[param] = input_field.isChecked()
                else:
                    value = input_field.text().strip()
                    if value:
                        params[param] = value
            
            # Add section and transformation to update values
            params["section"] = section
            params["transformation"] = transformation
            
            # Update element
            self.element.update_values(params)
            
            # Update DOF if changed
            new_dof = int(self.dof_combo.currentText())
            if new_dof != self.element._ndof:
                self.element._ndof = new_dof
            
            QMessageBox.information(self, "Success", 
                                  f"Element '{self.element.tag}' updated successfully!")
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update element: {str(e)}")


def is_beam_element(element_type: str) -> bool:
    """Checks if a given element type string corresponds to a known beam element.

    Args:
        element_type: The string identifier of the element type to check.

    Returns:
        True if the element type is a recognized beam element, False otherwise.
    
    Example:
        >>> is_beam_element("ElasticBeamColumn")
        True
        >>> is_beam_element("truss")
        False
        >>> is_beam_element("elasticBeamColumn") # Case-insensitive check
        True
    """
    beam_types = [
        'elasticbeamcolumn',
        'dispbeamcolumn',
        'nonlinearbeamcolumn',
        'forcebasedbeamcolumn'
    ]
    return element_type.lower() in beam_types


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    from femora.components.section.section_opensees import ElasticSection
    from femora.components.transformation.transformation import GeometricTransformation3D

    app = QApplication(sys.argv)

    # Create test data
    section = ElasticSection(user_name="Test Section", E=200000, A=0.01, Iz=1e-6)
    transformation = GeometricTransformation3D(
        transf_type="Linear",
        vecxz_x=1, vecxz_y=0, vecxz_z=-1,
        d_xi=0, d_yi=0, d_zi=0,
        d_xj=1, d_yj=0, d_zj=0
    )

    # Test creation dialog
    creation_dialog = BeamElementCreationDialog("ElasticBeamColumn")
    creation_dialog.show()

    # If you want to test the edit dialog, you need a dummy element instance.
    # Here is an example assuming your element class is ElasticBeamColumn and takes these arguments:
    from femora.components.element import ElasticBeamColumnElement

    # Create a dummy element for editing
    dummy_element = ElasticBeamColumnElement(ndof=6, section=section, transformation=transformation)
    # Test edit dialog
    edit_dialog = BeamElementEditDialog(dummy_element)
    edit_dialog.show()

    sys.exit(app.exec())