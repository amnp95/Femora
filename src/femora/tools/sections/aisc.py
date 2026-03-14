import math
from typing import Dict, Union, Optional
from femora.components.section.section_opensees import ElasticSection, FiberSection
from femora.components.section.section_base import Section


# AISC Section Database moved to aisc_data.py

def create_section(name: str, model, material, type: str = "Elastic", unit_system: str = "in", user_name: str = None) -> Section:
    """
    Create a Femora Section object from an AISC database name using the provided model instance.

    Args:
        name (str): AISC section name (e.g., "W14X90").
        model (MeshMaker): Femora MeshMaker instance (or similar model object) with .section manager.
        material (Material): Femora material object.
        type (str, optional): 'Elastic' or 'Fiber'. Defaults to "Elastic".
        unit_system (str, optional): Target unit system for geometric properties ('in', 'ft', 'm', 'cm', 'mm'). 
                                     Defaults to "in". Material properties (E, G) are NOT converted.
        user_name (str, optional): Custom name for the created section. If None, defaults to 'name'.

    Returns:
        Section: A standard Femora section object (ElasticSection or FiberSection).
    
    Raises:
        ValueError: If section name is not found in database.
    """
    try:
        from .aisc_data import AISC_DATABASE
    except ImportError:
        # Fallback if relative import fails
        from femora.tools.sections.aisc_data import AISC_DATABASE

    if name not in AISC_DATABASE:
        raise ValueError(f"Section {name} not found in AISC database.")

    if user_name is None:
        user_name = name

    # Unit conversion scales (from inches to target)
    scales = {
        'in': 1.0,
        'ft': 1.0/12.0,
        'm': 0.0254,
        'cm': 2.54,
        'mm': 25.4
    }
    
    if unit_system not in scales:
        raise ValueError(f"Unsupported unit system: {unit_system}. Supported: {list(scales.keys())}")
        
    scale = scales[unit_system]
    scale_area = scale ** 2
    scale_inertia = scale ** 4

    data_str = AISC_DATABASE[name]
    props = [float(x) for x in data_str.split()]

    # Parse properties based on section type (W vs HSS)
    is_w_section = name.startswith("W")

    if is_w_section and len(props) >= 14:
        # W Properties (AISC database order for these keys)
        # Scale geometric properties
        A = props[0] * scale_area
        d = props[1] * scale
        bf = props[2] * scale
        tw = props[3] * scale
        tf = props[4] * scale
        Ix = props[5] * scale_inertia
        Iy = props[6] * scale_inertia
        J = props[13] * scale_inertia
    elif not is_w_section and len(props) >= 14:
         # HSS mappings (approximate based on heuristics)
        A = props[0] * scale_area
        d = props[1] * scale # h
        bf = props[2] * scale # b
        tw = props[3] * scale # tdes
        tf = props[3] * scale # tdes
        Ix = props[4] * scale_inertia
        Iy = props[8] * scale_inertia
        J = props[12] * scale_inertia
    else:
         # Fallback / Error
        raise ValueError(f"Could not parse properties for {name}")

    if type == "Elastic":
        # Create Elastic Section
        # ElasticSection parameters: E, A, Iz, Iy, G, J
        
        # We need E and G from the material.
        # Assuming material has E and nu (or G) properties
        try:
            E_val = material.E
        except AttributeError:
             # properties might be in a params dict
             E_val = material.params.get('E', 29000.0) # Default to Steel E if missing

        try:
            if hasattr(material, 'G'):
                G_val = material.G
            elif hasattr(material, 'nu'):
                G_val = E_val / (2 * (1 + material.nu))
            else:
                G_val = material.params.get('G', E_val / (2 * (1 + 0.3)))
        except:
             G_val = E_val / 2.6

        return model.section.create_section(
            "Elastic",
            user_name=user_name,
            E=E_val,
            A=A,
            Iz=Iy, # Vertical axis (Weak)
            Iy=Ix, # Horizontal axis (Strong)
            G=G_val,
            J=J
        )
    
    elif type == "Fiber":
        raise NotImplementedError("Fiber section generation from AISC database not yet implemented.")

    else:
        raise ValueError(f"Unknown section type: {type}")
