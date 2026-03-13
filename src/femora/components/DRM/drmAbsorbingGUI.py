from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QSpinBox, QLabel, QDialogButtonBox, QColorDialog,
    QComboBox, QPushButton, QGridLayout, QMessageBox, QProgressDialog, QApplication,
    QSlider, QDialog, QDoubleSpinBox, QCheckBox, QFileDialog, QHBoxLayout, 
)
from qtpy.QtCore import Qt
from femora.gui.plotter import PlotterManager
from femora.components.MeshMaker import MeshMaker
from qtpy.QtWidgets import QSizePolicy
from femora.components.partitioner.partitioner import PartitionerRegistry

class AbsorbingMeshViewOptionsDialog(QDialog):
    """
    Dialog for modifying view options of the absorbing mesh
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("View Options for Absorbing Mesh")
        self.plotter = PlotterManager.get_plotter()
        self.meshmaker = MeshMaker.get_instance()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create a grid layout for organized options
        options_grid = QGridLayout()
        options_grid.setSpacing(10)
        
        row = 0
        
        # Scalars dropdown
        scalar_label = QLabel("Scalars:")
        self.scalar_combobox = QComboBox()
        self.scalar_combobox.addItems(self.meshmaker.assembler.AssembeledMesh.array_names)
        active_scalar = self.meshmaker.assembler.AssembeledMesh.active_scalars_name
        current_index = self.scalar_combobox.findText(active_scalar)
        self.scalar_combobox.setCurrentIndex(current_index)
        self.scalar_combobox.currentIndexChanged.connect(self.update_scalars)

        options_grid.addWidget(scalar_label, row, 0)
        options_grid.addWidget(self.scalar_combobox, row, 1)
        row += 1

        # Opacity slider
        opacity_label = QLabel("Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self.meshmaker.assembler.AssembeledActor.GetProperty().GetOpacity() * 100))
        self.opacity_slider.valueChanged.connect(self.update_opacity)

        options_grid.addWidget(opacity_label, row, 0)
        options_grid.addWidget(self.opacity_slider, row, 1)
        row += 1

        # Visibility checkbox
        self.visibility_checkbox = QCheckBox("Visible")
        self.visibility_checkbox.setChecked(self.meshmaker.assembler.AssembeledActor.GetVisibility())
        self.visibility_checkbox.stateChanged.connect(self.toggle_visibility)
        options_grid.addWidget(self.visibility_checkbox, row, 0, 1, 2)
        row += 1

        # Show edges checkbox
        self.show_edges_checkbox = QCheckBox("Show Edges")
        self.show_edges_checkbox.setChecked(self.meshmaker.assembler.AssembeledActor.GetProperty().GetEdgeVisibility())
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
        self.meshmaker.assembler.AssembeledMesh.active_scalars_name = scalars_name
        
        # Determine if the selected scalar is point data or cell data
        is_point_data = scalars_name in self.meshmaker.assembler.AssembeledMesh.point_data.keys()
        
        # Update the mapper with the correct scalar data type
        mapper = self.meshmaker.assembler.AssembeledActor.GetMapper()
        if is_point_data:
            mapper.SetScalarModeToUsePointData()
        else:
            mapper.SetScalarModeToUseCellData()
        
        # Set the array name and range
        self.meshmaker.assembler.AssembeledActor.mapper.array_name = scalars_name
        self.meshmaker.assembler.AssembeledActor.mapper.scalar_range = self.meshmaker.assembler.AssembeledMesh.get_data_range(scalars_name)
        
        # Update the scalar bar title
        if self.plotter.scalar_bar is not None:
            self.plotter.scalar_bar.SetTitle(scalars_name)
        
        self.plotter.update_scalar_bar_range(self.meshmaker.assembler.AssembeledMesh.get_data_range(scalars_name))
        self.plotter.update()
        self.plotter.render()
    
    def update_opacity(self, value):
        """Update absorbing mesh opacity"""
        self.meshmaker.assembler.AssembeledActor.GetProperty().SetOpacity(value / 100.0)
        self.plotter.render()

    def update_edge_visibility(self, state):
        """Toggle edge visibility"""
        self.meshmaker.assembler.AssembeledActor.GetProperty().SetEdgeVisibility(bool(state))
        self.plotter.render()

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
            self.meshmaker.assembler.AssembeledActor.GetProperty().SetColor(vtk_color)
            self.plotter.render()

    def toggle_visibility(self, state):
        """Toggle absorbing mesh visibility"""
        self.meshmaker.assembler.AssembeledActor.SetVisibility(bool(state))
        self.plotter.render()


class AbsorbingGUI(QWidget):
    def __init__(self, parent=None):
        """
        Initialize the AbsorbingGUI.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.meshmaker = MeshMaker.get_instance()
        
        # Set size policy for the main widget
        # self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)
        
        # Absorbing Layer
        absorbingLayerBox = QGroupBox("Absorbing Layer")
        absorbingLayerBox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        absorbingLayerLayout = QGridLayout(absorbingLayerBox)
        
        # Add widgets
        absorbingLayerLayout.addWidget(QLabel("Geometry"), 0, 0)
        self.absorbingLayerCombox = QComboBox()
        self.absorbingLayerCombox.addItem("Rectangular")
        absorbingLayerLayout.addWidget(self.absorbingLayerCombox, 0, 1)
        
        absorbingLayerLayout.addWidget(QLabel("Type"), 1, 0)
        self.absorbingLayerTypeCombox = QComboBox()
        self.absorbingLayerTypeCombox.addItem("Rayleigh")
        self.absorbingLayerTypeCombox.addItem("PML")
        absorbingLayerLayout.addWidget(self.absorbingLayerTypeCombox, 1, 1)
        
        absorbingLayerLayout.addWidget(QLabel("Partition Algorithm"), 2, 0)
        self.absorbingLayerPartitionCombox = QComboBox()
        # DRM absorbing-layer partitioning is currently implemented only for kd-tree.
        # Keep the UI aligned with supported backends to avoid runtime errors.
        self.absorbingLayerPartitionCombox.addItems(
            [p for p in ["kd-tree"] if p in PartitionerRegistry.get_available_types(include_unavailable=True)]
        )
        absorbingLayerLayout.addWidget(self.absorbingLayerPartitionCombox, 2, 1)
        
        absorbingLayerLayout.addWidget(QLabel("Number of Partitions"), 3, 0)
        self.absorbingLayerPartitionLineEdit = QSpinBox()
        self.absorbingLayerPartitionLineEdit.setMinimum(0)
        self.absorbingLayerPartitionLineEdit.setMaximum(1000)
        absorbingLayerLayout.addWidget(self.absorbingLayerPartitionLineEdit, 3, 1)
        
        absorbingLayerLayout.addWidget(QLabel("Number of Layers"), 4, 0)
        self.absorbingLayerNumLayersLineEdit = QSpinBox()
        self.absorbingLayerNumLayersLineEdit.setMinimum(1)
        self.absorbingLayerNumLayersLineEdit.setMaximum(50)
        self.absorbingLayerNumLayersLineEdit.setValue(5)
        absorbingLayerLayout.addWidget(self.absorbingLayerNumLayersLineEdit, 4, 1)

        absorbingLayerLayout.addWidget(QLabel("Damping Factor"), 5, 0)
        self.dampingFactorSpinBox = QDoubleSpinBox()
        self.dampingFactorSpinBox.setMinimum(0.0)
        self.dampingFactorSpinBox.setMaximum(1.0)
        self.dampingFactorSpinBox.setSingleStep(0.01)
        self.dampingFactorSpinBox.setValue(0.95)
        absorbingLayerLayout.addWidget(self.dampingFactorSpinBox, 5, 1)

        # Add match damping checkbox
        self.matchDampingCheckbox = QCheckBox("Match Damping with Regular Domain")
        absorbingLayerLayout.addWidget(self.matchDampingCheckbox, 6, 0, 1, 2)

        # Add a button to add the absorbing layer
        self.addAbsorbingLayerButton = QPushButton("Add Absorbing Layer")
        self.addAbsorbingLayerButton.setStyleSheet("background-color: green")
        absorbingLayerLayout.addWidget(self.addAbsorbingLayerButton, 7, 0, 1, 2)
        self.addAbsorbingLayerButton.clicked.connect(self.add_absorbing_layer)

        # Add view options button
        self.viewOptionsButton = QPushButton("View Options")
        absorbingLayerLayout.addWidget(self.viewOptionsButton, 8, 0, 1, 2)
        self.viewOptionsButton.clicked.connect(self.show_view_options_dialog)

        absorbingLayerLayout.setContentsMargins(10, 10, 10, 10)
        absorbingLayerLayout.setSpacing(10)
        
        layout.addWidget(absorbingLayerBox)
        layout.setContentsMargins(10, 10, 10, 10)

    def add_absorbing_layer(self):
        response = QMessageBox.warning(
            self,
            "Warning",
            "Adding an absorbing layer will modify the mesh. Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if response == QMessageBox.No:
            return

        self.plotter = PlotterManager.get_plotter()

        if self.meshmaker.assembler.AssembeledActor is not None:
            PlotterManager.get_plotter().renderer.remove_actor(self.meshmaker.assembler.AssembeledActor)
            self.meshmaker.assembler.AssembeledActor = None

        # Get parameters from UI
        geometry = self.absorbingLayerCombox.currentText()
        absorbing_layer_type = self.absorbingLayerTypeCombox.currentText()
        partition_algorithm = self.absorbingLayerPartitionCombox.currentText()
        num_partitions = self.absorbingLayerPartitionLineEdit.value()
        num_layers = self.absorbingLayerNumLayersLineEdit.value()
        damping_factor = self.dampingFactorSpinBox.value()
        match_damping = self.matchDampingCheckbox.isChecked()

        # Create and configure progress dialog
        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setWindowTitle("Processing")
        self.progress_dialog.setLabelText("Creating absorbing layer...")
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setRange(0, 100)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        
        # Show the dialog
        self.progress_dialog.show()
        QApplication.processEvents()

        try:
            # Start the mesh operation
            self.meshmaker.drm.addAbsorbingLayer(
                num_layers,
                num_partitions,
                partition_algorithm,
                geometry,
                damping=damping_factor,
                matchDamping=match_damping,
                progress_callback=self.update_progress,
                type=absorbing_layer_type,
            )

            self.plotter.clear()
            self.meshmaker.assembler.AssembeledActor = self.plotter.add_mesh(
                self.meshmaker.assembler.AssembeledMesh,
                opacity=1.0,
                show_edges=True,
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)
        finally:
            self.progress_dialog.close()

    def update_progress(self, value):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setValue(int(value))
            QApplication.processEvents()

    def show_view_options_dialog(self):
        """Show the view options dialog for the absorbing mesh"""
        dialog = AbsorbingMeshViewOptionsDialog(self)
        dialog.exec_()


if __name__ == '__main__':
    import sys
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AbsorbingGUI()
    window.show()
    sys.exit(app.exec_())
