import pytest

from spirograph.console_ui.curve_analysis import (
    REFERENCE_ACTIVE_AREA_PROXY,
    REFERENCE_FOOTPRINT_RADIUS,
    RepeatMetrics,
    classify_closure_structure,
    classify_density,
    classify_symmetry_feel,
    compute_active_band_compression_factor,
    compute_curve_repeat_metrics,
    compute_density_score,
    compute_visual_density_score,
    describe_curve,
    describe_offset_tendency,
    estimate_curve_extent_radius,
    estimate_curve_inner_radius,
)
from spirograph.generation.requests import CircularSpiroRequest
from spirograph.generation.types import SpiroType


def test_compute_curve_repeat_metrics_hypotrochoid_uses_integer_gcd_semantics() -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=30,
        steps=180,
        curve_type=SpiroType.HYPOTROCHOID,
    )

    metrics = compute_curve_repeat_metrics(request)

    assert metrics.gcd_value == 15
    assert metrics.laps_to_close == 3
    assert metrics.spins_to_close == 5
    assert metrics.ratio == pytest.approx(120 / 45)
    assert metrics.offset_factor == pytest.approx(30 / 45)


def test_compute_curve_repeat_metrics_epitrochoid_spins_use_sum() -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=20,
        steps=180,
        curve_type=SpiroType.EPITROCHOID,
    )

    metrics = compute_curve_repeat_metrics(request)

    assert metrics.gcd_value == 15
    assert metrics.laps_to_close == 3
    assert metrics.spins_to_close == 11


def test_compute_curve_repeat_metrics_handles_small_float_radii_with_guards() -> None:
    request = CircularSpiroRequest(
        fixed_radius=1.2,
        rolling_radius=0.5,
        pen_distance=0.25,
        steps=120,
        curve_type=SpiroType.HYPOTROCHOID,
    )

    metrics = compute_curve_repeat_metrics(request)

    assert metrics.gcd_value == 1
    assert metrics.laps_to_close >= 1
    assert metrics.spins_to_close >= 1
    assert metrics.ratio == pytest.approx(2.4)
    assert metrics.offset_factor == pytest.approx(0.5)


@pytest.mark.parametrize(
    ('score', 'expected_label'),
    (
        (7.99, 'Low'),
        (8.0, 'Medium'),
        (24.99, 'Medium'),
        (25.0, 'High'),
        (79.99, 'High'),
        (80.0, 'Very High'),
    ),
)
def test_classify_density_bucket_thresholds(score: float, expected_label: str) -> None:
    assert classify_density(score) == expected_label


@pytest.mark.parametrize(
    ('laps', 'spins', 'expected'),
    (
        (1, 7, 'simple'),
        (8, 3, 'moderate'),
        (12, 29, 'moderate'),
        (30, 10, 'complex'),
    ),
)
def test_classify_closure_structure(laps: int, spins: int, expected: str) -> None:
    assert classify_closure_structure(laps, spins) == expected


def test_classify_symmetry_feel_strong_moderate_weak() -> None:
    strong_metrics = RepeatMetrics(
        gcd_value=1,
        laps_to_close=6,
        spins_to_close=10,
        ratio=2.02,
        offset_factor=1.0,
    )
    moderate_metrics = RepeatMetrics(
        gcd_value=1,
        laps_to_close=10,
        spins_to_close=12,
        ratio=2.1,
        offset_factor=1.0,
    )
    weak_metrics = RepeatMetrics(
        gcd_value=1,
        laps_to_close=30,
        spins_to_close=35,
        ratio=2.35,
        offset_factor=1.0,
    )

    assert classify_symmetry_feel(strong_metrics) == 'strong'
    assert classify_symmetry_feel(moderate_metrics) == 'moderate'
    assert classify_symmetry_feel(weak_metrics) == 'weak'


def test_describe_offset_tendency_is_curve_type_aware() -> None:
    hypo_text = describe_offset_tendency(1.3, SpiroType.HYPOTROCHOID)
    epi_text = describe_offset_tendency(1.3, SpiroType.EPITROCHOID)

    assert 'inner' in hypo_text
    assert 'outward' in epi_text


def test_estimate_curve_extent_radius_hypotrochoid_uses_abs_difference_plus_d() -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=60,
        steps=180,
        curve_type=SpiroType.HYPOTROCHOID,
    )

    assert estimate_curve_extent_radius(request) == pytest.approx(abs(120 - 45) + 60)


def test_estimate_curve_extent_radius_epitrochoid_uses_sum_plus_d() -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=60,
        steps=180,
        curve_type=SpiroType.EPITROCHOID,
    )

    assert estimate_curve_extent_radius(request) == pytest.approx(120 + 45 + 60)


def test_estimate_curve_inner_radius_hypotrochoid_uses_abs_abs_difference_minus_d() -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=60,
        steps=180,
        curve_type=SpiroType.HYPOTROCHOID,
    )

    expected = abs(abs(120 - 45) - 60)
    assert estimate_curve_inner_radius(request) == pytest.approx(expected)


def test_estimate_curve_inner_radius_epitrochoid_uses_radial_band_proxy_and_clamps() -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=60,
        steps=180,
        curve_type=SpiroType.EPITROCHOID,
    )

    inner_radius = estimate_curve_inner_radius(request)
    expected = abs((120 + 45) - 60)
    assert inner_radius == pytest.approx(expected)
    assert 0 <= inner_radius <= estimate_curve_extent_radius(request) * 0.98


@pytest.mark.parametrize(
    'curve_request',
    (
        CircularSpiroRequest(
            fixed_radius=120,
            rolling_radius=45,
            pen_distance=60,
            steps=180,
            curve_type=SpiroType.HYPOTROCHOID,
        ),
        CircularSpiroRequest(
            fixed_radius=120,
            rolling_radius=45,
            pen_distance=60,
            steps=180,
            curve_type=SpiroType.EPITROCHOID,
        ),
        CircularSpiroRequest(
            fixed_radius=10,
            rolling_radius=5,
            pen_distance=200,
            steps=180,
            curve_type=SpiroType.EPITROCHOID,
        ),
    ),
)
def test_radial_band_proxies_obey_inner_outer_invariants(curve_request: CircularSpiroRequest) -> None:
    outer_radius = estimate_curve_extent_radius(curve_request)
    inner_radius = estimate_curve_inner_radius(curve_request)

    assert outer_radius >= 1.0
    assert 0.0 <= inner_radius <= outer_radius * 0.98


@pytest.mark.parametrize('curve_type', (SpiroType.HYPOTROCHOID, SpiroType.EPITROCHOID))
def test_estimate_curve_extent_radius_increases_with_pen_distance(curve_type: SpiroType) -> None:
    small_d_request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=10,
        steps=180,
        curve_type=curve_type,
    )
    large_d_request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=60,
        steps=180,
        curve_type=curve_type,
    )

    assert estimate_curve_extent_radius(large_d_request) > estimate_curve_extent_radius(small_d_request)


def test_compute_visual_density_score_decreases_for_larger_footprint_same_metrics() -> None:
    metrics = RepeatMetrics(1, 30, 40, 3.0, 1.0)
    small_request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=20,
        steps=180,
        curve_type=SpiroType.HYPOTROCHOID,
    )
    large_request = CircularSpiroRequest(
        fixed_radius=320,
        rolling_radius=45,
        pen_distance=160,
        steps=180,
        curve_type=SpiroType.EPITROCHOID,
    )

    small_score = compute_visual_density_score(metrics, small_request)
    large_score = compute_visual_density_score(metrics, large_request)

    assert small_score > large_score


def test_compute_active_band_compression_factor_increases_with_larger_hole_same_outer_radius() -> None:
    smaller_hole_request = CircularSpiroRequest(
        fixed_radius=80,
        rolling_radius=30,
        pen_distance=90,
        steps=180,
        curve_type=SpiroType.EPITROCHOID,
    )
    larger_hole_request = CircularSpiroRequest(
        fixed_radius=140,
        rolling_radius=30,
        pen_distance=30,
        steps=180,
        curve_type=SpiroType.EPITROCHOID,
    )

    assert estimate_curve_extent_radius(smaller_hole_request) == pytest.approx(
        estimate_curve_extent_radius(larger_hole_request)
    )
    smaller_hole_factor = compute_active_band_compression_factor(smaller_hole_request)
    larger_hole_factor = compute_active_band_compression_factor(larger_hole_request)

    assert larger_hole_factor > smaller_hole_factor


def test_compute_active_band_compression_factor_has_reasonable_clamps() -> None:
    tiny_active_area_request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=60,
        pen_distance=1,
        steps=180,
        curve_type=SpiroType.HYPOTROCHOID,
    )
    huge_active_area_request = CircularSpiroRequest(
        fixed_radius=1000,
        rolling_radius=10,
        pen_distance=990,
        steps=180,
        curve_type=SpiroType.EPITROCHOID,
    )

    tiny_factor = compute_active_band_compression_factor(tiny_active_area_request)
    huge_factor = compute_active_band_compression_factor(huge_active_area_request)

    assert 0.75 <= tiny_factor <= 1.6
    assert 0.75 <= huge_factor <= 1.6
    assert REFERENCE_ACTIVE_AREA_PROXY > 0


def test_compute_visual_density_score_uses_lower_and_upper_footprint_clamps() -> None:
    metrics = RepeatMetrics(1, 30, 40, 3.0, 1.0)
    tiny_request = CircularSpiroRequest(
        fixed_radius=2,
        rolling_radius=1,
        pen_distance=0,
        steps=180,
        curve_type=SpiroType.HYPOTROCHOID,
    )
    huge_request = CircularSpiroRequest(
        fixed_radius=1000,
        rolling_radius=900,
        pen_distance=500,
        steps=180,
        curve_type=SpiroType.EPITROCHOID,
    )

    structural_score = compute_density_score(metrics)
    tiny_score = compute_visual_density_score(metrics, tiny_request)
    huge_score = compute_visual_density_score(metrics, huge_request)
    tiny_band_factor = compute_active_band_compression_factor(tiny_request)
    huge_band_factor = compute_active_band_compression_factor(huge_request)

    assert tiny_score == pytest.approx((structural_score / 0.65) * tiny_band_factor)
    assert huge_score == pytest.approx((structural_score / 1.75) * huge_band_factor)
    assert REFERENCE_FOOTPRINT_RADIUS > 0


def test_compute_visual_density_score_increases_with_larger_hole_when_outer_size_is_similar() -> None:
    metrics = RepeatMetrics(1, 30, 40, 3.0, 1.0)
    smaller_hole_request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=60,
        pen_distance=55,
        steps=180,
        curve_type=SpiroType.HYPOTROCHOID,
    )
    larger_hole_request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=60,
        pen_distance=10,
        steps=180,
        curve_type=SpiroType.HYPOTROCHOID,
    )

    smaller_hole_score = compute_visual_density_score(metrics, smaller_hole_request)
    larger_hole_score = compute_visual_density_score(metrics, larger_hole_request)

    assert larger_hole_score > smaller_hole_score


@pytest.mark.parametrize(
    'metrics, expected_label',
    (
        (RepeatMetrics(1, 2, 2, 1.5, 0.1), 'Low'),
        (RepeatMetrics(1, 12, 10, 2.5, 1.0), 'Medium'),
        (RepeatMetrics(1, 60, 90, 3.5, 1.4), 'High'),
        (RepeatMetrics(1, 120, 160, 5.0, 2.0), 'Very High'),
    ),
)
def test_compute_density_score_examples_classify_as_expected(
    metrics: RepeatMetrics,
    expected_label: str,
) -> None:
    score = compute_density_score(metrics)

    assert classify_density(score) == expected_label


@pytest.mark.parametrize('curve_type', (SpiroType.HYPOTROCHOID, SpiroType.EPITROCHOID))
def test_describe_curve_output_contains_new_labels_and_no_approx_lobes(
    capsys: pytest.CaptureFixture[str],
    curve_type: SpiroType,
) -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=60,
        steps=180,
        curve_type=curve_type,
    )

    describe_curve(request)
    output = capsys.readouterr().out

    assert 'Curve analysis:' in output
    assert 'Curve guidance:' not in output
    assert 'Closure repeats' in output
    assert 'Perceived symmetry while rendering' in output
    assert 'Visual density estimate' in output
    assert 'Estimated footprint radius' in output
    assert 'Estimated inner empty radius' in output
    assert 'Notes:' in output
    assert 'Interpretation:' not in output
    assert 'Symmetry feel' not in output
    assert 'approx lobes' not in output
