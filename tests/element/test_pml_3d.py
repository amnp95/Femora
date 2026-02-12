import sys
import os
import pytest
from typing import Optional

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'src'))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from femora.components.element import PML3DElement
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element

# Mock material with specific class name required by PML3DElement
class ElasticIsotropicMaterial(Material):
    def __init__(self, tag: int):
        super().__init__("nDMaterial", f"Mat{tag}", f"UserMat{tag}")
        self.tag = tag
        self._material_type = "nDMaterial"

    def to_tcl(self) -> str:
        return f"material {self.tag}"
    
    @classmethod
    def get_parameters(cls):
        return []

    @classmethod
    def get_description(cls):
        return []

class OtherMaterial(Material):
    def __init__(self, tag: int):
        super().__init__("nDMaterial", f"Mat{tag}", f"UserMat{tag}")
        self.tag = tag
        self._material_type = "nDMaterial"

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

def test_pml_3d_initialization_valid():
    """Test valid initialization of PML3DElement."""
    mat = ElasticIsotropicMaterial(1)
    # Defaults for some params
    ele = PML3DElement(ndof=9, material=mat, 
                       PML_Thickness=1.0, 
                       meshType='box', 
                       meshTypeParameters=[1.0, 2.0, 3.0, 4, 5, 6])
    
    assert ele.tag is not None
    assert ele.PML_Thickness == 1.0
    assert ele.meshType == "box"
    assert ele.m == 2.0 # Default checked

def test_pml_3d_invalid_inputs():
    """Test invalid inputs raise errors."""
    valid_mat = ElasticIsotropicMaterial(1)
    invalid_mat = OtherMaterial(2) # Wrong class name

    # Wrong ndof
    with pytest.raises(ValueError, match="requires 9 DOFs"):
        PML3DElement(ndof=3, material=valid_mat, PML_Thickness=1.0, meshType='box', meshTypeParameters="1,2,3,4,5,6")

    # Incompatible material class
    with pytest.raises(ValueError, match="not compatible"):
        PML3DElement(ndof=9, material=invalid_mat, PML_Thickness=1.0, meshType='box', meshTypeParameters="1,2,3,4,5,6")

    # Missing mandatory params
    with pytest.raises(TypeError):
        PML3DElement(ndof=9, material=valid_mat)

def test_pml_3d_to_tcl():
    """Test TCL command generation."""
    mat = ElasticIsotropicMaterial(1)
    nodes = [1, 2, 3, 4, 5, 6, 7, 8]
    
    # Case 1: Defaults (m, R)
    ele = PML3DElement(ndof=9, material=mat, 
                       PML_Thickness=0.5, 
                       meshType='general', 
                       meshTypeParameters="0.1,0.2,0.3,0.4,0.5,0.6")
    
    tcl = ele.to_tcl(tag=100, nodes=nodes)
    # Expected format:
    # element PML <tag> <nodes> <matTag> <thick> "general" <meshParams> "-Newmark" <gamma> <beta> <eta> <ksi> -m <m> -R <R>
    # Defaults: gamma=0.5, beta=0.25, eta=0.0833.., ksi=0.02083..
    # m=2.0, R=1e-8
    
    # Checking specific parts might be safer than full string match due to float precision
    assert "element PML 100 1 2 3 4 5 6 7 8 1 0.5 \"general\" 0.1 0.2 0.3 0.4 0.5 0.6" in tcl
    assert "\"-Newmark\" 0.5 0.25" in tcl
    assert "-m 2.0 -R 1e-08" in tcl

    # Case 2: Alpha-Beta
    ele_ab = PML3DElement(ndof=9, material=mat, 
                       PML_Thickness=0.5, 
                       meshType='box', 
                       meshTypeParameters=[1]*6,
                       alpha0=0.1, beta0=0.2)
    
    tcl_ab = ele_ab.to_tcl(tag=101, nodes=nodes)
    assert "-alphabeta 0.1 0.2" in tcl_ab
    assert "-m" not in tcl_ab

if __name__ == "__main__":
    try:
        from tests.element.test_pml_3d import *
        test_pml_3d_initialization_valid()
        test_pml_3d_invalid_inputs()
        test_pml_3d_to_tcl()
        print("All PML3DElement tests passed interactively!")
    except ImportError:
        pass
