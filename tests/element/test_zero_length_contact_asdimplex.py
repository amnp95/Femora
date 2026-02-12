import sys
import os
import pytest
from typing import Optional

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'src'))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from femora.components.element import ZeroLengthContactASDimplex
from femora.core.element_base import Element

@pytest.fixture(autouse=True)
def setup_teardown():
    Element.clear_all_elements()
    yield
    Element.clear_all_elements()

def test_zl_contact_initialization():
    """Test valid initialization."""
    ele = ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=2e8, mu=0.5)
    
    assert ele.tag is not None
    assert ele.params['Kn'] == 1e8
    assert ele.params['Kt'] == 2e8
    assert ele.params['mu'] == 0.5
    assert 'intType' not in ele.params # Default 0 is not stored if not explicit? 
    # Logic: if intType != 0: self.params['intType']...
    # So if 0, not in params.

def test_zl_contact_options():
    """Test optional parameters."""
    # With orient and intType
    ele = ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5, 
                                     orient=[1, 0, 0], intType=1)
    
    assert ele.params['orient'] == [1.0, 0.0, 0.0]
    assert ele.params['intType'] == 1

def test_zl_contact_invalid_inputs():
    """Test invalid inputs."""
    # Invalid orient
    with pytest.raises(ValueError, match="orient must be a list"):
        ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5, orient="invalid")

    with pytest.raises(ValueError, match="orient must be a list"):
        ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5, orient=[1, 2])

    # NOTE: intType validation is in validate_element_parameters but constructor logic 
    # for intType is inline: if intType != 0: self.params['intType'] = int(intType)
    # It doesn't seem to call validate_element_parameters in __init__.
    # Let's verify if explicit intType validation is enforced in init.
    # The code says:
    # if intType != 0: self.params['intType'] = int(intType)
    # It casts to int. If I pass "invalid", it might raise ValueError from float/int conversion?
    # But it doesn't check if it's 0 or 1 in init, only in validate_element_parameters.
    # But validate_element_parameters is NOT called in __init__ for this element!
    # This might be another bug or design choice.

def test_zl_contact_to_tcl():
    """Test TCL generation."""
    nodes = [10, 20]
    
    # Basic
    ele = ZeroLengthContactASDimplex(ndof=3, Kn=100.0, Kt=200.0, mu=0.3)
    tcl = ele.to_tcl(tag=1, nodes=nodes)
    expected = "element zeroLengthContactASDimplex 1 10 20 100.0 200.0 0.3"
    assert tcl == expected

    # With options
    ele_opt = ZeroLengthContactASDimplex(ndof=3, Kn=100.0, Kt=200.0, mu=0.3,
                                         orient=[0, 1, 0], intType=1)
    tcl_opt = ele_opt.to_tcl(tag=2, nodes=nodes)
    # Order: basic ... -orient ... -intType ...
    expected_opt = "element zeroLengthContactASDimplex 2 10 20 100.0 200.0 0.3 -orient 0.0 1.0 0.0 -intType 1"
    assert tcl_opt == expected_opt

    # Incorrect nodes
    with pytest.raises(ValueError):
        ele.to_tcl(tag=1, nodes=[10, 20, 30])
