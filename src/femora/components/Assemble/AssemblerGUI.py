import sys
from typing import List


from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QWidget, QDialog, QCheckBox, QLabel, QListWidget, QListWidgetItem, QSlider, QColorDialog,
    QSpinBox, QComboBox, QMessageBox, QHeaderView, QTableWidget, QTableWidgetItem, QDialogButtonBox, QMenu
)



from femora.components.Mesh.meshPartBase import MeshPart
from femora.components.Assemble.Assembler import Assembler
from femora.gui.plotter import PlotterManager
from femora.components.partitioner.partitioner import PartitionerRegistry

class AssemblyManagerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create Assembly Section button
        create_section_btn = QPushButton("Create New Assembly Section")
        create_section_btn.clicked.connect(self.open_assembly_section_creation_dialog)
        layout.addWidget(create_section_btn)
        
        # Assembly sections table
        self.assembly_sections_table = QTableWidget()
        self.assembly_sections_table.setColumnCount(3)  # Tag, Mesh Parts, Partitions
        self.assembly_sections_table.setHorizontalHeaderLabels([
            "Name", "Mesh Parts", "Partitions"
        ])
        header = self.assembly_sections_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Enable context menu (right-click menu)
        self.assembly_sections_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.assembly_sections_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Select full rows when clicking
        self.assembly_sections_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.assembly_sections_table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.assembly_sections_table)
        
        # Button layout for actions
        button_layout = QVBoxLayout()  # Changed from QHBoxLayout to QVBoxLayout
        
        # First row: Refresh and Clear buttons
        first_row_layout = QHBoxLayout()
        
        # Refresh assembly sections button
        refresh_btn = QPushButton("Refresh Assembly Sections List")
        refresh_btn.clicked.connect(self.refresh_assembly_sections_list)
        first_row_layout.addWidget(refresh_btn)
        
        # Clear all assembly parts button
        clear_all_btn = QPushButton("Clear All Assembly Parts")
        clear_all_btn.clicked.connect(self.clear_all_assembly_parts)
        first_row_layout.addWidget(clear_all_btn)
        
        button_layout.addLayout(first_row_layout)
        
        # Second row: Plot all assembly parts button
        second_row_layout = QHBoxLayout()
        
        # Plot all assembly parts button
        plot_all_btn = QPushButton("Plot All Assembly Parts")
        plot_all_btn.clicked.connect(self.plot_all_assembly_parts)
        second_row_layout.addWidget(plot_all_btn)
        
        button_layout.addLayout(second_row_layout)
        
        layout.addLayout(button_layout)

        # Group Box for Assembling the whole model
        groupBox = QGroupBox("Assemble the whole model")
        groupBoxLayout = QVBoxLayout()
        groupBox.setLayout(groupBoxLayout)
        layout.addWidget(groupBox)

        sublayout = QHBoxLayout()
        # checkbox for merging points
        self.merge_points_checkbox = QCheckBox("Merge Points")
        self.merge_points_checkbox.setChecked(True)
        sublayout.addWidget(self.merge_points_checkbox)
    
        # push button for view options
        view_options_btn = QPushButton("View Options")
        view_options_btn.clicked.connect(self.open_assembled_mesh_view_options_dialog)
        sublayout.addWidget(view_options_btn)

        groupBoxLayout.addLayout(sublayout)


        # Assemble button
        assemble_btn = QPushButton("Assemble model")
        assemble_btn.setStyleSheet("background-color: #6b7232")
        assemble_btn.clicked.connect(self.assemble_model)
        groupBoxLayout.addWidget(assemble_btn)



        # delete button
        delete_btn = QPushButton("Clear Assembled Model")
        delete_btn.setStyleSheet("background-color: #A85D6E")
        delete_btn.clicked.connect(self.delete_assembled_model)
        groupBoxLayout.addWidget(delete_btn)








        
        # Initial refresh
        self.refresh_assembly_sections_list()


    def open_assembled_mesh_view_options_dialog(self):
        """
        Open dialog to modify view options of the assembled mesh
        """
        dialog = AssembledMeshViewOptionsDialog(self)
        dialog.exec()

    def delete_assembled_model(self):
        """
        Delete the assembled model
        """
        assembler = Assembler.get_instance()
        plotter = PlotterManager.get_plotter()
        if assembler.AssembeledActor is not None:
            plotter.remove_actor(assembler.AssembeledActor)
            assembler.AssembeledActor = None
            assembler.AssembeledMesh = None
            plotter.clear()
            plotter.update()
            plotter.render()
        else:
            QMessageBox.warning(self, "Error", "No assembled model to delete")


    def assemble_model(self):
        """
        Assemble the whole model
        """
        try:
            self.refresh_assembly_sections_list()
            from femora.gui.progress_gui import get_progress_callback_gui

            assembler = Assembler.get_instance()

            # GUI progress bar callback (mirrors console-based Progress)
            progress_cb = get_progress_callback_gui("Assembling")

            assembler.Assemble(
                merge_points=self.merge_points_checkbox.isChecked(),
                progress_callback=progress_cb,
            )
            
            if assembler.AssembeledMesh is not None:
                self.plotter = PlotterManager.get_plotter()
                self.plotter.clear()
                assembler.AssembeledActor = self.plotter.add_mesh(  assembler.AssembeledMesh, 
                                        opacity=1.0,
                                        scalars = "Core",
                                        style='surface',
                                        show_edges=True,)
        except ValueError as e:
            QMessageBox.warning(self, "Input Error",
                                f"Invalid input: {str(e)}\nPlease enter appropriate values.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")



    
    def solo_view_section(self, current_tag):
        """
        Show only the selected section by hiding all other sections
        """
        try:
            assembler = Assembler.get_instance()
            plotter = PlotterManager.get_plotter()
            
            # Get all assembly sections
            sections = assembler.get_sections()
            
            # Iterate through all sections
            for tag, section in sections.items():
                if tag == current_tag:
                    # Show the current section
                    section.actor.SetVisibility(True)
                else:
                    # Hide all other sections
                    section.actor.SetVisibility(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def refresh_assembly_sections_list(self):
        """
        Update the assembly sections table with current sections
        """
        # Get the Assembler instance
        assembler = Assembler.get_instance()
        
        # Clear existing rows
        self.assembly_sections_table.setRowCount(0)
        
        # Get all assembly sections
        assembly_sections = assembler.get_sections()
        
        # Set row count
        self.assembly_sections_table.setRowCount(len(assembly_sections))
        
        # Populate table
        for row, (tag, section) in enumerate(assembly_sections.items()):
            # Name (Section{tag})
            name_item = QTableWidgetItem(f"Section{tag}")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.assembly_sections_table.setItem(row, 0, name_item)
            
            # Mesh Parts
            mesh_parts_str = ", ".join(section.meshparts)
            mesh_parts_item = QTableWidgetItem(mesh_parts_str)
            mesh_parts_item.setFlags(mesh_parts_item.flags() & ~Qt.ItemIsEditable)
            self.assembly_sections_table.setItem(row, 1, mesh_parts_item)
            
            # Partitions
            partitions_item = QTableWidgetItem(str(section.num_partitions))
            partitions_item.setFlags(partitions_item.flags() & ~Qt.ItemIsEditable)
            self.assembly_sections_table.setItem(row, 2, partitions_item)
    
    def show_context_menu(self, position):
        """
        Show context menu for assembly sections table
        """
        menu = QMenu(self)
        
        view_action = menu.addAction("View")
        solo_view_action = menu.addAction("Solo View")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(self.assembly_sections_table.viewport().mapToGlobal(position))
        
        if action is None:
            return
        
        # Get the selected row
        selected_row = self.assembly_sections_table.currentRow()
        if selected_row < 0:
            return
            
        # Get the tag from the first column (it's in format "Section{tag}")
        name_item = self.assembly_sections_table.item(selected_row, 0)
        if not name_item:
            return
            
        # Extract the tag number from the section name
        tag = int(name_item.text().replace("Section", ""))
        
        if action == view_action:
            self.handle_view_action(tag)
        elif action == solo_view_action:
            self.handle_solo_view_action(tag)
        elif action == delete_action:
            self.handle_delete_action(tag)

    def handle_view_action(self, tag):
        """
        Handle the view action from the context menu
        """
        try:
            section = Assembler.get_instance().get_section(tag)
            
            # Check if section is plotted (has an actor)
            if section.actor is None:
                QMessageBox.warning(
                    self, 
                    "Assembly Section Not Plotted", 
                    f"The assembly section '{tag}' is not currently plotted in the viewer. "
                    f"Please use 'Plot All Assembly Parts' first to visualize it."
                )
            else:
                self.open_section_view_dialog(section)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def handle_solo_view_action(self, tag):
        """
        Handle the solo view action from the context menu
        """
        try:
            section = Assembler.get_instance().get_section(tag)
            
            # Check if section is plotted (has an actor)
            if section.actor is None:
                QMessageBox.warning(
                    self, 
                    "Assembly Section Not Plotted", 
                    f"The assembly section '{tag}' is not currently plotted in the viewer. "
                    f"Please use 'Plot All Assembly Parts' first to visualize it."
                )
            else:
                self.solo_view_section(tag)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def handle_delete_action(self, tag):
        """
        Handle the delete action from the context menu
        """
        self.delete_assembly_section(tag)
    
    def open_section_view_dialog(self, section):
        """
        Open a dialog to view assembly section details
        """
        dialog = AssemblySectionViewOptionsDialog(section, self)
        dialog.exec()
    
    def delete_assembly_section(self, tag):
        """
        Delete an assembly section
        """
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            'Delete Assembly Section', 
            f"Are you sure you want to delete assembly section with tag '{tag}'?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                assembler = Assembler.get_instance()
                # remove the actor from the plotter
                plotter = PlotterManager.get_plotter()
                plotter.remove_actor(assembler.get_section(tag).actor)
                assembler.delete_section(tag)
                self.refresh_assembly_sections_list()
            except KeyError:
                QMessageBox.warning(self, "Error", f"Assembly section with tag '{tag}' not found")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def open_assembly_section_creation_dialog(self):
        """
        Open dialog to create a new assembly section
        """
        from femora.components.Assemble.AssemblerGUI import AssemblySectionCreationDialog
        
        dialog = AssemblySectionCreationDialog(self)
        
        # Refresh the list if a new section was created
        if dialog.exec() == QDialog.Accepted:
            self.refresh_assembly_sections_list()

    def plot_all_assembly_parts(self):
        """
        Plot all assembly parts in the plotter
        """
        assembler = Assembler.get_instance()
        plotter = PlotterManager.get_plotter()
        plotter.clear()
        for section in assembler.get_sections().values():
            actor = plotter.add_mesh(section.mesh,
                                        show_edges=True,
                                     opacity=1.0,
                                     scalars=None,
                                     style='surface',
                                     color="royalblue")
            section.assign_actor(actor)
        plotter.update()
        plotter.render()

    def clear_all_assembly_parts(self):
        """
        Delete all assembly sections from the system
        """
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            'Clear All Assembly Parts', 
            "Are you sure you want to delete all assembly sections?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            assembler = Assembler.get_instance()
            plotter = PlotterManager.get_plotter()
            
            # Remove all actors from the plotter
            for section in assembler.get_sections().values():
                if section.actor is not None:
                    plotter.remove_actor(section.actor)
            
            # Clear all assembly sections from the Assembler
            assembler.clear_assembly_sections()
            
            # Refresh the table to reflect the changes
            self.refresh_assembly_sections_list()
            
            # Update the plotter
            plotter.update()
            plotter.render()

class AssemblySectionViewOptionsDialog(QDialog):
    """
    Dialog for modifying view options of an Assembly Section
    """
    def __init__(self, section, parent=None):
        super().__init__(parent)
        self.section = section
        self.setWindowTitle(f"View Options for Section{section.tag}")
        self.plotter = PlotterManager.get_plotter()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create a grid layout for organized options
        options_grid = QGridLayout()
        options_grid.setSpacing(10)
        
        row = 0



        # sclars dropdown
        scalars_label = QLabel("Scalars:")
        self.scalars_combobox = QComboBox()
        self.scalars_combobox.addItems(section.mesh.array_names)
        active_scalars = section.mesh.active_scalars_name
        current_index = self.scalars_combobox.findText(active_scalars)
        self.scalars_combobox.currentIndexChanged.connect(self.update_scalars)
        options_grid.addWidget(scalars_label, row, 0)
        options_grid.addWidget(self.scalars_combobox, row, 1)
        row += 1

        # Opacity slider
        opacity_label = QLabel("Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(section.actor.GetProperty().GetOpacity() * 100))
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        
        options_grid.addWidget(opacity_label, row, 0)
        options_grid.addWidget(self.opacity_slider, row, 1)
        row += 1
        
        # Visibility checkbox
        self.visibility_checkbox = QCheckBox("Visible")
        self.visibility_checkbox.setChecked(section.actor.GetVisibility())
        self.visibility_checkbox.stateChanged.connect(self.toggle_visibility)
        options_grid.addWidget(self.visibility_checkbox, row, 0, 1, 2)
        row += 1
        
        # Show edges checkbox
        self.show_edges_checkbox = QCheckBox("Show Edges")
        self.show_edges_checkbox.setChecked(section.actor.GetProperty().GetEdgeVisibility())
        self.show_edges_checkbox.stateChanged.connect(self.update_edge_visibility)
        options_grid.addWidget(self.show_edges_checkbox, row, 0, 1, 2)
        row += 1
        
        # Color selection
        color_label = QLabel("Color:")
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        
        options_grid.addWidget(color_label, row, 0)
        options_grid.addWidget(self.color_button, row, 1)
        
        # Add the grid layout to the main layout
        layout.addLayout(options_grid)
        
        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


    def update_scalars(self):
        """Update the scalars for the assembly section"""
        scalars_name = self.scalars_combobox.currentText()
        self.section.mesh.active_scalars_name = scalars_name
        self.section.actor.mapper.array_name = scalars_name
        self.section.actor.mapper.scalar_range = self.section.mesh.get_data_range(scalars_name)

        # self.plotter.update_scalar_bar_title(scalars_name)
        self.plotter.update_scalar_bar_range(self.section.mesh.get_data_range(scalars_name))
        self.plotter.update()
        self.plotter.render()
    
    def update_opacity(self, value):
        """Update assembly section opacity"""
        self.section.actor.GetProperty().SetOpacity(value / 100.0)
    
    def update_edge_visibility(self, state):
        """Toggle edge visibility"""
        self.section.actor.GetProperty().SetEdgeVisibility(bool(state))
    
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
            self.section.actor.GetProperty().SetColor(vtk_color)
    
    def toggle_visibility(self, state):
        """Toggle assembly section visibility"""
        self.section.actor.SetVisibility(bool(state))




class AssembledMeshViewOptionsDialog(QDialog):
    """
    Dialog for modifying view options of the assembled mesh
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("View Options for Assembled Mesh")
        self.plotter = PlotterManager.get_plotter()
        self.assembler = Assembler.get_instance()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create a grid layout for organized options
        options_grid = QGridLayout()
        options_grid.setSpacing(10)
        
        row = 0
        
        # scalars dropdown
        scalar_label = QLabel("Scalars:")
        self.scalar_combobox = QComboBox()
        self.scalar_combobox.addItems(self.assembler.AssembeledMesh.array_names)
        active_scalar = self.assembler.AssembeledMesh.active_scalars_name
        current_index = self.scalar_combobox.findText(active_scalar)
        self.scalar_combobox.currentIndexChanged.connect(self.update_scalars)

        options_grid.addWidget(scalar_label, row, 0)
        options_grid.addWidget(self.scalar_combobox, row, 1)
        row += 1

        # Opacity slider
        opacity_label = QLabel("Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self.assembler.AssembeledActor.GetProperty().GetOpacity() * 100))
        self.opacity_slider.valueChanged.connect(self.update_opacity)

        options_grid.addWidget(opacity_label, row, 0)
        options_grid.addWidget(self.opacity_slider, row, 1)
        row += 1

        # Visibility checkbox
        self.visibility_checkbox = QCheckBox("Visible")
        self.visibility_checkbox.setChecked(self.assembler.AssembeledActor.GetVisibility())
        self.visibility_checkbox.stateChanged.connect(self.toggle_visibility)
        options_grid.addWidget(self.visibility_checkbox, row, 0, 1, 2)
        row += 1

        # Show edges checkbox
        self.show_edges_checkbox = QCheckBox("Show Edges")
        self.show_edges_checkbox.setChecked(self.assembler.AssembeledActor.GetProperty().GetEdgeVisibility())
        self.show_edges_checkbox.stateChanged.connect(self.update_edge_visibility)
        options_grid.addWidget(self.show_edges_checkbox, row, 0, 1, 2)
        row += 1

        # Color selection
        color_label = QLabel("Color:")
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)

        options_grid.addWidget(color_label, row, 0)
        options_grid.addWidget(self.color_button, row, 1)


        # Add the grid layout to the main layout
        layout.addLayout(options_grid)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def update_scalars(self):
        """Update the scalars for the assembled mesh"""
        scalars_name = self.scalar_combobox.currentText()
        self.assembler.AssembeledMesh.active_scalars_name = scalars_name
        
        # Determine if the selected scalar is point data or cell data
        is_point_data = scalars_name in self.assembler.AssembeledMesh.point_data.keys()
        
        # Update the mapper with the correct scalar data type
        mapper = self.assembler.AssembeledActor.GetMapper()
        if is_point_data:
            mapper.SetScalarModeToUsePointData()
        else:
            mapper.SetScalarModeToUseCellData()
        
        # Set the array name and range
        self.assembler.AssembeledActor.mapper.array_name = scalars_name
        self.assembler.AssembeledActor.mapper.scalar_range = self.assembler.AssembeledMesh.get_data_range(scalars_name)
        
        # Update the scalar bar title
        if self.plotter.scalar_bar is not None:
            self.plotter.scalar_bar.SetTitle(scalars_name)
        
        self.plotter.update_scalar_bar_range(self.assembler.AssembeledMesh.get_data_range(scalars_name))
        self.plotter.update()
        self.plotter.render()
    
    def update_opacity(self, value):
        """Update assembled mesh opacity"""
        self.assembler.AssembeledActor.GetProperty().SetOpacity(value / 100.0)

    def update_edge_visibility(self, state):
        """Toggle edge visibility"""
        self.assembler.AssembeledActor.GetProperty().SetEdgeVisibility(bool(state))

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
            self.assembler.AssembeledActor.GetProperty().SetColor(vtk_color)

    def toggle_visibility(self, state):
        """Toggle assembled mesh visibility"""
        self.assembler.AssembeledActor.SetVisibility(bool(state))











class AssemblySectionCreationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Assembly Section")
        self.setModal(True)
        self.Assembler = Assembler.get_instance()
        self.plotter = PlotterManager.get_plotter()
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Mesh Parts Selection
        mesh_parts_label = QLabel("Select Mesh Parts:")
        main_layout.addWidget(mesh_parts_label)
        
        # List of Mesh Parts
        self.mesh_parts_list = QListWidget()
        self.mesh_parts_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Populate the list with available mesh parts
        self._populate_mesh_parts()
        
        main_layout.addWidget(self.mesh_parts_list)
        
        # Partitioning Options Layout
        options_layout = QVBoxLayout()
        
        # Number of Partitions
        num_partitions_layout = QHBoxLayout()
        num_partitions_label = QLabel("Number of Partitions:")
        self.num_partitions_spinbox = QSpinBox()
        self.num_partitions_spinbox.setMinimum(0)
        self.num_partitions_spinbox.setMaximum(100)
        self.num_partitions_spinbox.setValue(0)
        
        num_partitions_layout.addWidget(num_partitions_label)
        num_partitions_layout.addWidget(self.num_partitions_spinbox)
        options_layout.addLayout(num_partitions_layout)
        
        # Partition Algorithm
        partition_algo_layout = QHBoxLayout()
        partition_algo_label = QLabel("Partition Algorithm:")
        self.partition_algo_combobox = QComboBox()
        self.partition_algo_combobox.addItems(PartitionerRegistry.get_available_types())
        
        partition_algo_layout.addWidget(partition_algo_label)
        partition_algo_layout.addWidget(self.partition_algo_combobox)
        options_layout.addLayout(partition_algo_layout)
        
        main_layout.addLayout(options_layout)
        
        # Merge Points Checkbox
        self.merge_points_checkbox = QCheckBox("Merge Points")
        self.merge_points_checkbox.setChecked(True)
        main_layout.addWidget(self.merge_points_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("Add Section")
        ok_button.clicked.connect(self.create_section)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def _populate_mesh_parts(self):
        """
        Populate the list with available mesh parts.
        
        Uses the class method from MeshPart to retrieve existing mesh parts.
        """
        # Retrieve existing mesh parts
        existing_mesh_parts = list(MeshPart._mesh_parts.keys())
        
        # Add to the list widget
        for mesh_part in existing_mesh_parts:
            self.mesh_parts_list.addItem(QListWidgetItem(mesh_part))
    
    def get_selected_mesh_parts(self) -> List[str]:
        """
        Retrieve selected mesh part names.
        
        Returns:
            List[str]: List of selected mesh part names
        """
        return [item.text() for item in self.mesh_parts_list.selectedItems()]
    
    def get_partition_settings(self):
        """
        Retrieve partition settings from the dialog.
        
        Returns:
            Tuple containing number of partitions, algorithm, and merge points flag
        """
        return (
            self.num_partitions_spinbox.value(),
            self.partition_algo_combobox.currentText(),
            self.merge_points_checkbox.isChecked()
        )
    
    def create_section(self):
        """
        Create the assembly section based on the selected mesh parts and settings.
        """
        try:
            self.section = self.Assembler.create_section( 
                meshparts=self.get_selected_mesh_parts(),
                num_partitions=self.num_partitions_spinbox.value(),
                partition_algorithm=self.partition_algo_combobox.currentText(),
                merging_points=self.merge_points_checkbox.isChecked()
            )
            self.update_plotter()
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Input Error",
                                f"Invalid input: {str(e)}\nPlease enter appropriate values.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def update_plotter(self):
        """
        Update the plotter with the new assembly section
        """
        meshparts = MeshPart.get_mesh_parts()
        for mesh_part in self.get_selected_mesh_parts():
            actor = meshparts[mesh_part].actor
            if actor is not None:
                self.plotter.remove_actor(actor)
        actor = self.plotter.add_mesh(self.section.mesh,
                                        opacity=1.0,
                                        scalars = None,
                                        style='surface',
                                        show_edges=True,
                                        color="royalblue",)
        self.section.assign_actor(actor)
        

        

            
        


if __name__ == "__main__":
    '''
    Test the AssemblyManagerTab GUI
    '''
    from PySide6.QtWidgets import QApplication
    import sys

    # Preliminary setup of mesh parts for testing
    from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
    from femora.components.element.std_brick import stdBrickElement
    from femora.components.Mesh.meshPartInstance import StructuredRectangular3D

    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Create some test materials and elements
    elastic = ElasticIsotropicMaterial(user_name="Steel", E=200e3, nu=0.3, rho=7.85e-9)
    stdbrik1 = stdBrickElement(ndof=3, material=elastic, b1=0, b2=0, b3=-10)
    
    # Create some test mesh parts
    StructuredRectangular3D(user_name="base", element=stdbrik1, 
                            **{'X Min': -50, 'X Max': 50, 'Y Min': -50, 'Y Max': 50, 
                               'Z Min': -30, 'Z Max': -20, 'Nx Cells': 10, 'Ny Cells': 10, 'Nz Cells': 10})
    StructuredRectangular3D(user_name="middle", element=stdbrik1,
                            **{'X Min': -50, 'X Max': 50, 'Y Min': -50, 'Y Max': 50, 
                               'Z Min': -20, 'Z Max': -10, 'Nx Cells': 10, 'Ny Cells': 10, 'Nz Cells': 10})
    StructuredRectangular3D(user_name="top", element=stdbrik1,
                            **{'X Min': -50, 'X Max': 50, 'Y Min': -50, 'Y Max': 50, 
                               'Z Min': -10, 'Z Max': 0, 'Nx Cells': 10, 'Ny Cells': 10, 'Nz Cells': 10})

    # Create and display the main window
    window = AssemblyManagerTab()
    window.show()
    
    sys.exit(app.exec())