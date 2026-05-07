from typing import Dict, List, Union

from femora.components.section.section_base import Section, SectionManager
from femora.core.element_base import Element, ElementRegistry


class TrussElement(Element):
    """OpenSees truss element using a section definition.

    Tcl form:
        ``element trussSection <tag> <iNode> <jNode> <secTag>
        <-rho rho> <-cMass cFlag> <-doRayleigh rFlag>``

    Cross-section properties and axial stiffness come from the ``Section`` object
    (typically ``section Elastic`` for elastic struts/braces).
    """

    def __init__(
        self,
        ndof: int,
        section: Union[Section, int, str],
        rho: float = 0.0,
        cMass: int = 0,
        doRayleigh: int = 0,
        **kwargs,
    ):
        """Create a truss element definition.

        Args:
            ndof: Number of nodal DOFs in the surrounding model (2, 3, or 6).
            section: Section object, tag, or user name.
            rho: Optional mass per unit length.
            cMass: Consistent mass flag, ``0`` or ``1``.
            doRayleigh: Rayleigh damping flag, ``0`` or ``1``.
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If inputs are invalid or the section cannot be resolved.
        """
        if ndof not in (2, 3, 6):
            raise ValueError("TrussElement requires 2, 3, or 6 DOFs")

        if section is None:
            raise ValueError("TrussElement requires a section")
        resolved_section = self._resolve_section(section)

        rho = float(rho)
        if rho < 0.0:
            raise ValueError("TrussElement rho must be non-negative")

        cMass = int(cMass)
        doRayleigh = int(doRayleigh)
        if cMass not in (0, 1):
            raise ValueError("cMass must be 0 or 1")
        if doRayleigh not in (0, 1):
            raise ValueError("doRayleigh must be 0 or 1")

        super().__init__(
            "trussSection",
            ndof,
            material=None,
            section=resolved_section,
            rho=rho,
            cMass=cMass,
            doRayleigh=doRayleigh,
            **kwargs,
        )
        self.rho = rho
        self.cMass = cMass
        self.doRayleigh = doRayleigh

    @staticmethod
    def _resolve_section(section_input: Union[Section, int, str]) -> Section:
        """Resolve a section object, tag, or user name."""
        if isinstance(section_input, Section):
            return section_input
        if isinstance(section_input, (int, str)):
            return SectionManager().get_section(section_input)
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this truss element."""
        if len(nodes) != 2:
            raise ValueError("TrussElement requires exactly 2 nodes")
        if self._section is None:
            raise ValueError("TrussElement requires a section")

        cmd = [
            "element",
            "trussSection",
            str(tag),
            str(nodes[0]),
            str(nodes[1]),
            str(self._section.tag),
        ]
        if self.rho != 0.0:
            cmd.extend(["-rho", str(self.rho)])
        if self.cMass != 0:
            cmd.extend(["-cMass", str(self.cMass)])
        if self.doRayleigh != 0:
            cmd.extend(["-doRayleigh", str(self.doRayleigh)])
        return " ".join(cmd)

    @classmethod
    def get_parameters(cls) -> List[str]:
        return ["rho", "cMass", "doRayleigh"]

    @classmethod
    def get_description(cls) -> List[str]:
        return [
            "Mass per unit length",
            "Consistent mass flag, 0 or 1",
            "Rayleigh damping flag, 0 or 1",
        ]

    @staticmethod
    def get_possible_dofs() -> List[str]:
        return ["2", "3", "6"]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[float, int]]:
        validated: Dict[str, Union[float, int]] = {}
        if "rho" in kwargs:
            rho = float(kwargs["rho"])
            if rho < 0.0:
                raise ValueError("rho must be non-negative")
            validated["rho"] = rho
        for key in ("cMass", "doRayleigh"):
            if key in kwargs:
                value = int(kwargs[key])
                if value not in (0, 1):
                    raise ValueError(f"{key} must be 0 or 1")
                validated[key] = value
        return validated

    def get_values(self, keys: List[str]) -> Dict[str, Union[float, int]]:
        return {key: getattr(self, key) for key in keys if hasattr(self, key)}

    def update_values(self, values: Dict[str, Union[float, int]]) -> None:
        validated = self.validate_element_parameters(**values)
        for key, value in validated.items():
            setattr(self, key, value)

    def get_mass_per_length(self) -> float:
        return self.rho


ElementRegistry.register_element_type("Truss", TrussElement)
ElementRegistry.register_element_type("truss", TrussElement)
ElementRegistry.register_element_type("trussSection", TrussElement)
