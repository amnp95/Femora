import sys
import os
import pytest
from typing import Optional

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'src'))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from femora.components.element import SSPbrickElement
from femora.components.Material.materialBase import Material

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

from femora.core.element_base import Element

@pytest.fixture(autouse=True)
def setup_teardown():
    Material.clear_all()
    Element.clear_all_elements()
    yield
    Material.clear_all()
    Element.clear_all_elements()

def test_ssp_brick_initialization():
    """Test valid initialization of SSPbrickElement."""
    mat = DummyMaterial(1, "nDMaterial")
    ele = SSPbrickElement(ndof=3, material=mat)
    assert ele.tag is not None
    assert ele.tag > 0
    assert ele._material == mat
    assert ele.b1 == 0.0
    assert ele.b2 == 0.0
    assert ele.b3 == 0.0

def test_ssp_brick_invalid_inputs():
    """Test invalid inputs raise errors."""
    valid_mat = DummyMaterial(1, "nDMaterial")
    invalid_mat = DummyMaterial(2, "UniaxialMaterial")

    # Wrong ndof
    with pytest.raises(ValueError, match="requires 3 DOFs"):
        SSPbrickElement(ndof=6, material=valid_mat)

    # Incompatible material
    with pytest.raises(ValueError, match="not compatible"):
        SSPbrickElement(ndof=3, material=invalid_mat)

def test_ssp_brick_optional_params():
    """Test initialization with optional body forces."""
    mat = DummyMaterial(1, "nDMaterial")
    ele = SSPbrickElement(ndof=3, material=mat, b1=10.0, b2=0.0, b3=-9.81)
    
    assert ele.b1 == 10.0
    assert ele.b2 == 0.0
    assert ele.b3 == -9.81

def test_ssp_brick_to_tcl():
    """Test TCL command generation."""
    mat = DummyMaterial(1, "nDMaterial")
    ele = SSPbrickElement(ndof=3, material=mat)
    
    # 8 nodes required
    nodes = [1, 2, 3, 4, 5, 6, 7, 8]
    tcl = ele.to_tcl(tag=100, nodes=nodes)
    expected = "element SSPbrick 100 1 2 3 4 5 6 7 8 1"
    assert tcl == expected

    # With body forces
    ele_bf = SSPbrickElement(ndof=3, material=mat, b1=1.0, b2=2.0)
    tcl_bf = ele_bf.to_tcl(tag=101, nodes=nodes)
    # Note: b3 is missing, so it shouldn't be in the string if logic iterates over keys in params
    # But wait, logic is: " ".join(str(self.params[key]) for key in keys if key in self.params)
    # keys are ["b1", "b2", "b3"]
    expected_bf = "element SSPbrick 101 1 2 3 4 5 6 7 8 1 1.0 2.0"
    assert tcl_bf == expected_bf

    # Invalid node count
    with pytest.raises(ValueError, match="requires 8 nodes"):
        ele.to_tcl(tag=100, nodes=[1, 2, 3])

def test_ssp_brick_update_values():
    """Test updating parameters."""
    mat = DummyMaterial(1, "nDMaterial")
    ele = SSPbrickElement(ndof=3, material=mat)
    
    ele.update_values({"b1": 5.0, "b3": -10.0})
    assert ele.b1 == 5.0
    assert ele.b3 == -10.0
    assert ele.b2 == 0.0

    values = ele.get_values(["b1", "b2", "b3"])
    assert values["b1"] == 5.0
    assert values["b2"] == 0.0
    assert values["b3"] == -10.0

if __name__ == "__main__":
    # Allow running as standalone script
    # This part is just for quick manual verification if needed
    try:
        from tests.element.test_ssp_brick import *
        test_ssp_brick_initialization()
        test_ssp_brick_invalid_inputs()
        test_ssp_brick_optional_params()
        test_ssp_brick_to_tcl()
        test_ssp_brick_update_values()
        print("All SSPbrickElement tests passed interactively!")
    except ImportError:
        pass
