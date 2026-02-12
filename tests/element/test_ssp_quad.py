import sys
import os
import pytest
from typing import Optional

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'src'))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from femora.components.element import SSPQuadElement
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element

class DummyMaterial(Material):
    def __init__(self, tag: int, mat_type: str):
        super().__init__(mat_type, f"DummyMat{tag}", f"UserDummyMat{tag}")
        self.tag = tag
        self._material_type = mat_type


    def to_tcl(self) -> str:
        return f"material {self.tag}"
    
    @classmethod
    def get_parameters(cls):
        return []

    @classmethod
    def get_description(cls):
        return []

@pytest.fixture(autouse=True)
def setup_teardown():
    Material.clear_all()
    Element.clear_all_elements()
    yield
    Material.clear_all()
    Element.clear_all_elements()

def test_ssp_quad_initialization():
    """Test valid initialization of SSPQuadElement."""
    mat = DummyMaterial(1, "nDMaterial")
    # Missing required params
    with pytest.raises(TypeError):
        SSPQuadElement(ndof=2, material=mat)

    # Valid init
    ele = SSPQuadElement(ndof=2, material=mat, Type="PlaneStrain", Thickness=0.1)
    assert ele.tag is not None
    assert ele.tag > 0
    assert ele._material == mat
    assert ele.Type == "PlaneStrain"
    assert ele.Thickness == 0.1

def test_ssp_quad_invalid_inputs():
    """Test invalid inputs raise errors."""
    valid_mat = DummyMaterial(1, "nDMaterial")
    invalid_mat = DummyMaterial(2, "UniaxialMaterial")

    # Wrong ndof
    with pytest.raises(ValueError, match="requires 2 DOFs"):
        SSPQuadElement(ndof=3, material=valid_mat, Type="PlaneStrain", Thickness=0.1)

    # Incompatible material
    with pytest.raises(ValueError, match="not compatible"):
        SSPQuadElement(ndof=2, material=invalid_mat, Type="PlaneStrain", Thickness=0.1)

def test_ssp_quad_optional_params():
    """Test initialization with optional body forces."""
    mat = DummyMaterial(1, "nDMaterial")
    ele = SSPQuadElement(ndof=2, material=mat, Type="PlaneStress", Thickness=0.5, b1=1.0, b2=-10.0)
    
    assert ele.b1 == 1.0
    assert ele.b2 == -10.0
    assert ele.Type == "PlaneStress"

def test_ssp_quad_to_tcl():
    """Test TCL command generation."""
    mat = DummyMaterial(1, "nDMaterial")
    ele = SSPQuadElement(ndof=2, material=mat, Type="PlaneStrain", Thickness=0.2)
    
    # 4 nodes required
    nodes = [1, 2, 3, 4]
    tcl = ele.to_tcl(tag=100, nodes=nodes)
    # Order: Type, Thickness, b1, b2
    # Since b1, b2 not present, they are skipped?
    # Logic: " ".join(str(self.params[key]) for key in keys if key in self.params)
    # keys = ["Type", "Thickness", "b1", "b2"]
    expected = "element SSPquad 100 1 2 3 4 1 PlaneStrain 0.2"
    assert tcl == expected

    # With body forces
    ele_bf = SSPQuadElement(ndof=2, material=mat, Type="PlaneStress", Thickness=0.2, b1=5.0, b2=6.0)
    tcl_bf = ele_bf.to_tcl(tag=101, nodes=nodes)
    expected_bf = "element SSPquad 101 1 2 3 4 1 PlaneStress 0.2 5.0 6.0"
    assert tcl_bf == expected_bf

    # Invalid node count
    with pytest.raises(ValueError, match="requires 4 nodes"):
        ele.to_tcl(tag=100, nodes=[1, 2, 3])

if __name__ == "__main__":
    try:
        from tests.element.test_ssp_quad import *
        test_ssp_quad_initialization()
        test_ssp_quad_invalid_inputs()
        test_ssp_quad_optional_params()
        test_ssp_quad_to_tcl()
        print("All SSPQuadElement tests passed interactively!")
    except ImportError:
        pass
