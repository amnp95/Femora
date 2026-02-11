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
    def __init__(self, parent=None):
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
        """Open dialog to create a new element of selected type"""
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
        """Update the elements table with current elements"""
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

    def open_element_edit_dialog(self, element):
        """Open dialog to edit an existing element"""
        # Check if it's a beam element
        print(element.element_type)
        if is_beam_element(element.element_type):
            dialog = BeamElementEditDialog(element, self)
        else:
            dialog = ElementEditDialog(element, self)
            
        if dialog.exec() == QDialog.Accepted:
            self.refresh_elements_list()

    def delete_element(self, tag):
        """Delete an element from the system"""
        # Confirm deletion
        reply = QMessageBox.question(self, 'Delete Element', 
                                     f"Are you sure you want to delete element with tag {tag}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            Element.delete_element(tag)
            self.refresh_elements_list()


class ElementCreationDialog(QDialog):
    def __init__(self, element_type, parent=None):
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
    def __init__(self, element, parent=None):
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