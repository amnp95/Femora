"""
Utilities for managing material selection in GUI dialogs.

This module provides helper functions to populate QComboBox widgets with
material data from the Femora project, apply filters, and retrieve
selections. It simplifies material management within graphical user
interfaces for structural analysis sections.
"""

from qtpy.QtWidgets import QComboBox
from femora.components.Material.materialBase import Material


def setup_material_dropdown(combo_box: QComboBox, material_filter=None, placeholder_text="Select Material"):
    """Populates a QComboBox with available materials, optionally filtered.

    This function fetches all materials registered in the Femora system,
    sorts them by user-defined name, and adds them to the provided QComboBox.
    It supports an optional filter function to display only specific types
    of materials and allows for custom placeholder text.

    Args:
        combo_box: The QComboBox widget to populate with materials.
        material_filter: Optional. A callable filter function that takes
            a `Material` object as an argument and returns `True` if the
            material should be included in the dropdown, `False` otherwise.
            Example: `lambda mat: mat.material_type == 'uniaxialMaterial'`.
        placeholder_text: The text to display for the initial, non-material
            selection option in the dropdown.

    Example:
        >>> from qtpy.QtWidgets import QComboBox
        >>> from unittest.mock import Mock
        >>> # Mock materials for a runnable example
        >>> original_get_all = Material.get_all_materials
        >>> Material.get_all_materials = Mock(return_value={
        ...     1: Mock(spec=Material, user_name="Steel A", tag=1, material_type='uniaxialMaterial', material_name='steel01'),
        ...     2: Mock(spec=Material, user_name="Concrete B", tag=2, material_type='nDMaterial', material_name='conc01'),
        ...     3: Mock(spec=Material, user_name="Elastic Mat", tag=3, material_type='uniaxialMaterial', material_name='elastic')
        ... })
        >>> material_combo = QComboBox()
        >>> setup_material_dropdown(material_combo,
        ...     material_filter=lambda m: m.material_type == 'uniaxialMaterial',
        ...     placeholder_text="Choose Uniaxial")
        >>> print(material_combo.count()) # Placeholder + Steel A + Elastic Mat
        3
        >>> print(material_combo.itemText(1))
        Steel A (Tag: 1, Type: uniaxialMaterial - steel01)
        >>> Material.get_all_materials = original_get_all # Clean up mock
    """
    combo_box.clear()
    combo_box.addItem(placeholder_text, None)
    
    all_materials = Material.get_all_materials()
    
    if not all_materials:
        combo_box.addItem("No materials available", None)
        combo_box.setEnabled(False)
        return
    
    combo_box.setEnabled(True)
    
    # Sort materials by name for better user experience
    sorted_materials = sorted(all_materials.items(), key=lambda x: x[1].user_name.lower())
    
    for tag, material in sorted_materials:
        # Apply filter if provided
        if material_filter and not material_filter(material):
            continue
            
        # Create descriptive display name
        display_name = f"{material.user_name} (Tag: {tag}, Type: {material.material_type} - {material.material_name})"
        combo_box.addItem(display_name, material)




def setup_any_material_dropdown(combo_box: QComboBox):
    """Populates a QComboBox with all available materials without any filter.

    This is a convenience function that calls `setup_material_dropdown`
    with no specific filter, making all registered materials available
    for selection. The placeholder text defaults to "Select Any Material".

    Args:
        combo_box: The QComboBox widget to populate.

    Example:
        >>> from qtpy.QtWidgets import QComboBox
        >>> from unittest.mock import Mock
        >>> original_get_all = Material.get_all_materials
        >>> Material.get_all_materials = Mock(return_value={
        ...     1: Mock(spec=Material, user_name="Steel A", tag=1, material_type='uniaxialMaterial', material_name='steel01')
        ... })
        >>> material_combo = QComboBox()
        >>> setup_any_material_dropdown(material_combo)
        >>> print(material_combo.itemText(0))
        Select Any Material
        >>> Material.get_all_materials = original_get_all # Clean up mock
    """
    setup_material_dropdown(combo_box, None, "Select Any Material")


def get_material_by_combo_selection(combo_box: QComboBox):
    """Retrieves the currently selected `Material` object from a QComboBox.

    This function extracts the data associated with the currently selected
    item in the provided combo box, which is expected to be a `Material`
    instance.

    Args:
        combo_box: The QComboBox from which to retrieve the selection.

    Returns:
        The selected `Material` object, or `None` if no material is selected
        (e.g., if the placeholder item is active).

    Example:
        >>> from qtpy.QtWidgets import QComboBox
        >>> from unittest.mock import Mock
        >>> # Mock a material
        >>> mock_material = Mock(spec=Material, user_name="Concrete C30", tag=101, material_type='nDMaterial', material_name='conc01')
        >>> combo = QComboBox()
        >>> combo.addItem("Select Material", None)
        >>> combo.addItem("Concrete C30 (Tag: 101)", mock_material)
        >>> combo.setCurrentIndex(1)
        >>> selected = get_material_by_combo_selection(combo)
        >>> print(selected.tag)
        101
        >>> combo.setCurrentIndex(0)
        >>> selected = get_material_by_combo_selection(combo)
        >>> print(selected is None)
        True
    """
    return combo_box.currentData()


def set_combo_to_material(combo_box: QComboBox, material):
    """Sets the selection of a QComboBox to a specific `Material` object.

    If the material is already present in the combo box, its index is selected.
    If the material is not found, it is added to the combo box, and then selected.
    If `None` is provided, the placeholder item is selected (index 0).

    Args:
        combo_box: The QComboBox to update.
        material: The `Material` object to select, or `None` to select
            the placeholder.

    Example:
        >>> from qtpy.QtWidgets import QComboBox
        >>> from unittest.mock import Mock
        >>> # Mock materials for a runnable example
        >>> mock_material_a = Mock(spec=Material, user_name="Steel A", tag=1, material_type='uniaxialMaterial', material_name='steel01')
        >>> mock_material_b = Mock(spec=Material, user_name="Concrete B", tag=2, material_type='nDMaterial', material_name='conc01')
        >>> mock_material_c = Mock(spec=Material, user_name="Alloy C", tag=3, material_type='uniaxialMaterial', material_name='alloy01')
        >>>
        >>> combo = QComboBox()
        >>> # Manually add items to simulate a pre-populated dropdown
        >>> combo.addItem("Placeholder", None)
        >>> combo.addItem(f"{mock_material_a.user_name} (Tag: {mock_material_a.tag})", mock_material_a)
        >>> combo.addItem(f"{mock_material_b.user_name} (Tag: {mock_material_b.tag})", mock_material_b)
        >>>
        >>> set_combo_to_material(combo, mock_material_a)
        >>> print(combo.currentText())
        Steel A (Tag: 1)
        >>>
        >>> set_combo_to_material(combo, None)
        >>> print(combo.currentText())
        Placeholder
        >>>
        >>> # Material not in list, should be added
        >>> set_combo_to_material(combo, mock_material_c)
        >>> print(combo.currentText())
        Alloy C (Tag: 3, Type: uniaxialMaterial - alloy01)
    """
    if material is None:
        combo_box.setCurrentIndex(0)  # Select placeholder
        return
    
    for i in range(combo_box.count()):
        if combo_box.itemData(i) == material:
            combo_box.setCurrentIndex(i)
            return
    
    # If material not found, add it and select it
    display_name = f"{material.user_name} (Tag: {material.tag}, Type: {material.material_type} - {material.material_name})"
    combo_box.addItem(display_name, material)
    combo_box.setCurrentIndex(combo_box.count() - 1)


def validate_material_selection(combo_box: QComboBox, field_name="Material"):
    """Validates that a valid material has been selected in the QComboBox.

    Checks if the currently selected item in the combo box corresponds to
    a valid `Material` object (i.e., not the placeholder item).

    Args:
        combo_box: The QComboBox whose selection is to be validated.
        field_name: Optional. The name of the field to use in error messages,
            e.g., "Concrete Material" or "Steel Section Material".

    Returns:
        A tuple containing:
        - `is_valid` (bool): `True` if a material is selected, `False` otherwise.
        - `material` (`Material` or `None`): The selected material object
            if `is_valid` is `True`, otherwise `None`.
        - `error_message` (str): An empty string if `is_valid` is `True`,
            otherwise a descriptive error message.

    Example:
        >>> from qtpy.QtWidgets import QComboBox
        >>> from unittest.mock import Mock
        >>> mock_material = Mock(spec=Material, user_name="Test Mat", tag=99, material_type='uniaxialMaterial', material_name='testmat')
        >>> combo_valid = QComboBox()
        >>> combo_valid.addItem("Select Material", None)
        >>> combo_valid.addItem("Test Mat (Tag: 99)", mock_material)
        >>> combo_valid.setCurrentIndex(1)
        >>> is_valid, mat, msg = validate_material_selection(combo_valid, "My Field")
        >>> print(is_valid)
        True
        >>> print(mat.tag)
        99

        >>> combo_invalid = QComboBox()
        >>> combo_invalid.addItem("Select Material", None)
        >>> combo_invalid.setCurrentIndex(0)
        >>> is_valid, mat, msg = validate_material_selection(combo_invalid)
        >>> print(is_valid)
        False
        >>> print(msg)
        Please select a material.
    """
    material = get_material_by_combo_selection(combo_box)
    
    if material is None:
        return False, None, f"Please select a {field_name.lower()}."
    
    return True, material, ""


def refresh_all_material_dropdowns(*combo_boxes):
    """Refreshes one or more material dropdowns, preserving current selections.

    This function iterates through the provided QComboBoxes, re-populates
    each one with the latest list of available materials (using
    `setup_any_material_dropdown`), and then attempts to restore the
    previously selected material if it still exists. This is useful when
    the global list of materials might have changed, for example, after
    adding a new material.

    Args:
        *combo_boxes: A variable number of `QComboBox` objects to refresh.

    Example:
        >>> from qtpy.QtWidgets import QComboBox
        >>> from unittest.mock import Mock
        >>> # Mock some materials and make Material.get_all_materials return them
        >>> original_get_all = Material.get_all_materials
        >>>
        >>> # Initial materials
        >>> Material.get_all_materials = Mock(return_value={
        ...     1: Mock(spec=Material, user_name="Steel A", tag=1, material_type='uniaxialMaterial', material_name='steel01'),
        ...     2: Mock(spec=Material, user_name="Concrete B", tag=2, material_type='nDMaterial', material_name='conc01')
        ... })
        >>>
        >>> combo1 = QComboBox()
        >>> combo2 = QComboBox()
        >>> setup_any_material_dropdown(combo1)
        >>> setup_any_material_dropdown(combo2)
        >>>
        >>> # Select Steel A in combo1
        >>> set_combo_to_material(combo1, Material.get_all_materials()[1])
        >>> print(combo1.currentText())
        Steel A (Tag: 1, Type: uniaxialMaterial - steel01)
        >>>
        >>> # Simulate a material being added and refresh
        >>> new_materials = Material.get_all_materials()
        >>> new_materials[3] = Mock(spec=Material, user_name="Alloy C", tag=3, material_type='uniaxialMaterial', material_name='alloy01')
        >>> Material.get_all_materials.return_value = new_materials # Update the mock's return value
        >>>
        >>> refresh_all_material_dropdowns(combo1, combo2)
        >>> print(combo1.currentText()) # Should still be selected
        Steel A (Tag: 1, Type: uniaxialMaterial - steel01)
        >>> print(any("Alloy C" in combo2.itemText(i) for i in range(combo2.count()))) # New material should be available
        True
        >>> Material.get_all_materials = original_get_all # Clean up mock
    """
    for combo_box in combo_boxes:
        current_selection = get_material_by_combo_selection(combo_box)
        # Assume the combo box has a setup function attribute or use generic setup
        setup_any_material_dropdown(combo_box)
        if current_selection:
            set_combo_to_material(combo_box, current_selection)


# This dictionary provides predefined callable filters that can be used with
# `setup_material_dropdown` to easily populate combo boxes with specific
# categories of materials.
#
# Keys:
# - 'any': No filter applied, returns all materials.
# - 'concrete': Filters for 'nDMaterial' types containing 'concrete' or 'elastic'
#   in their `user_name` (case-insensitive) or `material_name`.
# - 'steel': Filters for 'uniaxialMaterial' types containing 'steel', 'rebar',
#   or 'elastic' in their `user_name` (case-insensitive) or `material_name`.
# - 'uniaxial': Filters specifically for materials with `material_type == 'uniaxialMaterial'`.
# - 'nDMaterial': Filters specifically for materials with `material_type == 'nDMaterial'`.
MATERIAL_FILTERS = {
    'any': None,
    'concrete': lambda mat: (mat.material_type == 'nDMaterial' and 
                            ('concrete' in mat.user_name.lower() or 
                             'elastic' in mat.material_name.lower())),
    'steel': lambda mat: (mat.material_type == 'uniaxialMaterial' and 
                         ('steel' in mat.user_name.lower() or 
                          'rebar' in mat.user_name.lower() or
                          'elastic' in mat.material_name.lower())),
    'uniaxial': lambda mat: mat.material_type == 'uniaxialMaterial',
    'nDMaterial': lambda mat: mat.material_type == 'nDMaterial',
}


def setup_filtered_material_dropdown(combo_box: QComboBox, filter_type: str):
    """Populates a QComboBox with materials filtered by a predefined type.

    This function utilizes the `MATERIAL_FILTERS` dictionary to apply a
    specific material filter, making it easier to set up dropdowns for
    common material categories like 'concrete' or 'steel'.

    Args:
        combo_box: The QComboBox widget to populate.
        filter_type: The key from `MATERIAL_FILTERS` specifying the
            type of filter to apply (e.g., 'any', 'concrete', 'steel',
            'uniaxial', 'nDMaterial').

    Raises:
        ValueError: If `filter_type` is not a recognized key in
            `MATERIAL_FILTERS`.

    Example:
        >>> from qtpy.QtWidgets import QComboBox
        >>> from unittest.mock import Mock
        >>> # Mock some materials for a runnable example
        >>> original_get_all = Material.get_all_materials
        >>> Material.get_all_materials = Mock(return_value={
        ...     1: Mock(spec=Material, user_name="Steel A", tag=1, material_type='uniaxialMaterial', material_name='steel01'),
        ...     2: Mock(spec=Material, user_name="Concrete B", tag=2, material_type='nDMaterial', material_name='conc01'),
        ...     3: Mock(spec=Material, user_name="Elastic Mat", tag=3, material_type='uniaxialMaterial', material_name='elastic')
        ... })
        >>>
        >>> steel_combo = QComboBox()
        >>> setup_filtered_material_dropdown(steel_combo, 'steel')
        >>> # Check for 'Steel A' and 'Elastic Mat' (as 'elastic' is covered by 'steel' filter)
        >>> print(any("Steel A" in steel_combo.itemText(i) for i in range(steel_combo.count())))
        True
        >>> print(any("Elastic Mat" in steel_combo.itemText(i) for i in range(steel_combo.count())))
        True
        >>> print(any("Concrete B" in steel_combo.itemText(i) for i in range(steel_combo.count())))
        False
        >>> Material.get_all_materials = original_get_all # Clean up mock
    """
    if filter_type not in MATERIAL_FILTERS:
        raise ValueError(f"Unknown filter type: {filter_type}. Available: {list(MATERIAL_FILTERS.keys())}")
    
    filter_func = MATERIAL_FILTERS[filter_type]
    placeholder = f"Select {filter_type.title()} Material" if filter_type != 'any' else "Select Material"
    
    setup_material_dropdown(combo_box, filter_func, placeholder)


def setup_uniaxial_material_dropdown(combo_box: QComboBox, placeholder_text="Select Uniaxial Material"):
    """Populates a QComboBox specifically with uniaxial materials.

    This is a convenience function that applies a filter to show only
    materials classified as 'uniaxialMaterial', commonly used for
    RCSection materials.

    Args:
        combo_box: The QComboBox widget to populate.
        placeholder_text: The text for the initial placeholder option.

    Example:
        >>> from qtpy.QtWidgets import QComboBox
        >>> from unittest.mock import Mock
        >>> # Mock some materials for a runnable example
        >>> original_get_all = Material.get_all_materials
        >>> Material.get_all_materials = Mock(return_value={
        ...     1: Mock(spec=Material, user_name="Steel A", tag=1, material_type='uniaxialMaterial', material_name='steel01'),
        ...     2: Mock(spec=Material, user_name="Concrete B", tag=2, material_type='nDMaterial', material_name='conc01')
        ... })
        >>>
        >>> uniaxial_combo = QComboBox()
        >>> setup_uniaxial_material_dropdown(uniaxial_combo)
        >>> # Should only contain Steel A (and placeholder)
        >>> print(any("Steel A" in uniaxial_combo.itemText(i) for i in range(uniaxial_combo.count())))
        True
        >>> print(any("Concrete B" in uniaxial_combo.itemText(i) for i in range(uniaxial_combo.count())))
        False
        >>> Material.get_all_materials = original_get_all # Clean up mock
    """
    def is_uniaxial(mat):
        return mat.material_type == 'uniaxialMaterial'
    setup_material_dropdown(combo_box, is_uniaxial, placeholder_text)


if __name__ == "__main__":
    print("Section GUI Utilities - for use in section dialog files")
    print("Available functions:")
    print("- setup_material_dropdown()")
    print("- setup_concrete_material_dropdown()")
    print("- setup_steel_material_dropdown()")
    print("- setup_any_material_dropdown()")
    print("- validate_material_selection()")
    print("- refresh_all_material_dropdowns()")