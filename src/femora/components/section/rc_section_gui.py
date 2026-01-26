"""Provides dialogs for creating and editing Reinforced Concrete (RC) sections.

This module encapsulates the user interface logic for interacting with
`RCSection` objects, ensuring consistency by utilizing `RCSection` class
methods for parameter management and validation.
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QFormLayout, QMessageBox, 
    QGridLayout, QFrame, QTextBrowser, QGroupBox, QWidget
)
from qtpy.QtCore import Qt

from femora.components.section.section_opensees import RCSection
from femora.components.Material.materialBase import Material
from femora.components.section.section_gui_utils import (
    setup_uniaxial_material_dropdown, get_material_by_combo_selection, set_combo_to_material, validate_material_selection
)

class RCSectionCreationDialog(QDialog):
    """A dialog for creating new Reinforced Concrete (RC) sections.

    This dialog provides a graphical interface to define and create `RCSection`
    objects by collecting user inputs for geometric and material parameters. It
    reverages `RCSection` class methods for parameter retrieval, description,
    and validation, ensuring data consistency.

    Attributes:
        parameters (list[str]): A list of parameter names required for the RC section.
        descriptions (list[str]): A list of detailed descriptions for each parameter.
        user_name_input (QLineEdit): Input field for the new section's unique name.
        param_inputs (dict[str, QWidget]): A dictionary mapping parameter names
            to their respective input widgets (QLineEdit or QComboBox).
        created_section (RCSection): The `RCSection` object created upon successful
            submission of the dialog. This attribute is set only after the
            `create_section` method successfully executes and the dialog
            accepts.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.section.section_opensees import RCSection
        >>> from femora.components.Material.uniaxial_concrete import Concrete01
        >>> from femora.components.Material.uniaxial_steel import Steel01
        >>> app = QApplication([])
        >>> Concrete01("C_example", 30, 0.002, 0.004) # Register example materials
        >>> Steel01("S_example", 400, 0.001)
        >>> dialog = RCSectionCreationDialog()
        >>> # To actually interact with the dialog, use dialog.exec_().
        >>> # For this example, we just show it can be instantiated.
        >>> print(dialog.windowTitle())
        Create RC Section
        >>> app.quit()
    """

    def __init__(self, parent=None):
        """Initializes the RCSectionCreationDialog.

        Args:
            parent (QWidget, optional): The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Create RC Section")
        self.setMinimumSize(800, 600)
        
        self.parameters = RCSection.get_parameters()
        self.descriptions = RCSection.get_description()
        
        main_layout = QHBoxLayout(self)
        
        # Left side - Parameters
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Section name group
        name_group = QGroupBox("Section Identification")
        name_layout = QFormLayout(name_group)
        self.user_name_input = QLineEdit()
        self.user_name_input.setPlaceholderText("Enter unique section name")
        name_layout.addRow("Section Name:", self.user_name_input)
        left_layout.addWidget(name_group)
        
        # Parameters group
        parameters_group = QGroupBox("Section Parameters")
        parameters_layout = QGridLayout(parameters_group)
        self.param_inputs = {}
        
        for row, (param, description) in enumerate(zip(self.parameters, self.descriptions)):
            param_label = QLabel(f"{param}:")
            if param in ("core_material", "cover_material", "steel_material"):
                param_input = QComboBox()
                setup_uniaxial_material_dropdown(param_input, f"Select {param.replace('_', ' ').capitalize()}")
                param_input.setToolTip(f"Select {param.replace('_', ' ')} (uniaxial material)")
            else:
                param_input = QLineEdit()
                param_input.setPlaceholderText(f"Enter {param}")
                param_input.setToolTip("Enter a positive number")
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            parameters_layout.addWidget(param_label, row, 0)
            parameters_layout.addWidget(param_input, row, 1)
            parameters_layout.addWidget(desc_label, row, 2)
            self.param_inputs[param] = param_input
        left_layout.addWidget(parameters_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Section")
        create_btn.clicked.connect(self.create_section)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        left_layout.addLayout(btn_layout)
        left_layout.addStretch()
        main_layout.addWidget(left_widget)
        
        # Vertical line separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Right side - Help text from class
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        help_display = QTextBrowser()
        help_display.setHtml(RCSection.get_help_text())
        right_layout.addWidget(help_display)
        main_layout.addWidget(right_widget)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def create_section(self):
        """Attempts to create an `RCSection` object based on user inputs.

        This method validates the collected section name and parameters,
        including material selections. If all inputs are valid, a new
        `RCSection` instance is created and stored in `self.created_section`,
        and the dialog is accepted. Otherwise, error messages are displayed.

        Raises:
            ValueError: If any numeric parameter input is invalid or
                if section validation fails (e.g., non-positive dimensions).
            KeyError: If a material selected in the dropdown cannot be found.
            Exception: For any other unexpected errors during section creation.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.section.section_opensees import RCSection
            >>> from femora.components.Material.uniaxial_concrete import Concrete01
            >>> from femora.components.Material.uniaxial_steel import Steel01
            >>> app = QApplication([])
            >>> Concrete01("ConcreteC30", 30, 0.002, 0.004)
            >>> Steel01("SteelS400", 400, 0.001)
            >>> dialog = RCSectionCreationDialog()
            >>> dialog.user_name_input.setText("NewRCSection")
            >>> dialog.param_inputs["core_material"].setCurrentText("ConcreteC30")
            >>> dialog.param_inputs["cover_material"].setCurrentText("ConcreteC30")
            >>> dialog.param_inputs["steel_material"].setCurrentText("SteelS400")
            >>> dialog.param_inputs["depth"].setText("600")
            >>> dialog.param_inputs["width"].setText("400")
            >>> dialog.param_inputs["cover_depth"].setText("60")
            >>> dialog.param_inputs["num_bars_top"].setText("4")
            >>> dialog.param_inputs["bar_area_top"].setText("400")
            >>> dialog.param_inputs["num_bars_bottom"].setText("4")
            >>> dialog.param_inputs["bar_area_bottom"].setText("400")
            >>> dialog.create_section()
            >>> if dialog.result() == QApplication.DialogCode.Accepted:
            ...     section = dialog.created_section
            ...     print(section.user_name)
            NewRCSection
            >>> app.quit()
        """
        try:
            user_name = self.user_name_input.text().strip()
            if not user_name:
                QMessageBox.warning(self, "Input Error", "Please enter a section name.")
                return
            try:
                existing_section = RCSection.get_section_by_name(user_name)
                QMessageBox.warning(self, "Input Error", f"Section with name '{user_name}' already exists.")
                return
            except KeyError:
                pass
            # Collect materials
            core_material = get_material_by_combo_selection(self.param_inputs["core_material"])
            cover_material = get_material_by_combo_selection(self.param_inputs["cover_material"])
            steel_material = get_material_by_combo_selection(self.param_inputs["steel_material"])
            # Validate materials
            if not core_material:
                QMessageBox.warning(self, "Input Error", "Please select a core material.")
                return
            if not cover_material:
                QMessageBox.warning(self, "Input Error", "Please select a cover material.")
                return
            if not steel_material:
                QMessageBox.warning(self, "Input Error", "Please select a steel material.")
                return
            # Collect numeric parameters
            params = {}
            for param in self.parameters:
                if param not in ["core_material", "cover_material", "steel_material"]:
                    value = self.param_inputs[param].text().strip()
                    if value:
                        params[param] = value
            try:
                validated_params = RCSection.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            self.created_section = RCSection(user_name=user_name, core_material=core_material, cover_material=cover_material, steel_material=steel_material, **validated_params)
            QMessageBox.information(self, "Success", f"RC section '{user_name}' created successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")

class RCSectionEditDialog(QDialog):
    """A dialog for editing the parameters of an existing Reinforced Concrete (RC) section.

    This dialog provides a graphical interface to modify the geometric and
    material parameters of an already instantiated `RCSection` object. It uses
    `RCSection` class methods for parameter retrieval, description, and
    validation, ensuring data consistency during updates.

    Attributes:
        section (RCSection): The `RCSection` object currently being edited by the dialog.
        parameters (list[str]): A list of parameter names editable for the RC section.
        descriptions (list[str]): A list of detailed descriptions for each parameter.
        tag_label (QLabel): Displays the unique tag of the section.
        user_name_label (QLabel): Displays the user-defined name of the section.
        type_label (QLabel): Displays the type name of the section.
        param_inputs (dict[str, QWidget]): A dictionary mapping parameter names
            to their respective input widgets (QLineEdit or QComboBox).

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.section.section_opensees import RCSection
        >>> from femora.components.Material.uniaxial_concrete import Concrete01
        >>> from femora.components.Material.uniaxial_steel import Steel01
        >>> app = QApplication([])
        >>> # Ensure materials exist for the section
        >>> concrete_mat = Concrete01("C_edit_ex", 30, 0.002, 0.004)
        >>> steel_mat = Steel01("S_edit_ex", 400, 0.001)
        >>> # Create an existing section to edit
        >>> existing_section = RCSection(
        ...     user_name="MyEditableSection", depth=500, width=300, cover_depth=50,
        ...     num_bars_top=2, bar_area_top=200, num_bars_bottom=2, bar_area_bottom=200,
        ...     core_material=concrete_mat, cover_material=concrete_mat, steel_material=steel_mat
        ... )
        >>> dialog = RCSectionEditDialog(existing_section)
        >>> # To actually interact with the dialog, use dialog.exec_().
        >>> # For this example, we just show it can be instantiated with an existing section.
        >>> print(dialog.windowTitle())
        Edit RC Section: MyEditableSection
        >>> app.quit()
    """
    def __init__(self, section: RCSection, parent=None):
        """Initializes the RCSectionEditDialog.

        Args:
            section: The `RCSection` object to be edited.
            parent (QWidget, optional): The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        self.section = section
        self.setWindowTitle(f"Edit RC Section: {section.user_name}")
        self.setMinimumSize(800, 600)
        self.parameters = section.get_parameters()
        self.descriptions = section.get_description()
        main_layout = QHBoxLayout(self)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        info_group = QGroupBox("Section Information")
        info_layout = QFormLayout(info_group)
        self.tag_label = QLabel(str(section.tag))
        self.user_name_label = QLabel(section.user_name)
        self.type_label = QLabel(section.section_name)
        info_layout.addRow("Tag:", self.tag_label)
        info_layout.addRow("Name:", self.user_name_label)
        info_layout.addRow("Type:", self.type_label)
        left_layout.addWidget(info_group)
        current_values = section.get_values(self.parameters)
        parameters_group = QGroupBox("Section Parameters")
        parameters_layout = QGridLayout(parameters_group)
        self.param_inputs = {}
        for row, (param, description) in enumerate(zip(self.parameters, self.descriptions)):
            param_label = QLabel(f"{param}:")
            if param == "core_material":
                param_input = QComboBox()
                setup_uniaxial_material_dropdown(param_input, "Select Core Material")
                set_combo_to_material(param_input, section.core_material)
                param_input.setToolTip("Select core concrete material (uniaxial)")
            elif param == "cover_material":
                param_input = QComboBox()
                setup_uniaxial_material_dropdown(param_input, "Select Cover Material")
                set_combo_to_material(param_input, section.cover_material)
                param_input.setToolTip("Select cover concrete material (uniaxial)")
            elif param == "steel_material":
                param_input = QComboBox()
                setup_uniaxial_material_dropdown(param_input, "Select Steel Material")
                set_combo_to_material(param_input, section.steel_material)
                param_input.setToolTip("Select steel reinforcement material (uniaxial)")
            else:
                param_input = QLineEdit()
                current_value = current_values.get(param)
                if current_value is not None:
                    param_input.setText(str(current_value))
                param_input.setPlaceholderText(f"Enter {param}")
                param_input.setToolTip("Enter a positive number")
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-size: 10px;")
            parameters_layout.addWidget(param_label, row, 0)
            parameters_layout.addWidget(param_input, row, 1)
            parameters_layout.addWidget(desc_label, row, 2)
            self.param_inputs[param] = param_input
        left_layout.addWidget(parameters_group)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        left_layout.addLayout(btn_layout)
        left_layout.addStretch()
        main_layout.addWidget(left_widget)
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        help_display = QTextBrowser()
        help_display.setHtml(section.__class__.get_help_text())
        right_layout.addWidget(help_display)
        main_layout.addWidget(right_widget)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)
    def save_changes(self):
        """Attempts to save changes to the `RCSection` object based on user inputs.

        This method validates the collected material selections and numeric parameters.
        If all inputs are valid, the `self.section` object is updated with the
        new values, and the dialog is accepted. Otherwise, error messages are displayed.

        Raises:
            ValueError: If any numeric parameter input is invalid or
                if section validation fails (e.g., non-positive dimensions).
            KeyError: If a material selected in the dropdown cannot be found.
            Exception: For any other unexpected errors during section update.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> from femora.components.section.section_opensees import RCSection
            >>> from femora.components.Material.uniaxial_concrete import Concrete01
            >>> from femora.components.Material.uniaxial_steel import Steel01
            >>> app = QApplication([])
            >>> concrete_mat = Concrete01("C_save_ex", 30, 0.002, 0.004)
            >>> steel_mat = Steel01("S_save_ex", 400, 0.001)
            >>> existing_section = RCSection(
            ...     user_name="SectionToModify", depth=500, width=300, cover_depth=50,
            ...     num_bars_top=2, bar_area_top=200, num_bars_bottom=2, bar_area_bottom=200,
            ...     core_material=concrete_mat, cover_material=concrete_mat, steel_material=steel_mat
            ... )
            >>> dialog = RCSectionEditDialog(existing_section)
            >>> # Modify a parameter
            >>> dialog.param_inputs["depth"].setText("700")
            >>> dialog.param_inputs["num_bars_top"].setText("3")
            >>> dialog.save_changes()
            >>> if dialog.result() == QApplication.DialogCode.Accepted:
            ...     print(existing_section.depth)
            700.0
            ...     print(existing_section.num_bars_top)
            3.0
            >>> app.quit()
        """
        try:
            core_material = get_material_by_combo_selection(self.param_inputs["core_material"])
            cover_material = get_material_by_combo_selection(self.param_inputs["cover_material"])
            steel_material = get_material_by_combo_selection(self.param_inputs["steel_material"])
            if not core_material:
                QMessageBox.warning(self, "Input Error", "Please select a core material.")
                return
            if not cover_material:
                QMessageBox.warning(self, "Input Error", "Please select a cover material.")
                return
            if not steel_material:
                QMessageBox.warning(self, "Input Error", "Please select a steel material.")
                return
            params = {}
            for param in self.parameters:
                if param not in ["core_material", "cover_material", "steel_material"]:
                    value = self.param_inputs[param].text().strip()
                    if value:
                        params[param] = value
            try:
                validated_params = self.section.__class__.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            update_values = dict(validated_params)
            update_values["core_material"] = core_material
            update_values["cover_material"] = cover_material
            update_values["steel_material"] = steel_material
            self.section.update_values(update_values)
            QMessageBox.information(self, "Success", f"Section '{self.section.user_name}' updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update section: {str(e)}")