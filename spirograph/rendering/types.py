from abc import ABC, abstractmethod
from dataclasses import dataclass

from spirograph.generation.types import Point2D

from .settings import RenderSettings


@dataclass(frozen=True, slots=True)
class DrawablePath:
    points: tuple[Point2D, ...]
    color: str
    width: float


@dataclass(frozen=True, slots=True)
class RenderPlan:
    paths: tuple[DrawablePath, ...]


class CurveRenderer(ABC):
    @abstractmethod
    def render(self, plan: RenderPlan, settings: RenderSettings) -> None:
        raise NotImplementedError
