import random

import math

from spirograph.generation.requests import CircularSpiroRequest
from .types import RandomComplexity, RandomConstraintMode, RandomEvolutionMode


def evolve_value(
    previous: int | None,
    base_min: int,
    base_max: int,
    evolution: RandomEvolutionMode,
    jump_scale: float = 0.5,
) -> int:
    if previous is None or evolution is RandomEvolutionMode.RANDOM:
        return random.randint(base_min, base_max)

    if evolution is RandomEvolutionMode.JUMP and random.random() < 0.25:
        span = base_max - base_min
        jump = int(span * jump_scale)
        return max(base_min, min(base_max, previous + random.randint(-jump, jump)))

    span = base_max - base_min
    drift = max(3, int(span * 0.25))
    return max(base_min, min(base_max, previous + random.randint(-drift, drift)))


def random_fixed_circle_radius(prev: CircularSpiroRequest | None, evolution: RandomEvolutionMode) -> int:
    base_min, base_max = 100, 320
    prev_val = int(prev.fixed_radius) if prev else None
    return evolve_value(prev_val, base_min, base_max, evolution)


def random_rolling_circle_radius(
    fixed_radius: int,
    prev: CircularSpiroRequest | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_r = int(prev.rolling_radius) if prev else None

    if complexity is RandomComplexity.SIMPLE:
        ratio_min, ratio_max = 2.5, 4.5
    elif complexity is RandomComplexity.DENSE:
        ratio_min, ratio_max = 5.0, 14.0
    else:
        ratio_min, ratio_max = 3.5, 9.0

    if constraint is RandomConstraintMode.PHYSICAL:
        max_r = fixed_radius - 1
    elif constraint is RandomConstraintMode.EXTENDED:
        max_r = int(fixed_radius * 2.0)
    else:
        max_r = int(fixed_radius * 3.0)

    base_min = 2
    base_max = max_r

    def laps_to_close_for(candidate_r: int) -> int:
        return candidate_r // math.gcd(fixed_radius, candidate_r)

    best_r: int | None = None
    best_laps: int | None = None

    for _ in range(80):
        candidate_r = evolve_value(prev_r, base_min, base_max, evolution)
        candidate_r = max(2, candidate_r)

        laps = laps_to_close_for(candidate_r)

        if best_laps is None or laps < best_laps:
            best_r = candidate_r
            best_laps = laps

        if laps <= 200:
            return candidate_r

    if best_r is None:
        return max(2, evolve_value(prev_r, base_min, base_max, evolution))

    return best_r


def random_pen_offset(
    rolling_radius: int,
    prev: CircularSpiroRequest | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_d = int(prev.pen_distance) if prev else None

    if complexity is RandomComplexity.SIMPLE:
        max_factor = 1.2
    elif complexity is RandomComplexity.DENSE:
        max_factor = 2.2
    else:
        max_factor = 1.6

    if constraint is RandomConstraintMode.WILD:
        max_factor *= 1.5

    base_min = 1
    base_max = int(rolling_radius * max_factor)

    return evolve_value(prev_d, base_min, base_max, evolution)
