import pytest
import numpy as np
import pyvista as pv
from femora.components.Element.elements_opensees_beam import DispBeamColumnElement
from femora.components.Mesh.meshPartInstance import SingleLineMesh, StructuredLineMesh
from femora.components.section.section_base import Section # We need a dummy section
from femora.components.transformation.transformation import GeometricTransformation # And dummy transformation

class DummySection(Section):
    def __init__(self, tag=1):
        super().__init__("Dummy", "Elastic", tag=tag)
    def to_tcl(self): return ""
    @classmethod
    def get_parameters(cls): return []
    @classmethod
    def validate_parameters(cls, **kwargs): return {}
    def update_parameters(self, **kwargs): pass

class DummyTransform(GeometricTransformation):
    def __init__(self, tag=1):
        super().__init__("Linear", tag=tag) # Assuming Linear exists or base accepts it
    def to_tcl(self): return ""
    @classmethod
    def get_parameters(cls): return []
    
@pytest.fixture
def dummy_setup():
    sec = DummySection(1)
    transf = DummyTransform(1)
    return sec, transf

def test_single_line_mass(dummy_setup):
    sec, transf = dummy_setup
    rho = 10.0
    length = 2.0
    
    elem = DispBeamColumnElement(ndof=3, section=sec, transformation=transf, massDens=rho)
    
    # Create single line mesh length=2, x0=0, x1=2
    mesh_part = SingleLineMesh("test_single", elem, x0=0, y0=0, z0=0, x1=length, y1=0, z1=0)
    
    # Check total mass
    # Total mass = 2.0 * 10.0 = 20.0
    # 2 nodes, each should have 10.0
    
    mass_array = mesh_part.mesh.point_data["Mass"]
    assert mass_array is not None
    
    # Check node 0
    np.testing.assert_allclose(mass_array[0, :3], [10.0, 10.0, 10.0])
    # Check node 1
    np.testing.assert_allclose(mass_array[1, :3], [10.0, 10.0, 10.0])

def test_structured_line_mass(dummy_setup):
    sec, transf = dummy_setup
    rho = 5.0
    length = 1.0
    spacing = 1.0
    grid_size = 2 # 3 points: 0, 1, 2
    
    elem = DispBeamColumnElement(ndof=6, section=sec, transformation=transf, massDens=rho)
    
    # 1D line of columns
    # grid_size_1=0 -> 1 point, grid_size_2=0 -> 1 point ? No, grid_size is segments usually
    # StructuredLineMesh creates a grid of lines normal to the plane.
    # grid_size_1=2, grid_size_2=0 => 3x1 grid points.
    
    mesh_part = StructuredLineMesh("test_grid", elem, 
                                   grid_size_1=1, grid_size_2=0, 
                                   spacing_1=spacing, 
                                   length=length,
                                   massDens=rho # wait, massDens is on element
                                   )
    
    # We have 2 grid points (0,0) and (1,0).
    # From each grid point, a line of length 1 extends in Normal Z.
    # Total 2 lines.
    # Each line mass = 1.0 * 5.0 = 5.0.
    # Nodal masses:
    # Each line has 2 nodes (start, end).
    # Start nodes: 2.5 each.
    # End nodes: 2.5 each.
    
    mass_array = mesh_part.mesh.point_data["Mass"]
    
    # Total 4 points.
    assert mesh_part.mesh.n_points == 4
    
    # Verify all have 2.5 on translational DOFs
    for i in range(4):
        np.testing.assert_allclose(mass_array[i, :3], [2.5, 2.5, 2.5])

    mesh_part.export_tcl("test_structured_line_mass.tcl")

