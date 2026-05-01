from __future__ import annotations

from typing import List, Optional, Union

from femora.components.TimeSeries.timeSeriesBase import TimeSeries
from femora.core.ground_motion_base import GroundMotion


class PlainGroundMotion(GroundMotion):
    """OpenSees Plain ground motion."""

    def __init__(
        self,
        accel: Optional[TimeSeries] = None,
        vel: Optional[TimeSeries] = None,
        disp: Optional[TimeSeries] = None,
        integrator: Optional[str] = None,
        integrator_args: Optional[List[Union[int, float, str]]] = None,
        factor: float = 1.0,
    ):
        super().__init__("Plain")

        if accel is None and vel is None and disp is None:
            raise ValueError("At least one of accel, vel, or disp must be provided")
        for name, series in (("accel", accel), ("vel", vel), ("disp", disp)):
            if series is not None and not isinstance(series, TimeSeries):
                raise ValueError(f"{name} must be a TimeSeries object")

        if integrator is not None:
            integrator = str(integrator)
            if not integrator:
                raise ValueError("integrator must not be empty")

        if integrator_args is None:
            integrator_args = []
        if not isinstance(integrator_args, (list, tuple)):
            raise ValueError("integrator_args must be a list or tuple")

        try:
            factor = float(factor)
        except Exception:
            raise ValueError("factor must be numeric")

        self.accel = accel
        self.vel = vel
        self.disp = disp
        self.integrator = integrator
        self.integrator_args = list(integrator_args)
        self.factor = factor

    def to_tcl(self) -> str:
        cmd = f"groundMotion {self._require_tag()} Plain"
        if self.accel is not None:
            cmd += f" -accel {self.accel.tag}"
        if self.vel is not None:
            cmd += f" -vel {self.vel.tag}"
        if self.disp is not None:
            cmd += f" -disp {self.disp.tag}"
        if self.integrator is not None:
            cmd += f" -int {self.integrator}"
            if self.integrator_args:
                cmd += " " + " ".join(map(str, self.integrator_args))
        if self.factor != 1.0:
            cmd += f" -fact {self.factor}"
        return cmd
