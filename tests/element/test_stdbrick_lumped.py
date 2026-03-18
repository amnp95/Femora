import pytest
from femora.components.Material.materialBase import Material
from femora.components.Element.elementsOpenSees import stdBrickElement


class DummyNDMaterial(Material):
    def __init__(self, user_name="dummyND"):
        super().__init__(material_type='nDMaterial', material_name='DummyND', user_name=user_name)
    @classmethod
    def get_parameters(cls):
        return []
    @classmethod
    def get_description(cls):
        return []
    def to_tcl(self):
        return ""


@pytest.fixture(autouse=True)
def clear_materials():
    Material.clear_all()
    yield
    Material.clear_all()


def test_stdbrick_to_tcl_with_lumped_flag():
    # Create a dummy nD material so stdBrickElement can use its tag
    mat = DummyNDMaterial()
    # stdBrick requires 3 DOFs
    elem = stdBrickElement(ndof=3, material=mat, b1=1.0, b2=2.0, b3=3.0, lumped=True)
    tcl = elem.to_tcl(tag=1, nodes=[1,2,3,4,5,6,7,8])
    # Ensure numeric body forces are present and '-lumped' flag is appended
    assert "element stdBrick 1 1 2 3 4 5 6 7 8 {} 1.0 2.0 3.0 -lumped".format(mat.tag) == tcl


def test_stdbrick_to_tcl_without_lumped():
    mat = DummyNDMaterial()
    elem = stdBrickElement(ndof=3, material=mat)
    tcl = elem.to_tcl(tag=10, nodes=[10,20,30,40,50,60,70,80])
    # Should not include '-lumped' and no trailing spaces
    expected = "element stdBrick 10 10 20 30 40 50 60 70 80 {}".format(mat.tag)
    assert tcl == expected
