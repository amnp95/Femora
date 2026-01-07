"""
Parallel Section GUI Dialogs
Uses ParallelSection class methods instead of hardcoding
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFormLayout, QMessageBox, QGridLayout, QFrame, QTextBrowser, QGroupBox, QWidget, QListWidget, QListWidgetItem
)
from qtpy.QtCore import Qt

from femora.components.section.section_opensees import ParallelSection
from femora.components.section.section_base import Section

class ParallelSectionCreationDialog(QDialog):
    """Dialog for creating new ParallelSection objects.

    This dialog allows users to define a new `ParallelSection` by providing a
    unique name and selecting multiple existing `Section` objects to combine
    in parallel. It leverages the `ParallelSection` class methods for parameter
    retrieval and validation.

    Attributes:
        parameters (dict): The parameters schema retrieved from `ParallelSection.get_parameters()`.
        descriptions (dict): Descriptive texts for parameters from `ParallelSection.get_description()`.
        user_name_input (QLineEdit): Input field for the new section's user-defined name.
        sections_list (QListWidget): Displays all available `Section` objects for multi-selection.
        created_section (ParallelSection): Stores the successfully created `ParallelSection` instance
            after the dialog is accepted.
    
    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.section.section_base import Section
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> app = QApplication([])
        >>> # Ensure some sections exist for combination
        >>> _ = ElasticSection(tag=1001, user_name="Steel Section", E=200e9, G=77e9, A=0.01, Ix=1e-5, Iy=2e-5, J=3e-5, mass_density=7850)
        >>> _ = ElasticSection(tag=1002, user_name="Concrete Section", E=30e9, G=12e9, A=0.05, Ix=5e-4, Iy=6e-4, J=7e-4, mass_density=2400)
        >>>
        >>> dialog = ParallelSectionCreationDialog()
        >>> # In a real application, you would show the dialog and wait for interaction
        >>> # For a programmatic example, we simulate input
        >>> dialog.user_name_input.setText("MyParallelSection")
        >>> steel_item = dialog.sections_list.findItems("Steel Section (Tag: 1001)", Qt.MatchExactly)[0]
        >>> concrete_item = dialog.sections_list.findItems("Concrete Section (Tag: 1002)", Qt.MatchExactly)[0]
        >>> steel_item.setSelected(True)
        >>> concrete_item.setSelected(True)
        >>>
        >>> # Simulate clicking "Create Section"
        >>> dialog.create_section()
        >>>
        >>> if dialog.result() == QDialog.Accepted: # Check if dialog was accepted
        ...     new_section = dialog.created_section
        ...     print(f"Created Parallel Section: {new_section.user_name} (Tag: {new_section.tag})")
        ...     print(f"Combined sections: {[s.user_name for s in new_section.sections]}")
    """
    def __init__(self, parent: QWidget = None):
        """Initializes the ParallelSectionCreationDialog.

        Args:
            parent: The parent widget for this dialog. Defaults to `None`.
        """
        super().__init__(parent)
        self.setWindowTitle("Create Parallel Section")
        self.setMinimumSize(600, 400)
        
        self.parameters = ParallelSection.get_parameters()
        self.descriptions = ParallelSection.get_description()
        
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
        
        # Sections group
        sections_group = QGroupBox("Sections to Combine in Parallel")
        sections_layout = QVBoxLayout(sections_group)
        self.sections_list = QListWidget()
        self.sections_list.setSelectionMode(QListWidget.MultiSelection)
        for tag, section in Section.get_all_sections().items():
            item = QListWidgetItem(f"{section.user_name} (Tag: {tag})")
            item.setData(Qt.UserRole, section)
            self.sections_list.addItem(item)
        sections_layout.addWidget(self.sections_list)
        left_layout.addWidget(sections_group)
        
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
        help_display.setHtml(ParallelSection.get_help_text())
        right_layout.addWidget(help_display)
        main_layout.addWidget(right_widget)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(2, 2)

    def create_section(self):
        """Attempts to create a new ParallelSection based on user input.

        This method validates the user-provided section name and the selected
        list of sections. If validation is successful, a new `ParallelSection`
        instance is created and stored in `self.created_section`, and the dialog
        is accepted. On any error, a warning message box is displayed.
        """
        try:
            user_name = self.user_name_input.text().strip()
            if not user_name:
                QMessageBox.warning(self, "Input Error", "Please enter a section name.")
                return
            try:
                # Check if a section with this user_name already exists globally
                existing_section = Section.get_section_by_name(user_name)
                QMessageBox.warning(self, "Input Error", f"Section with name '{user_name}' already exists.")
                return
            except KeyError:
                pass # Name is unique, proceed
            
            selected_items = self.sections_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Input Error", "Please select at least one section to combine.")
                return
            sections = [item.data(Qt.UserRole) for item in selected_items]
            params = {'sections': sections}
            
            # The ParallelSection constructor handles its own validation,
            # but we can optionally call a static validation method if available.
            # Assuming ParallelSection has an internal validation or constructor handles it.
            # For this example, we directly pass to constructor.
            
            self.created_section = ParallelSection(user_name=user_name, **params)
            QMessageBox.information(self, "Success", f"Parallel Section '{user_name}' created successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")

class ParallelSectionEditDialog(QDialog):
    """Dialog for editing an existing ParallelSection object.

    This dialog allows users to modify the list of constituent `Section` objects
    that form an existing `ParallelSection`. It displays the section's current
    properties and provides a multi-selection list of all available sections.

    Attributes:
        section (ParallelSection): The `ParallelSection` instance being edited.
        parameters (dict): The parameters schema retrieved from `section.get_parameters()`.
        descriptions (dict): Descriptive texts for parameters from `section.get_description()`.
        tag_label (QLabel): Displays the unique tag of the `ParallelSection`.
        user_name_label (QLabel): Displays the user-defined name of the `ParallelSection`.
        type_label (QLabel): Displays the type name of the `ParallelSection` (e.g., 'ParallelSection').
        sections_list (QListWidget): Displays all available `Section` objects, with the
            currently combined ones pre-selected.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.section.section_base import Section
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> app = QApplication([])
        >>> s1 = ElasticSection(tag=2001, user_name="Steel Section", E=200e9, G=77e9, A=0.01, Ix=1e-5, Iy=2e-5, J=3e-5, mass_density=7850)
        >>> s2 = ElasticSection(tag=2002, user_name="Concrete Section", E=30e9, G=12e9, A=0.05, Ix=5e-4, Iy=6e-4, J=7e-4, mass_density=2400)
        >>> s3 = ElasticSection(tag=2003, user_name="Wood Section", E=10e9, G=4e9, A=0.02, Ix=1e-5, Iy=1e-5, J=1e-5, mass_density=800)
        >>> existing_parallel_section = ParallelSection(user_name="MyExistingParallel", sections=[s1, s2])
        >>>
        >>> dialog = ParallelSectionEditDialog(existing_parallel_section)
        >>> # Simulate user interaction: deselect Concrete, select Wood
        >>> concrete_item = dialog.sections_list.findItems("Concrete Section (Tag: 2002)", Qt.MatchExactly)[0]
        >>> wood_item = dialog.sections_list.findItems("Wood Section (Tag: 2003)", Qt.MatchExactly)[0]
        >>> concrete_item.setSelected(False)
        >>> wood_item.setSelected(True)
        >>>
        >>> # Simulate clicking "Save Changes"
        >>> dialog.save_changes()
        >>>
        >>> if dialog.result() == QDialog.Accepted: # Check if dialog was accepted
        ...     print(f"Updated Parallel Section: {existing_parallel_section.user_name}")
        ...     print(f"New combined sections: {[s.user_name for s in existing_parallel_section.sections]}")
    """
    def __init__(self, section: ParallelSection, parent: QWidget = None):
        """Initializes the ParallelSectionEditDialog.

        Args:
            section: The `ParallelSection` object to be edited.
            parent: The parent widget for this dialog. Defaults to `None`.
        """
        super().__init__(parent)
        self.section = section
        self.setWindowTitle(f"Edit Parallel Section: {section.user_name}")
        self.setMinimumSize(600, 400)
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
        # Sections group
        sections_group = QGroupBox("Sections to Combine in Parallel")
        sections_layout = QVBoxLayout(sections_group)
        self.sections_list = QListWidget()
        self.sections_list.setSelectionMode(QListWidget.MultiSelection)
        all_sections = list(Section.get_all_sections().values())
        for s in all_sections:
            item = QListWidgetItem(f"{s.user_name} (Tag: {s.tag})")
            item.setData(Qt.UserRole, s)
            self.sections_list.addItem(item)
            if s in section.sections:
                item.setSelected(True)
        sections_layout.addWidget(self.sections_list)
        left_layout.addWidget(sections_group)
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
        """Attempts to save changes to the `ParallelSection` based on user selections.

        This method updates the `sections` attribute of the `self.section` object
        with the currently selected constituent sections from the list.
        If successful, a confirmation message is shown and the dialog is accepted.
        On any error, a warning message box is displayed.
        """
        try:
            selected_items = self.sections_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Input Error", "Please select at least one section to combine.")
                return
            sections = [item.data(Qt.UserRole) for item in selected_items]
            
            # Update the existing ParallelSection instance
            self.section.sections = sections
            QMessageBox.information(self, "Success", f"Section '{self.section.user_name}' updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update section: {str(e)}")