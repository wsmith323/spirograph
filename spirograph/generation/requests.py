from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class EngineRequest(Protocol):
    pass


@dataclass(frozen=True, slots=True)
class CircularSpiroRequest:
    fixed_radius: float
    rolling_radius: float
    pen_distance: float
    steps: int

    def __post_init__(self) -> None:
        if self.fixed_radius <= 0:
            raise ValueError("fixed_radius must be > 0")
        if self.rolling_radius <= 0:
            raise ValueError("rolling_radius must be > 0")
        if self.pen_distance < 0:
            raise ValueError("pen_distance must be >= 0")
        if self.steps <= 0:
            raise ValueError("steps must be > 0")
