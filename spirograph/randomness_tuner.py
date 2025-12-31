#!/usr/bin/env python3
"""
Sampling script for spirograph CLI randomness tuning.

Run from repo root:
  python3 -m spirograph.cli.sample_randomness --samples 1000

Or:
  python3 spirograph/cli/sample_randomness.py --samples 2000 --seed 123
"""

import argparse
import random
import statistics
from dataclasses import asdict
from typing import Iterable

import math

from spirograph.cli.constants import RandomComplexity, RandomConstraintMode, RandomEvolutionMode
from spirograph.cli.randomness import (
    COMPLEXITY_PROFILES,
    get_last_rolling_radius_selection_debug,
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

    ratio_outside = 0
    lobes_outside_tolerance = 0
    diff_below = 0
    offset_outside = 0
    gcd_eq_1 = 0

    constructed_count = 0
    sampled_count = 0
    constructed_considered_total = 0
    sampled_considered_total = 0

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

        d = int(
            random_pen_offset(
                rolling_radius=r,
                prev=session.last_request,
                complexity=session.random_complexity,
                constraint=session.random_constraint_mode,
                evolution=session.random_evolution_mode,
            )
        )

        g = math.gcd(R, r)
        lobe_count = max(1, R // g)
        laps = max(1, r // g)
        ratio = (R / r) if r else float('inf')
        diff = abs(R - r)
        offset_factor = (d / r) if r else float('inf')
        lobe_error = abs(lobe_count - profile.lobes_target)

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

        if not (profile.ratio_min <= ratio <= profile.ratio_max):
            ratio_outside += 1
        if lobe_error > profile.lobes_tolerance:
            lobes_outside_tolerance += 1
        if diff < profile.diff_min:
            diff_below += 1
        if not (
            profile.offset_min_factor
            <= offset_factor
            <= profile.offset_max_factor * (1.5 if constraint is RandomConstraintMode.WILD else 1.0)
        ):
            offset_outside += 1
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
        },
    }


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

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.seed is not None:
        random.seed(args.seed)

    constraint = RandomConstraintMode(args.constraint)
    evolution = RandomEvolutionMode(args.evolution)

    complexities = [RandomComplexity(args.only)] if args.only else list(RandomComplexity)

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

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
