from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from spirograph.generation.types import Point2D


@dataclass(frozen=True, slots=True)
class Color:
    r: int
    g: int
    b: int
    a: int = 255

    @property
    def as_rgb(self) -> tuple[int, int, int]:
        return self.r, self.g, self.b

    @property
    def as_hex(self) -> str:
        return f'#{self.r:02x}{self.g:02x}{self.b:02x}'


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
    def render(self, plan: RenderPlan, settings: 'RenderSettings') -> None:
        raise NotImplementedError


class ColorMode(Enum):
    FIXED = 'fixed'
    RANDOM_PER_RUN = 'random_per_run'
    RANDOM_PER_LAP = 'random_per_lap'
    RANDOM_EVERY_N_LAPS = 'random_every_n_laps'
    RANDOM_PER_SPIN = 'random_per_spin'
    RANDOM_EVERY_N_SPINS = 'random_every_n_spins'


@dataclass(frozen=True, slots=True)
class RenderSettings:
    color: Color = Color(0, 0, 0)
    color_mode: ColorMode = ColorMode.FIXED
    interval: int = 1
    width: float = 1.0
    speed: int = 0
