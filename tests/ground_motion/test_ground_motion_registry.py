import inspect

import pytest

from femora.components.TimeSeries.timeSeriesBase import TimeSeries
from femora.components.ground_motion import (
    InterpolatedGroundMotion,
    PlainGroundMotion,
)
from femora.core.ground_motion_manager import GroundMotionManager


@pytest.fixture(autouse=True)
def clear_managers():
    TimeSeries.reset()
    yield
    TimeSeries.reset()


def constant_series():
    from femora.components.TimeSeries.timeSeriesBase import ConstantTimeSeries

    return ConstantTimeSeries(factor=1.0)


def test_plain_ground_motion_is_not_self_registering():
    ts = constant_series()
    manager = GroundMotionManager()
    gm = PlainGroundMotion(accel=ts)

    assert gm.tag is None
    assert manager.get_all() == {}


def test_managers_are_independent():
    ts = constant_series()
    manager1 = GroundMotionManager()
    manager2 = GroundMotionManager()

    gm1 = manager1.plain(accel=ts)
    gm2 = manager2.plain(disp=ts)

    assert gm1.tag == 1
    assert gm2.tag == 1
    assert manager1.get_all() == {1: gm1}
    assert manager2.get_all() == {1: gm2}


def test_manager_assigns_sequential_tags():
    ts = constant_series()
    manager = GroundMotionManager()

    gm1 = manager.plain(accel=ts)
    gm2 = manager.plain(disp=ts)

    assert gm1.tag == 1
    assert gm2.tag == 2
    assert manager.get(1) is gm1
    assert manager.get(2) is gm2


def test_manager_tag_start_and_reassignment():
    ts = constant_series()
    manager = GroundMotionManager()
    manager.set_tag_start(10)

    gm1 = manager.plain(accel=ts)
    gm2 = manager.plain(vel=ts)
    gm3 = manager.plain(disp=ts)

    assert [gm1.tag, gm2.tag, gm3.tag] == [10, 11, 12]

    manager.remove(11)

    assert gm1.tag == 10
    assert gm3.tag == 11
    assert manager.get_all() == {10: gm1, 11: gm3}
    assert gm2.tag is None


def test_manager_can_add_explicit_instance():
    ts = constant_series()
    manager = GroundMotionManager()
    gm = PlainGroundMotion(accel=ts)

    returned = manager.add(gm)

    assert returned is gm
    assert gm.tag == 1


def test_plain_ground_motion_to_tcl():
    accel = constant_series()
    disp = constant_series()
    manager = GroundMotionManager()
    gm = manager.plain(
        accel=accel,
        disp=disp,
        integrator="Trapezoidal",
        factor=2.5,
    )

    assert gm.to_tcl() == "groundMotion 1 Plain -accel 1 -disp 2 -int Trapezoidal -fact 2.5"


def test_interpolated_ground_motion_to_tcl():
    ts = constant_series()
    manager = GroundMotionManager()
    gm1 = manager.plain(accel=ts)
    gm2 = manager.plain(disp=ts)
    interpolated = manager.interpolated(
        ground_motions=[gm1, gm2],
        factors=[0.25, 0.75],
    )

    assert isinstance(interpolated, InterpolatedGroundMotion)
    assert interpolated.to_tcl() == "groundMotion 3 Interpolated 1 2 -fact 0.25 0.75"


def test_manager_instance_convenience_methods():
    ts = constant_series()
    manager = GroundMotionManager()

    gm = manager.plain(accel=ts)

    assert gm.tag == 1
    assert manager.get(1) is gm


def test_manager_factory_signatures_follow_constructors():
    plain_signature = inspect.signature(GroundMotionManager().plain)
    constructor_signature = inspect.signature(PlainGroundMotion.__init__)

    assert list(plain_signature.parameters) == list(constructor_signature.parameters)[1:]
    assert plain_signature.parameters["accel"].default is None
    assert plain_signature.parameters["factor"].default == 1.0


def test_interpolated_factory_signature_follows_constructor():
    interpolated_signature = inspect.signature(GroundMotionManager().interpolated)
    constructor_signature = inspect.signature(InterpolatedGroundMotion.__init__)

    assert list(interpolated_signature.parameters) == list(constructor_signature.parameters)[1:]
    assert "ground_motions" in interpolated_signature.parameters
    assert "factors" in interpolated_signature.parameters
