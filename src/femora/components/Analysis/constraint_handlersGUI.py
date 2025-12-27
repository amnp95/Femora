from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QMessageBox, QHeaderView, QGridLayout,
    QCheckBox, QGroupBox, QDoubleSpinBox, QRadioButton
)

from femora.utils.validator import DoubleValidator
from femora.components.Analysis.constraint_handlers import (
    ConstraintHandler, ConstraintHandlerManager,
    PlainConstraintHandler, TransformationConstraintHandler,
    PenaltyConstraintHandler, LagrangeConstraintHandler,
    AutoConstraintHandler
)

class ConstraintHandlerManagerTab(QDialog):
    """Manages the creation, editing, and deletion of constraint handlers in a GUI tab.

    This dialog provides an interface to interact with the `ConstraintHandlerManager`
    to define and configure various types of constraint handlers for a Femora model.

    Attributes:
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers.
        handler_type_combo (QComboBox): Dropdown to select the type of constraint
            handler to create.
        handlers_table (QTableWidget): Table displaying existing constraint handlers
            with their tags, types, and parameters.
        checkboxes (list[QCheckBox]): List of checkboxes for selecting handlers
            in the `handlers_table`.
        edit_btn (QPushButton): Button to open the edit dialog for the selected handler.
        delete_selected_btn (QPushButton): Button to delete the selected handler.
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the ConstraintHandlerManagerTab dialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = ConstraintHandlerManagerTab()
            >>> manager_tab.show()
            >>> # sys.exit(app.exec_()) # Uncomment to run the full application
        """
        super().__init__(parent)

        # Setup dialog properties
        self.setWindowTitle("Constraint Handler Manager")
        self.resize(800, 500)

        # Get the constraint handler manager instance
        self.handler_manager = ConstraintHandlerManager()

        # Main layout
        layout = QVBoxLayout(self)

        # Handler type selection
        type_layout = QGridLayout()

        # Handler type dropdown
        self.handler_type_combo = QComboBox()
        self.handler_type_combo.addItems(self.handler_manager.get_available_types())

        create_handler_btn = QPushButton("Create New Handler")
        create_handler_btn.clicked.connect(self.open_handler_creation_dialog)

        type_layout.addWidget(QLabel("Handler Type:"), 0, 0)
        type_layout.addWidget(self.handler_type_combo, 0, 1)
        type_layout.addWidget(create_handler_btn, 1, 0, 1, 2)

        layout.addLayout(type_layout)

        # Handlers table
        self.handlers_table = QTableWidget()
        self.handlers_table.setColumnCount(4)  # Select, Tag, Type, Parameters
        self.handlers_table.setHorizontalHeaderLabels(["Select", "Tag", "Type", "Parameters"])
        self.handlers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.handlers_table.setSelectionMode(QTableWidget.SingleSelection)
        header = self.handlers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        layout.addWidget(self.handlers_table)

        # Action buttons
        buttons_layout = QHBoxLayout()

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected_handler)

        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.clicked.connect(self.delete_selected_handler)

        refresh_btn = QPushButton("Refresh Handlers List")
        refresh_btn.clicked.connect(self.refresh_handlers_list)

        buttons_layout.addWidget(self.edit_btn)
        buttons_layout.addWidget(self.delete_selected_btn)
        buttons_layout.addWidget(refresh_btn)

        layout.addLayout(buttons_layout)

        # Initial refresh
        self.refresh_handlers_list()

        # Disable edit/delete buttons initially
        self.update_button_state()

    def refresh_handlers_list(self):
        """Updates the handlers table with the current list of constraint handlers.

        This method clears the existing table content and repopulates it with
        handlers retrieved from the `handler_manager`, including their tags, types,
        and parameters. It also re-initializes the selection checkboxes.
        """
        self.handlers_table.setRowCount(0)
        handlers = self.handler_manager.get_all_handlers()

        self.handlers_table.setRowCount(len(handlers))
        self.checkboxes = []  # Changed from radio_buttons to checkboxes

        # Hide vertical header (row indices)
        self.handlers_table.verticalHeader().setVisible(False)

        for row, (tag, handler) in enumerate(handlers.items()):
            # Select checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("QCheckBox::indicator { width: 15px; height: 15px; }")
            # Connect checkboxes to a common slot to ensure mutual exclusivity
            checkbox.toggled.connect(lambda checked, btn=checkbox: self.on_checkbox_toggled(checked, btn))
            self.checkboxes.append(checkbox)
            checkbox_cell = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_cell)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.handlers_table.setCellWidget(row, 0, checkbox_cell)

            # Tag
            tag_item = QTableWidgetItem(str(tag))
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            self.handlers_table.setItem(row, 1, tag_item)

            # Handler Type
            type_item = QTableWidgetItem(handler.handler_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.handlers_table.setItem(row, 2, type_item)

            # Parameters
            params = handler.get_values()
            params_str = ", ".join([f"{k}: {v}" for k, v in params.items()]) if params else "None"
            params_item = QTableWidgetItem(params_str)
            params_item.setFlags(params_item.flags() & ~Qt.ItemIsEditable)
            self.handlers_table.setItem(row, 3, params_item)

        self.update_button_state()

    def on_checkbox_toggled(self, checked: bool, btn: QCheckBox):
        """Handles checkbox toggling to ensure mutual exclusivity of selections.

        When a checkbox is checked, all other checkboxes in the table are unchecked.

        Args:
            checked: True if the checkbox is checked, False otherwise.
            btn: The QCheckBox instance that was toggled.
        """
        if checked:
            # Uncheck all other checkboxes
            for checkbox in self.checkboxes:
                if checkbox != btn and checkbox.isChecked():
                    checkbox.setChecked(False)
        self.update_button_state()

    def update_button_state(self):
        """Enables or disables edit and delete buttons based on handler selection.

        Buttons are enabled if at least one handler is selected via its checkbox,
        otherwise they are disabled.
        """
        enable_buttons = any(cb.isChecked() for cb in self.checkboxes) if hasattr(self, 'checkboxes') else False
        self.edit_btn.setEnabled(enable_buttons)
        self.delete_selected_btn.setEnabled(enable_buttons)

    def get_selected_handler_tag(self) -> int | None:
        """Retrieves the tag of the currently selected constraint handler.

        Returns:
            int | None: The integer tag of the selected handler, or None if no
                handler is selected.
        """
        for row, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                tag_item = self.handlers_table.item(row, 1)
                return int(tag_item.text())
        return None

    def open_handler_creation_dialog(self):
        """Opens a specialized dialog for creating a new constraint handler.

        The dialog type depends on the handler type selected in the dropdown.
        Upon successful creation, the handlers list is refreshed.

        Raises:
            QMessageBox.warning: If no creation dialog is available for the
                selected handler type.
        """
        handler_type = self.handler_type_combo.currentText()

        if handler_type.lower() == "plain":
            dialog = PlainConstraintHandlerDialog(self)
        elif handler_type.lower() == "transformation":
            dialog = TransformationConstraintHandlerDialog(self)
        elif handler_type.lower() == "penalty":
            dialog = PenaltyConstraintHandlerDialog(self)
        elif handler_type.lower() == "lagrange":
            dialog = LagrangeConstraintHandlerDialog(self)
        elif handler_type.lower() == "auto":
            dialog = AutoConstraintHandlerDialog(self)
        else:
            QMessageBox.warning(self, "Error", f"No creation dialog available for handler type: {handler_type}")
            return

        if dialog.exec() == QDialog.Accepted:
            self.refresh_handlers_list()

    def edit_selected_handler(self):
        """Opens a dialog to edit the parameters of the selected constraint handler.

        Only certain handler types (Penalty, Lagrange, Auto) have editable parameters.
        For others, an info message is displayed. Upon successful editing,
        the handlers list is refreshed.

        Raises:
            QMessageBox.warning: If no handler is selected or no edit dialog
                is available for the handler type.
            QMessageBox.critical: For unexpected errors during the edit process.
        """
        tag = self.get_selected_handler_tag()
        if tag is None:
            QMessageBox.warning(self, "Warning", "Please select a handler to edit")
            return

        try:
            handler = self.handler_manager.get_handler(tag)

            if handler.handler_type.lower() == "plain":
                QMessageBox.information(self, "Info", "Plain constraint handler has no parameters to edit")
                return
            elif handler.handler_type.lower() == "transformation":
                QMessageBox.information(self, "Info", "Transformation constraint handler has no parameters to edit")
                return
            elif handler.handler_type.lower() == "penalty":
                dialog = PenaltyConstraintHandlerEditDialog(handler, self)
            elif handler.handler_type.lower() == "lagrange":
                dialog = LagrangeConstraintHandlerEditDialog(handler, self)
            elif handler.handler_type.lower() == "auto":
                dialog = AutoConstraintHandlerEditDialog(handler, self)
            else:
                QMessageBox.warning(self, "Error", f"No edit dialog available for handler type: {handler.handler_type}")
                return

            if dialog.exec() == QDialog.Accepted:
                self.refresh_handlers_list()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_selected_handler(self):
        """Deletes the currently selected constraint handler.

        A confirmation dialog is presented to the user before deletion.

        Raises:
            QMessageBox.warning: If no handler is selected.
        """
        tag = self.get_selected_handler_tag()
        if tag is None:
            QMessageBox.warning(self, "Warning", "Please select a handler to delete")
            return

        self.delete_handler(tag)

    def delete_handler(self, tag: int):
        """Deletes a constraint handler with the given tag from the system.

        A confirmation dialog is displayed before proceeding with the deletion.

        Args:
            tag: The unique integer tag of the handler to be deleted.
        """
        reply = QMessageBox.question(
            self, 'Delete Constraint Handler',
            f"Are you sure you want to delete constraint handler with tag {tag}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.handler_manager.remove_handler(tag)
            self.refresh_handlers_list()

    def select_handler(self, tag: int) -> bool:
        """Selects the constraint handler with the specified tag in the table.

        First refreshes the list to ensure all handlers are present, then finds
        and checks the checkbox corresponding to the given tag.

        Args:
            tag: The unique integer tag of the handler to select.

        Returns:
            bool: True if the handler was found and selected, False otherwise.
        """
        # Refresh the list to ensure we have the latest handlers
        self.refresh_handlers_list()

        # Find and check the checkbox for the handler with the specified tag
        for row in range(self.handlers_table.rowCount()):
            tag_item = self.handlers_table.item(row, 1)
            if tag_item and int(tag_item.text()) == tag:
                # Check the checkbox for this handler
                if row < len(self.checkboxes):
                    self.checkboxes[row].setChecked(True)
                return True

        return False


class PlainConstraintHandlerDialog(QDialog):
    """Dialog for creating a Plain Constraint Handler.

    This handler does not follow constraint definitions across model evolution
    and has no additional parameters.

    Attributes:
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers, used to create the new handler.
        handler (PlainConstraintHandler | None): The created handler instance,
            set upon successful creation.
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the PlainConstraintHandlerDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> dialog = PlainConstraintHandlerDialog()
            >>> # if dialog.exec() == QDialog.Accepted:
            >>> #     print(f"Created Plain handler with tag: {dialog.handler.tag}")
            >>> # app.exec_() # For testing, typically dialogs are shown by parent
        """
        super().__init__(parent)
        self.setWindowTitle("Create Plain Constraint Handler")
        self.handler_manager = ConstraintHandlerManager()

        # Main layout
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel("Plain constraint handler does not follow the constraint definitions across the model evolution.\nIt has no additional parameters.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_handler)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def create_handler(self):
        """Attempts to create a new PlainConstraintHandler and accepts the dialog.

        If successful, the `handler` attribute is set. If an error occurs during
        creation, a critical message box is displayed.
        """
        try:
            # Create handler
            self.handler = self.handler_manager.create_handler("plain")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class TransformationConstraintHandlerDialog(QDialog):
    """Dialog for creating a Transformation Constraint Handler.

    This handler performs static condensation of constraint degrees of freedom
    and has no additional parameters.

    Attributes:
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers, used to create the new handler.
        handler (TransformationConstraintHandler | None): The created handler instance,
            set upon successful creation.
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the TransformationConstraintHandlerDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> dialog = TransformationConstraintHandlerDialog()
            >>> # if dialog.exec() == QDialog.Accepted:
            >>> #     print(f"Created Transformation handler with tag: {dialog.handler.tag}")
            >>> # app.exec_() # For testing, typically dialogs are shown by parent
        """
        super().__init__(parent)
        self.setWindowTitle("Create Transformation Constraint Handler")
        self.handler_manager = ConstraintHandlerManager()

        # Main layout
        layout = QVBoxLayout(self)

        # Info label
        info = QLabel("Transformation constraint handler performs static condensation of the constraint degrees of freedom.\nIt has no additional parameters.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_handler)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def create_handler(self):
        """Attempts to create a new TransformationConstraintHandler and accepts the dialog.

        If successful, the `handler` attribute is set. If an error occurs during
        creation, a critical message box is displayed.
        """
        try:
            # Create handler
            self.handler = self.handler_manager.create_handler("transformation")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class PenaltyConstraintHandlerDialog(QDialog):
    """Dialog for creating a Penalty Constraint Handler.

    This handler uses penalty numbers to enforce constraints and allows
    configuration of `alpha_s` and `alpha_m` parameters.

    Attributes:
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers, used to create the new handler.
        double_validator (DoubleValidator): A validator for double spin box inputs.
        alpha_s_spin (QDoubleSpinBox): Input field for the Alpha S penalty value.
        alpha_m_spin (QDoubleSpinBox): Input field for the Alpha M penalty value.
        handler (PenaltyConstraintHandler | None): The created handler instance,
            set upon successful creation.
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the PenaltyConstraintHandlerDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> dialog = PenaltyConstraintHandlerDialog()
            >>> # if dialog.exec() == QDialog.Accepted:
            >>> #     print(f"Created Penalty handler with tag: {dialog.handler.tag}")
            >>> #     print(f"Alpha S: {dialog.handler.alpha_s}, Alpha M: {dialog.handler.alpha_m}")
            >>> # app.exec_() # For testing, typically dialogs are shown by parent
        """
        super().__init__(parent)
        self.setWindowTitle("Create Penalty Constraint Handler")
        self.handler_manager = ConstraintHandlerManager()
        self.double_validator = DoubleValidator()

        # Main layout
        layout = QVBoxLayout(self)

        # Parameters group
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)

        # Alpha S
        self.alpha_s_spin = QDoubleSpinBox()
        self.alpha_s_spin.setDecimals(6)
        self.alpha_s_spin.setRange(1e-12, 1e12)
        self.alpha_s_spin.setValue(1.0)
        params_layout.addRow("Alpha S:", self.alpha_s_spin)

        # Alpha M
        self.alpha_m_spin = QDoubleSpinBox()
        self.alpha_m_spin.setDecimals(6)
        self.alpha_m_spin.setRange(1e-12, 1e12)
        self.alpha_m_spin.setValue(1.0)
        params_layout.addRow("Alpha M:", self.alpha_m_spin)

        layout.addWidget(params_group)

        # Info label
        info = QLabel("Penalty constraint handler uses penalty numbers to enforce constraints.\n"
                     "- Alpha S: Penalty value for single-point constraints\n"
                     "- Alpha M: Penalty value for multi-point constraints")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_handler)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def create_handler(self):
        """Attempts to create a new PenaltyConstraintHandler with the specified parameters.

        If successful, the `handler` attribute is set and the dialog is accepted.
        If an error occurs, a critical message box is displayed.
        """
        try:
            # Collect parameters
            alpha_s = self.alpha_s_spin.value()
            alpha_m = self.alpha_m_spin.value()

            # Create handler
            self.handler = self.handler_manager.create_handler("penalty", alpha_s=alpha_s, alpha_m=alpha_m)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class PenaltyConstraintHandlerEditDialog(QDialog):
    """Dialog for editing an existing Penalty Constraint Handler.

    This dialog allows modification of the `alpha_s` and `alpha_m` parameters
    of a specific `PenaltyConstraintHandler`.

    Attributes:
        handler (PenaltyConstraintHandler): The `PenaltyConstraintHandler` instance
            being edited.
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers, used to save the updated handler.
        double_validator (DoubleValidator): A validator for double spin box inputs.
        alpha_s_spin (QDoubleSpinBox): Input field for the Alpha S penalty value.
        alpha_m_spin (QDoubleSpinBox): Input field for the Alpha M penalty value.
    """

    def __init__(self, handler: PenaltyConstraintHandler, parent: QWidget = None):
        """Initializes the PenaltyConstraintHandlerEditDialog.

        Args:
            handler: The `PenaltyConstraintHandler` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> from femora.components.Analysis.constraint_handlers import PenaltyConstraintHandler
            >>> # Create a dummy handler for demonstration
            >>> dummy_handler = PenaltyConstraintHandler(tag=1, alpha_s=0.1, alpha_m=0.2)
            >>> app = QApplication(sys.argv)
            >>> dialog = PenaltyConstraintHandlerEditDialog(dummy_handler)
            >>> # The dialog would normally be shown like:
            >>> # if dialog.exec() == QDialog.Accepted:
            >>> #     print(f"Handler updated via dialog, new params: {dialog.handler.alpha_s}, {dialog.handler.alpha_m}")
            >>> # print(f"Initial handler params: {dummy_handler.alpha_s}, {dummy_handler.alpha_m}")
            >>> # app.exec_() # For testing, typically dialogs are shown by parent
        """
        super().__init__(parent)
        self.handler = handler
        self.setWindowTitle(f"Edit Penalty Constraint Handler (Tag: {handler.tag})")
        self.handler_manager = ConstraintHandlerManager()
        self.double_validator = DoubleValidator()

        # Main layout
        layout = QVBoxLayout(self)

        # Parameters group
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)

        # Alpha S
        self.alpha_s_spin = QDoubleSpinBox()
        self.alpha_s_spin.setDecimals(6)
        self.alpha_s_spin.setRange(1e-12, 1e12)
        self.alpha_s_spin.setValue(handler.alpha_s)
        params_layout.addRow("Alpha S:", self.alpha_s_spin)

        # Alpha M
        self.alpha_m_spin = QDoubleSpinBox()
        self.alpha_m_spin.setDecimals(6)
        self.alpha_m_spin.setRange(1e-12, 1e12)
        self.alpha_m_spin.setValue(handler.alpha_m)
        params_layout.addRow("Alpha M:", self.alpha_m_spin)

        layout.addWidget(params_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_handler)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_handler(self):
        """Saves the edited parameters for the Penalty Constraint Handler.

        The old handler with the same tag is removed from the manager, and a
        new handler with the updated parameters (and the same tag) is created.
        The dialog is then accepted. If an error occurs, a critical message
        box is displayed.
        """
        try:
            # Collect parameters
            alpha_s = self.alpha_s_spin.value()
            alpha_m = self.alpha_m_spin.value()

            # Remove the old handler and create a new one with the same tag
            tag = self.handler.tag
            self.handler_manager.remove_handler(tag)

            # Create new handler
            self.handler = self.handler_manager.create_handler("penalty", alpha_s=alpha_s, alpha_m=alpha_m)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class LagrangeConstraintHandlerDialog(QDialog):
    """Dialog for creating a Lagrange Constraint Handler.

    This handler uses Lagrange multipliers to enforce constraints and allows
    configuration of `alpha_s` and `alpha_m` parameters.

    Attributes:
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers, used to create the new handler.
        double_validator (DoubleValidator): A validator for double spin box inputs.
        alpha_s_spin (QDoubleSpinBox): Input field for the Alpha S scaling factor.
        alpha_m_spin (QDoubleSpinBox): Input field for the Alpha M scaling factor.
        handler (LagrangeConstraintHandler | None): The created handler instance,
            set upon successful creation.
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the LagrangeConstraintHandlerDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> dialog = LagrangeConstraintHandlerDialog()
            >>> # if dialog.exec() == QDialog.Accepted:
            >>> #     print(f"Created Lagrange handler with tag: {dialog.handler.tag}")
            >>> #     print(f"Alpha S: {dialog.handler.alpha_s}, Alpha M: {dialog.handler.alpha_m}")
            >>> # app.exec_() # For testing, typically dialogs are shown by parent
        """
        super().__init__(parent)
        self.setWindowTitle("Create Lagrange Constraint Handler")
        self.handler_manager = ConstraintHandlerManager()
        self.double_validator = DoubleValidator()

        # Main layout
        layout = QVBoxLayout(self)

        # Parameters group
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)

        # Alpha S
        self.alpha_s_spin = QDoubleSpinBox()
        self.alpha_s_spin.setDecimals(6)
        self.alpha_s_spin.setRange(1e-12, 1e12)
        self.alpha_s_spin.setValue(1.0)
        params_layout.addRow("Alpha S:", self.alpha_s_spin)

        # Alpha M
        self.alpha_m_spin = QDoubleSpinBox()
        self.alpha_m_spin.setDecimals(6)
        self.alpha_m_spin.setRange(1e-12, 1e12)
        self.alpha_m_spin.setValue(1.0)
        params_layout.addRow("Alpha M:", self.alpha_m_spin)

        layout.addWidget(params_group)

        # Info label
        info = QLabel("Lagrange multipliers constraint handler uses Lagrange multipliers to enforce constraints.\n"
                     "- Alpha S: Scaling factor for single-point constraints\n"
                     "- Alpha M: Scaling factor for multi-point constraints")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_handler)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def create_handler(self):
        """Attempts to create a new LagrangeConstraintHandler with the specified parameters.

        If successful, the `handler` attribute is set and the dialog is accepted.
        If an error occurs, a critical message box is displayed.
        """
        try:
            # Collect parameters
            alpha_s = self.alpha_s_spin.value()
            alpha_m = self.alpha_m_spin.value()

            # Create handler
            self.handler = self.handler_manager.create_handler("lagrange", alpha_s=alpha_s, alpha_m=alpha_m)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class LagrangeConstraintHandlerEditDialog(QDialog):
    """Dialog for editing an existing Lagrange Constraint Handler.

    This dialog allows modification of the `alpha_s` and `alpha_m` parameters
    of a specific `LagrangeConstraintHandler`.

    Attributes:
        handler (LagrangeConstraintHandler): The `LagrangeConstraintHandler` instance
            being edited.
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers, used to save the updated handler.
        double_validator (DoubleValidator): A validator for double spin box inputs.
        alpha_s_spin (QDoubleSpinBox): Input field for the Alpha S scaling factor.
        alpha_m_spin (QDoubleSpinBox): Input field for the Alpha M scaling factor.
    """

    def __init__(self, handler: LagrangeConstraintHandler, parent: QWidget = None):
        """Initializes the LagrangeConstraintHandlerEditDialog.

        Args:
            handler: The `LagrangeConstraintHandler` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> from femora.components.Analysis.constraint_handlers import LagrangeConstraintHandler
            >>> # Create a dummy handler for demonstration
            >>> dummy_handler = LagrangeConstraintHandler(tag=2, alpha_s=0.3, alpha_m=0.4)
            >>> app = QApplication(sys.argv)
            >>> dialog = LagrangeConstraintHandlerEditDialog(dummy_handler)
            >>> # The dialog would normally be shown like:
            >>> # if dialog.exec() == QDialog.Accepted:
            >>> #     print(f"Handler updated via dialog, new params: {dialog.handler.alpha_s}, {dialog.handler.alpha_m}")
            >>> # print(f"Initial handler params: {dummy_handler.alpha_s}, {dummy_handler.alpha_m}")
            >>> # app.exec_() # For testing, typically dialogs are shown by parent
        """
        super().__init__(parent)
        self.handler = handler
        self.setWindowTitle(f"Edit Lagrange Constraint Handler (Tag: {handler.tag})")
        self.handler_manager = ConstraintHandlerManager()
        self.double_validator = DoubleValidator()

        # Main layout
        layout = QVBoxLayout(self)

        # Parameters group
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)

        # Alpha S
        self.alpha_s_spin = QDoubleSpinBox()
        self.alpha_s_spin.setDecimals(6)
        self.alpha_s_spin.setRange(1e-12, 1e12)
        self.alpha_s_spin.setValue(handler.alpha_s)
        params_layout.addRow("Alpha S:", self.alpha_s_spin)

        # Alpha M
        self.alpha_m_spin = QDoubleSpinBox()
        self.alpha_m_spin.setDecimals(6)
        self.alpha_m_spin.setRange(1e-12, 1e12)
        self.alpha_m_spin.setValue(handler.alpha_m)
        params_layout.addRow("Alpha M:", self.alpha_m_spin)

        layout.addWidget(params_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_handler)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_handler(self):
        """Saves the edited parameters for the Lagrange Constraint Handler.

        The old handler with the same tag is removed from the manager, and a
        new handler with the updated parameters (and the same tag) is created.
        The dialog is then accepted. If an error occurs, a critical message
        box is displayed.
        """
        try:
            # Collect parameters
            alpha_s = self.alpha_s_spin.value()
            alpha_m = self.alpha_m_spin.value()

            # Remove the old handler and create a new one with the same tag
            tag = self.handler.tag
            self.handler_manager.remove_handler(tag)

            # Create new handler
            self.handler = self.handler_manager.create_handler("lagrange", alpha_s=alpha_s, alpha_m=alpha_m)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class AutoConstraintHandlerDialog(QDialog):
    """Dialog for creating an Auto Constraint Handler.

    This handler automatically selects penalty values for compatibility constraints
    and allows configuration of verbosity and penalty override values.

    Attributes:
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers, used to create the new handler.
        double_validator (DoubleValidator): A validator for double spin box inputs.
        verbose_checkbox (QCheckBox): Checkbox to enable verbose output.
        auto_penalty_spin (QDoubleSpinBox): Input field for the auto-calculated
            penalty value. Represents None if its value is 1e-12, reflecting
            its "None" special value text.
        user_penalty_spin (QDoubleSpinBox): Input field for the user-defined
            penalty value. Represents None if its value is 1e-12, reflecting
            its "None" special value text.
        handler (AutoConstraintHandler | None): The created handler instance,
            set upon successful creation.
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the AutoConstraintHandlerDialog.

        Args:
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> dialog = AutoConstraintHandlerDialog()
            >>> # if dialog.exec() == QDialog.Accepted:
            >>> #     print(f"Created Auto handler with tag: {dialog.handler.tag}")
            >>> #     print(f"Verbose: {dialog.handler.verbose}")
            >>> #     print(f"Auto Penalty: {dialog.handler.auto_penalty}")
            >>> #     print(f"User Penalty: {dialog.handler.user_penalty}")
            >>> # app.exec_() # For testing, typically dialogs are shown by parent
        """
        super().__init__(parent)
        self.setWindowTitle("Create Auto Constraint Handler")
        self.handler_manager = ConstraintHandlerManager()
        self.double_validator = DoubleValidator()

        # Main layout
        layout = QVBoxLayout(self)

        # Parameters group
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)

        # Verbose
        self.verbose_checkbox = QCheckBox()
        params_layout.addRow("Verbose Output:", self.verbose_checkbox)

        # Auto Penalty
        self.auto_penalty_spin = QDoubleSpinBox()
        self.auto_penalty_spin.setDecimals(6)
        self.auto_penalty_spin.setRange(1e-12, 1e12)
        self.auto_penalty_spin.setValue(1.0)
        self.auto_penalty_spin.setSpecialValueText("None")
        params_layout.addRow("Auto Penalty:", self.auto_penalty_spin)

        # User Penalty
        self.user_penalty_spin = QDoubleSpinBox()
        self.user_penalty_spin.setDecimals(6)
        self.user_penalty_spin.setRange(1e-12, 1e12)
        self.user_penalty_spin.setValue(1.0)
        self.user_penalty_spin.setSpecialValueText("None")
        params_layout.addRow("User Penalty:", self.user_penalty_spin)

        layout.addWidget(params_group)

        # Info label
        info = QLabel("Auto constraint handler automatically selects the penalty value for compatibility constraints.\n"
                     "- Verbose: Output extra information during analysis\n"
                     "- Auto Penalty: Value for automatically calculated penalty\n"
                     "- User Penalty: Value for user-defined penalty")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_handler)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def create_handler(self):
        """Attempts to create a new AutoConstraintHandler with the specified parameters.

        If successful, the `handler` attribute is set and the dialog is accepted.
        If an error occurs, a critical message box is displayed.
        """
        try:
            # Collect parameters
            verbose = self.verbose_checkbox.isChecked()
            auto_penalty = self.auto_penalty_spin.value() if self.auto_penalty_spin.value() != 1e-12 else None
            user_penalty = self.user_penalty_spin.value() if self.user_penalty_spin.value() != 1e-12 else None

            # Create handler
            self.handler = self.handler_manager.create_handler("auto",
                                                             verbose=verbose,
                                                             auto_penalty=auto_penalty,
                                                             user_penalty=user_penalty)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class AutoConstraintHandlerEditDialog(QDialog):
    """Dialog for editing an existing Auto Constraint Handler.

    This dialog allows modification of the verbose, auto_penalty, and user_penalty
    parameters of a specific `AutoConstraintHandler`.

    Attributes:
        handler (AutoConstraintHandler): The `AutoConstraintHandler` instance
            being edited.
        handler_manager (ConstraintHandlerManager): The backend manager for
            constraint handlers, used to save the updated handler.
        double_validator (DoubleValidator): A validator for double spin box inputs.
        verbose_checkbox (QCheckBox): Checkbox to enable verbose output.
        auto_penalty_spin (QDoubleSpinBox): Input field for the auto-calculated
            penalty value. Represents None if its value is 1e-12, reflecting
            its "None" special value text.
        user_penalty_spin (QDoubleSpinBox): Input field for the user-defined
            penalty value. Represents None if its value is 1e-12, reflecting
            its "None" special value text.
    """

    def __init__(self, handler: AutoConstraintHandler, parent: QWidget = None):
        """Initializes the AutoConstraintHandlerEditDialog.

        Args:
            handler: The `AutoConstraintHandler` instance to be edited.
            parent: The parent widget of this dialog. Defaults to None.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> from femora.components.Analysis.constraint_handlers import AutoConstraintHandler
            >>> # Create a dummy handler for demonstration
            >>> dummy_handler = AutoConstraintHandler(tag=3, verbose=True, auto_penalty=1e5, user_penalty=None)
            >>> app = QApplication(sys.argv)
            >>> dialog = AutoConstraintHandlerEditDialog(dummy_handler)
            >>> # The dialog would normally be shown like:
            >>> # if dialog.exec() == QDialog.Accepted:
            >>> #     print(f"Handler updated via dialog, new params: {dialog.handler.verbose}, {dialog.handler.auto_penalty}, {dialog.handler.user_penalty}")
            >>> # print(f"Initial handler params: {dummy_handler.verbose}, {dummy_handler.auto_penalty}, {dummy_handler.user_penalty}")
            >>> # app.exec_() # For testing, typically dialogs are shown by parent
        """
        super().__init__(parent)
        self.handler = handler
        self.setWindowTitle(f"Edit Auto Constraint Handler (Tag: {handler.tag})")
        self.handler_manager = ConstraintHandlerManager()
        self.double_validator = DoubleValidator()

        # Main layout
        layout = QVBoxLayout(self)

        # Parameters group
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)

        # Verbose
        self.verbose_checkbox = QCheckBox()
        self.verbose_checkbox.setChecked(handler.verbose)
        params_layout.addRow("Verbose Output:", self.verbose_checkbox)

        # Auto Penalty
        self.auto_penalty_spin = QDoubleSpinBox()
        self.auto_penalty_spin.setDecimals(6)
        self.auto_penalty_spin.setRange(1e-12, 1e12)
        if handler.auto_penalty is not None:
            self.auto_penalty_spin.setValue(handler.auto_penalty)
        else:
            self.auto_penalty_spin.setValue(1e-12)  # Use minimum value to represent None
        self.auto_penalty_spin.setSpecialValueText("None")
        params_layout.addRow("Auto Penalty:", self.auto_penalty_spin)

        # User Penalty
        self.user_penalty_spin = QDoubleSpinBox()
        self.user_penalty_spin.setDecimals(6)
        self.user_penalty_spin.setRange(1e-12, 1e12)
        if handler.user_penalty is not None:
            self.user_penalty_spin.setValue(handler.user_penalty)
        else:
            self.user_penalty_spin.setValue(1e-12)  # Use minimum value to represent None
        self.user_penalty_spin.setSpecialValueText("None")
        params_layout.addRow("User Penalty:", self.user_penalty_spin)

        layout.addWidget(params_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_handler)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_handler(self):
        """Saves the edited parameters for the Auto Constraint Handler.

        The old handler with the same tag is removed from the manager, and a
        new handler with the updated parameters (and the same tag) is created.
        The dialog is then accepted. If an error occurs, a critical message
        box is displayed.
        """
        try:
            # Collect parameters
            verbose = self.verbose_checkbox.isChecked()
            auto_penalty = self.auto_penalty_spin.value() if self.auto_penalty_spin.value() != 1e-12 else None
            user_penalty = self.user_penalty_spin.value() if self.user_penalty_spin.value() != 1e-12 else None

            # Remove the old handler and create a new one with the same tag
            tag = self.handler.tag
            self.handler_manager.remove_handler(tag)

            # Create new handler
            self.handler = self.handler_manager.create_handler("auto",
                                                             verbose=verbose,
                                                             auto_penalty=auto_penalty,
                                                             user_penalty=user_penalty)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    import sys

    # Create the Qt Application
    app = QApplication(sys.argv)
    window = ConstraintHandlerManagerTab()
    window.show()
    sys.exit(app.exec_())