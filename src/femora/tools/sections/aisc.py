# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import math
from fractions import Fraction
from typing import Dict, Union, Optional, Tuple
from femora.components.section.beam import ElasticSection
from femora.components.section.fiber import FiberSection
from femora.core.section_base import Section


# AISC Section Database moved to aisc_data.py

def get_section_properties(name: str, unit_system: str = "in") -> Dict[str, float]:
    """Read AISC geometry without creating a material or an OpenSees section.

    Args:
        name: W or rectangular HSS shape in the bundled database.
        unit_system: Geometry units: in, ft, m, cm, or mm.

    Returns:
        Area A, local bending inertias Iy/Iz, Saint-Venant torsional constant
        J, and dimensions d, bf, tw, tf. Local Iy is AISC strong-axis Ix.
        No elastic modulus, shear modulus, density, or stiffness is inferred.

    Example:
        ```python
        properties = get_section_properties("W14X90", unit_system="m")
        torsional_stiffness = 76.923e6 * properties["J"]
        ```
    """
    try:
        from .aisc_data import AISC_DATABASE
    except ImportError:
        # Fallback if relative import fails
        from femora.tools.sections.aisc_data import AISC_DATABASE

    if name not in AISC_DATABASE:
        raise ValueError(f"Section {name} not found in AISC database.")

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
    elif name.startswith("HSS") and len(props) == 15:
        # Bundled HSS rows: weight, A, flat h, flat b, tdes, Ix, ... Iy, ... J, C.
        dimensions = name[3:].split("X")
        if len(dimensions) != 3:
            raise ValueError("Only rectangular HSS shapes are supported")
        d, bf = (float(Fraction(value)) * scale for value in dimensions[:2])
        A = props[1] * scale_area
        tw = tf = props[4] * scale
        Ix = props[5] * scale_inertia
        Iy = props[9] * scale_inertia
        J = props[13] * scale_inertia
    else:
         # Fallback / Error
        raise ValueError(f"Could not parse properties for {name}")

    return dict(A=A, Iy=Ix, Iz=Iy, J=J, d=d, bf=bf, tw=tw, tf=tf)


def create_section(name: str, model, material, type: str = "Elastic", unit_system: str = "in", user_name: str = None,
                   *, GJ: Optional[float] = None, flange_fibers: Tuple[int, int] = (12, 4),
                   web_fibers: Tuple[int, int] = (4, 16)) -> Section:
    """Create a managed elastic or fiber section from an AISC shape name.

    Supports W shapes and rectangular/square HSS shapes in the bundled database.
    ``type="Elastic"`` uses tabulated area, inertias, and torsional constant.
    ``type="Fiber"`` creates three rectangular patches for W shapes or four
    nonoverlapping wall patches for HSS shapes.

    Args:
        name (str): AISC section name (e.g., "W14X90").
        model (Model): Femora Model instance with a ``section`` manager.
        material (Material): Femora material object.
        type (str, optional): 'Elastic' or 'Fiber'. Defaults to "Elastic".
        unit_system (str, optional): Target unit system for geometric properties ('in', 'ft', 'm', 'cm', 'mm').
                                     Defaults to "in". Material properties (E, G) are NOT converted.
        user_name (str, optional): Custom name for the created section. If None, defaults to 'name'.
        GJ: Finite positive elastic torsional stiffness, required for 3D fiber
            sections. It is stiffness (shear modulus times torsional constant),
            not J alone. Ignored for elastic sections, which obtain G and J
            from the reference material and database.
        flange_fibers: Pair ``(ny, nz)`` of positive integers. Defaults to
            ``(12, 4)`` per flange, across width and through thickness.
            For HSS these counts apply to the top and bottom walls.
        web_fibers: Pair ``(ny, nz)`` of positive integers. Defaults to
            ``(4, 16)`` through thickness and along depth. For HSS these counts
            apply to each side wall. Only used for fiber sections.

    Returns:
        Section: A standard Femora section object (ElasticSection or FiberSection).

    Raises:
        ValueError: Shape, units, fiber counts, dimensions, GJ, or fiber material
            are invalid. Fiber materials must be uniaxial and managed by model.

    Note:
        **Materials.** Elastic sections use a reference material's E and G/nu.
        Fibers require a uniaxial stress-strain material, such as Elastic or
        Steel01. Choosing fibers alone does not imply yielding: the assigned
        material controls the response. Material parameters are never converted.

        **Axes.** Local x runs along the member. Section width is local y and
        depth is local z. AISC strong-axis Ix maps to local Iy; AISC weak-axis
        Iy maps to local Iz. ``get_Iy()`` and ``get_Iz()`` on the returned
        section follow these local axes, independently of its global orientation.

        **Approximation.** Fiber patches omit W fillets and use sharp HSS
        corners with nominal outer dimensions and tabulated design thickness.
        Their area and inertias therefore need not equal database values exactly.
        Increasing fiber counts reduces discretization error, not geometric
        approximation error. Fibers do not model local plate buckling.

        **Torsion.** GJ remains elastic even when axial/bending fibers yield.
        ``FiberSection.get_J()`` returns a geometric approximation, not the
        tabulated Saint-Venant torsional constant used to choose GJ.

    Examples:
        Create elastic and yielding W sections in m, kN, tonne, s:

        ```python
        from femora import Model
        from femora.tools.sections import aisc

        model = Model()
        reference = model.material.nd.elastic_isotropic(
            user_name="reference", E=200e6, nu=0.3, rho=7.85,
        )
        elastic = aisc.create_section(
            "W14X90", model, reference, unit_system="m", user_name="column_elastic",
        )
        steel = model.material.uniaxial.steel01(
            user_name="steel", Fy=345000, E0=200e6, b=0.01,
        )
        fiber = aisc.create_section(
            "W14X90", model, steel, type="Fiber", unit_system="m",
            user_name="column_fiber", GJ=elastic.G * elastic.J,
            flange_fibers=(12, 4), web_fibers=(4, 16),
        )
        print(elastic.get_Iy(), fiber.get_Iy())
        print(elastic.get_Iz(), fiber.get_Iz())
        # fiber.plot() displays the cross-section patches and fibers.
        ```

        Refine both section directions for a sensitivity check:

        ```python
        fine = aisc.create_section(
            "W14X90", model, steel, type="Fiber", unit_system="m",
            user_name="column_fine", GJ=elastic.G * elastic.J,
            flange_fibers=(24, 8), web_fibers=(8, 32),
        )
        ```

        Create a rectangular tube with the same material law. The fiber
        generator uses four walls; no special brace buckling behavior is added:

        ```python
        tube_reference = aisc.create_section(
            "HSS8X8X3/8", model, reference, unit_system="m",
            user_name="tube_reference",
        )
        tube = aisc.create_section(
            "HSS8X8X3/8", model, steel, type="Fiber", unit_system="m",
            user_name="tube_fiber", GJ=tube_reference.G * tube_reference.J,
        )
        ```
    """
    if user_name is None:
        user_name = name
    geometry = get_section_properties(name, unit_system)
    A, Ix, Iy, J = (geometry[key] for key in ("A", "Iy", "Iz", "J"))
    d, bf, tw, tf = (geometry[key] for key in ("d", "bf", "tw", "tf"))
    is_w_section = name.startswith("W")

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
        if getattr(material, "material_type", None) != "uniaxialMaterial":
            raise ValueError("Fiber sections require a uniaxial material")
        if model.material.get(material.tag) is not material:
            raise ValueError("Fiber material must belong to the supplied model")
        if GJ is None or not math.isfinite(float(GJ)) or float(GJ) <= 0:
            raise ValueError("A finite positive GJ is required for a 3D fiber section")
        for counts in (flange_fibers, web_fibers):
            if len(counts) != 2 or any(isinstance(n, bool) or not isinstance(n, int) or n < 1 for n in counts):
                raise ValueError("Fiber subdivisions must be pairs of positive integers")
        if not (0 < 2*tw < bf and 0 < 2*tf < d):
            raise ValueError("Invalid section dimensions")
        section = model.section.fiber.section(user_name=user_name, GJ=float(GJ))
        # Local y spans the flange width, matching the existing elastic section axes.
        for z1, z2 in ((-d/2, -d/2+tf), (d/2-tf, d/2)):
            section.add_rectangular_patch(material, *flange_fibers, -bf/2, z1, bf/2, z2)
        if is_w_section:
            section.add_rectangular_patch(material, *web_fibers, -tw/2, -d/2+tf, tw/2, d/2-tf)
        else:
            # Sharp-corner approximation; no local plate buckling or corner strengthening.
            for y1, y2 in ((-bf/2, -bf/2+tw), (bf/2-tw, bf/2)):
                section.add_rectangular_patch(material, *web_fibers, y1, -d/2+tf, y2, d/2-tf)
        return section

    else:
        raise ValueError(f"Unknown section type: {type}")
