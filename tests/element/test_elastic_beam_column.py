import sys
import os
import pytest
from typing import Optional

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'src'))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from femora.components.element import ElasticBeamColumnElement
from femora.core.element_base import Element
from femora.components.section.section_base import Section
from femora.components.transformation.transformation import GeometricTransformation

# Mock classes
class MockSection(Section):
    def __init__(self, tag):
        self.tag = tag
        self.section_type = "MockSection"
        self.user_name = f"Sec{tag}"
        self.section_name = "Mock"
        self.material = None
    
    def to_tcl(self):
        return f"section {self.tag}"

    @classmethod
    def get_parameters(cls): return []
    @classmethod
    def get_description(cls): return []
    @classmethod
    def get_help_text(cls): return ""
    @classmethod
    def validate_section_parameters(cls, **kwargs): return kwargs
    def get_values(self, keys): return {}
    def update_values(self, values): pass

class MockTransformation(GeometricTransformation):
    def __init__(self, tag):
        self._transf_tag = tag
        self._transformation_type = "Linear"
        self._dimension = 3
    
    @property
    def tag(self):
        return self._transf_tag

    def to_tcl(self):
        return f"geomTransf {self.tag}"
    
    def has_joint_offsets(self):
        return False

@pytest.fixture(autouse=True)
def setup_teardown():
    Element.clear_all_elements()
    yield
    Element.clear_all_elements()

def test_elastic_beam_init_valid():
    """Test valid initialization."""
    sec = MockSection(1)
    transf = MockTransformation(1)
    
    ele = ElasticBeamColumnElement(ndof=3, section=sec, transformation=transf)
    assert ele.tag is not None
    assert ele._section == sec
    assert ele._transformation == transf

def test_elastic_beam_options():
    """Test optional parameters."""
    sec = MockSection(1)
    transf = MockTransformation(1)
    
    ele = ElasticBeamColumnElement(ndof=3, section=sec, transformation=transf, 
                                   massDens=10.0, cMass=True)
    
    assert ele.massDens == 10.0
    assert ele.cMass is True

def test_elastic_beam_invalid_inputs():
    """Test invalid inputs."""
    sec = MockSection(1)
    transf = MockTransformation(1)
    
    # Wrong ndof
    with pytest.raises(ValueError, match="requires 3"):
        ElasticBeamColumnElement(ndof=4, section=sec, transformation=transf)
    
    # Missing dependencies
    with pytest.raises(ValueError, match="requires a section"):
        ElasticBeamColumnElement(ndof=3, section=None, transformation=transf)
        
def test_elastic_beam_to_tcl():
    """Test TCL generation."""
    nodes = [10, 20]
    sec = MockSection(1)
    transf = MockTransformation(2)
    
    # Make sure we account for auto-tagging. 
    # If setup_teardown works, we start fresh.
    # Note: MockSection/MockTransformation invoke manual tag in my mock, 
    # but base class might use class-level counters if I didn't override things perfectly.
    # But I set self.tag manually in MockSection.
    
    # Defaults
    ele = ElasticBeamColumnElement(ndof=3, section=sec, transformation=transf)
    # Expected: element elasticBeamColumn <tag> <iNode> <jNode> <secTag> <transfTag>
    tcl = ele.to_tcl(tag=1, nodes=nodes)
    expected = "element elasticBeamColumn 1 10 20 1 2"
    assert tcl == expected

    # With options
    ele_opt = ElasticBeamColumnElement(ndof=3, section=sec, transformation=transf, 
                                       massDens=0.5, cMass=True)
    tcl_opt = ele_opt.to_tcl(tag=2, nodes=nodes)
    expected_opt = "element elasticBeamColumn 2 10 20 1 2 -mass 0.5 -cMass"
    assert tcl_opt == expected_opt
