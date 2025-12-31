from dataclasses import dataclass

from spirograph.generation import CircularSpiroRequest, SpiroType
from spirograph.rendering.constants import ColorMode
from spirograph.rendering.data_types import Color
from .constants import RandomComplexity, RandomConstraintMode, RandomEvolutionMode


@dataclass(slots=True)
class CliSessionState:
    random_complexity: RandomComplexity = RandomComplexity.SIMPLE
    random_constraint_mode: RandomConstraintMode = RandomConstraintMode.EXTENDED
    random_evolution_mode: RandomEvolutionMode = RandomEvolutionMode.RANDOM
    curve_type: SpiroType = SpiroType.HYPOTROCHOID

    color_mode: ColorMode = ColorMode.RANDOM_EVERY_N_LAPS
    color: Color = Color(0, 0, 0)
    laps_per_color: int = 20
    spins_per_color: int = 20

    line_width: float = 1.0
    drawing_speed: int = 5

    locked_fixed_radius: int | None = None
    locked_rolling_radius: int | None = None
    locked_pen_distance: int | None = None

    last_request: CircularSpiroRequest | None = None

    def __post_init__(self) -> None:
        self._normalize_random_modes()

    def _normalize_random_modes(self) -> None:
        if not isinstance(self.random_complexity, RandomComplexity):
            self.random_complexity = RandomComplexity(self.random_complexity)
        if not isinstance(self.random_constraint_mode, RandomConstraintMode):
            self.random_constraint_mode = RandomConstraintMode(self.random_constraint_mode)
        if not isinstance(self.random_evolution_mode, RandomEvolutionMode):
            self.random_evolution_mode = RandomEvolutionMode(self.random_evolution_mode)
