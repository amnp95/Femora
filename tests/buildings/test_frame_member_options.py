import pytest

from femora import Model
from femora.tools.buildings import SteelConcentricallyBracedFrame3D


@pytest.mark.parametrize("formulation", ["force_based"])
def test_build_member_formulation(formulation):
    model = Model()
    model.clear_model()
    material = model.material.uniaxial.elastic(E=200e6)
    calls = []

    def factory(**kwargs):
        from femora.tools.sections import aisc
        calls.append(kwargs["category"])
        return aisc.create_section(kwargs["section_name"], kwargs["model"],
                                   kwargs["material"], type="Fiber", GJ=1e5, unit_system="m",
                                   user_name=kwargs["category"])

    frame = SteelConcentricallyBracedFrame3D(
        num_stories=1, x_bays=[8], y_bays=[8],
        member_formulation=formulation, section_factory=factory,
        member_options={"Beam_X": {"integration_points": 7}},
    )
    frame.build(model, material, G=76.923e6)
    assert {"Beam_X", "Beam_Y", "Column_X", "Column_Y"}.issuperset(calls)
    assert calls


@pytest.mark.parametrize("options", [
    {"member_formulation": "wrong"}, {"integration_points": 1},
    {"integration_points": 5.5}, {"section_factory": 42},
    {"member_options": {"brace": {}}},
])
def test_invalid_member_options(options):
    with pytest.raises(ValueError):
        SteelConcentricallyBracedFrame3D(**options)
