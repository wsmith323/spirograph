from dataclasses import dataclass
from enum import Enum

from .types import Color


class ColorMode(Enum):
    FIXED = "fixed"
    RANDOM_PER_RUN = "random_per_run"
    RANDOM_PER_LAP = "random_per_lap"
    RANDOM_EVERY_N_LAPS = "random_every_n_laps"
    RANDOM_PER_SPIN = "random_per_spin"
    RANDOM_EVERY_N_SPINS = "random_every_n_spins"


@dataclass(frozen=True, slots=True)
class RenderSettings:
    color: Color = Color(0, 0, 0)
    color_mode: ColorMode = ColorMode.FIXED
    interval: int = 1
    width: float = 1.0
    speed: int = 0
