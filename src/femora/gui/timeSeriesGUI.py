from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout,
    QCheckBox
)
from qtpy.QtCore import Qt

from femora.components.TimeSeries.timeSeriesBase import (
    TimeSeries, TimeSeriesRegistry, ConstantTimeSeries, LinearTimeSeries,
    TrigTimeSeries, RampTimeSeries, TriangularTimeSeries, RectangularTimeSeries,
    PulseTimeSeries, PathTimeSeries
)

class TimeSeriesManagerTab(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # TimeSeries type selection
        type_layout = QGridLayout()
        self.time_series_type_combo = QComboBox()
        self.time_series_type_combo.addItems(TimeSeriesRegistry.get_time_series_types())
        
        create_time_series_btn = QPushButton("Create New Time Series")
        create_time_series_btn.clicked.connect(self.open_time_series_creation_dialog)
        
        type_layout.addWidget(QLabel("Time Series Type:"), 0, 0)
        type_layout.addWidget(self.time_series_type_combo, 0, 1, 1, 2)
        type_layout.addWidget(create_time_series_btn, 1, 0, 1, 3)
        
        layout.addLayout(type_layout)
        
        # Time Series table
        self.time_series_table = QTableWidget()
        self.time_series_table.setColumnCount(5)  # Tag, Type, Parameters, Edit, Delete
        self.time_series_table.setHorizontalHeaderLabels(["Tag", "Type", "Parameters", "Edit", "Delete"])
        header = self.time_series_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.time_series_table)
        
        # Refresh time series button
        refresh_btn = QPushButton("Refresh Time Series List")
        refresh_btn.clicked.connect(self.refresh_time_series_list)
        layout.addWidget(refresh_btn)
        
        # Initial refresh
        self.refresh_time_series_list()

    def open_time_series_creation_dialog(self):
        """Open dialog to create a new time series of selected type"""
        time_series_type = self.time_series_type_combo.currentText()
        dialog = TimeSeriesCreationDialog(time_series_type, self)
        
        if dialog.exec() == QDialog.Accepted:
            self.refresh_time_series_list()

    def refresh_time_series_list(self):
        """Update the time series table with current time series"""
        self.time_series_table.setRowCount(0)
        time_series_list = TimeSeries.get_all_time_series()
        
        self.time_series_table.setRowCount(len(time_series_list))
        for row, (tag, time_series) in enumerate(time_series_list.items()):
            # Tag
            tag_item = QTableWidgetItem(str(tag))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            self.time_series_table.setItem(row, 0, tag_item)
            
            # Time Series Type
            type_item = QTableWidgetItem(time_series.series_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.time_series_table.setItem(row, 1, type_item)
            
            # Parameters 
            params = time_series.get_values()
            params_str = ", ".join([f"{k}: {v}" for k, v in params.items()])
            params_item = QTableWidgetItem(params_str)
            params_item.setFlags(params_item.flags() & ~Qt.ItemIsEditable)
            self.time_series_table.setItem(row, 2, params_item)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, ts=time_series: self.open_time_series_edit_dialog(ts))
            self.time_series_table.setCellWidget(row, 3, edit_btn)

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, t=tag: self.delete_time_series(t))
            self.time_series_table.setCellWidget(row, 4, delete_btn)

    def open_time_series_edit_dialog(self, time_series):
        """Open dialog to edit an existing time series"""
        dialog = TimeSeriesEditDialog(time_series, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_time_series_list()

    def delete_time_series(self, tag):
        """Delete a time series from the system"""
        reply = QMessageBox.question(
            self, 'Delete Time Series',
            f"Are you sure you want to delete time series with tag {tag}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            TimeSeries.remove_time_series(tag)
            self.refresh_time_series_list()


class TimeSeriesCreationDialog(QDialog):
    def __init__(self, time_series_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Create {time_series_type} Time Series")
        self.time_series_type = time_series_type
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Get the time series class
        self.time_series_class = TimeSeriesRegistry._time_series_types.get(time_series_type.lower())
        
        if not self.time_series_class:
            QMessageBox.critical(self, "Error", f"Time series type {time_series_type} not found.")
            self.reject()
            return
        
        # Parameter inputs
        self.param_inputs = {}
        parameters = self.time_series_class.get_Parameters()
        
        # Create a grid layout for parameter inputs
        grid_layout = QGridLayout()
        
        # Add label and input fields to the grid layout
        row = 0
        for param_name, param_description in parameters:
            label = QLabel(param_name)
            
            # Use appropriate input widget based on parameter type
            if param_name in ["useLast", "prependZero"]:
                input_field = QCheckBox()
                input_field.setChecked(False)
            else:
                input_field = QLineEdit()
            
            # Add description
            grid_layout.addWidget(label, row, 0)
            grid_layout.addWidget(input_field, row, 1)
            grid_layout.addWidget(QLabel(param_description), row, 2)
            
            self.param_inputs[param_name] = input_field
            row += 1
        
        form_layout.addRow(grid_layout)
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_time_series)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def create_time_series(self):
        try:
            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                if isinstance(input_field, QCheckBox):
                    params[param] = input_field.isChecked()
                else:
                    value = input_field.text().strip()
                    if value:
                        params[param] = value
            
            # Create time series
            time_series = TimeSeriesRegistry.create_time_series(self.time_series_type, **params)
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class TimeSeriesEditDialog(QDialog):
    def __init__(self, time_series, parent=None):
        super().__init__(parent)
        self.time_series = time_series
        self.setWindowTitle(f"Edit {time_series.series_type} Time Series (Tag: {time_series.tag})")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Parameter inputs
        self.param_inputs = {}
        parameters = time_series.__class__.get_Parameters()
        current_values = time_series.get_values()
        
        # Create a grid layout for parameter inputs
        grid_layout = QGridLayout()
        
        # Add label and input fields to the grid layout
        row = 0
        for param_name, param_description in parameters:
            label = QLabel(param_name)
            
            # Use appropriate input widget based on parameter type
            if param_name in ["useLast", "prependZero"]:
                input_field = QCheckBox()
                input_field.setChecked(current_values.get(param_name, False))
            else:
                input_field = QLineEdit()
                # Set current value if available
                if param_name in current_values and current_values[param_name] is not None:
                    input_field.setText(str(current_values[param_name]))
            
            # Add description
            grid_layout.addWidget(label, row, 0)
            grid_layout.addWidget(input_field, row, 1)
            grid_layout.addWidget(QLabel(param_description), row, 2)
            
            self.param_inputs[param_name] = input_field
            row += 1
        
        form_layout.addRow(grid_layout)
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_time_series)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_time_series(self):
        try:
            # Collect parameters
            params = {}
            for param, input_field in self.param_inputs.items():
                if isinstance(input_field, QCheckBox):
                    params[param] = input_field.isChecked()
                else:
                    value = input_field.text().strip()
                    if value:
                        params[param] = value
            
            # Update time series
            self.time_series.update_values(**params)
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    import sys
    
    # Create sample time series for testing
    ConstantTimeSeries(factor=1.0)
    LinearTimeSeries(factor=2.0)
    TrigTimeSeries(tStart=0.0, tEnd=10.0, period=1.0, factor=1.0, shift=0.0)
    RampTimeSeries(tStart=0.0, tRamp=5.0, cFactor=1.5)
    TriangularTimeSeries(tStart=0.0, tEnd=10.0, period=2.0, factor=1.0, shift=0.0)
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    window = TimeSeriesManagerTab()
    window.show()
    sys.exit(app.exec())