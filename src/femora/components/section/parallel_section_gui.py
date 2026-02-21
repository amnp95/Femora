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
    """Dialog for creating new ParallelSection sections.

    This dialog allows users to specify a unique name for a new parallel
    section and select multiple existing sections to combine in parallel.
    It leverages the static methods of the `ParallelSection` class for
    parameter retrieval and validation.

    Attributes:
        parameters (dict): The parameters required for a ParallelSection,
            retrieved from `ParallelSection.get_parameters()`.
        descriptions (dict): Descriptions for the ParallelSection parameters,
            retrieved from `ParallelSection.get_description()`.
        user_name_input (QLineEdit): Input field for the new section's name.
        sections_list (QListWidget): List widget displaying available sections
            for selection.
        created_section (ParallelSection): The `ParallelSection` instance
            created upon successful dialog acceptance.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.section.section_base import Section
        >>> from femora.components.section.section_opensees import ElasticSection
        >>> # Assume some sections exist for selection
        >>> _ = QApplication([]) # Required for Qt widgets in a script
        >>> s1 = ElasticSection(user_name="Steel_1", E=200e9, G=77e9, A=0.01, Iz=8.33e-05, Iy=8.33e-05, J=1.66e-04)
        >>> s2 = ElasticSection(user_name="Concrete_2", E=30e9, G=12e9, A=0.02, Iz=1.0e-04, Iy=1.0e-04, J=2.0e-04)
        >>> dialog = ParallelSectionCreationDialog()
        >>> if dialog.exec_():
        ...     new_section = dialog.created_section
        ...     print(f"Created section: {new_section.user_name} (Tag: {new_section.tag})")
        ...     # Further interaction with new_section
        ...     # Remove sections for cleanup in example
        ...     Section.remove_section_by_tag(s1.tag)
        ...     Section.remove_section_by_tag(s2.tag)
        ...     Section.remove_section_by_tag(new_section.tag)
    """

    def __init__(self, parent=None):
        """Initializes the ParallelSectionCreationDialog.

        Args:
            parent (QWidget, optional): The parent widget for this dialog.
                Defaults to None.
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
        """Handles the creation of a new ParallelSection.

        This method is connected to the 'Create Section' button. It performs
        the following steps:
        1. Validates that a unique section name has been entered.
        2. Validates that at least one component section has been selected.
        3. Retrieves the selected `Section` objects.
        4. Calls `ParallelSection.validate_section_parameters` to ensure
           the selected sections are valid for combination.
        5. Instantiates a new `ParallelSection` with the provided name and
           selected component sections.
        6. Displays success or error messages using `QMessageBox`.
        7. If successful, sets `self.created_section` and accepts the dialog.
        """
        try:
            user_name = self.user_name_input.text().strip()
            if not user_name:
                QMessageBox.warning(self, "Input Error", "Please enter a section name.")
                return
            try:
                existing_section = ParallelSection.get_section_by_name(user_name)
                QMessageBox.warning(self, "Input Error", f"Section with name '{user_name}' already exists.")
                return
            except KeyError:
                pass
            selected_items = self.sections_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Input Error", "Please select at least one section to combine.")
                return
            sections = [item.data(Qt.UserRole) for item in selected_items]
            params = {'sections': sections}
            try:
                validated_params = ParallelSection.validate_section_parameters(**params)
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return
            self.created_section = ParallelSection(user_name=user_name, **params)
            QMessageBox.information(self, "Success", f"Parallel Section '{user_name}' created successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create section: {str(e)}")

class ParallelSectionEditDialog(QDialog):
    """Dialog for editing an existing ParallelSection.

    This dialog displays the properties of an existing `ParallelSection`
    and allows the user to modify the component sections that are combined
    in parallel.

    Attributes:
        section (ParallelSection): The `ParallelSection` instance being edited.
        parameters (dict): The parameters definition for the section type.
        descriptions (dict): Descriptions of the section parameters.
        tag_label (QLabel): Displays the unique tag of the section.
        user_name_label (QLabel): Displays the user-defined name of the section.
        type_label (QLabel): Displays the type of the section (e.g., 'ParallelSection').
        sections_list (QListWidget): List widget displaying all available sections,
            with currently combined sections pre-selected.

    Example:
        >>> from qtpy.QtWidgets import QApplication
        >>> from femora.components.section.section_base import Section
        >>> from femora.components.section.section_opensees import ElasticSection, ParallelSection
        >>> # Assume some sections exist and a parallel section needs editing
        >>> _ = QApplication([]) # Required for Qt widgets in a script
        >>> s1 = ElasticSection(user_name="Steel_Beam", E=200e9, G=77e9, A=0.01, Iz=8.33e-05, Iy=8.33e-05, J=1.66e-04)
        >>> s2 = ElasticSection(user_name="Concrete_Slab", E=30e9, G=12e9, A=0.02, Iz=1.0e-04, Iy=1.0e-04, J=2.0e-04)
        >>> current_parallel = ParallelSection(user_name="Combined_Section", sections=[s1, s2])
        >>>
        >>> dialog = ParallelSectionEditDialog(section=current_parallel)
        >>> if dialog.exec_():
        ...     print(f"Updated section '{current_parallel.user_name}' with sections:")
        ...     for s in current_parallel.sections:
        ...         print(f"- {s.user_name} (Tag: {s.tag})")
        ...     # Remove sections for cleanup in example
        ...     Section.remove_section_by_tag(s1.tag)
        ...     Section.remove_section_by_tag(s2.tag)
        ...     Section.remove_section_by_tag(current_parallel.tag)
    """
    def __init__(self, section: ParallelSection, parent=None):
        """Initializes the ParallelSectionEditDialog.

        Args:
            section: The `ParallelSection` instance to be edited.
            parent (QWidget, optional): The parent widget for this dialog.
                Defaults to None.
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
        """Handles saving changes to the existing ParallelSection.

        This method is connected to the 'Save Changes' button. It performs
        the following steps:
        1. Validates that at least one component section has been selected.
        2. Updates the `sections` attribute of the `self.section` object
           with the newly selected component sections.
        3. Displays success or error messages using `QMessageBox`.
        """
        try:
            selected_items = self.sections_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Input Error", "Please select at least one section to combine.")
                return
            sections = [item.data(Qt.UserRole) for item in selected_items]
            self.section.sections = sections
            QMessageBox.information(self, "Success", f"Section '{self.section.user_name}' updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update section: {str(e)}")