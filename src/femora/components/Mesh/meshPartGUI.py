'''
This module provides the GUI components for managing mesh parts in the DRM Analyzer application.
It includes the main tab for managing mesh parts, as well as dialogs for creating, editing, and viewing mesh parts.
Classes:
    MeshPartManagerTab(QWidget): Main tab for managing mesh parts.
    MeshPartViewOptionsDialog(QDialog): Dialog for modifying view options of a MeshPart instance.
    MeshPartCreationDialog(QDialog): Dialog for creating a new mesh part.
    MeshPartEditDialog(QDialog): Dialog for editing an existing mesh part.
Functions:
    update_mesh_part_types(category): Update mesh part types based on selected category.
    open_mesh_part_creation_dialog(): Open dialog to create a new mesh part of selected type.
    open_mesh_part_view_dialog(mesh_part): Open dialog to modify view options for a mesh part.
    refresh_mesh_parts_list(): Update the mesh parts table with current mesh parts.
    open_mesh_part_edit_dialog(mesh_part): Open dialog to edit an existing mesh part.
    delete_mesh_part(user_name): Delete a mesh part from the system.
    update_opacity(value): Update mesh part opacity.
    update_edge_visibility(state): Toggle edge visibility.
    choose_color(): Open color picker dialog.
    toggle_visibility(state): Toggle mesh part visibility.
    open_element_creation_dialog(): Opens the ElementCreationDialog for creating a new element.
    create_mesh_part(): Create a new mesh part based on input.
    update_plotter(): Update the plotter with the new mesh part.
    save_mesh_part(): Save changes to the mesh part.

'''
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QGroupBox, QMessageBox, QHeaderView, QGridLayout, 
    QCheckBox, QDialogButtonBox, QColorDialog, QSlider, QTabWidget, QTextEdit,
    QMenu
)
from qtpy.QtCore import Qt

from femora.components.Mesh.meshPartBase import MeshPart, MeshPartRegistry
from femora.core.element_base import ElementRegistry
from femora.gui.components.element.element_gui import ElementCreationDialog
from femora.gui.components.element.beam_gui import BeamElementCreationDialog, is_beam_element
from femora.gui.plotter import PlotterManager
from femora.components.Mesh.meshPartInstance import *


class MeshPartManagerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Mesh part type selection
        type_layout = QGridLayout()
        self.mesh_part_category_combo = QComboBox()
        self.mesh_part_category_combo.addItems(MeshPartRegistry.get_mesh_part_categories())
        
        # Update mesh part types when category changes
        self.mesh_part_category_combo.currentTextChanged.connect(self.update_mesh_part_types)
        
        # Mesh part type dropdown
        self.mesh_part_type_combo = QComboBox()
        
        # Initialize mesh part types for first category
        self.update_mesh_part_types(self.mesh_part_category_combo.currentText())
        
        create_mesh_part_btn = QPushButton("Create New Mesh Part")
        create_mesh_part_btn.clicked.connect(self.open_mesh_part_creation_dialog)
        
        type_layout.addWidget(QLabel("Mesh Part Category:"), 0, 0)
        type_layout.addWidget(self.mesh_part_category_combo, 0, 1)
        type_layout.addWidget(QLabel("Mesh Part Type:"), 1, 0)
        type_layout.addWidget(self.mesh_part_type_combo, 1, 1)
        type_layout.addWidget(create_mesh_part_btn, 2, 0, 1, 2)
        
        layout.addLayout(type_layout)
        
        # Mesh parts table
        self.mesh_parts_table = QTableWidget()
        self.mesh_parts_table.setColumnCount(3)  # Name, Category, Type
        self.mesh_parts_table.setHorizontalHeaderLabels(["Name", "Category", "Type"])
        header = self.mesh_parts_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # Stretch all columns
        
        # Enable context menu (right-click menu)
        self.mesh_parts_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mesh_parts_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Select full rows when clicking
        self.mesh_parts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.mesh_parts_table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.mesh_parts_table)
        
        # Button layout for actions
        button_layout = QVBoxLayout()  # Changed from QHBoxLayout to QVBoxLayout
        
        # First row: Refresh and Clear buttons
        first_row_layout = QHBoxLayout()
        
        # Refresh mesh parts button
        refresh_btn = QPushButton("Refresh Mesh Parts List")
        refresh_btn.clicked.connect(self.refresh_mesh_parts_list)
        first_row_layout.addWidget(refresh_btn)
        
        # Clear all mesh parts button
        clear_all_btn = QPushButton("Clear All Mesh Parts")
        clear_all_btn.clicked.connect(self.clear_all_mesh_parts)
        first_row_layout.addWidget(clear_all_btn)
        
        button_layout.addLayout(first_row_layout)
        
        # Second row: Plot all mesh parts button
        second_row_layout = QHBoxLayout()
        
        # Plot all mesh parts button
        plot_all_btn = QPushButton("Plot All Mesh Parts")
        plot_all_btn.clicked.connect(self.plot_all_mesh_parts)
        second_row_layout.addWidget(plot_all_btn)
        
        button_layout.addLayout(second_row_layout)
        
        layout.addLayout(button_layout)
        
        # Initial refresh
        self.refresh_mesh_parts_list()

    def update_mesh_part_types(self, category):
        """Update mesh part types based on selected category"""
        self.mesh_part_type_combo.clear()
        self.mesh_part_type_combo.addItems(MeshPartRegistry.get_mesh_part_types(category))

    def open_mesh_part_creation_dialog(self):
        """
        Open dialog to create a new mesh part of selected type
        """
        category = self.mesh_part_category_combo.currentText()
        mesh_part_type = self.mesh_part_type_combo.currentText()
        
        dialog = MeshPartCreationDialog(category, mesh_part_type, self)
        
        # Only refresh if a mesh part was actually created
        if dialog.exec() == QDialog.Accepted and hasattr(dialog, 'created_mesh_part'):
            self.refresh_mesh_parts_list()

    def open_mesh_part_view_dialog(self, mesh_part):
        """
        Open dialog to modify view options for a mesh part
        """
        dialog = MeshPartViewOptionsDialog(mesh_part, self)
        dialog.exec()

    def refresh_mesh_parts_list(self):
        """
        Update the mesh parts table with current mesh parts
        """
        # Clear existing rows
        self.mesh_parts_table.setRowCount(0)
        
        # Get all mesh parts
        mesh_parts = MeshPart.get_mesh_parts()
        
        # Set row count
        self.mesh_parts_table.setRowCount(len(mesh_parts))
        
        # Populate table
        for row, (user_name, mesh_part) in enumerate(mesh_parts.items()):
            # Name
            name_item = QTableWidgetItem(user_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.mesh_parts_table.setItem(row, 0, name_item)
            
            # Category
            category_item = QTableWidgetItem(str(mesh_part.category))
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsEditable)
            self.mesh_parts_table.setItem(row, 1, category_item)
            
            # Mesh Part Type
            type_item = QTableWidgetItem(mesh_part.mesh_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.mesh_parts_table.setItem(row, 2, type_item)

    def show_context_menu(self, position):
        """
        Show context menu for mesh parts table
        """
        menu = QMenu(self)
        
        view_action = menu.addAction("View")
        edit_action = menu.addAction("Edit")
        info_action = menu.addAction("Info")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(self.mesh_parts_table.viewport().mapToGlobal(position))
        
        if action == view_action:
            self.handle_view_action()
        elif action == edit_action:
            self.handle_edit_action()
        elif action == info_action:
            self.handle_info_action()
        elif action == delete_action:
            self.handle_delete_action()

    def handle_view_action(self):
        """
        Handle the view action from the context menu
        """
        selected_row = self.mesh_parts_table.currentRow()
        if selected_row >= 0:
            user_name = self.mesh_parts_table.item(selected_row, 0).text()
            mesh_part = MeshPart.get_mesh_parts().get(user_name)
            if mesh_part:
                # Check if mesh part is plotted (has an actor)
                if mesh_part.actor is None:
                    QMessageBox.warning(
                        self, 
                        "Mesh Part Not Plotted", 
                        f"The mesh part '{user_name}' is not currently plotted in the viewer. "
                        f"Please use 'Plot All Mesh Parts' first to visualize it."
                    )
                else:
                    self.open_mesh_part_view_dialog(mesh_part)

    def handle_edit_action(self):
        """
        Handle the edit action from the context menu
        """
        selected_row = self.mesh_parts_table.currentRow()
        if selected_row >= 0:
            user_name = self.mesh_parts_table.item(selected_row, 0).text()
            mesh_part = MeshPart.get_mesh_parts().get(user_name)
            if mesh_part:
                self.open_mesh_part_edit_dialog(mesh_part)

    def handle_info_action(self):
        """
        Handle the info action from the context menu
        """
        selected_row = self.mesh_parts_table.currentRow()
        if selected_row >= 0:
            user_name = self.mesh_parts_table.item(selected_row, 0).text()
            mesh_part = MeshPart.get_mesh_parts().get(user_name)
            if mesh_part:
                self.open_mesh_part_info_dialog(mesh_part)

    def handle_delete_action(self):
        """
        Handle the delete action from the context menu
        """
        selected_row = self.mesh_parts_table.currentRow()
        if selected_row >= 0:
            user_name = self.mesh_parts_table.item(selected_row, 0).text()
            self.delete_mesh_part(user_name)

    def open_mesh_part_edit_dialog(self, mesh_part):
        """
        Open dialog to edit an existing mesh part
        """
        dialog = MeshPartEditDialog(mesh_part, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_mesh_parts_list()

    def open_mesh_part_info_dialog(self, mesh_part):
        """
        Open dialog to show mesh part information
        """
        dialog = MeshPartInfoDialog(mesh_part, self)
        dialog.exec()

    def delete_mesh_part(self, user_name):
        """
        Delete a mesh part from the system
        """
        # Confirm deletion
        reply = QMessageBox.question(self, 'Delete Mesh Part', 
                                     f"Are you sure you want to delete mesh part '{user_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            actor = MeshPart._mesh_parts[user_name].actor
            PlotterManager.get_plotter().remove_actor(actor)
            MeshPart.delete_mesh_part(user_name)
            self.refresh_mesh_parts_list()

    def plot_all_mesh_parts(self):
        """
        Plot all mesh parts in the plotter
        """
        plotter = PlotterManager.get_plotter()
        
        # Clear the plotter first
        plotter.clear()
        
        # Add all mesh parts to the plotter
        for mesh_part in MeshPart.get_mesh_parts().values():
            mesh_part.generate_mesh()
            mesh_part.actor = plotter.add_mesh(mesh_part.mesh, 
                                              style="surface",
                                              opacity=1.0,
                                              show_edges=True)
        
        # Reset camera to show all mesh parts
        plotter.reset_camera()

    def clear_all_mesh_parts(self):
        """
        Clear all mesh parts from the system
        """
        # Confirm clearing all mesh parts
        reply = QMessageBox.question(self, 'Clear All Mesh Parts', 
                                     "Are you sure you want to clear all mesh parts?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            plotter = PlotterManager.get_plotter()
            plotter.clear()
            MeshPart.clear_all_mesh_parts()
            self.refresh_mesh_parts_list()


class MeshPartViewOptionsDialog(QDialog):
    """
    Dialog for modifying view options of a MeshPart instance
    """
    def __init__(self, mesh_part, parent=None):
        super().__init__(parent)
        self.mesh_part = mesh_part
        self.setWindowTitle(f"View Options for {mesh_part.user_name}")
       
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create a grid layout for organized options
        options_grid = QGridLayout()
        options_grid.setSpacing(10)  # Add some spacing between grid items
        
        # Opacity slider
        opacity_label = QLabel("Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(mesh_part.actor.GetProperty().GetOpacity() * 100))
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        
        options_grid.addWidget(opacity_label, 0, 0)
        options_grid.addWidget(self.opacity_slider, 0, 1)
        
        # Visibility checkbox
        self.visibility_checkbox = QCheckBox("Visible")
        self.visibility_checkbox.setChecked(True)
        self.visibility_checkbox.stateChanged.connect(self.toggle_visibility)
        options_grid.addWidget(self.visibility_checkbox, 1, 0, 1, 2)
        
        # Show edges checkbox
        self.show_edges_checkbox = QCheckBox("Show Edges")
        self.show_edges_checkbox.setChecked(mesh_part.actor.GetProperty().GetEdgeVisibility())
        self.show_edges_checkbox.stateChanged.connect(self.update_edge_visibility)
        options_grid.addWidget(self.show_edges_checkbox, 2, 0, 1, 2)
        
        # Color selection
        color_label = QLabel("Color:")
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        
        options_grid.addWidget(color_label, 3, 0)
        options_grid.addWidget(self.color_button, 3, 1)
        
        # Add the grid layout to the main layout
        layout.addLayout(options_grid)
        
        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def update_opacity(self, value):
        """Update mesh part opacity"""
        self.mesh_part.actor.GetProperty().SetOpacity(value / 100.0)
    
    def update_edge_visibility(self, state):
        """Toggle edge visibility"""
        self.mesh_part.actor.GetProperty().SetEdgeVisibility(bool(state))
    
    def choose_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor()
        if color.isValid():
            # Convert QColor to VTK color (0-1 range)
            vtk_color = (
                color.redF(),
                color.greenF(),
                color.blueF()
            )
            self.mesh_part.actor.GetProperty().SetColor(vtk_color)
    
    def toggle_visibility(self, state):
        """Toggle mesh part visibility"""
        self.mesh_part.actor.visibility = bool(state)


class MeshPartCreationDialog(QDialog):
    """
    Dialog for creating a new mesh part
    """
    
    def __init__(self, category, mesh_part_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Create New {mesh_part_type} Mesh Part")
        
        # Store the created mesh part
        self.created_mesh_part = None
        self.created_element = None
        
        # Main Layout as horizontal to put notes on right
        main_layout = QHBoxLayout(self)
        
        # Left side content
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Group Box for Username and Element
        user_element_group = QGroupBox("User and Element Selection")
        user_element_layout = QGridLayout(user_element_group)

        # User Name input
        self.user_name_input = QLineEdit()
        user_element_layout.addWidget(QLabel("User Name:"), 0, 0)
        user_element_layout.addWidget(self.user_name_input, 0, 1, 1, 2)

        # Element selection
        self.create_element_btn = QPushButton("Create Element")
        self.element_combo = QComboBox()
        self.element_combo.addItems(ElementRegistry.get_element_types())
        user_element_layout.addWidget(QLabel("Element:"), 1, 0)
        user_element_layout.addWidget(self.element_combo, 1, 1)
        user_element_layout.addWidget(self.create_element_btn, 1, 2)
        self.create_element_btn.clicked.connect(self.open_element_creation_dialog)

        # Region selection
        self.region_combo = QComboBox()
        self.refresh_regions()
        self.edit_region_btn = QPushButton("Manage Regions")
        self.edit_region_btn.clicked.connect(self.open_region_dialog)
        user_element_layout.addWidget(QLabel("Region:"), 2, 0)
        user_element_layout.addWidget(self.region_combo, 2, 1)
        user_element_layout.addWidget(self.edit_region_btn, 2, 2)

        left_layout.addWidget(user_element_group)

        # Group Box for Dynamic Parameters
        parameters_group = QGroupBox("Mesh Part Parameters")
        parameters_layout = QGridLayout(parameters_group)

        self.parameter_inputs = {}
        self.mesh_part_class = MeshPartRegistry._mesh_part_types[category][mesh_part_type]
        for row, (param_name, param_description) in enumerate(self.mesh_part_class.get_parameters()):
            param_input = QLineEdit()
            parameters_layout.addWidget(QLabel(f"{param_name}:"), row, 0)
            parameters_layout.addWidget(param_input, row, 1)
            parameters_layout.addWidget(QLabel(f"({param_description})"), row, 2)
            self.parameter_inputs[param_name] = param_input

        left_layout.addWidget(parameters_group)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_mesh_part)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(create_btn)
        buttons_layout.addWidget(cancel_btn)

        left_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(left_panel)
        
        # Right side notes panel
        notes_panel = QWidget()
        notes_layout = QVBoxLayout(notes_panel)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        
        # Get notes from mesh part class
        notes = self.mesh_part_class.get_Notes()
        
        # Create notebook for tabbed notes
        notes_tabs = QTabWidget()
        
        # Description tab
        desc_tab = QWidget()
        desc_layout = QVBoxLayout(desc_tab)
        desc_text = QTextEdit()
        desc_text.setPlainText(notes["description"])
        desc_text.setReadOnly(True)
        desc_layout.addWidget(desc_text)
        notes_tabs.addTab(desc_tab, "Description")
        
        # Usage tab
        usage_tab = QWidget()
        usage_layout = QVBoxLayout(usage_tab)
        usage_text = QTextEdit()
        usage_text.setPlainText("\n".join(f"• {item}" for item in notes["usage"]))
        usage_text.setReadOnly(True)
        usage_layout.addWidget(usage_text)
        notes_tabs.addTab(usage_tab, "Usage")
        
        # Limitations tab
        limits_tab = QWidget()
        limits_layout = QVBoxLayout(limits_tab)
        limits_text = QTextEdit()
        limits_text.setPlainText("\n".join(f"• {item}" for item in notes["limitations"]))
        limits_text.setReadOnly(True)
        limits_layout.addWidget(limits_text)
        notes_tabs.addTab(limits_tab, "Limitations")
        
        # Tips tab
        tips_tab = QWidget()
        tips_layout = QVBoxLayout(tips_tab)
        tips_text = QTextEdit()
        tips_text.setPlainText("\n".join(f"• {item}" for item in notes["tips"]))
        tips_text.setReadOnly(True)
        tips_layout.addWidget(tips_text)
        notes_tabs.addTab(tips_tab, "Tips")
        
        notes_layout.addWidget(notes_tabs)
        main_layout.addWidget(notes_panel)
        
        # Set a reasonable size for the dialog
        self.resize(1000, 600)

    def refresh_regions(self):
        """
        Refresh the regions combo box with current regions
        """
        self.region_combo.clear()
        regions = RegionBase.get_all_regions()
        for tag, region in regions.items():
            self.region_combo.addItem(f"{region.name} (Tag: {tag}, Type: {region.get_type()})", region)

    def open_region_dialog(self):
            """
            Open the region management dialog and refresh regions when it closes
            """
            from femora.components.Region.regionGUI import RegionManagerTab
            dialog = RegionManagerTab(self)
            # Connect to the finished signal which is emitted regardless of how the dialog is closed
            dialog.finished.connect(self.refresh_regions)
            dialog.exec()

    def open_element_creation_dialog(self):
        """
        Opens the appropriate ElementCreationDialog for creating a new element.
        """
        element_type = self.element_combo.currentText()
    
        if not element_type:
            QMessageBox.warning(self, "Error", "Please select an element type before creating.")
            return
        
        # Use lowercase comparison for element compatibility
        if not self.mesh_part_class.is_elemnt_compatible(element_type.lower()):
            QMessageBox.warning(self, "Error", f"Element type {element_type} is not compatible with this mesh part.\n Compatible elements are: {self.mesh_part_class._compatible_elements}")
            return

        # Use appropriate dialog based on element type
        if is_beam_element(element_type):
            dialog = BeamElementCreationDialog(element_type, parent=self)
        else:
            dialog = ElementCreationDialog(element_type, parent=self)
            
        if dialog.exec() == QDialog.Accepted:
            self.created_element = dialog.created_element

    def create_mesh_part(self):
        """
        Create a new mesh part based on input
        """
        try:
            # Validate and collect parameters
            user_name = self.user_name_input.text().strip()
            if not user_name:
                raise ValueError("User name cannot be empty")

            if not self.created_element:
                raise ValueError("Please create an element first")

            # Get selected region
            selected_region = self.region_combo.currentData()
            if not selected_region:
                raise ValueError("Please select a region")

            # Collect and validate parameters
            params = {name: widget.text().strip() for name, widget in self.parameter_inputs.items()}

            # Get the current mesh part class
            category = self.parent().mesh_part_category_combo.currentText()
            mesh_part_type = self.parent().mesh_part_type_combo.currentText()
            mesh_part_class = MeshPartRegistry._mesh_part_types[category][mesh_part_type]

            # Validate parameters and create mesh part
            validated_params = mesh_part_class.validate_parameters(**params)
            mesh_part = mesh_part_class(user_name=user_name,
                                      element=self.created_element,
                                      region=selected_region,
                                      **validated_params)

            # Mark as created and accept the dialog
            self.created_mesh_part = mesh_part
            self.update_plotter()
            self.accept()

        except Exception as e:
            if self.created_element:
                # Remove the element from the registry if it exists
                try:
                    from femora.core.element_base import ElementRegistry
                    if hasattr(ElementRegistry, 'delete_element'):
                        ElementRegistry.delete_element(self.created_element.user_name)
                except:
                    pass  # Ignore if delete_element doesn't exist
            QMessageBox.warning(self, "Error", str(e))

    def update_plotter(self):
        """
        Update the plotter with the new mesh part
        """
        self.plotter = PlotterManager.get_plotter()
        self.created_mesh_part.generate_mesh()
        self.created_mesh_part.actor = self.plotter.add_mesh(self.created_mesh_part.mesh, 
                                                           style="surface",
                                                           opacity=1.0,
                                                           show_edges=True)

class MeshPartEditDialog(QDialog):
    """
    Dialog for editing an existing mesh part
    """
    def __init__(self, mesh_part, parent=None):
        super().__init__(parent)
        self.mesh_part = mesh_part
        self.setWindowTitle(f"Edit Mesh Part: {mesh_part.user_name}")
        
        # Main Layout as horizontal to put notes on right
        main_layout = QHBoxLayout(self)
        
        # Left side content
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Group Box for Read-Only Information
        info_group = QGroupBox("Mesh Part Information")
        info_layout = QGridLayout(info_group)

        # User Name (read-only)
        info_layout.addWidget(QLabel("User Name:"), 0, 0)
        user_name_label = QLabel(mesh_part.user_name)
        info_layout.addWidget(user_name_label, 0, 1)

        # Element (read-only)
        info_layout.addWidget(QLabel("Element:"), 1, 0)
        element_label = QLabel(str(mesh_part.element.element_type))
        info_layout.addWidget(element_label, 1, 1)

        # Material (read-only)
        info_layout.addWidget(QLabel("Material:"), 2, 0)
        if mesh_part.element._material is not None:
            material_label = QLabel(f"{mesh_part.element._material.user_name} ({mesh_part.element._material.material_type}-{mesh_part.element._material.material_name})")
        else:
            # For beam elements, show section info instead
            material_label = QLabel(f"Section: {mesh_part.element._section.user_name} (Beam Element)")
        info_layout.addWidget(material_label, 2, 1)

        # ndof (read-only)
        info_layout.addWidget(QLabel("num dof:"), 3, 0)
        ndof_label = QLabel(str(mesh_part.element._ndof))
        info_layout.addWidget(ndof_label, 3, 1)

        # Region selection
        info_layout.addWidget(QLabel("Region:"), 4, 0)
        self.region_combo = QComboBox()
        self.refresh_regions()
        info_layout.addWidget(self.region_combo, 4, 1)
        
        # Set current region
        current_region_index = self.region_combo.findData(mesh_part.region)
        if current_region_index >= 0:
            self.region_combo.setCurrentIndex(current_region_index)
            
        # Edit regions button
        edit_region_btn = QPushButton("Manage Regions")
        edit_region_btn.clicked.connect(self.open_region_dialog)
        info_layout.addWidget(edit_region_btn, 4, 2)

        left_layout.addWidget(info_group)

        # Group Box for Dynamic Parameters
        parameters_group = QGroupBox("Mesh Part Parameters")
        parameters_layout = QGridLayout(parameters_group)

        # Dynamically add parameter inputs based on mesh part type
        self.parameter_inputs = {}
        for row, (param_name, param_description) in enumerate(type(mesh_part).get_parameters()):
            current_value = mesh_part.params.get(param_name, '')
            param_input = QLineEdit(str(current_value))
            parameters_layout.addWidget(QLabel(f"{param_name}:"), row, 0)
            parameters_layout.addWidget(param_input, row, 1)
            parameters_layout.addWidget(QLabel(f"({param_description})"), row, 2)
            self.parameter_inputs[param_name] = param_input

        left_layout.addWidget(parameters_group)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_mesh_part)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)

        left_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(left_panel)
        
        # Right side notes panel
        notes_panel = QWidget()
        notes_layout = QVBoxLayout(notes_panel)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        
        # Get notes from mesh part class
        notes = type(mesh_part).get_Notes()
        
        # Create notebook for tabbed notes
        notes_tabs = QTabWidget()
        
        # Description tab
        desc_tab = QWidget()
        desc_layout = QVBoxLayout(desc_tab)
        desc_text = QTextEdit()
        desc_text.setPlainText(notes["description"])
        desc_text.setReadOnly(True)
        desc_layout.addWidget(desc_text)
        notes_tabs.addTab(desc_tab, "Description")
        
        # Usage tab
        usage_tab = QWidget()
        usage_layout = QVBoxLayout(usage_tab)
        usage_text = QTextEdit()
        usage_text.setPlainText("\n".join(f"• {item}" for item in notes["usage"]))
        usage_text.setReadOnly(True)
        usage_layout.addWidget(usage_text)
        notes_tabs.addTab(usage_tab, "Usage")
        
        # Limitations tab
        limits_tab = QWidget()
        limits_layout = QVBoxLayout(limits_tab)
        limits_text = QTextEdit()
        limits_text.setPlainText("\n".join(f"• {item}" for item in notes["limitations"]))
        limits_text.setReadOnly(True)
        limits_layout.addWidget(limits_text)
        notes_tabs.addTab(limits_tab, "Limitations")
        
        # Tips tab
        tips_tab = QWidget()
        tips_layout = QVBoxLayout(tips_tab)
        tips_text = QTextEdit()
        tips_text.setPlainText("\n".join(f"• {item}" for item in notes["tips"]))
        tips_text.setReadOnly(True)
        tips_layout.addWidget(tips_text)
        notes_tabs.addTab(tips_tab, "Tips")
        
        notes_layout.addWidget(notes_tabs)
        main_layout.addWidget(notes_panel)
        
        # Set a reasonable size for the dialog
        self.resize(1000, 600)

    def refresh_regions(self):
        """
        Refresh the regions combo box with current regions
        """
        self.region_combo.clear()
        regions = RegionBase.get_all_regions()
        for tag, region in regions.items():
            self.region_combo.addItem(f"{region.name} (Tag: {tag}, Type: {region.get_type()})", region)

    def open_region_dialog(self):
        """
        Open the region management dialog and refresh regions when it closes
        """
        from femora.components.Region.regionGUI import RegionManagerTab
        dialog = RegionManagerTab(self)
        dialog.finished.connect(self.refresh_regions)
        dialog.exec()

    def save_mesh_part(self):
        """
        Save changes to the mesh part
        """
        try:
            # Update region
            selected_region = self.region_combo.currentData()
            if selected_region:
                self.mesh_part.region = selected_region
            
            # Collect and validate parameters
            params = {}
            for param_name, input_widget in self.parameter_inputs.items():
                params[param_name] = input_widget.text().strip()
            
            # Validate parameters
            self.mesh_part.update_parameters(**params)

            # Regenerate mesh if needed
            self.update_plotter()
            self.accept()
        
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def update_plotter(self):
        """
        Update the plotter with the new mesh part
        """
        self.plotter = PlotterManager.get_plotter()
        self.plotter.remove_actor(self.mesh_part.actor)
        self.mesh_part.generate_mesh()
        self.mesh_part.actor = self.plotter.add_mesh(self.mesh_part.mesh, 
                                                    style="surface",
                                                    opacity=1.0,
                                                    show_edges=True)

class MeshPartNotesDialog(QDialog):
    """Dialog to display mesh part type notes"""
    def __init__(self, parent, mesh_part_class):
        super().__init__(parent)
        self.setWindowTitle(f"Notes - {mesh_part_class.__name__}")
        self.setGeometry(100, 100, 600, 400)
        
        # Make dialog modal
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # Create main frame with padding
        main_frame = QVBoxLayout(self)
        
        # Get notes from mesh part class
        notes = mesh_part_class.get_Notes()
        
        # Create notebook for tabbed view
        notebook = QTabWidget()
        main_frame.addWidget(notebook)
        
        # Description tab
        desc_frame = QWidget()
        notebook.addTab(desc_frame, "Description")
        desc_layout = QVBoxLayout(desc_frame)
        desc_text = QTextEdit()
        desc_text.setPlainText(notes["description"])
        desc_text.setReadOnly(True)
        desc_layout.addWidget(desc_text)
        
        # Usage tab
        usage_frame = QWidget()
        notebook.addTab(usage_frame, "Usage")
        usage_layout = QVBoxLayout(usage_frame)
        usage_text = QTextEdit()
        for item in notes["usage"]:
            usage_text.append(f"• {item}\n")
        usage_text.setReadOnly(True)
        usage_layout.addWidget(usage_text)
        
        # Limitations tab
        limits_frame = QWidget()
        notebook.addTab(limits_frame, "Limitations")
        limits_layout = QVBoxLayout(limits_frame)
        limits_text = QTextEdit()
        for item in notes["limitations"]:
            limits_text.append(f"• {item}\n")
        limits_text.setReadOnly(True)
        limits_layout.addWidget(limits_text)
        
        # Tips tab
        tips_frame = QWidget()
        notebook.addTab(tips_frame, "Tips")
        tips_layout = QVBoxLayout(tips_frame)
        tips_text = QTextEdit()
        for item in notes["tips"]:
            tips_text.append(f"• {item}\n")
        tips_text.setReadOnly(True)
        tips_layout.addWidget(tips_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        close_layout.addStretch()
        tips_layout.addLayout(close_layout)


class MeshPartInfoDialog(QDialog):
    """Dialog to display mesh part information"""
    def __init__(self, mesh_part, parent=None):
        super().__init__(parent)
        self.mesh_part = mesh_part
        self.setWindowTitle(f"Mesh Part Info - {mesh_part.user_name}")
        self.setGeometry(100, 100, 800, 600)
        
        # Make dialog modal
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Create text area for mesh information
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Populate the text area with mesh information
        self.populate_mesh_info()
    
    def populate_mesh_info(self):
        """Populate the text area with mesh part information"""
        info_text = f"Mesh Part Information\n"
        info_text += f"=" * 50 + "\n\n"
        
        # Basic mesh part info
        info_text += f"Name: {self.mesh_part.user_name}\n"
        info_text += f"Category: {self.mesh_part.category}\n"
        info_text += f"Type: {self.mesh_part.mesh_type}\n"
        info_text += f"Element Type: {self.mesh_part.element.element_type}\n"
        
        if hasattr(self.mesh_part.element, '_material') and self.mesh_part.element._material:
            info_text += f"Material: {self.mesh_part.element._material.user_name}\n"
        
        if hasattr(self.mesh_part.element, '_section') and self.mesh_part.element._section:
            info_text += f"Section: {self.mesh_part.element._section.user_name}\n"
        
        if hasattr(self.mesh_part.element, '_transformation') and self.mesh_part.element._transformation:
            transformation = self.mesh_part.element._transformation
            if hasattr(transformation, 'user_name'):
                info_text += f"Transformation: {transformation.user_name}\n"
            elif hasattr(transformation, 'transf_tag'):
                info_text += f"Transformation: {transformation.transf_tag}\n"
            else:
                info_text += f"Transformation: {transformation}\n"
        
        info_text += f"Region: {self.mesh_part.region.name if self.mesh_part.region else 'None'}\n"
        info_text += f"Number of DOFs: {self.mesh_part.element._ndof}\n\n"
        
        # Parameters
        info_text += f"Parameters:\n"
        info_text += f"-" * 20 + "\n"
        for param_name, param_value in self.mesh_part.params.items():
            info_text += f"{param_name}: {param_value}\n"
        
        info_text += f"\nMesh Information:\n"
        info_text += f"-" * 20 + "\n"
        
        # Print the mesh object
        info_text += f"Mesh Object:\n"
        info_text += f"{self.mesh_part.mesh}\n\n"
        
        # Additional mesh details
        if hasattr(self.mesh_part.mesh, 'n_points'):
            info_text += f"Number of Points: {self.mesh_part.mesh.n_points}\n"
        
        if hasattr(self.mesh_part.mesh, 'n_cells'):
            info_text += f"Number of Cells: {self.mesh_part.mesh.n_cells}\n"
        
        if hasattr(self.mesh_part.mesh, 'bounds'):
            bounds = self.mesh_part.mesh.bounds
            info_text += f"Bounds: X[{bounds[0]:.3f}, {bounds[1]:.3f}], "
            info_text += f"Y[{bounds[2]:.3f}, {bounds[3]:.3f}], "
            info_text += f"Z[{bounds[4]:.3f}, {bounds[5]:.3f}]\n"
        
        # Set the text
        self.text_area.setPlainText(info_text)


if __name__ == "__main__":
    '''
    Test the MeshPartManagerTab GUI
    '''
    from PySide6.QtWidgets import QApplication
    from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial, ElasticUniaxialMaterial
    import sys
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    ElasticIsotropicMaterial(user_name="Steel",    E=200e3, nu=0.3,  rho=7.85e-9)
    ElasticIsotropicMaterial(user_name="Concrete", E=30e3,  nu=0.2,  rho=24e-9)
    ElasticIsotropicMaterial(user_name="Aluminum", E=70e3,  nu=0.33, rho=2.7e-9)
    ElasticUniaxialMaterial(user_name="Steel2",    E=200e3, eta=0.1)


    # Create and display the main window
    window = MeshPartManagerTab()
    window.show()

    
    sys.exit(app.exec())