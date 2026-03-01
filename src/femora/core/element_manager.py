from femora.components.element import SSPQuadElement, stdBrickElement, PML3DElement, SSPbrickElement
from femora.components.element import DispBeamColumnElement, ForceBeamColumnElement, ElasticBeamColumnElement
from femora.components.element import GhostNodeElement


class _BrickElements:
    """Provides convenient aliases for various brick element classes.

    This internal class aggregates different types of 3D brick elements
    (standard, PML, SSP) for easy access within the Femora framework.

    Attributes:
        std (type[stdBrickElement]): An alias for the standard 3D brick element.
        pml3d (type[PML3DElement]): An alias for the 3D PML brick element.
        ssp (type[SSPbrickElement]): An alias for the SSP (Solid Shell Plate)
            3D brick element.

    Example:
        >>> from femora.elements import _BrickElements
        >>> std_brick_class = _BrickElements.std
        >>> print(std_brick_class.__name__)
        stdBrickElement
    """
    std = stdBrickElement
    pml3d = PML3DElement
    ssp = SSPbrickElement


class _QuadElements:
    """Provides a convenient alias for quadrilateral element classes.

    This internal class aggregates different types of 2D quadrilateral
    elements for easy access within the Femora framework.

    Attributes:
        ssp (type[SSPQuadElement]): An alias for the SSP (Solid Shell Plate)
            quadrilateral element.

    Example:
        >>> from femora.elements import _QuadElements
        >>> ssp_quad_class = _QuadElements.ssp
        >>> print(ssp_quad_class.__name__)
        SSPQuadElement
    """
    ssp = SSPQuadElement


class _BeamElements:
    """Provides convenient aliases for various beam-column element classes.

    This internal class aggregates different types of beam-column elements
    (displacement, force, elastic) for easy access within the Femora framework.

    Attributes:
        disp (type[DispBeamColumnElement]): An alias for the displacement-based
            beam-column element.
        force (type[ForceBeamColumnElement]): An alias for the force-based
            beam-column element.
        elastic (type[ElasticBeamColumnElement]): An alias for the elastic
            beam-column element.

    Example:
        >>> from femora.elements import _BeamElements
        >>> disp_beam_class = _BeamElements.disp
        >>> print(disp_beam_class.__name__)
        DispBeamColumnElement
    """
    disp = DispBeamColumnElement
    force = ForceBeamColumnElement
    elastic = ElasticBeamColumnElement


class _SpecialElements:
    """Provides convenient aliases for special purpose element classes.

    This internal class aggregates specialized elements like the Ghost Node
    element for easy access within the Femora framework.

    Attributes:
        ghost_node (type[GhostNodeElement]): An alias for the Ghost Node element,
            often used in advanced numerical techniques like domain decomposition.

    Example:
        >>> from femora.elements import _SpecialElements
        >>> ghost_node_class = _SpecialElements.ghost_node
        >>> print(ghost_node_class.__name__)
        GhostNodeElement
    """
    ghost_node = GhostNodeElement