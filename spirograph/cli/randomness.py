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
    lobes_ranges: list[tuple[int, int]]
    laps_target: float
    laps_tolerance: float
    laps_max_hard: int
    offset_min_factor: float
    offset_max_factor: float
    diff_min: int
    fixed_radius_step: int | None
    fallback_ratio_slack: float
    enforce_diff_min_in_fallback: bool
    preferred_radius_bias: float
    ratio_sample_bias: float
    avoid_gcd_eq_1: bool
    constructed_m_candidates: int
    constructed_top_n: int
    sample_count: int
    lobes_retry_count: int


COMPLEXITY_PROFILES: dict[RandomComplexity, ComplexityProfile] = {
    RandomComplexity.SIMPLE: ComplexityProfile(
        ratio_min=1.15,
        ratio_max=2.2,
        lobes_ranges=[(6, 14)],
        laps_target=6.0,
        laps_tolerance=4.0,
        laps_max_hard=24,
        offset_min_factor=0.30,
        offset_max_factor=0.75,
        diff_min=20,
        fixed_radius_step=10,
        fallback_ratio_slack=0.20,
        enforce_diff_min_in_fallback=True,
        preferred_radius_bias=0.8,
        ratio_sample_bias=0.0,
        avoid_gcd_eq_1=True,
        constructed_m_candidates=24,
        constructed_top_n=10,
        sample_count=250,
        lobes_retry_count=6,
    ),
    RandomComplexity.MEDIUM: ComplexityProfile(
        ratio_min=2.2,
        ratio_max=4.5,
        lobes_ranges=[(10, 26)],
        laps_target=10.0,
        laps_tolerance=6.0,
        laps_max_hard=48,
        offset_min_factor=0.25,
        offset_max_factor=1.35,
        diff_min=12,
        fixed_radius_step=5,
        fallback_ratio_slack=0.35,
        enforce_diff_min_in_fallback=True,
        preferred_radius_bias=0.85,
        ratio_sample_bias=0.0,
        avoid_gcd_eq_1=True,
        constructed_m_candidates=30,
        constructed_top_n=12,
        sample_count=300,
        lobes_retry_count=4,
    ),
    RandomComplexity.COMPLEX: ComplexityProfile(
        ratio_min=4.5,
        ratio_max=7.5,
        lobes_ranges=[(20, 60)],
        laps_target=14.0,
        laps_tolerance=8.0,
        laps_max_hard=72,
        offset_min_factor=0.20,
        offset_max_factor=1.45,
        diff_min=8,
        fixed_radius_step=2,
        fallback_ratio_slack=0.50,
        enforce_diff_min_in_fallback=True,
        preferred_radius_bias=0.85,
        # ratio_sample_bias: positive values bias sampling toward the high end of the ratio window (smaller r, more lobes).
        # Keep this modest to avoid Turtle "band saturation" and preserve visible variety.
        ratio_sample_bias=0.15,
        avoid_gcd_eq_1=True,
        constructed_m_candidates=36,
        constructed_top_n=14,
        sample_count=300,
        lobes_retry_count=4,
    ),
    RandomComplexity.DENSE: ComplexityProfile(
        ratio_min=7.5,
        ratio_max=16.0,
        lobes_ranges=[(20, 100)],
        laps_target=18.0,
        laps_tolerance=12.0,
        laps_max_hard=96,
        offset_min_factor=0.15,
        offset_max_factor=2.20,
        diff_min=5,
        fixed_radius_step=None,
        fallback_ratio_slack=1.00,
        enforce_diff_min_in_fallback=True,
        preferred_radius_bias=0.9,
        # ratio_sample_bias: positive values bias sampling toward the high end of the ratio window (smaller r, more lobes).
        # Keep this modest to avoid Turtle "band saturation" and preserve visible variety.
        ratio_sample_bias=0.35,
        avoid_gcd_eq_1=True,
        constructed_m_candidates=36,
        constructed_top_n=20,
        sample_count=450,
        lobes_retry_count=7,
    ),
}

DIVISOR_RICH_RADII = [
    120,
    126,
    128,
    132,
    140,
    144,
    150,
    156,
    160,
    168,
    176,
    180,
    192,
    196,
    200,
    210,
    216,
    224,
    240,
    252,
    256,
    264,
    270,
    280,
    288,
    300,
    308,
    312,
    320,
]

_LAST_ROLLING_RADIUS_SELECTION_DEBUG: dict[str, object] | None = None


def get_last_rolling_radius_selection_debug() -> dict[str, object] | None:
    return _LAST_ROLLING_RADIUS_SELECTION_DEBUG


def _set_last_selection_debug(**kwargs: object) -> None:
    global _LAST_ROLLING_RADIUS_SELECTION_DEBUG
    _LAST_ROLLING_RADIUS_SELECTION_DEBUG = dict(kwargs)


_LAST_PEN_OFFSET_SELECTION_DEBUG: dict[str, object] | None = None


def get_last_pen_offset_selection_debug() -> dict[str, object] | None:
    return _LAST_PEN_OFFSET_SELECTION_DEBUG


def _set_last_pen_offset_debug(**kwargs: object) -> None:
    global _LAST_PEN_OFFSET_SELECTION_DEBUG
    _LAST_PEN_OFFSET_SELECTION_DEBUG = dict(kwargs)


def evolve_value(
    previous: int | None,
    base_min: int,
    base_max: int,
    evolution: RandomEvolutionMode,
    jump_scale: float = 0.5,
) -> int:
    if previous is None or evolution == RandomEvolutionMode.RANDOM:
        return random.randint(base_min, base_max)

    if evolution == RandomEvolutionMode.JUMP and random.random() < 0.25:
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


def lobes_anchor_for(profile: ComplexityProfile) -> int:
    if not profile.lobes_ranges:
        return 1
    centers = [(low + high) / 2.0 for low, high in profile.lobes_ranges]
    return max(1, int(round(sum(centers) / len(centers))))


def lobes_error_for(profile: ComplexityProfile, lobes: int) -> float:
    if not profile.lobes_ranges:
        return float('inf')
    deltas: list[int] = []
    for low, high in profile.lobes_ranges:
        if low <= lobes <= high:
            return 0.0
        if lobes < low:
            deltas.append(low - lobes)
        else:
            deltas.append(lobes - high)
    return float(min(deltas)) if deltas else float('inf')


def lobes_in_range_for(profile: ComplexityProfile, lobes: int) -> bool:
    return any(low <= lobes <= high for low, high in profile.lobes_ranges)


def _m_targets_for(profile: ComplexityProfile) -> list[int]:
    targets: set[int] = set()
    for low, high in profile.lobes_ranges:
        low_i = max(1, int(low))
        high_i = max(low_i, int(high))
        targets.add(low_i)
        targets.add(high_i)

        center = int(round((low_i + high_i) / 2.0))
        center = max(low_i, min(high_i, center))
        targets.add(center)

        for delta in (-2, 2):
            c = center + delta
            if low_i <= c <= high_i:
                targets.add(c)

    return sorted(t for t in targets if t >= 1)


def _score_fixed_radius_candidate(candidate: int, profile: ComplexityProfile) -> tuple[float, float]:
    divs = _divisors(candidate)
    if not divs:
        return (float('inf'), float('inf'))

    best: tuple[float, float] | None = None
    ratio_min, ratio_max = profile.ratio_min, profile.ratio_max
    laps_target = int(round(profile.laps_target))
    for g in divs:
        if g <= 0:
            continue
        if profile.avoid_gcd_eq_1 and g == 1:
            continue
        m = candidate // g
        if m <= 0:
            continue

        k_min = max(1, int(math.ceil(m / ratio_max)))
        k_max = max(1, int(math.floor(m / ratio_min)))
        if k_max < k_min:
            continue

        k_candidates = {
            k_min,
            k_max,
            laps_target - 2,
            laps_target - 1,
            laps_target,
            laps_target + 1,
            laps_target + 2,
        }

        for k in k_candidates:
            if k < k_min or k > k_max:
                continue
            if math.gcd(m, k) != 1:
                continue
            if k > profile.laps_max_hard:
                continue

            laps_error = abs(float(k) - profile.laps_target)
            lobes_error = lobes_error_for(profile, m)
            key = (lobes_error, laps_error)
            if best is None or key < best:
                best = key

    if best is None:
        return (float('inf'), float('inf'))
    return best


def _fixed_radius_has_in_range_solution(candidate: int, profile: ComplexityProfile) -> bool:
    divs = _divisors(candidate)
    if not divs:
        return False

    ratio_min, ratio_max = profile.ratio_min, profile.ratio_max

    for g in divs:
        if g <= 0:
            continue
        if profile.avoid_gcd_eq_1 and g == 1:
            continue

        m = candidate // g
        if m <= 0:
            continue

        # Feasibility requires m to be in the configured lobe ranges.
        if not lobes_in_range_for(profile, m):
            continue

        k_min = max(1, int(math.ceil(m / ratio_max)))
        k_max = max(1, int(math.floor(m / ratio_min)))
        if k_max < k_min:
            continue

        k_candidates = {k_min, k_max}
        laps_target = int(round(profile.laps_target))
        for delta in (-2, -1, 0, 1, 2):
            k_candidates.add(laps_target + delta)

        for k in sorted(k_candidates):
            if k < k_min or k > k_max:
                continue
            if k > profile.laps_max_hard:
                continue
            if math.gcd(m, k) != 1:
                continue
            return True

    return False


def _preferred_fixed_radius(raw: int, base_min: int, base_max: int, profile: ComplexityProfile) -> int:
    clamped = max(base_min, min(base_max, raw))
    clamped_feasible = _fixed_radius_has_in_range_solution(clamped, profile)
    preferred = [r for r in DIVISOR_RICH_RADII if base_min <= r <= base_max]
    if not preferred:
        return _snap_fixed_radius(clamped, base_min, base_max, profile)

    scored: list[tuple[tuple[float, float, int], int]] = []
    for candidate in preferred:
        lobes_error, laps_error = _score_fixed_radius_candidate(candidate, profile)
        score = (lobes_error, laps_error, abs(candidate - clamped))
        scored.append((score, candidate))
    scored.sort(key=lambda item: item[0])

    if scored and math.isfinite(scored[0][0][0]):
        nearest = [candidate for _, candidate in scored[:6]]
    else:
        nearest = _closest_values(preferred, clamped, count=6)

    # If the raw/clamped radius is infeasible under this profile, force a divisor-rich choice.
    # This prevents downstream rolling-radius selection from having no possible gcd>1 solutions
    # within the ratio window (common when clamped is prime and avoid_gcd_eq_1=True).
    if not clamped_feasible and nearest:
        return random.choice(nearest)

    use_preferred = random.random() < profile.preferred_radius_bias
    if use_preferred and nearest:
        return random.choice(nearest)

    return _snap_fixed_radius(clamped, base_min, base_max, profile)


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


def _randint_beta(low: int, high: int, alpha: float, beta: float) -> int:
    if high <= low:
        return low
    x = random.betavariate(alpha, beta)
    return low + int(round(x * (high - low)))


def _clamp01(x: float) -> float:
    return 0.0 if x <= 0.0 else 1.0 if x >= 1.0 else x


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _randint_from_int_union(
    low: int,
    high: int,
    left: tuple[int, int] | None,
    right: tuple[int, int] | None,
) -> int:
    intervals: list[tuple[int, int]] = []
    if left is not None and left[0] <= left[1]:
        intervals.append(left)
    if right is not None and right[0] <= right[1]:
        intervals.append(right)

    if not intervals:
        return random.randint(low, high)

    if len(intervals) == 1:
        a, b = intervals[0]
        return random.randint(a, b)

    (a1, b1), (a2, b2) = intervals
    w1 = b1 - a1 + 1
    w2 = b2 - a2 + 1
    total = w1 + w2
    if total <= 0:
        return random.randint(low, high)

    if random.random() < (w1 / total):
        return random.randint(a1, b1)
    return random.randint(a2, b2)


def _randint_from_int_union_biased(
    low: int,
    high: int,
    left: tuple[int, int] | None,
    right: tuple[int, int] | None,
    *,
    right_pref: float,
) -> int:
    if left is None and right is None:
        return random.randint(low, high)

    if left is not None and right is None:
        return random.randint(left[0], left[1])

    if right is not None and left is None:
        return random.randint(right[0], right[1])

    # Both intervals exist: choose right with a smooth preference.
    rp = _clamp01(float(right_pref))
    if random.random() < rp:
        return random.randint(right[0], right[1])
    return random.randint(left[0], left[1])


def _subtract_interval(
    allowed: list[tuple[int, int]],
    forbidden: tuple[int, int],
) -> list[tuple[int, int]]:
    f_lo, f_hi = forbidden
    if f_lo > f_hi:
        return allowed

    out: list[tuple[int, int]] = []
    for a_lo, a_hi in allowed:
        if a_hi < f_lo or a_lo > f_hi:
            out.append((a_lo, a_hi))
            continue

        # Overlap: possibly split.
        left = (a_lo, min(a_hi, f_lo - 1))
        right = (max(a_lo, f_hi + 1), a_hi)

        if left[0] <= left[1]:
            out.append(left)
        if right[0] <= right[1]:
            out.append(right)

    return out


def _randint_from_intervals_with_high_bias(
    *,
    low: int,
    high: int,
    intervals: list[tuple[int, int]],
    high_pref: float,
) -> int:
    clean = [(lo, hi) for lo, hi in intervals if lo <= hi]
    if not clean:
        return random.randint(low, high)

    if len(clean) == 1:
        lo, hi = clean[0]
        return random.randint(lo, hi)

    # Sort by upper bound; "highest" interval is last.
    clean.sort(key=lambda p: (p[1], p[0]))
    hp = _clamp01(float(high_pref))

    if len(clean) == 2:
        left, right = clean[0], clean[1]
        return _randint_from_int_union_biased(low, high, left, right, right_pref=hp)

    # len(clean) >= 3: cap to the best 3 intervals by upper bound.
    # (We should not exceed 3 from subtracting two bands, but be defensive.)
    clean = clean[-3:]
    high_interval = clean[-1]
    rest = clean[:-1]

    if random.random() < hp:
        return random.randint(high_interval[0], high_interval[1])

    # Otherwise choose among the rest proportional to width.
    widths = [max(0, hi - lo + 1) for lo, hi in rest]
    total = sum(widths)
    if total <= 0:
        lo, hi = rest[0]
        return random.randint(lo, hi)

    pick = random.randint(1, total)
    acc = 0
    for (lo, hi), w in zip(rest, widths):
        acc += w
        if pick <= acc:
            return random.randint(lo, hi)

    lo, hi = rest[-1]
    return random.randint(lo, hi)


def random_fixed_circle_radius(session: 'CliSessionState') -> int:
    base_min, base_max = 100, 320
    prev = session.last_request
    prev_val = int(prev.fixed_radius) if prev else None
    raw = evolve_value(prev_val, base_min, base_max, session.random_evolution_mode)
    profile = COMPLEXITY_PROFILES[session.random_complexity]
    return _preferred_fixed_radius(raw, base_min, base_max, profile)


def random_fixed_circle_radius_for(prev: CircularSpiroRequest | None, session: 'CliSessionState') -> int:
    base_min, base_max = 100, 320
    prev_val = int(prev.fixed_radius) if prev else None
    raw = evolve_value(prev_val, base_min, base_max, session.random_evolution_mode)
    profile = COMPLEXITY_PROFILES[session.random_complexity]
    return _preferred_fixed_radius(raw, base_min, base_max, profile)


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

    if constraint == RandomConstraintMode.PHYSICAL:
        max_r = fixed_radius - 1
    elif constraint == RandomConstraintMode.EXTENDED:
        max_r = int(fixed_radius * 2.0)
    else:
        max_r = int(fixed_radius * 3.0)

    base_min = 2
    base_max = max_r

    def laps_to_close_for(candidate_r: int) -> int:
        return candidate_r // math.gcd(fixed_radius, candidate_r)

    def select_once() -> int:
        diff_min = profile.diff_min
        if constraint == RandomConstraintMode.WILD:
            diff_min = max(2, int(diff_min * 0.7))

        ratio_weight = 10_000
        lobes_weight = 8_000
        laps_weight = 2_000
        diff_weight = 20_000

        min_ratio_allowed = ratio_min - profile.fallback_ratio_slack
        max_ratio_allowed = ratio_max + profile.fallback_ratio_slack
        r_min_ratio = int(math.ceil(fixed_radius / max_ratio_allowed))
        r_max_ratio = int(math.floor(fixed_radius / min_ratio_allowed))
        r_min_ratio = max(base_min, min(base_max, r_min_ratio))
        r_max_ratio = max(base_min, min(base_max, r_max_ratio))
        fallback_used = False
        fallback_stage: str | None = None
        fallback_candidates_total = 0
        fallback_candidates_considered = 0
        fallback_best_key: tuple[float, float, int] | None = None
        fallback_best_candidate: int | None = None

        # ---------------------------------------------------------------------
        # Phase 1: construction (divisor/gcd-driven)
        # ---------------------------------------------------------------------
        constructed_considered = 0
        divs = _divisors(fixed_radius)
        if divs:
            # Work in m-space, where m = R / g is the lobe count when gcd(R, r) == g.
            # With r = g * k and gcd(m, k) == 1, we get:
            #   gcd(R, r) = g
            #   lobes = m
            #   ratio = R / r = (g*m) / (g*k) = m / k
            # So for a given m, the ratio bounds imply a k-range.
            m_values = sorted({fixed_radius // g for g in divs if g > 0})
            m_candidates_set: set[int] = set()
            m_targets = _m_targets_for(profile)

            # Pull nearest m-values to each target within lobes_ranges.
            # Use a small per-target fanout to avoid exploding the candidate set.
            per_target = 3
            for m_t in m_targets:
                for m in _closest_values(m_values, m_t, count=per_target):
                    m_candidates_set.add(m)

            # Backfill around the old anchor if we did not reach the desired candidate count.
            if len(m_candidates_set) < profile.constructed_m_candidates:
                m_anchor = max(1, int(round(float(lobes_anchor_for(profile)))))
                for m in _closest_values(
                    m_values,
                    m_anchor,
                    count=(profile.constructed_m_candidates - len(m_candidates_set)),
                ):
                    m_candidates_set.add(m)

            m_candidates = sorted(m_candidates_set)[: profile.constructed_m_candidates]

            best_strict_in: list[tuple[tuple[float, float, float, int], int]] = []
            best_strict_out: list[tuple[tuple[float, float, float, int], int]] = []
            best_slack_in: list[tuple[tuple[float, float, float, int], int]] = []
            best_slack_out: list[tuple[tuple[float, float, float, int], int]] = []
            top_n = profile.constructed_top_n

            for m in m_candidates:
                if m <= 0:
                    continue
                if fixed_radius % m != 0:
                    continue

                g = fixed_radius // m
                if g <= 0:
                    continue
                if profile.avoid_gcd_eq_1 and g == 1:
                    continue

                # Strict k-range implied by ratio bounds: ratio = m / k.
                k_min_strict = max(1, int(math.ceil(m / ratio_max)))
                k_max_strict = max(1, int(math.floor(m / ratio_min)))

                # Slack k-range for fallback only.
                k_min_slack = max(1, int(math.ceil(m / max_ratio_allowed)))
                k_max_slack = max(1, int(math.floor(m / min_ratio_allowed)))

                def iter_k_values(k_min: int, k_max: int) -> list[int]:
                    if k_max < k_min:
                        return []
                    span = k_max - k_min
                    if span <= 16:
                        return list(range(k_min, k_max + 1))
                    center = (k_min + k_max) // 2
                    candidates = {
                        k_min,
                        k_min + 1,
                        k_min + 2,
                        center - 4,
                        center - 2,
                        center - 1,
                        center,
                        center + 1,
                        center + 2,
                        center + 4,
                        k_max - 2,
                        k_max - 1,
                        k_max,
                    }
                    return sorted(k for k in candidates if k_min <= k <= k_max)

                strict_ks = iter_k_values(k_min_strict, k_max_strict)
                slack_ks = iter_k_values(k_min_slack, k_max_slack)

                for is_strict, ks in ((True, strict_ks), (False, slack_ks)):
                    if is_strict and not ks:
                        continue
                    if (not is_strict) and (best_strict_in or best_strict_out):
                        # Only consider slack candidates if we haven't found any strict ones yet.
                        continue

                    for k in ks:
                        if k <= 0:
                            continue
                        if math.gcd(m, k) != 1:
                            continue

                        candidate_r = g * k
                        if candidate_r < base_min or candidate_r > base_max:
                            continue

                        ratio = fixed_radius / candidate_r
                        is_slack_ratio = min_ratio_allowed <= ratio <= max_ratio_allowed
                        if not is_slack_ratio:
                            continue
                        is_strict_ratio = ratio_min <= ratio <= ratio_max

                        diff = abs(fixed_radius - candidate_r)
                        if profile.enforce_diff_min_in_fallback and diff < diff_min:
                            continue

                        lobes_error = lobes_error_for(profile, m)
                        lobes_in_range = lobes_error == 0.0

                        # ratio penalty is only non-zero when using slack.
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

                        laps = k
                        if laps > profile.laps_max_hard:
                            continue

                        laps_error = abs(float(laps) - profile.laps_target)

                        constructed_considered += 1
                        key = (laps_error, lobes_error, diff_penalty, ratio_penalty, laps)

                        if is_strict_ratio and lobes_in_range:
                            bucket = best_strict_in
                        elif is_strict_ratio and not lobes_in_range:
                            bucket = best_strict_out
                        elif (not is_strict_ratio) and lobes_in_range:
                            bucket = best_slack_in
                        else:
                            bucket = best_slack_out
                        bucket.append((key, candidate_r))
                        bucket.sort(key=lambda item: item[0])
                        if len(bucket) > top_n:
                            del bucket[top_n:]

            if best_strict_in:
                candidate_bucket = best_strict_in
                bucket_name = 'strict_in'
            elif best_slack_in:
                candidate_bucket = best_slack_in
                bucket_name = 'slack_in'
            elif best_strict_out:
                candidate_bucket = best_strict_out
                bucket_name = 'strict_out'
            elif best_slack_out:
                candidate_bucket = best_slack_out
                bucket_name = 'slack_out'
            else:
                candidate_bucket = []
            if candidate_bucket:
                chosen_key, chosen = random.choice(candidate_bucket)
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
                    constructed_choice_bucket=bucket_name,
                    constructed_choice_bucket_size=len(candidate_bucket),
                    constructed_bucket_counts={
                        'strict_in': len(best_strict_in),
                        'strict_out': len(best_strict_out),
                        'slack_in': len(best_slack_in),
                        'slack_out': len(best_slack_out),
                    },
                    constructed_choice_lobes_in_range=(bucket_name in ('strict_in', 'slack_in')),
                    constructed_choice_key=chosen_key,
                )
                return chosen

        # ---------------------------------------------------------------------
        # Phase 2: sampling (existing approach)
        # ---------------------------------------------------------------------
        best_valid_r: int | None = None
        best_valid_score: float | None = None
        best_fallback_r: int | None = None
        best_fallback_key: tuple[float, float, float, int] | None = None
        sampled_considered = 0
        samples = profile.sample_count

        for _ in range(samples):
            if random.random() < profile.ratio_sample_bias:
                ratio_sample = random.uniform(ratio_min, ratio_max)
                candidate_r = int(round(fixed_radius / ratio_sample))
                candidate_r = max(base_min, min(base_max, candidate_r))
            else:
                candidate_r = evolve_value(prev_r, base_min, base_max, evolution)
                candidate_r = max(2, candidate_r)

            sampled_considered += 1

            g = math.gcd(fixed_radius, candidate_r)
            if profile.avoid_gcd_eq_1 and g == 1:
                continue

            laps = candidate_r // g
            laps_error = abs(float(laps) - profile.laps_target)
            ratio = fixed_radius / candidate_r

            if ratio < ratio_min:
                ratio_penalty = ratio_min - ratio
            elif ratio > ratio_max:
                ratio_penalty = ratio - ratio_max
            else:
                ratio_penalty = 0.0

            lobes = max(1, fixed_radius // g)
            lobes_error = lobes_error_for(profile, lobes)

            diff = abs(fixed_radius - candidate_r)
            if diff < diff_min:
                diff_penalty = diff_min - diff
            else:
                diff_penalty = 0.0

            if min_ratio_allowed <= ratio <= max_ratio_allowed:
                if not (profile.enforce_diff_min_in_fallback and diff < diff_min):
                    fallback_key = (lobes_error, laps_error, diff_penalty, ratio_penalty, laps)
                    if best_fallback_key is None or fallback_key < best_fallback_key:
                        best_fallback_r = candidate_r
                        best_fallback_key = fallback_key

            if (
                ratio_penalty == 0.0
                and diff >= diff_min
                and laps <= profile.laps_max_hard
                and lobes_in_range_for(profile, lobes)
                and laps_error <= profile.laps_tolerance
            ):
                score = (
                    lobes_error * lobes_weight
                    + laps_error * laps_weight
                    + ratio_penalty * ratio_weight
                    + diff_penalty * diff_weight
                    + laps
                )
                if best_valid_score is None or score < best_valid_score:
                    best_valid_r = candidate_r
                    best_valid_score = score

        chosen = best_valid_r if best_valid_r is not None else best_fallback_r
        if chosen is None and profile.ratio_sample_bias > 0.0:
            ratio_candidate: int | None = None
            for _ in range(50):
                ratio = random.uniform(ratio_min, ratio_max)
                candidate_r = int(round(fixed_radius / ratio))
                candidate_r = max(base_min, min(base_max, candidate_r))
                ratio_actual = fixed_radius / candidate_r
                if not (ratio_min <= ratio_actual <= ratio_max):
                    continue
                g = math.gcd(fixed_radius, candidate_r)
                if profile.avoid_gcd_eq_1 and g == 1:
                    continue
                laps = candidate_r // g
                if laps > profile.laps_max_hard:
                    continue
                ratio_candidate = candidate_r
                break

            if ratio_candidate is None and not profile.avoid_gcd_eq_1:
                for _ in range(50):
                    ratio = random.uniform(ratio_min, ratio_max)
                    candidate_r = int(round(fixed_radius / ratio))
                    candidate_r = max(base_min, min(base_max, candidate_r))
                    ratio_actual = fixed_radius / candidate_r
                    if not (ratio_min <= ratio_actual <= ratio_max):
                        continue
                    g = math.gcd(fixed_radius, candidate_r)
                    laps = candidate_r // max(1, g)
                    if laps > profile.laps_max_hard:
                        continue
                    ratio_candidate = candidate_r
                    break

            if ratio_candidate is not None:
                chosen = ratio_candidate

        if chosen is None:
            best_effort: int | None = None
            fallback_attempts = 0
            for _ in range(80):
                fallback_attempts += 1
                candidate_r = max(2, evolve_value(prev_r, base_min, base_max, evolution))

                g = math.gcd(fixed_radius, candidate_r)
                if profile.avoid_gcd_eq_1 and g == 1:
                    continue

                laps = candidate_r // max(1, g)
                if laps > profile.laps_max_hard:
                    continue

                ratio = fixed_radius / candidate_r
                if not (min_ratio_allowed <= ratio <= max_ratio_allowed):
                    continue

                diff = abs(fixed_radius - candidate_r)
                if profile.enforce_diff_min_in_fallback and diff < diff_min:
                    continue

                best_effort = candidate_r
                break

            if best_effort is not None:
                fallback_used = True
                fallback_stage = 'evolved_constrained'
                fallback_candidates_total = fallback_attempts
                fallback_candidates_considered = fallback_attempts

            if best_effort is None:
                # Ratio-derived constrained fallback search: build a small candidate set within the slack ratio window.
                candidates: set[int] = set()
                if r_min_ratio <= r_max_ratio:
                    candidates.add(r_min_ratio)
                    candidates.add(r_max_ratio)

                    # Lap-target candidates using plausible gcd values.
                    target_laps = max(1, int(round(profile.laps_target)))
                    divs = _divisors(fixed_radius)
                    for g in divs:
                        if g <= 0:
                            continue
                        if profile.avoid_gcd_eq_1 and g == 1:
                            continue
                        candidate_r = g * target_laps
                        if r_min_ratio <= candidate_r <= r_max_ratio:
                            candidates.add(candidate_r)

                    # Random samples from the allowed ratio-derived range.
                    span = r_max_ratio - r_min_ratio
                    sample_n = 40 if span > 0 else 0
                    for _ in range(sample_n):
                        candidates.add(random.randint(r_min_ratio, r_max_ratio))

                best_key: tuple[float, float, int] | None = None
                best_candidate: int | None = None
                fallback_candidates_total = len(candidates)
                for candidate_r in sorted(candidates):
                    fallback_candidates_considered += 1
                    g = math.gcd(fixed_radius, candidate_r)
                    if profile.avoid_gcd_eq_1 and g == 1:
                        continue

                    laps = candidate_r // max(1, g)
                    if laps > profile.laps_max_hard:
                        continue

                    ratio = fixed_radius / candidate_r
                    if not (min_ratio_allowed <= ratio <= max_ratio_allowed):
                        continue

                    diff = abs(fixed_radius - candidate_r)
                    if profile.enforce_diff_min_in_fallback and diff < diff_min:
                        continue

                    lobes = max(1, fixed_radius // max(1, g))
                    lobes_error = lobes_error_for(profile, lobes)
                    laps_error = abs(float(laps) - profile.laps_target)

                    if prev_r is not None:
                        drift = abs(candidate_r - prev_r)
                    else:
                        drift = abs(candidate_r - fixed_radius)

                    key = (laps_error, lobes_error, drift)
                    if best_key is None or key < best_key:
                        best_key = key
                        best_candidate = candidate_r

                if best_candidate is not None:
                    fallback_used = True
                    fallback_stage = 'ratio_candidates'
                    fallback_best_key = best_key
                    fallback_best_candidate = best_candidate
                    best_effort = best_candidate
                else:
                    # Absolute last resort: keep behavior "never fail", but this should be extremely rare now.
                    fallback_used = True
                    fallback_stage = 'evolved_last_resort'
                    best_effort = max(2, evolve_value(prev_r, base_min, base_max, evolution))

            chosen = best_effort

        chosen_g = math.gcd(fixed_radius, chosen)
        chosen_lobes = max(1, fixed_radius // chosen_g)
        chosen_laps = chosen // max(1, chosen_g)
        chosen_ratio = fixed_radius / chosen
        chosen_diff = abs(fixed_radius - chosen)
        _set_last_selection_debug(
            phase='sampled',
            fixed_radius=fixed_radius,
            chosen_r=chosen,
            chosen_gcd=chosen_g,
            chosen_lobes=chosen_lobes,
            chosen_laps=chosen_laps,
            chosen_ratio=chosen_ratio,
            chosen_diff=chosen_diff,
            constructed_candidates_considered=0,
            sampled_candidates_considered=sampled_considered,
            fallback_used=fallback_used,
            fallback_stage=fallback_stage,
            fallback_candidates_total=fallback_candidates_total,
            fallback_candidates_considered=fallback_candidates_considered,
            fallback_best_key=fallback_best_key,
            fallback_best_candidate=fallback_best_candidate,
            fallback_ratio_range=(r_min_ratio, r_max_ratio),
            fallback_ratio_window=(min_ratio_allowed, max_ratio_allowed),
            fallback_ratio_bounds=(ratio_min, ratio_max),
            fallback_diff_min=diff_min,
            fallback_prev_r=prev_r,
        )
        return chosen

    attempts = max(1, profile.lobes_retry_count + 1)
    best_candidate: int | None = None
    best_key: tuple[float, float] | None = None

    for _ in range(attempts):
        candidate = select_once()
        g = math.gcd(fixed_radius, candidate)
        lobe_count = max(1, fixed_radius // g)
        lobes_error = lobes_error_for(profile, lobe_count)

        laps = candidate // max(1, g)
        laps_error = abs(float(laps) - profile.laps_target)

        key = (lobes_error, laps_error)
        if best_key is None or key < best_key:
            best_key = key
            best_candidate = candidate

        if lobes_in_range_for(profile, lobe_count):
            return candidate

    if best_candidate is not None:
        return best_candidate

    return max(2, evolve_value(prev_r, base_min, base_max, evolution))


def random_pen_offset(
    *,
    fixed_radius: int,
    rolling_radius: int,
    prev: CircularSpiroRequest | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_d = int(prev.pen_distance) if prev else None

    profile = COMPLEXITY_PROFILES[complexity]
    d_min = max(1, int(math.ceil(rolling_radius * profile.offset_min_factor)))
    d_max = max(d_min, int(math.floor(rolling_radius * profile.offset_max_factor)))
    if constraint == RandomConstraintMode.WILD:
        d_max = int(d_max * 1.5)
        d_max = max(d_min, d_max)
    effective_max = d_max

    diff = abs(int(fixed_radius) - int(rolling_radius))
    ratio = (float(fixed_radius) / float(rolling_radius)) if rolling_radius else float('inf')
    t = _clamp01((ratio - 2.0) / 10.0)
    ratio_t = t

    # Diff band (ratio-driven, smooth)
    band_frac = _lerp(0.12, 0.30, t)
    diff_low = max(1, int(round(diff * (1.0 - band_frac))))
    diff_high = max(diff_low, int(round(diff * (1.0 + band_frac))))

    if evolution == RandomEvolutionMode.RANDOM:
        # Smooth profile-driven shaping enforced in integer space to avoid rounding/clamping leaks into d/r≈1.
        t = _clamp01((profile.offset_max_factor - 0.75) / (2.20 - 0.75))
        min_ratio_guard = _lerp(0.25, 0.45, t)
        band_base = _lerp(0.20, 0.30, t)
        band_effective = band_base
        dmax_over_r: float | None = None

        radius_mul: float | None = None
        radius_lo = 18.0
        radius_hi = 30.0
        if rolling_radius > 0:
            dmax_over_r = d_max / float(rolling_radius)
            # When d_max is large relative to r, a wide r-band removes too much of the feasible region.
            # Shrink band smoothly from 1.0x to 0.60x as dmax_over_r goes from 1.35 to 2.20.
            lo, hi = 1.35, 2.20
            if dmax_over_r > lo:
                u = min(1.0, (dmax_over_r - lo) / (hi - lo))
                shrink = _lerp(1.0, 0.60, u)
                band_effective = band_base * shrink
            rr = float(rolling_radius)
            if rr <= radius_lo:
                radius_mul = 1.25
            elif rr >= radius_hi:
                radius_mul = 1.00
            else:
                u = (rr - radius_lo) / (radius_hi - radius_lo)
                radius_mul = _lerp(1.25, 1.00, u)
            band_effective *= radius_mul

        guard_r = int(math.ceil(rolling_radius * min_ratio_guard))

        a = diff
        a_guard_factor = _lerp(0.08, 0.18, t)
        guard_a = int(math.ceil(a * a_guard_factor))

        # Prevent a-based guard from collapsing variety by pushing effective_min above the r-band exclusion.
        # Cap guard_a in r-space so the left interval (below the r-band) can still exist.
        # Smoothly approach the band edge as complexity increases, but stay below band_low_r.
        guard_a_cap_factor = _lerp(0.55, 0.68, t)
        guard_a_cap = int(math.floor(rolling_radius * guard_a_cap_factor))
        guard_a = min(guard_a, guard_a_cap)

        effective_min = max(d_min, guard_r, guard_a)
        # Geometry-conditioned floor on d/r to eliminate thin-annulus tail at high a/r.
        # This is not complexity special-casing; it is driven by geometry (a vs r) and smooth profile t.
        use_r_floor = a >= (3.0 * rolling_radius) and rolling_radius > 0
        min_factor_floor = _lerp(0.28, 0.38, t)
        floor_r = int(math.ceil(rolling_radius * min_factor_floor))
        if use_r_floor:
            effective_min = max(effective_min, floor_r)

        # Clamp diff-band to the effective allowed pen-distance range so it cannot produce out-of-band d/r.
        diff_low_eff = max(int(effective_min), int(diff_low))
        diff_high_eff = min(int(effective_max), int(diff_high))
        diff_eff_empty = diff_high_eff < diff_low_eff

        # Mid-band: bridge between r_scaled's high end (d_max) and the effective diff-band low (diff_low_eff).
        # Use a stable center and a span that scales with the gap, with a non-trivial minimum.
        mid_anchor_low = int(d_max)
        mid_anchor_high = int(diff_low_eff)

        mid_center = int(round((mid_anchor_low + mid_anchor_high) / 2.0))

        gap = max(0, mid_anchor_high - mid_anchor_low)
        min_span = max(6, int(round(0.15 * max(1, rolling_radius))))
        mid_span = max(min_span, int(round(0.45 * gap)))

        mid_low = max(int(effective_min), mid_center - mid_span)
        mid_high = min(int(effective_max), mid_center + mid_span)
        mid_empty = mid_high < mid_low

        # Rebalanced weights:
        # - low t: mostly r_scaled
        # - high t: mostly mid_band
        # - diff_band: occasional, not common
        w_r = _lerp(0.78, 0.30, ratio_t)
        w_diff = _lerp(0.05, 0.18, ratio_t)
        w_mid = max(0.0, 1.0 - (w_r + w_diff))

        # Normalize defensively if floating error makes sum != 1.0.
        w_sum = w_r + w_mid + w_diff
        if w_sum > 0:
            w_r /= w_sum
            w_mid /= w_sum
            w_diff /= w_sum

        u = random.random()

        # Prefer modes that have non-empty intervals.
        r_ok = d_max >= d_min
        mid_ok = not mid_empty
        diff_ok = not diff_eff_empty

        if u < w_r:
            selection_mode = 'r_scaled'
        elif u < (w_r + w_mid):
            selection_mode = 'mid_band'
        else:
            selection_mode = 'diff_band'

        if selection_mode == 'mid_band' and not mid_ok:
            selection_mode = 'r_scaled' if r_ok else ('diff_band' if diff_ok else 'r_scaled')
        elif selection_mode == 'r_scaled' and not r_ok:
            selection_mode = 'mid_band' if mid_ok else ('diff_band' if diff_ok else 'r_scaled')
        elif selection_mode == 'diff_band' and not diff_ok:
            selection_mode = 'mid_band' if mid_ok else ('r_scaled' if r_ok else 'diff_band')

        final_low: int
        final_high: int
        diff_band_weight_t = ratio_t

        # Band exclusion around r (existing concept).
        band_low_r = int(math.floor(rolling_radius * (1.0 - band_effective)))
        band_high_r = int(math.ceil(rolling_radius * (1.0 + band_effective)))
        band_low_d = band_low_r
        band_high_d = band_high_r

        forbidden_r = (band_low_r, band_high_r)

        # Optional band exclusion around a = |R - r| (new concept for high R/r).
        band_a = _lerp(0.10, 0.18, t)
        band_low_a = int(math.floor(a * (1.0 - band_a)))
        band_high_a = int(math.ceil(a * (1.0 + band_a)))
        forbidden_a = (band_low_a, band_high_a)

        use_a_band = a >= (3 * rolling_radius) and a > 0

        allowed: list[tuple[int, int]] = [(effective_min, d_max)]
        allowed = _subtract_interval(allowed, forbidden_r)
        if use_a_band:
            allowed = _subtract_interval(allowed, forbidden_a)

        if effective_min > d_max:
            # Guards can legitimately exceed the profile-based max when a is large and r is small.
            # In that case, choosing d_min reintroduces the tiny-d ring tail.
            # Choose the largest in-profile value instead.
            final_low = d_max
            final_high = d_max
            _set_last_pen_offset_debug(
                fixed_radius=fixed_radius,
                rolling_radius=rolling_radius,
                d_min=d_min,
                d_max=d_max,
                effective_min=effective_min,
                effective_max=effective_max,
                chosen_d=d_max,
                chosen_factor=(d_max / rolling_radius) if rolling_radius else float('inf'),
                t=t,
                min_ratio_guard=min_ratio_guard,
                band=band_effective,
                band_base=band_base,
                band_effective=band_effective,
                band_effective_post_radius=band_effective,
                radius_mul=radius_mul,
                dmax_over_r=dmax_over_r,
                guard_r=guard_r,
                a=a,
                a_guard_factor=a_guard_factor,
                guard_a=guard_a,
                guard_a_cap_factor=guard_a_cap_factor,
                guard_a_cap=guard_a_cap,
                use_r_floor=use_r_floor,
                min_factor_floor=min_factor_floor,
                floor_r=floor_r,
                band_low_d=band_low_d,
                band_high_d=band_high_d,
                diff=diff,
                diff_low=diff_low,
                diff_high=diff_high,
                diff_low_eff=diff_low_eff,
                diff_high_eff=diff_high_eff,
                diff_eff_empty=diff_eff_empty,
                diff_band_weight_t=diff_band_weight_t,
                used_diff_band=False,
                selection_mode='r_scaled',
                mode_weights={'w_r': w_r, 'w_mid': w_mid, 'w_diff': w_diff},
                mid_low=mid_low,
                mid_high=mid_high,
                mid_empty=mid_empty,
                final_low=final_low,
                final_high=final_high,
                empty_range_fallback=True,
            )
            return d_max

        used_fallback_full_range = not allowed

        # Mild high-side preference increases radial span for large a without blowing out smaller regimes.
        high_pref = _lerp(0.55, 0.70, t)
        high_pref_base = high_pref
        high_pref_effective = high_pref_base
        w_left: int | None = None
        w_right: int | None = None
        width_share: float | None = None
        left_interval: tuple[int, int] | None = None
        right_interval: tuple[int, int] | None = None

        clean = [(lo, hi) for lo, hi in allowed if lo <= hi]
        if len(clean) == 2:
            clean.sort(key=lambda p: (p[1], p[0]))
            left_i, right_i = clean[0], clean[1]
            left_interval = left_i
            right_interval = right_i
            w_left = max(0, left_i[1] - left_i[0] + 1)
            w_right = max(0, right_i[1] - right_i[0] + 1)
            total_w = w_left + w_right
            if total_w > 0:
                width_share = w_right / float(total_w)
                high_pref_effective = 0.5 + (high_pref_base - 0.5) * width_share
                high_pref_effective = _clamp01(float(high_pref_effective))
                # Global cap: prevents the outside-push preference from dominating variety when bands/guards create
                # a narrow left interval and a wide right interval (common at higher complexities).
                high_pref_effective = min(high_pref_effective, 0.65)
                # If the left interval is extremely small, a strong preference for the right interval collapses variety.
                # This is a geometry-based rule (not complexity-based).
                if w_left <= 2:
                    high_pref_effective = min(high_pref_effective, 0.55)
                elif w_left <= 4:
                    high_pref_effective = min(high_pref_effective, 0.60)
        if selection_mode == 'diff_band':
            final_low, final_high = diff_low_eff, diff_high_eff
            chosen_d = random.randint(final_low, final_high)
        elif selection_mode == 'mid_band':
            final_low, final_high = mid_low, mid_high
            chosen_d = random.randint(final_low, final_high)
        else:
            chosen_d = _randint_from_intervals_with_high_bias(
                low=effective_min,
                high=d_max,
                intervals=allowed,
                high_pref=high_pref_effective,
            )
            if left_interval is not None and right_interval is not None and w_left is not None:
                if left_interval[0] <= chosen_d <= left_interval[1]:
                    # Tiny-left intervals can yield low radial span; occasionally re-roll into a capped right interval.
                    if w_left <= 2 and rolling_radius > 0 and random.random() < 0.40:
                        right_cap = min(right_interval[1], int(math.floor(rolling_radius * 1.55)))
                        if right_interval[0] <= right_cap:
                            chosen_d = random.randint(right_interval[0], right_cap)
                elif right_interval[0] <= chosen_d <= right_interval[1]:
                    # Offset the extra right picks by nudging some larger-left cases back toward the left interval.
                    if w_left >= 4 and random.random() < 0.30:
                        chosen_d = random.randint(left_interval[0], left_interval[1])
            final_low, final_high = effective_min, d_max
        chosen_factor = (chosen_d / rolling_radius) if rolling_radius else float('inf')

        _set_last_pen_offset_debug(
            rolling_radius=rolling_radius,
            complexity=complexity.value,
            constraint=constraint.value,
            evolution=evolution.value,
            d_min=d_min,
            d_max=d_max,
            effective_min=effective_min,
            t=t,
            min_ratio_guard=min_ratio_guard,
            band=band_effective,
            band_base=band_base,
            band_effective=band_effective,
            band_effective_post_radius=band_effective,
            radius_mul=radius_mul,
            dmax_over_r=dmax_over_r,
            fixed_radius=fixed_radius,
            a=a,
            a_guard_factor=a_guard_factor,
            guard_r=guard_r,
            guard_a=guard_a,
            guard_a_cap_factor=guard_a_cap_factor,
            guard_a_cap=guard_a_cap,
            band_low_r=band_low_r,
            band_high_r=band_high_r,
            band_low_d=band_low_d,
            band_high_d=band_high_d,
            band_a=band_a,
            band_low_a=band_low_a,
            band_high_a=band_high_a,
            use_a_band=use_a_band,
            diff=diff,
            diff_low=diff_low,
            diff_high=diff_high,
            diff_low_eff=diff_low_eff,
            diff_high_eff=diff_high_eff,
            diff_eff_empty=diff_eff_empty,
            diff_band_weight_t=diff_band_weight_t,
            used_diff_band=selection_mode == 'diff_band',
            selection_mode=selection_mode,
            mode_weights={'w_r': w_r, 'w_mid': w_mid, 'w_diff': w_diff},
            mid_low=mid_low,
            mid_high=mid_high,
            mid_empty=mid_empty,
            final_low=final_low,
            final_high=final_high,
            use_r_floor=use_r_floor,
            min_factor_floor=min_factor_floor,
            floor_r=floor_r,
            effective_max=effective_max,
            allowed_intervals=allowed,
            high_pref=high_pref,
            high_pref_base=high_pref_base,
            high_pref_effective=high_pref_effective,
            interval_w_left=w_left,
            interval_w_right=w_right,
            interval_width_share=width_share,
            used_fallback_full_range=used_fallback_full_range,
            chosen_d=chosen_d,
            chosen_factor=chosen_factor,
            empty_range_fallback=False,
        )
        return chosen_d

    return evolve_value(prev_d, d_min, d_max, evolution)
