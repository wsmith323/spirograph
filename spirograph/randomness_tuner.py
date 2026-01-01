#!/usr/bin/env python3
"""
Sampling script for spirograph CLI randomness tuning.

Run from repo root (recommended):
  python3 -m spirograph.randomness_tuner --samples 1000

Or run as a script:
  python3 spirograph/randomness_tuner.py --samples 2000 --seed 123

Notes:
- This module lives in the `spirograph` package (not `spirograph.cli`).
- The tuner imports CLI randomness helpers from `spirograph.cli.*`.
"""

import argparse
import random
import statistics
from dataclasses import asdict, replace
from typing import Iterable

import math

from spirograph.cli.constants import RandomComplexity, RandomConstraintMode, RandomEvolutionMode
from spirograph.cli.randomness import (
    COMPLEXITY_PROFILES,
    get_last_pen_offset_selection_debug,
    get_last_rolling_radius_selection_debug,
    lobes_error_for,
    lobes_in_range_for,
    random_fixed_circle_radius,
    random_pen_offset,
    random_rolling_circle_radius,
)
from spirograph.cli.session import CliSessionState
from spirograph.generation.requests import CircularSpiroRequest


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return float('nan')
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def summarize_floats(values: list[float]) -> dict[str, float]:
    if not values:
        return {'count': 0}
    v = sorted(values)
    return {
        'count': float(len(values)),
        'mean': statistics.fmean(values),
        'p05': percentile(v, 5),
        'p50': percentile(v, 50),
        'p95': percentile(v, 95),
        'min': v[0],
        'max': v[-1],
    }


def summarize_ints(values: list[int]) -> dict[str, float]:
    return summarize_floats([float(x) for x in values])


def pearson_corr_for(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return float('nan')
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(ys)
    cov = 0.0
    var_x = 0.0
    var_y = 0.0
    for x, y in zip(xs, ys):
        dx = x - mean_x
        dy = y - mean_y
        cov += dx * dy
        var_x += dx * dx
        var_y += dy * dy
    denom = math.sqrt(var_x * var_y)
    if denom == 0.0:
        return float('nan')
    return cov / denom


def radial_span_norm_for(R: int, r: int, d: int) -> float:
    if R <= 0 or r <= 0 or d <= 0:
        return float('inf')

    g = math.gcd(R, r)
    laps = max(1, r // max(1, g))

    steps = 360 * laps
    steps = max(360, steps)
    steps = min(3000, steps)

    inside = r <= R
    a = (R - r) if inside else (R + r)
    a_over_r = a / float(r)

    rho_min = float('inf')
    rho_max = 0.0

    t_max = 2.0 * math.pi * laps
    for i in range(steps + 1):
        t = (t_max * i) / steps
        ct = math.cos(t)
        st = math.sin(t)
        c2 = math.cos(a_over_r * t)
        s2 = math.sin(a_over_r * t)

        if inside:
            x = a * ct + d * c2
            y = a * st - d * s2
        else:
            x = a * ct - d * c2
            y = a * st - d * s2

        rho = math.hypot(x, y)
        if rho < rho_min:
            rho_min = rho
        if rho > rho_max:
            rho_max = rho

    if rho_max <= 0.0 or not math.isfinite(rho_min):
        return float('inf')

    return (rho_max - rho_min) / rho_max


def rho_min_over_max_for(R: int, r: int, d: int) -> float:
    if R <= 0 or r <= 0 or d <= 0:
        return float('inf')

    g = math.gcd(R, r)
    laps = max(1, r // max(1, g))

    steps = 360 * laps
    steps = max(360, steps)
    steps = min(3000, steps)

    inside = r <= R
    a = (R - r) if inside else (R + r)
    a_over_r = a / float(r)

    rho_min = float('inf')
    rho_max = 0.0

    t_max = 2.0 * math.pi * laps
    for i in range(steps + 1):
        t = (t_max * i) / steps
        ct = math.cos(t)
        st = math.sin(t)
        c2 = math.cos(a_over_r * t)
        s2 = math.sin(a_over_r * t)

        if inside:
            x = a * ct + d * c2
            y = a * st - d * s2
        else:
            x = a * ct - d * c2
            y = a * st - d * s2

        rho = math.hypot(x, y)
        if rho < rho_min:
            rho_min = rho
        if rho > rho_max:
            rho_max = rho

    if rho_max <= 0.0 or not math.isfinite(rho_min):
        return float('inf')

    return rho_min / rho_max


def sharpness_p95_abs_turn_rad_for(R: int, r: int, d: int) -> float:
    """
    Compute a cuspiness/roundness proxy: the 95th percentile of absolute turning angles (radians)
    between successive segments along the sampled curve.

    Higher => sharper direction changes (pointier lobes).
    Lower  => smoother turns (rounder lobes).
    """
    if R <= 0 or r <= 0 or d <= 0:
        return float('nan')

    g = math.gcd(R, r)
    laps = max(1, r // max(1, g))

    # Use the same step sizing policy as radial_span_norm_for / rho_min_over_max_for.
    steps = 360 * laps
    steps = max(360, steps)
    steps = min(3000, steps)

    inside = r <= R
    a = (R - r) if inside else (R + r)
    a_over_r = a / float(r)

    # Collect points (x,y). We need at least 3 points for a turning angle.
    xs: list[float] = []
    ys: list[float] = []
    t_max = 2.0 * math.pi * laps
    for i in range(steps + 1):
        t = (t_max * i) / steps
        ct = math.cos(t)
        st = math.sin(t)
        c2 = math.cos(a_over_r * t)
        s2 = math.sin(a_over_r * t)

        if inside:
            x = a * ct + d * c2
            y = a * st - d * s2
        else:
            x = a * ct - d * c2
            y = a * st - d * s2

        xs.append(x)
        ys.append(y)

    if len(xs) < 3:
        return float('nan')

    # Compute absolute turning angles. For each triple (p0, p1, p2):
    # angle = atan2(cross(v1, v2), dot(v1, v2)), with v1=p1-p0, v2=p2-p1.
    abs_turns: list[float] = []
    for i in range(1, len(xs) - 1):
        x0, y0 = xs[i - 1], ys[i - 1]
        x1, y1 = xs[i], ys[i]
        x2, y2 = xs[i + 1], ys[i + 1]

        v1x, v1y = (x1 - x0), (y1 - y0)
        v2x, v2y = (x2 - x1), (y2 - y1)

        # Skip degenerate steps.
        n1 = math.hypot(v1x, v1y)
        n2 = math.hypot(v2x, v2y)
        if n1 <= 1e-12 or n2 <= 1e-12:
            continue

        cross = v1x * v2y - v1y * v2x
        dot = v1x * v2x + v1y * v2y
        angle = math.atan2(cross, dot)
        abs_turns.append(abs(angle))

    if not abs_turns:
        return float('nan')

    abs_turns.sort()
    # 95th percentile index (nearest-rank style).
    idx = int(round(0.95 * (len(abs_turns) - 1)))
    idx = max(0, min(len(abs_turns) - 1, idx))
    return abs_turns[idx]


def run_for_complexity(
    *,
    complexity: RandomComplexity,
    samples: int,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> dict[str, object]:
    profile = COMPLEXITY_PROFILES[complexity]
    # Make results reproducible per complexity even when running multiple complexities in one run
    # (seed still set globally outside; this just prevents ordering effects from leaking too much)
    local_rng = random.Random()
    local_rng.setstate(random.getstate())

    session = CliSessionState()
    session.random_complexity = complexity
    session.random_constraint_mode = constraint
    session.random_evolution_mode = evolution

    Rs: list[int] = []
    rs: list[int] = []
    ds: list[int] = []

    ratios: list[float] = []
    gcds: list[int] = []
    lobes: list[int] = []
    lobe_errors: list[float] = []
    laps_to_close: list[int] = []
    diffs: list[int] = []
    offset_factors: list[float] = []
    ringness_values: list[float] = []
    radial_span_norms: list[float] = []
    rho_min_over_max_values: list[float] = []
    sharpness_p95_values: list[float] = []

    ratio_outside = 0
    lobes_outside_tolerance = 0
    diff_below = 0
    offset_outside = 0
    ring_like = 0
    offset_small = 0
    offset_near_one = 0
    offset_prolate = 0
    offset_large = 0
    gcd_eq_1 = 0
    visual_ring_like = 0

    constructed_count = 0
    sampled_count = 0
    constructed_considered_total = 0
    sampled_considered_total = 0
    fallback_used_count = 0
    fallback_candidates_total = 0
    fallback_candidates_considered = 0
    fallback_stage_counts: dict[str, int] = {}
    fallback_last_resort_samples: list[dict[str, object]] = []
    fallback_last_resort_cap = 5
    pen_fallback_full_range_count = 0
    diff_band_used_count = 0
    pen_near_one_samples: list[dict[str, object]] = []
    pen_near_one_cap = 5
    pen_bias_samples: list[dict[str, object]] = []
    pen_bias_samples_cap = 8
    center_reach_samples: list[dict[str, object]] = []
    center_reach_cap = 8

    for _ in range(samples):
        R = int(random_fixed_circle_radius(session))
        r = int(
            random_rolling_circle_radius(
                fixed_radius=R,
                prev=session.last_request,
                complexity=session.random_complexity,
                constraint=session.random_constraint_mode,
                evolution=session.random_evolution_mode,
            )
        )
        debug = get_last_rolling_radius_selection_debug() or {}
        phase = debug.get('phase')
        if phase == 'constructed':
            constructed_count += 1
            constructed_considered_total += int(debug.get('constructed_candidates_considered', 0))
        elif phase == 'sampled':
            sampled_count += 1
            sampled_considered_total += int(debug.get('sampled_candidates_considered', 0))
            if debug.get('fallback_used'):
                fallback_used_count += 1
                fallback_candidates_total += int(debug.get('fallback_candidates_total', 0))
                fallback_candidates_considered += int(debug.get('fallback_candidates_considered', 0))
                stage = debug.get('fallback_stage')
                if isinstance(stage, str):
                    fallback_stage_counts[stage] = fallback_stage_counts.get(stage, 0) + 1
                    if stage == 'evolved_last_resort' and len(fallback_last_resort_samples) < fallback_last_resort_cap:
                        fallback_last_resort_samples.append(
                            {
                                'fixed_radius': debug.get('fixed_radius'),
                                'chosen_r': debug.get('chosen_r'),
                                'chosen_ratio': debug.get('chosen_ratio'),
                                'chosen_laps': debug.get('chosen_laps'),
                                'chosen_diff': debug.get('chosen_diff'),
                                'chosen_gcd': debug.get('chosen_gcd'),
                                'prev_r': debug.get('fallback_prev_r'),
                                'ratio_window': debug.get('fallback_ratio_window'),
                                'ratio_bounds': debug.get('fallback_ratio_bounds'),
                                'ratio_range': debug.get('fallback_ratio_range'),
                                'diff_min': debug.get('fallback_diff_min'),
                            }
                        )

        d = int(
            random_pen_offset(
                fixed_radius=R,
                rolling_radius=r,
                prev=session.last_request,
                complexity=session.random_complexity,
                constraint=session.random_constraint_mode,
                evolution=session.random_evolution_mode,
            )
        )
        pen_debug = get_last_pen_offset_selection_debug() or {}
        if pen_debug.get('used_diff_band'):
            diff_band_used_count += 1
        if pen_debug.get('used_fallback_full_range'):
            pen_fallback_full_range_count += 1
        # Capture a small sample of pen-offset bias/interval debug to verify high_pref adjustments.
        if len(pen_bias_samples) < pen_bias_samples_cap:
            hp_base = pen_debug.get('high_pref_base')
            hp_eff = pen_debug.get('high_pref_effective')
            w_left = pen_debug.get('interval_w_left')
            w_right = pen_debug.get('interval_w_right')
            w_share = pen_debug.get('interval_width_share')
            mode = pen_debug.get('selection_mode')
            used_db = pen_debug.get('used_diff_band')

            # Only record when at least one of the new fields is present (avoids noise if code path differs).
            if (
                any(v is not None for v in (hp_base, hp_eff, w_left, w_right, w_share))
                or mode is not None
                or used_db is not None
            ):
                pen_bias_samples.append(
                    {
                        'rolling_radius': pen_debug.get('rolling_radius'),
                        'chosen_d': pen_debug.get('chosen_d'),
                        'chosen_factor': pen_debug.get('chosen_factor'),
                        'effective_min': pen_debug.get('effective_min'),
                        'd_min': pen_debug.get('d_min'),
                        'd_max': pen_debug.get('d_max'),
                        'band': pen_debug.get('band'),
                        'band_base': pen_debug.get('band_base'),
                        'band_effective': pen_debug.get('band_effective'),
                        'radius_mul': pen_debug.get('radius_mul'),
                        'band_low_d': pen_debug.get('band_low_d'),
                        'band_high_d': pen_debug.get('band_high_d'),
                        'left': pen_debug.get('left'),
                        'right': pen_debug.get('right'),
                        'high_pref_base': hp_base,
                        'high_pref_effective': hp_eff,
                        'interval_w_left': w_left,
                        'interval_w_right': w_right,
                        'interval_width_share': w_share,
                        'diff': pen_debug.get('diff'),
                        'diff_low': pen_debug.get('diff_low'),
                        'diff_high': pen_debug.get('diff_high'),
                        'diff_band_weight_t': pen_debug.get('diff_band_weight_t'),
                        'used_diff_band': used_db,
                        'selection_mode': mode,
                        'final_low': pen_debug.get('final_low'),
                        'final_high': pen_debug.get('final_high'),
                        'used_fallback_full_range': pen_debug.get('used_fallback_full_range'),
                        'empty_range_fallback': pen_debug.get('empty_range_fallback'),
                    }
                )
        if len(pen_near_one_samples) < pen_near_one_cap:
            chosen_factor = pen_debug.get('chosen_factor')
            if isinstance(chosen_factor, (int, float)) and 0.80 <= chosen_factor <= 1.20:
                pen_near_one_samples.append(
                    {
                        'rolling_radius': pen_debug.get('rolling_radius'),
                        'chosen_d': pen_debug.get('chosen_d'),
                        'chosen_factor': chosen_factor,
                        'effective_min': pen_debug.get('effective_min'),
                        'd_min': pen_debug.get('d_min'),
                        'd_max': pen_debug.get('d_max'),
                        'band': pen_debug.get('band'),
                        'band_low_d': pen_debug.get('band_low_d'),
                        'band_high_d': pen_debug.get('band_high_d'),
                        'left': pen_debug.get('left'),
                        'right': pen_debug.get('right'),
                    }
                )

        g = math.gcd(R, r)
        lobe_count = max(1, R // g)
        laps = max(1, r // g)
        ratio = (R / r) if r else float('inf')
        diff = abs(R - r)
        offset_factor = (d / r) if r else float('inf')
        denom = d + r
        ringness = (abs(d - r) / denom) if denom else float('inf')
        lobe_error = lobes_error_for(profile, lobe_count)
        rsn = radial_span_norm_for(R, r, d)
        rho_min_over_max = rho_min_over_max_for(R, r, d)
        sharpness_p95 = sharpness_p95_abs_turn_rad_for(R, r, d)

        Rs.append(R)
        rs.append(r)
        ds.append(d)
        ratios.append(ratio)
        gcds.append(g)
        lobes.append(lobe_count)
        lobe_errors.append(lobe_error)
        laps_to_close.append(laps)
        diffs.append(diff)
        offset_factors.append(offset_factor)
        ringness_values.append(ringness)
        radial_span_norms.append(rsn)
        rho_min_over_max_values.append(rho_min_over_max)
        sharpness_p95_values.append(sharpness_p95)

        if (
            len(center_reach_samples) < center_reach_cap
            and math.isfinite(rho_min_over_max)
            and rho_min_over_max <= 0.12
        ):
            center_reach_samples.append(
                {
                    'fixed_radius': R,
                    'rolling_radius': r,
                    'pen_distance': d,
                    'lobes': lobe_count,
                    'laps': laps,
                    'ratio_R_over_r': ratio,
                    'diff_abs_R_minus_r': diff,
                    'offset_factor_d_over_r': offset_factor,
                    'rho_min_over_max': rho_min_over_max,
                    'sharpness_p95_abs_turn_rad': sharpness_p95,
                }
            )

        if not (profile.ratio_min <= ratio <= profile.ratio_max):
            ratio_outside += 1
        if not lobes_in_range_for(profile, lobe_count):
            lobes_outside_tolerance += 1
        if diff < profile.diff_min:
            diff_below += 1
        if not (
            profile.offset_min_factor
            <= offset_factor
            <= profile.offset_max_factor * (1.5 if constraint is RandomConstraintMode.WILD else 1.0)
        ):
            offset_outside += 1
        if offset_factor <= 0.35:
            offset_small += 1
        if 0.80 <= offset_factor <= 1.20:
            offset_near_one += 1
        if offset_factor >= 1.05:
            offset_prolate += 1
        if offset_factor >= 1.60:
            offset_large += 1
        if ringness <= 0.10:
            ring_like += 1
        if rsn <= 0.12:
            visual_ring_like += 1
        if g == 1:
            gcd_eq_1 += 1

        session.last_request = CircularSpiroRequest(
            fixed_radius=R,
            rolling_radius=r,
            pen_distance=d,
            steps=1,
            curve_type=session.curve_type,
        )

    selection_debug_summary = {
        'constructed_pct': 100.0 * constructed_count / samples,
        'sampled_pct': 100.0 * sampled_count / samples,
        'constructed_candidates_considered_avg': (constructed_considered_total / constructed_count)
        if constructed_count
        else 0.0,
        'sampled_candidates_considered_avg': (sampled_considered_total / sampled_count) if sampled_count else 0.0,
        'fallback_used_pct': 100.0 * fallback_used_count / samples,
        'fallback_candidates_total_avg': (fallback_candidates_total / fallback_used_count)
        if fallback_used_count
        else 0.0,
        'fallback_candidates_considered_avg': (fallback_candidates_considered / fallback_used_count)
        if fallback_used_count
        else 0.0,
        'fallback_stage_counts': fallback_stage_counts,
        'fallback_last_resort_samples': fallback_last_resort_samples,
        'pen_fallback_full_range_pct': 100.0 * pen_fallback_full_range_count / samples,
        'diff_band_used_pct': 100.0 * diff_band_used_count / samples,
        'pen_near_one_samples': pen_near_one_samples,
        'pen_bias_samples': pen_bias_samples,
        'center_reach_samples': center_reach_samples,
    }

    return {
        'complexity': complexity.value,
        'constraint': constraint.value,
        'evolution': evolution.value,
        'profile': asdict(profile),
        'violations': {
            'ratio_outside_profile_pct': 100.0 * ratio_outside / samples,
            'lobes_outside_tolerance_pct': 100.0 * lobes_outside_tolerance / samples,
            'diff_below_profile_pct': 100.0 * diff_below / samples,
            'offset_outside_profile_pct': 100.0 * offset_outside / samples,
            'offset_small_pct': 100.0 * offset_small / samples,
            'offset_near_one_pct': 100.0 * offset_near_one / samples,
            'offset_prolate_pct': 100.0 * offset_prolate / samples,
            'offset_large_pct': 100.0 * offset_large / samples,
            'ring_like_pct': 100.0 * ring_like / samples,
            'visual_ring_like_pct': 100.0 * visual_ring_like / samples,
            'gcd_eq_1_pct': 100.0 * gcd_eq_1 / samples,
        },
        'selection_debug_summary': selection_debug_summary,
        'stats': {
            'R': summarize_ints(Rs),
            'r': summarize_ints(rs),
            'd': summarize_ints(ds),
            'ratio_R_over_r': summarize_floats(ratios),
            'gcd_R_r': summarize_ints(gcds),
            'lobes_est': summarize_ints(lobes),
            'lobes_error': summarize_floats(lobe_errors),
            'laps_to_close': summarize_ints(laps_to_close),
            'diff_abs_R_minus_r': summarize_ints(diffs),
            'offset_factor_d_over_r': summarize_floats(offset_factors),
            'ringness_abs_d_minus_r_over_sum': summarize_floats(ringness_values),
            'radial_span_norm': summarize_floats(radial_span_norms),
            'rho_min_over_max': summarize_floats(rho_min_over_max_values),
            'sharpness_p95_abs_turn_rad': summarize_floats(sharpness_p95_values),
            'corr_rho_min_over_max_vs_offset_factor': pearson_corr_for(
                rho_min_over_max_values,
                offset_factors,
            ),
            'corr_sharpness_vs_rho_min_over_max': pearson_corr_for(
                sharpness_p95_values,
                rho_min_over_max_values,
            ),
            'corr_sharpness_vs_offset_factor': pearson_corr_for(
                sharpness_p95_values,
                offset_factors,
            ),
        },
    }


def _set_profiles(profiles: dict[RandomComplexity, object]) -> None:
    COMPLEXITY_PROFILES.clear()
    COMPLEXITY_PROFILES.update(profiles)


def _score_result(result: dict[str, object]) -> tuple[float, float]:
    violations = result.get('violations', {})
    lobes_outside = float(violations.get('lobes_outside_tolerance_pct', 0.0))
    ratio_outside = float(violations.get('ratio_outside_profile_pct', 0.0))
    return (lobes_outside, ratio_outside)


def auto_tune_profiles(
    *,
    samples: int,
    max_iterations: int,
    step_m_candidates: int,
    step_top_n: int,
    step_samples: int,
    step_lobes_retry: int,
    max_m_candidates: int,
    max_top_n: int,
    max_samples: int,
    max_lobes_retry: int,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
    complexities: list[RandomComplexity],
) -> None:
    base_profiles = dict(COMPLEXITY_PROFILES)

    for complexity in complexities:
        base_profile = base_profiles[complexity]
        best_profile = base_profile
        COMPLEXITY_PROFILES[complexity] = best_profile
        baseline = run_for_complexity(
            complexity=complexity,
            samples=samples,
            constraint=constraint,
            evolution=evolution,
        )
        best_score = _score_result(baseline)

        for _ in range(max_iterations):
            candidates = []
            for m_delta, top_delta, sample_delta in (
                (step_m_candidates, 0, 0),
                (-step_m_candidates, 0, 0),
                (0, step_top_n, 0),
                (0, -step_top_n, 0),
                (0, 0, step_samples),
                (0, 0, -step_samples),
                (step_m_candidates, step_top_n, 0),
                (step_m_candidates, -step_top_n, 0),
                (-step_m_candidates, step_top_n, 0),
                (-step_m_candidates, -step_top_n, 0),
                (step_m_candidates, 0, step_samples),
                (step_m_candidates, 0, -step_samples),
                (-step_m_candidates, 0, step_samples),
                (-step_m_candidates, 0, -step_samples),
                (0, step_top_n, step_samples),
                (0, step_top_n, -step_samples),
                (0, -step_top_n, step_samples),
                (0, -step_top_n, -step_samples),
                (step_m_candidates, step_top_n, step_samples),
                (step_m_candidates, step_top_n, -step_samples),
                (step_m_candidates, -step_top_n, step_samples),
                (step_m_candidates, -step_top_n, -step_samples),
                (-step_m_candidates, step_top_n, step_samples),
                (-step_m_candidates, step_top_n, -step_samples),
                (-step_m_candidates, -step_top_n, step_samples),
                (-step_m_candidates, -step_top_n, -step_samples),
            ):
                for retry_delta in (-step_lobes_retry, 0, step_lobes_retry):
                    new_m = best_profile.constructed_m_candidates + m_delta
                    new_top = best_profile.constructed_top_n + top_delta
                    new_samples = best_profile.sample_count + sample_delta
                    new_retry = best_profile.lobes_retry_count + retry_delta

                    new_m = max(base_profile.constructed_m_candidates, min(new_m, max_m_candidates))
                    new_top = max(base_profile.constructed_top_n, min(new_top, max_top_n))
                    new_samples = max(base_profile.sample_count, min(new_samples, max_samples))
                    new_retry = max(base_profile.lobes_retry_count, min(new_retry, max_lobes_retry))

                    if (
                        new_m == best_profile.constructed_m_candidates
                        and new_top == best_profile.constructed_top_n
                        and new_samples == best_profile.sample_count
                        and new_retry == best_profile.lobes_retry_count
                    ):
                        continue
                    candidates.append(
                        replace(
                            best_profile,
                            constructed_m_candidates=new_m,
                            constructed_top_n=new_top,
                            sample_count=new_samples,
                            lobes_retry_count=new_retry,
                        )
                    )

            if not candidates:
                break

            improved = False
            for candidate in candidates:
                COMPLEXITY_PROFILES[complexity] = candidate
                result = run_for_complexity(
                    complexity=complexity,
                    samples=samples,
                    constraint=constraint,
                    evolution=evolution,
                )
                score = _score_result(result)
                if score < best_score:
                    best_score = score
                    best_profile = candidate
                    improved = True

            COMPLEXITY_PROFILES[complexity] = best_profile
            if not improved:
                break

        base_profiles[complexity] = best_profile

    _set_profiles(base_profiles)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=500)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument(
        '--constraint',
        choices=[m.value for m in RandomConstraintMode],
        default=RandomConstraintMode.EXTENDED.value,
    )
    parser.add_argument(
        '--evolution',
        choices=[m.value for m in RandomEvolutionMode],
        default=RandomEvolutionMode.RANDOM.value,
    )
    parser.add_argument(
        '--only',
        choices=[c.value for c in RandomComplexity],
        default=None,
        help='Run only one complexity value',
    )
    parser.add_argument('--auto-tune', action='store_true', help='Auto-tune candidate counts in a bounded loop')
    parser.add_argument('--auto-samples', type=int, default=400, help='Samples per auto-tune iteration')
    parser.add_argument('--auto-iterations', type=int, default=4)
    parser.add_argument('--auto-step-m', type=int, default=6)
    parser.add_argument('--auto-step-top', type=int, default=4)
    parser.add_argument('--auto-step-samples', type=int, default=50)
    parser.add_argument('--auto-step-retry', type=int, default=1)
    parser.add_argument('--auto-max-m', type=int, default=60)
    parser.add_argument('--auto-max-top', type=int, default=30)
    parser.add_argument('--auto-max-samples', type=int, default=600)
    parser.add_argument('--auto-max-retry', type=int, default=8)

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.seed is not None:
        random.seed(args.seed)

    constraint = RandomConstraintMode(args.constraint)
    evolution = RandomEvolutionMode(args.evolution)

    complexities = [RandomComplexity(args.only)] if args.only else list(RandomComplexity)

    if args.auto_tune:
        auto_tune_profiles(
            samples=args.auto_samples,
            max_iterations=args.auto_iterations,
            step_m_candidates=args.auto_step_m,
            step_top_n=args.auto_step_top,
            step_samples=args.auto_step_samples,
            step_lobes_retry=args.auto_step_retry,
            max_m_candidates=args.auto_max_m,
            max_top_n=args.auto_max_top,
            max_samples=args.auto_max_samples,
            max_lobes_retry=args.auto_max_retry,
            constraint=constraint,
            evolution=evolution,
            complexities=complexities,
        )

    results: list[dict[str, object]] = []
    for c in complexities:
        results.append(
            run_for_complexity(
                complexity=c,
                samples=args.samples,
                constraint=constraint,
                evolution=evolution,
            )
        )

    for result in results:
        print('=' * 80)
        print(f'complexity={result["complexity"]} constraint={result["constraint"]} evolution={result["evolution"]}')
        print('profile:', result['profile'])
        print('violations:', result['violations'])
        print('selection_debug_summary:', result.get('selection_debug_summary'))
        print('stats:')
        for k, v in result['stats'].items():
            print(f'  {k}: {v}')

    if results:
        print('=' * 80)
        print('corr_rho_min_over_max_vs_offset_factor_ranked (abs desc):')
        ranked = []
        for result in results:
            stats = result.get('stats', {})
            corr = stats.get('corr_rho_min_over_max_vs_offset_factor')
            if not isinstance(corr, (int, float)) or not math.isfinite(corr):
                corr = float('nan')
            ranked.append((result.get('complexity'), corr))
        ranked.sort(key=lambda item: abs(item[1]) if math.isfinite(item[1]) else -1.0, reverse=True)
        for complexity, corr in ranked:
            print(f'  {complexity}: {corr}')

        print('=' * 80)
        print('corr_sharpness_vs_rho_min_over_max_ranked (abs desc):')
        ranked = []
        for result in results:
            stats = result.get('stats', {})
            corr = stats.get('corr_sharpness_vs_rho_min_over_max')
            if not isinstance(corr, (int, float)) or not math.isfinite(corr):
                corr = float('nan')
            ranked.append((result.get('complexity'), corr))
        ranked.sort(key=lambda item: abs(item[1]) if math.isfinite(item[1]) else -1.0, reverse=True)
        for complexity, corr in ranked:
            print(f'  {complexity}: {corr}')

        print('=' * 80)
        print('corr_sharpness_vs_offset_factor_ranked (abs desc):')
        ranked = []
        for result in results:
            stats = result.get('stats', {})
            corr = stats.get('corr_sharpness_vs_offset_factor')
            if not isinstance(corr, (int, float)) or not math.isfinite(corr):
                corr = float('nan')
            ranked.append((result.get('complexity'), corr))
        ranked.sort(key=lambda item: abs(item[1]) if math.isfinite(item[1]) else -1.0, reverse=True)
        for complexity, corr in ranked:
            print(f'  {complexity}: {corr}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
