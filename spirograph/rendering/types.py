from dataclasses import dataclass

from spirograph.generation.types import Point2D


@dataclass(frozen=True, slots=True)
class DrawablePath:
    points: tuple[Point2D, ...]
    color: str
    width: float


@dataclass(frozen=True, slots=True)
class RenderPlan:
    paths: tuple[DrawablePath, ...]
