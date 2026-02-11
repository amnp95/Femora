import sys
import os
import pytest
from typing import Optional

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'src'))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from femora.components.element import stdBrickElement
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
    Element.clear_all_elements() # Use correct method

def test_std_brick_initialization():
    """Test valid initialization of stdBrickElement."""
    mat = DummyMaterial(1, "nDMaterial")
    
    # Valid init
    ele = stdBrickElement(ndof=3, material=mat)
    assert ele.tag is not None
    assert ele.tag > 0
    assert ele._material == mat
    assert ele.b1 == 0.0
    assert ele.b2 == 0.0
    assert ele.b3 == 0.0
    assert ele.lumped is False

def test_std_brick_invalid_inputs():
    """Test invalid inputs raise errors."""
    valid_mat = DummyMaterial(1, "nDMaterial")
    invalid_mat = DummyMaterial(2, "UniaxialMaterial")

    # Wrong ndof
    with pytest.raises(ValueError, match="requires 3 DOFs"):
        stdBrickElement(ndof=6, material=valid_mat)

    # Incompatible material
    with pytest.raises(ValueError, match="not compatible"):
        stdBrickElement(ndof=3, material=invalid_mat)

def test_std_brick_optional_params():
    """Test initialization with optional params."""
    mat = DummyMaterial(1, "nDMaterial")
    ele = stdBrickElement(ndof=3, material=mat, b1=1.0, b3=3.0, lumped=True)
    
    assert ele.b1 == 1.0
    assert ele.b2 == 0.0
    assert ele.b3 == 3.0
    assert ele.lumped is True

def test_std_brick_to_tcl():
    """Test TCL command generation."""
    mat = DummyMaterial(1, "nDMaterial")
    nodes = [1, 2, 3, 4, 5, 6, 7, 8]

    # Minimal
    ele = stdBrickElement(ndof=3, material=mat)
    tcl = ele.to_tcl(tag=100, nodes=nodes)
    expected = "element stdBrick 100 1 2 3 4 5 6 7 8 1"
    assert tcl == expected

    # With all params
    ele_full = stdBrickElement(ndof=3, material=mat, b1=1.0, b2=2.0, b3=3.0, lumped=True)
    tcl_full = ele_full.to_tcl(tag=101, nodes=nodes)
    expected_full = "element stdBrick 101 1 2 3 4 5 6 7 8 1 1.0 2.0 3.0 -lumped"
    assert tcl_full == expected_full

    # With sparse params (The bug case!)
    # b3 provided, b1/b2 missing. OpenSees expects: b1 b2 b3
    ele_sparse = stdBrickElement(ndof=3, material=mat, b3=3.0)
    tcl_sparse = ele_sparse.to_tcl(tag=102, nodes=nodes)
    
    # Expected behavior: fill missing leading args with 0.0
    expected_sparse = "element stdBrick 102 1 2 3 4 5 6 7 8 1 0.0 0.0 3.0"
    
    # Current buggy behavior would be: "... 1 3.0" which implies b1=3.0
    assert tcl_sparse == expected_sparse

    # Invalid node count
    with pytest.raises(ValueError, match="requires 8 nodes"):
        ele.to_tcl(tag=100, nodes=[1, 2, 3])

if __name__ == "__main__":
    try:
        from tests.element.test_std_brick import *
        test_std_brick_initialization()
        test_std_brick_invalid_inputs()
        test_std_brick_optional_params()
        test_std_brick_to_tcl()
        print("All stdBrickElement tests passed interactively!")
    except ImportError:
        pass
