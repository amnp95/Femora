# Provides direct references to element classes for autocompletion and easy access
from femora.components.element import SSPQuadElement, stdBrickElement, PML3DElement, SSPbrickElement
from femora.components.element import DispBeamColumnElement, ForceBeamColumnElement, ElasticBeamColumnElement
from femora.components.element import GhostNodeElement
from femora.components.element import TrussElement


class _BrickElements:
    std = stdBrickElement
    pml3d = PML3DElement
    ssp = SSPbrickElement

class _QuadElements:
    ssp = SSPQuadElement

class _BeamElements:
    disp = DispBeamColumnElement
    force = ForceBeamColumnElement
    elastic = ElasticBeamColumnElement
    truss = TrussElement

class _SpecialElements:
    ghost_node = GhostNodeElement
