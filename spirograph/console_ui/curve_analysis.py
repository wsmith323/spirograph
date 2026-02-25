import math
from dataclasses import dataclass

from spirograph.generation import SpiroType
from spirograph.generation.requests import CircularSpiroRequest


@dataclass(frozen=True, slots=True)
class RepeatMetrics:
    gcd_value: int
    laps_to_close: int
    spins_to_close: int
    ratio: float
    offset_factor: float


def compute_curve_repeat_metrics(request: CircularSpiroRequest) -> RepeatMetrics:
    fixed_int = max(1, int(request.fixed_radius))
    rolling_int = max(1, int(request.rolling_radius))
    gcd_value = max(1, math.gcd(fixed_int, rolling_int))
    laps_to_close = max(1, rolling_int // gcd_value)

    if request.curve_type is SpiroType.HYPOTROCHOID:
        spin_numerator = abs(fixed_int - rolling_int)
    else:
        spin_numerator = fixed_int + rolling_int
    spins_to_close = max(1, spin_numerator // gcd_value)

    ratio = request.fixed_radius / request.rolling_radius if request.rolling_radius else 0.0
    offset_factor = request.pen_distance / request.rolling_radius if request.rolling_radius else 0.0
    return RepeatMetrics(
        gcd_value=gcd_value,
        laps_to_close=laps_to_close,
        spins_to_close=spins_to_close,
        ratio=ratio,
        offset_factor=offset_factor,
    )


def classify_closure_structure(laps: int, spins: int) -> str:
    complexity = max(laps, spins)
    if complexity < 8:
        return 'simple'
    if complexity < 30:
        return 'moderate'
    return 'complex'


def classify_symmetry_feel(metrics: RepeatMetrics) -> str:
    ratio_nearest_int_distance = abs(metrics.ratio - round(metrics.ratio))
    complexity = max(metrics.laps_to_close, metrics.spins_to_close)
    if ratio_nearest_int_distance < 0.08 and complexity <= 40:
        return 'strong'
    if ratio_nearest_int_distance >= 0.20 and complexity >= 20:
        return 'weak'
    return 'moderate'


def _offset_band_weight(offset_factor: float) -> float:
    if offset_factor < 0.3:
        return 0.2
    if offset_factor < 0.9:
        return 0.6
    if offset_factor < 1.2:
        return 1.0
    if offset_factor < 1.8:
        return 1.5
    return 1.8


def compute_density_score(metrics: RepeatMetrics) -> float:
    closure_score = 0.6 * metrics.laps_to_close + 0.4 * metrics.spins_to_close
    ratio_scaled = max(0.0, min(2.0, (metrics.ratio - 1.0) / 3.0))
    ratio_factor = 0.7 + 0.15 * ratio_scaled
    offset_factor_multiplier = 0.8 + 0.2 * _offset_band_weight(metrics.offset_factor)
    return closure_score * ratio_factor * offset_factor_multiplier


def classify_density(score: float) -> str:
    if score < 8:
        return 'Low'
    if score < 25:
        return 'Medium'
    if score < 80:
        return 'High'
    return 'Very High'


def describe_offset_tendency(offset_factor: float, curve_type: SpiroType) -> str:
    if curve_type is SpiroType.HYPOTROCHOID:
        if offset_factor < 0.3:
            return 'pen near center; likely soft inner petals'
        if offset_factor < 0.9:
            return 'pen inside roller; likely softer inner arcs'
        if offset_factor < 1.2:
            return 'pen near roller rim; likely classic spiky inner form'
        if offset_factor < 1.8:
            return 'pen outside roller; likely loopy inner self-intersections'
        return 'pen far outside roller; likely very loopy/chaotic inner crossings'

    if offset_factor < 0.3:
        return 'pen near center; likely broad smooth outer arcs'
    if offset_factor < 0.9:
        return 'pen inside roller; likely rounded outward petals'
    if offset_factor < 1.2:
        return 'pen near roller rim; likely classic spiky outer form'
    if offset_factor < 1.8:
        return 'pen outside roller; likely larger outward loops/intersections'
    return 'pen far outside roller; likely very large loopy outer crossings'


def _describe_curve_type(curve_type: SpiroType) -> str:
    if curve_type is SpiroType.HYPOTROCHOID:
        return 'rolling inside fixed circle (hypotrochoid)'
    return 'rolling outside fixed circle (epitrochoid)'


def _describe_ratio_complexity(ratio: float) -> str:
    if ratio < 2.0:
        return 'lower ratio; tends toward simpler large-scale structure'
    if ratio < 4.0:
        return 'moderate ratio; likely moderate repeat detail'
    return 'higher ratio; tends toward finer repeated detail'


def _build_density_notes(metrics: RepeatMetrics, density_label: str) -> str:
    drivers: list[str] = []
    if max(metrics.laps_to_close, metrics.spins_to_close) >= 30:
        drivers.append('high closure repeats')
    elif max(metrics.laps_to_close, metrics.spins_to_close) < 8:
        drivers.append('low closure repeats')

    if metrics.offset_factor >= 1.2:
        drivers.append('higher d/r (loopier style)')
    elif metrics.offset_factor < 0.3:
        drivers.append('low d/r (softer style)')

    if not drivers:
        drivers.append('balanced closure repeats and d/r')

    return f'{density_label} visual density is driven by {", ".join(drivers)}.'


def describe_curve(request: CircularSpiroRequest) -> None:
    metrics = compute_curve_repeat_metrics(request)
    closure_structure = classify_closure_structure(metrics.laps_to_close, metrics.spins_to_close)
    symmetry_feel = classify_symmetry_feel(metrics)
    density_score = compute_density_score(metrics)
    density_label = classify_density(density_score)
    ratio_desc = _describe_ratio_complexity(metrics.ratio)
    offset_desc = describe_offset_tendency(metrics.offset_factor, request.curve_type)
    notes = _build_density_notes(metrics, density_label)

    print('\nCurve analysis:')
    print(f'  Curve type: {_describe_curve_type(request.curve_type)}')
    print(
        '  Closure repeats: '
        f'laps~{metrics.laps_to_close}, spins~{metrics.spins_to_close} '
        f'(closure structure: {closure_structure})'
    )
    print(f'  Radius ratio R/r: {metrics.ratio:.3f} ({ratio_desc})')
    print(f'  Offset factor d/r: {metrics.offset_factor:.3f} ({offset_desc})')
    print(f'  Perceived symmetry while drawing: {symmetry_feel}')
    print(f'  Visual density estimate: {density_label}')
    print(
        '  Interpretation: This describes how clearly the repeating structure is perceived while tracing, '
        'not whether the curve closes.'
    )
    print(f'  Notes: {notes}\n')
