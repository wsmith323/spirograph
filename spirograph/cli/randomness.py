import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import math

from spirograph.generation.requests import CircularSpiroRequest
from .constants import RandomComplexity, RandomConstraintMode, RandomEvolutionMode

if TYPE_CHECKING:
    from .session import CliSessionState


@dataclass(frozen=True)
class ComplexityProfile:
    ratio_min: float
    ratio_max: float
    lobes_target: float
    lobes_tolerance: float
    offset_min_factor: float
    offset_max_factor: float
    diff_min: int
    fixed_radius_step: int | None
    fallback_ratio_slack: float
    enforce_diff_min_in_fallback: bool


COMPLEXITY_PROFILES: dict[RandomComplexity, ComplexityProfile] = {
    RandomComplexity.SIMPLE: ComplexityProfile(
        ratio_min=1.15,
        ratio_max=2.2,
        lobes_target=5.0,
        lobes_tolerance=2.5,
        offset_min_factor=0.30,
        offset_max_factor=0.75,
        diff_min=20,
        fixed_radius_step=10,
        fallback_ratio_slack=0.20,
        enforce_diff_min_in_fallback=True,
    ),
    RandomComplexity.MEDIUM: ComplexityProfile(
        ratio_min=2.2,
        ratio_max=4.5,
        lobes_target=14.0,
        lobes_tolerance=6.0,
        offset_min_factor=0.25,
        offset_max_factor=1.05,
        diff_min=12,
        fixed_radius_step=5,
        fallback_ratio_slack=0.35,
        enforce_diff_min_in_fallback=True,
    ),
    RandomComplexity.COMPLEX: ComplexityProfile(
        ratio_min=4.5,
        ratio_max=7.5,
        lobes_target=30.0,
        lobes_tolerance=12.0,
        offset_min_factor=0.20,
        offset_max_factor=1.45,
        diff_min=8,
        fixed_radius_step=2,
        fallback_ratio_slack=0.50,
        enforce_diff_min_in_fallback=True,
    ),
    RandomComplexity.DENSE: ComplexityProfile(
        ratio_min=7.5,
        ratio_max=16.0,
        lobes_target=90.0,
        lobes_tolerance=40.0,
        offset_min_factor=0.15,
        offset_max_factor=2.20,
        diff_min=5,
        fixed_radius_step=None,
        fallback_ratio_slack=1.00,
        enforce_diff_min_in_fallback=True,
    ),
}


_LAST_ROLLING_RADIUS_SELECTION_DEBUG: dict[str, object] | None = None


def get_last_rolling_radius_selection_debug() -> dict[str, object] | None:
    return _LAST_ROLLING_RADIUS_SELECTION_DEBUG


def _set_last_selection_debug(**kwargs: object) -> None:
    global _LAST_ROLLING_RADIUS_SELECTION_DEBUG
    _LAST_ROLLING_RADIUS_SELECTION_DEBUG = dict(kwargs)


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


def _snap_fixed_radius(raw: int, base_min: int, base_max: int, profile: ComplexityProfile) -> int:
    step = profile.fixed_radius_step
    if step is None:
        return max(base_min, min(base_max, raw))

    snapped = int(round(raw / step) * step)
    return max(base_min, min(base_max, snapped))


def _divisors(n: int) -> list[int]:
    if n <= 0:
        return []
    small: list[int] = []
    large: list[int] = []
    limit = int(math.isqrt(n))
    for d in range(1, limit + 1):
        if n % d == 0:
            small.append(d)
            other = n // d
            if other != d:
                large.append(other)
    large.reverse()
    return small + large


def _closest_values(values: list[int], target: int, count: int) -> list[int]:
    if not values:
        return []
    return sorted(values, key=lambda v: abs(v - target))[: max(1, count)]


def random_fixed_circle_radius(session: 'CliSessionState') -> int:
    base_min, base_max = 100, 320
    prev = session.last_request
    prev_val = int(prev.fixed_radius) if prev else None
    raw = evolve_value(prev_val, base_min, base_max, session.random_evolution_mode)
    profile = COMPLEXITY_PROFILES[session.random_complexity]
    return _snap_fixed_radius(raw, base_min, base_max, profile)


def random_fixed_circle_radius_for(prev: CircularSpiroRequest | None, session: 'CliSessionState') -> int:
    base_min, base_max = 100, 320
    prev_val = int(prev.fixed_radius) if prev else None
    raw = evolve_value(prev_val, base_min, base_max, session.random_evolution_mode)
    profile = COMPLEXITY_PROFILES[session.random_complexity]
    return _snap_fixed_radius(raw, base_min, base_max, profile)


def random_rolling_circle_radius(
    fixed_radius: int,
    prev: CircularSpiroRequest | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_r = int(prev.rolling_radius) if prev else None

    profile = COMPLEXITY_PROFILES[complexity]
    ratio_min, ratio_max = profile.ratio_min, profile.ratio_max

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

    diff_min = profile.diff_min
    if constraint is RandomConstraintMode.WILD:
        diff_min = max(2, int(diff_min * 0.7))

    ratio_weight = 10_000
    lobes_weight = 5_000
    diff_weight = 20_000

    min_ratio_allowed = ratio_min - profile.fallback_ratio_slack
    max_ratio_allowed = ratio_max + profile.fallback_ratio_slack

    # -------------------------------------------------------------------------
    # Phase 1: construction (divisor/gcd-driven)
    # -------------------------------------------------------------------------
    constructed_considered = 0
    divs = _divisors(fixed_radius)
    if divs:
        # For lobes ~= R / gcd(R, r), to hit lobes_target we want gcd ~= R / lobes_target.
        g_target = max(1, int(round(fixed_radius / max(1.0, profile.lobes_target))))
        gcd_candidates = _closest_values(divs, g_target, count=12)

        ratio_center = (ratio_min + ratio_max) / 2.0

        best_constructed_r: int | None = None
        best_constructed_key: tuple[float, float, float, int] | None = None

        for g in gcd_candidates:
            if g <= 0:
                continue

            k0 = max(1, int(round(fixed_radius / (ratio_center * g))))
            for k in (k0 - 6, k0 - 4, k0 - 2, k0 - 1, k0, k0 + 1, k0 + 2, k0 + 4, k0 + 6):
                if k <= 0:
                    continue
                candidate_r = k * g
                if candidate_r < base_min or candidate_r > base_max:
                    continue

                ratio = fixed_radius / candidate_r
                if not (min_ratio_allowed <= ratio <= max_ratio_allowed):
                    continue

                diff = abs(fixed_radius - candidate_r)
                if profile.enforce_diff_min_in_fallback and diff < diff_min:
                    continue

                lobes = max(1, fixed_radius // math.gcd(fixed_radius, candidate_r))
                lobes_error = abs(lobes - profile.lobes_target)

                if ratio < ratio_min:
                    ratio_penalty = ratio_min - ratio
                elif ratio > ratio_max:
                    ratio_penalty = ratio - ratio_max
                else:
                    ratio_penalty = 0.0

                if diff < diff_min:
                    diff_penalty = diff_min - diff
                else:
                    diff_penalty = 0.0

                laps = laps_to_close_for(candidate_r)

                constructed_considered += 1
                key = (lobes_error, diff_penalty, ratio_penalty, laps)
                if best_constructed_key is None or key < best_constructed_key:
                    best_constructed_r = candidate_r
                    best_constructed_key = key

        if best_constructed_r is not None:
            chosen = best_constructed_r
            chosen_g = math.gcd(fixed_radius, chosen)
            chosen_lobes = max(1, fixed_radius // chosen_g)
            _set_last_selection_debug(
                phase='constructed',
                fixed_radius=fixed_radius,
                chosen_r=chosen,
                chosen_gcd=chosen_g,
                chosen_lobes=chosen_lobes,
                constructed_candidates_considered=constructed_considered,
                sampled_candidates_considered=0,
            )
            return chosen

    # -------------------------------------------------------------------------
    # Phase 2: sampling (existing approach)
    # -------------------------------------------------------------------------
    best_valid_r: int | None = None
    best_valid_score: float | None = None
    best_fallback_r: int | None = None
    best_fallback_key: tuple[float, float, float, int] | None = None
    sampled_considered = 0
    samples = 200

    for _ in range(samples):
        candidate_r = evolve_value(prev_r, base_min, base_max, evolution)
        candidate_r = max(2, candidate_r)

        laps = laps_to_close_for(candidate_r)
        ratio = fixed_radius / candidate_r

        if ratio < ratio_min:
            ratio_penalty = ratio_min - ratio
        elif ratio > ratio_max:
            ratio_penalty = ratio - ratio_max
        else:
            ratio_penalty = 0.0

        lobes = max(1, fixed_radius // math.gcd(fixed_radius, candidate_r))
        lobes_error = abs(lobes - profile.lobes_target)

        diff = abs(fixed_radius - candidate_r)
        if diff < diff_min:
            diff_penalty = diff_min - diff
        else:
            diff_penalty = 0.0

        sampled_considered += 1

        if min_ratio_allowed <= ratio <= max_ratio_allowed:
            if not (profile.enforce_diff_min_in_fallback and diff < diff_min):
                fallback_key = (lobes_error, diff_penalty, ratio_penalty, laps)
                if best_fallback_key is None or fallback_key < best_fallback_key:
                    best_fallback_r = candidate_r
                    best_fallback_key = fallback_key

        if ratio_penalty == 0.0 and diff >= diff_min and laps <= 200 and lobes_error <= profile.lobes_tolerance:
            score = lobes_error * lobes_weight + ratio_penalty * ratio_weight + diff_penalty * diff_weight + laps
            if best_valid_score is None or score < best_valid_score:
                best_valid_r = candidate_r
                best_valid_score = score

    chosen = best_valid_r if best_valid_r is not None else best_fallback_r
    if chosen is None:
        chosen = max(2, evolve_value(prev_r, base_min, base_max, evolution))

    chosen_g = math.gcd(fixed_radius, chosen)
    chosen_lobes = max(1, fixed_radius // chosen_g)
    _set_last_selection_debug(
        phase='sampled',
        fixed_radius=fixed_radius,
        chosen_r=chosen,
        chosen_gcd=chosen_g,
        chosen_lobes=chosen_lobes,
        constructed_candidates_considered=0,
        sampled_candidates_considered=sampled_considered,
    )
    return chosen


def random_pen_offset(
    rolling_radius: int,
    prev: CircularSpiroRequest | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_d = int(prev.pen_distance) if prev else None

    profile = COMPLEXITY_PROFILES[complexity]
    d_min = max(1, int(rolling_radius * profile.offset_min_factor))
    d_max = max(d_min, int(rolling_radius * profile.offset_max_factor))
    if constraint is RandomConstraintMode.WILD:
        d_max = int(d_max * 1.5)
        d_max = max(d_min, d_max)

    return evolve_value(prev_d, d_min, d_max, evolution)
