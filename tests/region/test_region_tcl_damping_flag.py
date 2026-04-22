import importlib.util
import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


def _bootstrap_package(name: str, path: Path) -> None:
    if name in sys.modules:
        return
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module


def _load_module(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_bootstrap_package("femora", SRC_ROOT / "femora")
_bootstrap_package("femora.components", SRC_ROOT / "femora/components")
_bootstrap_package("femora.components.Damping", SRC_ROOT / "femora/components/Damping")
_bootstrap_package("femora.components.Region", SRC_ROOT / "femora/components/Region")

damping_module = _load_module(
    "femora.components.Damping.dampingBase",
    SRC_ROOT / "femora/components/Damping/dampingBase.py",
)
region_module = _load_module(
    "femora.components.Region.regionBase",
    SRC_ROOT / "femora/components/Region/regionBase.py",
)

DampingBase = damping_module.DampingBase
FrequencyRayleighDamping = damping_module.FrequencyRayleighDamping
RegionBase = region_module.RegionBase
ElementRegion = region_module.ElementRegion
NodeRegion = region_module.NodeRegion


class DummyDamping(DampingBase):
    def get_values(self):
        return {}

    def update_values(self, **kwargs):
        pass

    def to_tcl(self):
        return ""

    @staticmethod
    def get_Type() -> str:
        return "DummyDamping"


@pytest.fixture(autouse=True)
def reset_state():
    DampingBase.reset()
    RegionBase._regions = {}
    RegionBase._global_region = None
    yield
    DampingBase.reset()
    RegionBase._regions = {}
    RegionBase._global_region = None


def test_element_region_uses_damp_for_non_rayleigh_damping():
    damping = DummyDamping()
    region = ElementRegion(elements=[1, 2, 3], damping=damping)

    tcl = region.to_tcl()

    assert f"-damp {damping.tag}" in tcl
    assert "-damping" not in tcl


def test_node_region_uses_damp_for_non_rayleigh_damping():
    damping = DummyDamping()
    region = NodeRegion(nodes=[1, 2, 3], damping=damping)

    tcl = region.to_tcl()

    assert f"-damp {damping.tag}" in tcl
    assert "-damping" not in tcl


def test_element_region_keeps_rayleigh_option():
    damping = FrequencyRayleighDamping(f1=0.1, f2=10.0, dampingFactor=0.05)
    region = ElementRegion(elements=[1], damping=damping)

    tcl = region.to_tcl()

    assert "-rayleigh" in tcl
    assert "-damp" not in tcl
