import uuid

from femora.components.MeshMaker import MeshMaker
from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
from femora.components.Recorder.recorderBase import Recorder
from femora.tools.buildings.steel_frame import FEMA_SAC_SteelFrame


def test_steel_frame_story_drift_recorders_core_aware():
    """Smoke test: build a tiny frame, assemble with 2 partitions, and generate drift recorders."""

    # Avoid cross-test leakage from the global recorder registry.
    Recorder.clear_all()

    model = MeshMaker()

    steel = ElasticIsotropicMaterial(
        f"Steel_{uuid.uuid4().hex[:8]}",
        E=29000.0,
        nu=0.3,
    )

    name_prefix = f"TestFrameDrift_{uuid.uuid4().hex[:8]}"
    building = FEMA_SAC_SteelFrame(
        name_prefix=name_prefix,
        x_bays=[1.0, 1.0],
        y_bays=[1.0, 1.0],
        story_heights=[1.0, 1.0],
        n_ele_col=1,
        n_ele_beam=1,
        length_unit_system="m",
    )

    part = building.build(model, steel, material_density=0.0)

    model.assembler.create_section(
        meshparts=[part.user_name],
        num_partitions=2,
        merge_points=True,
    )
    model.assembler.Assemble()

    recorders = building.get_story_drift_recorders(model, file_prefix="TestDrift", dofs=(1, 2))

    assert len(recorders) == building.num_stories * 2

    tcls = [r.to_tcl() for r in recorders]
    for tcl in tcls:
        assert "recorder Drift" in tcl
        assert "-iNode" in tcl
        assert "-jNode" in tcl
        assert "-perpDirn 3" in tcl
        # MPI-safe filenames
        assert "$pid" in tcl
        # Core-aware guard
        assert tcl.strip().startswith("if {$pid ==")

    # Story-specific output naming
    assert any("Story01" in tcl for tcl in tcls)
    assert any("Story02" in tcl for tcl in tcls)
