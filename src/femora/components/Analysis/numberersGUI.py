from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QDialog, QMessageBox, QTableWidget, QTableWidgetItem, 
    QPushButton, QHeaderView, QCheckBox
)

from femora.components.Analysis.numberers import NumbererManager, Numberer


class NumbererManagerTab(QDialog):
    """A dialog window for managing and selecting numberers for a structural analysis.

    This dialog allows users to view available numbering algorithms (numberers),
    select an active one, and understand their descriptions. Numberers determine
    the mapping between equation numbers and degrees of freedom (DOFs) in the
    global stiffness matrix, influencing the sparsity and conditioning of the
    system matrix.

    Attributes:
        numberer_manager (NumbererManager): An instance of the NumbererManager
            to access and manage available numbering algorithms.
        numberers_table (QTableWidget): A table widget displaying the list of
            available numberers, their types, and descriptions. It supports
            single-row selection via checkboxes.
        checkboxes (list[QCheckBox]): A list of QCheckBox widgets, one for each
            numberer in the table, enabling mutual exclusive selection.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> manager_tab = NumbererManagerTab()
        >>> manager_tab.show()
        >>> # To interact, a user would typically click 'OK' or close the window.
        >>> # For a non-interactive test, we can simulate pressing 'OK'.
        >>> manager_tab.accept()
    """

    def __init__(self, parent: QWidget = None):
        """Initializes the NumbererManagerTab dialog.

        Args:
            parent: The parent widget of this dialog. If None, the dialog
                will be a top-level window.
        """
        super().__init__(parent)
        
        # Setup dialog properties
        self.setWindowTitle("Numberer Manager")
        self.resize(600, 400)
        
        # Get the numberer manager instance
        self.numberer_manager = NumbererManager()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Description label
        description = QLabel(
            "Numberers determine the mapping between equation numbers and DOFs. "
            "Only one numberer can be active at a time."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Table showing available numberers
        self.numberers_table = QTableWidget()
        self.numberers_table.setColumnCount(3)  # Select, Type, Description
        self.numberers_table.setHorizontalHeaderLabels(["Select", "Type", "Description"])
        self.numberers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.numberers_table.setSelectionMode(QTableWidget.SingleSelection)
        header = self.numberers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.numberers_table)
        
        # Initialize the table with available numberers
        self.initialize_numberers_table()
        
        # Add OK button at the bottom
        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)
        layout.addLayout(buttons_layout)

    def initialize_numberers_table(self):
        """Populates the numberers table with available numbering algorithms.

        This method retrieves all registered numberers from the NumbererManager,
        creates a row for each in the `numberers_table`, and adds a mutually
        exclusive checkbox for selection. It also sets the description for each
        numberer.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table() # This is called by __init__, but demonstrates use.
            >>> print(manager_tab.numberers_table.rowCount() > 0)
            True
            >>> manager_tab.accept()
        """
        numberers = self.numberer_manager.get_all_numberers()
        
        selected_numberer = self.get_selected_numberer()
        
        self.numberers_table.setRowCount(len(numberers))
        self.checkboxes = []  # Changed from radio_buttons to checkboxes
        
        # Hide vertical header (row indices)
        self.numberers_table.verticalHeader().setVisible(False)
        
        for row, (type_name, numberer) in enumerate(numberers.items()):
            # Select checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("QCheckBox::indicator { width: 15px; height: 15px; }")
            # Connect checkboxes to ensure mutual exclusivity
            checkbox.toggled.connect(lambda checked, btn=checkbox: self.on_checkbox_toggled(checked, btn))
            self.checkboxes.append(checkbox)
            
            # If this was the previously selected numberer, check its checkbox
            if selected_numberer and selected_numberer == type_name:
                checkbox.setChecked(True)
            
            checkbox_cell = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_cell)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.numberers_table.setCellWidget(row, 0, checkbox_cell)
            
            # Numberer Type
            type_item = QTableWidgetItem(type_name.capitalize())
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.numberers_table.setItem(row, 1, type_item)
            
            # Description
            description = self.get_numberer_description(type_name)
            desc_item = QTableWidgetItem(description)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.numberers_table.setItem(row, 2, desc_item)

    def on_checkbox_toggled(self, checked: bool, btn: QCheckBox):
        """Handles the toggling of a checkbox to enforce mutual exclusivity.

        When a checkbox is checked, all other checkboxes in the `numberers_table`
        are unchecked to ensure only one numberer can be active at a time.

        Args:
            checked: True if the checkbox is checked, False otherwise.
            btn: The QCheckBox instance that triggered the signal.

        Example:
            >>> from qtpy.QtWidgets import QApplication, QCheckBox
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table()
            >>> if manager_tab.checkboxes and len(manager_tab.checkboxes) >= 2:
            ...     first_cb = manager_tab.checkboxes[0]
            ...     second_cb = manager_tab.checkboxes[1]
            ...
            ...     # Simulate checking the first checkbox
            ...     first_cb.setChecked(True)
            ...     print(f"First checkbox checked: {first_cb.isChecked()}")
            True
            ...
            ...     # Simulate checking the second checkbox
            ...     second_cb.setChecked(True)
            ...     print(f"First checkbox checked after second checked: {first_cb.isChecked()}")
            False
            ...     print(f"Second checkbox checked: {second_cb.isChecked()}")
            True
            >>> manager_tab.accept()
        """
        if checked:
            # Uncheck all other checkboxes
            for checkbox in self.checkboxes:
                if checkbox != btn and checkbox.isChecked():
                    checkbox.setChecked(False)

    def get_selected_numberer_type(self) -> str | None:
        """Retrieves the type name of the currently selected numberer.

        Iterates through the checkboxes in the table to find the one that
        is currently checked and returns its corresponding numberer type
        (e.g., "plain", "rcm").

        Returns:
            The lowercase string representation of the selected numberer's type,
            or None if no numberer is currently selected.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table()
            >>> if manager_tab.checkboxes:
            ...     # Simulate selecting the first numberer
            ...     manager_tab.checkboxes[0].setChecked(True)
            ...     selected_type = manager_tab.get_selected_numberer_type()
            ...     print(selected_type is not None)
            True
            >>> manager_tab.accept()
        """
        for row, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                type_item = self.numberers_table.item(row, 1)
                return type_item.text().lower()
        return None

    def get_selected_numberer(self) -> str | None:
        """Retrieves the type name of the numberer currently active in the program state.

        This method acts as a placeholder to fetch the globally active numberer type.
        In a full application, this would typically query a model or configuration
        object to determine the active numberer, rather than simply returning
        the first available one.

        Returns:
            The lowercase string representation of the currently active numberer's type,
            or None if no numberer is active or available.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table()
            >>> selected_numberer_initial = manager_tab.get_selected_numberer()
            >>> print(selected_numberer_initial is not None)
            True
            >>> manager_tab.accept()
        """
        # For this implementation, we'll just return the first numberer
        numberers = list(self.numberer_manager.get_all_numberers().keys())
        if numberers:
            return numberers[0]
        return None

    def select_numberer(self, numberer_type: str | Numberer | None):
        """Selects a numberer in the table based on its type or a Numberer instance.

        If a numberer matching the provided type is found in the table, its
        corresponding checkbox will be checked, automatically unchecking any
        previously selected numberer due to the mutual exclusivity logic.
        This method handles both string type names and actual Numberer objects.

        Args:
            numberer_type: The type name (e.g., "plain", "rcm") of the numberer
                to select, or an actual Numberer instance. If None, the method
                returns without making a selection.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table()
            >>> # Assume 'plain' numberer exists and is the first one
            >>> manager_tab.select_numberer("plain")
            >>> selected_type = manager_tab.get_selected_numberer_type()
            >>> print(selected_type == "plain")
            True
            >>> manager_tab.accept()
        """
        if numberer_type is None:
            return
            
        # Handle case when passed an actual numberer object
        if hasattr(numberer_type, "__class__"):
            # Get the class name and extract the type from it
            class_name = numberer_type.__class__.__name__
            # Remove "Numberer" from the end and convert to lowercase
            if class_name.endswith("Numberer"):
                numberer_type = class_name[:-8].lower()
            
        for row, checkbox in enumerate(self.checkboxes):
            type_item = self.numberers_table.item(row, 1)
            if type_item and type_item.text().lower() == numberer_type.lower():
                checkbox.setChecked(True)
                return

    def get_numberer_description(self, numberer_type: str) -> str:
        """Retrieves a descriptive text for a given numberer type.

        Provides user-friendly explanations for common numberer algorithms.

        Args:
            numberer_type: The lowercase string representation of the numberer type
                (e.g., "plain", "rcm", "amd").

        Returns:
            A string containing the description of the numberer, or "No description
            available." if the type is not recognized.

        Example:
            >>> manager_tab = NumbererManagerTab()
            >>> print(manager_tab.get_numberer_description("rcm"))
            Reverse Cuthill-McKee algorithm, reduces the bandwidth of the system matrix.
            >>> print(manager_tab.get_numberer_description("unknown"))
            No description available.
        """
        descriptions = {
            "plain": "Assigns equation numbers to DOFs based on the order in which nodes are created.",
            "rcm": "Reverse Cuthill-McKee algorithm, reduces the bandwidth of the system matrix.",
            "amd": "Alternate Minimum Degree algorithm, minimizes fill-in during matrix factorization."
        }
        return descriptions.get(numberer_type.lower(), "No description available.")


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    import sys
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    window = NumbererManagerTab()
    window.show()
    sys.exit(app.exec_())