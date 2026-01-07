from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QDialog, QMessageBox, QTableWidget, QTableWidgetItem, 
    QPushButton, QHeaderView, QCheckBox
)

from femora.components.Analysis.numberers import NumbererManager, Numberer


class NumbererManagerTab(QDialog):
    """A dialog for managing and selecting numberers in the Femora analysis.

    This dialog allows users to view available numberer types, read their
    descriptions, and select a single active numberer. Numberers define how
    degrees of freedom (DOFs) are mapped to global equation numbers, impacting
    the performance and memory usage of the solver.

    Attributes:
        numberer_manager (NumbererManager): The singleton manager for numberer
            instances.
        numberers_table (QTableWidget): Table displaying available numberers,
            their types, and descriptions.
        checkboxes (list[QCheckBox]): List of checkboxes, one for each numberer
            in the table, ensuring mutual exclusivity.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> manager_tab = NumbererManagerTab()
        >>> manager_tab.show()
        >>> # To interact: manager_tab.exec_() for modal dialog
        >>> # Get selected type after user interaction
        >>> selected_type = manager_tab.get_selected_numberer_type()
        >>> print(selected_type)
        plain # Assuming 'plain' is the default/first selected
    """

    def __init__(self, parent=None):
        """Initializes the NumbererManagerTab dialog.

        Args:
            parent (QWidget, optional): The parent widget for this dialog.
                Defaults to None.
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
        """Populates the numberers table with available numberers.

        This method retrieves all registered numberers from the `NumbererManager`,
        creates a row for each in the `numberers_table`, and adds a mutually
        exclusive checkbox for selection, the numberer type, and its description.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table() # Called internally by __init__
            >>> print(manager_tab.numberers_table.rowCount())
            3 # Assuming 3 numberers are registered (plain, rcm, amd)
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
        """Handles checkbox toggling to ensure mutual exclusivity among numberer selections.

        When a checkbox is checked, all other checkboxes in the table are
        automatically unchecked, ensuring only one numberer can be active at a time.

        Args:
            checked (bool): True if the checkbox is checked, False otherwise.
            btn (QCheckBox): The checkbox that was toggled.

        Example:
            >>> from qtpy.QtWidgets import QApplication, QCheckBox
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table()
            >>> # Simulate toggling the first checkbox
            >>> first_checkbox = manager_tab.checkboxes[0]
            >>> first_checkbox.setChecked(True) # This will trigger the method
            >>> assert first_checkbox.isChecked()
            >>> if len(manager_tab.checkboxes) > 1:
            ...     second_checkbox = manager_tab.checkboxes[1]
            ...     assert not second_checkbox.isChecked() # Ensure others are unchecked
        """
        if checked:
            # Uncheck all other checkboxes
            for checkbox in self.checkboxes:
                if checkbox != btn and checkbox.isChecked():
                    checkbox.setChecked(False)

    def get_selected_numberer_type(self) -> str | None:
        """Retrieves the type name of the currently selected numberer.

        Iterates through the checkboxes to find which one is checked and
        returns the corresponding numberer type from the table.

        Returns:
            str | None: The lowercase string name of the selected numberer (e.g., "plain", "rcm"),
                or None if no numberer is currently selected.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table()
            >>> manager_tab.checkboxes[0].setChecked(True)
            >>> print(manager_tab.get_selected_numberer_type())
            plain
        """
        for row, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                type_item = self.numberers_table.item(row, 1)
                return type_item.text().lower()
        return None

    def get_selected_numberer(self) -> str | None:
        """Retrieves the type name of the currently selected numberer from the program state.

        In this implementation, it returns the type of the first registered numberer
        as a default selection. A more robust implementation would track the
        currently active numberer within the application's model.

        Returns:
            str | None: The lowercase string name of the currently active numberer
                (e.g., "plain"), or None if no numberers are registered.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> # The manager_tab's __init__ will call initialize_numberers_table
            >>> # and this method is called within initialize_numberers_table
            >>> print(manager_tab.get_selected_numberer())
            plain # Assuming 'plain' is the first registered numberer
        """
        # For this implementation, we'll just return the first numberer
        numberers = list(self.numberer_manager.get_all_numberers().keys())
        if numberers:
            return numberers[0]
        return None

    def select_numberer(self, numberer_type: str | Numberer | None):
        """Sets the specified numberer as active in the table.

        This method attempts to find a numberer in the table matching the
        given type (string or Numberer object) and checks its corresponding
        checkbox. This will implicitly uncheck other checkboxes due to
        mutual exclusivity.

        Args:
            numberer_type (str | Numberer | None): The type name of the numberer
                to select (e.g., "plain", "rcm"), or a Numberer instance itself.
                If None, no action is taken.

        Example:
            >>> from qtpy.QtWidgets import QApplication
            >>> import sys
            >>> app = QApplication(sys.argv)
            >>> manager_tab = NumbererManagerTab()
            >>> manager_tab.initialize_numberers_table()
            >>> # Initially, the first numberer might be selected
            >>> assert manager_tab.get_selected_numberer_type() == 'plain'
            >>> # Select another numberer, e.g., 'rcm'
            >>> manager_tab.select_numberer("rcm")
            >>> print(manager_tab.get_selected_numberer_type())
            rcm
            >>> # You can also pass a Numberer object
            >>> from femora.components.Analysis.numberers import PlainNumberer
            >>> plain_numberer_instance = PlainNumberer()
            >>> manager_tab.select_numberer(plain_numberer_instance)
            >>> print(manager_tab.get_selected_numberer_type())
            plain
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
        """Provides a textual description for a given numberer type.

        Args:
            numberer_type (str): The lowercase string name of the numberer
                (e.g., "plain", "rcm", "amd").

        Returns:
            str: A descriptive string for the numberer, or "No description available."
                if the type is not recognized.

        Example:
            >>> manager_tab = NumbererManagerTab()
            >>> print(manager_tab.get_numberer_description("plain"))
            Assigns equation numbers to DOFs based on the order in which nodes are created.
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