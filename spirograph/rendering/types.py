from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from spirograph.generation.types import Point2D

if TYPE_CHECKING:
    from .settings import RenderSettings


@dataclass(frozen=True, slots=True)
class Color:
    r: int
    g: int
    b: int
    a: int = 255

    @property
    def as_rgb(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)


@dataclass(frozen=True, slots=True)
class DrawablePath:
    points: tuple[Point2D, ...]
    color: Color
    width: float


@dataclass(frozen=True, slots=True)
class RenderPlan:
    paths: tuple[DrawablePath, ...]


class CurveRenderer(ABC):
    @abstractmethod
    def render(self, plan: RenderPlan, settings: "RenderSettings") -> None:
        raise NotImplementedError
