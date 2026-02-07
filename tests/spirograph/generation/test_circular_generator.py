import pytest

from spirograph.generation.circular_generator import CircularSpiroGenerator
from spirograph.generation.requests import CircularSpiroRequest
from spirograph.generation.types import SpanKind, SpiroType


def test_generate_returns_steps_plus_one_points() -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=30,
        steps=120,
    )

    curve = CircularSpiroGenerator().generate(request)

    assert len(curve.points) == 121


def test_generate_sets_expected_laps_to_close_metadata() -> None:
    request = CircularSpiroRequest(
        fixed_radius=105,
        rolling_radius=45,
        pen_distance=15,
        steps=180,
    )

    curve = CircularSpiroGenerator().generate(request)

    assert curve.metadata['laps_to_close'] == 3


@pytest.mark.parametrize(
    ('fixed_radius', 'rolling_radius', 'pen_distance', 'steps'),
    (
        (0, 45, 10, 120),
        (120, 0, 10, 120),
        (120, 45, -1, 120),
        (120, 45, 10, 0),
    ),
)
def test_invalid_request_values_raise_value_error(
    fixed_radius: float,
    rolling_radius: float,
    pen_distance: float,
    steps: int,
) -> None:
    with pytest.raises(ValueError):
        CircularSpiroRequest(
            fixed_radius=fixed_radius,
            rolling_radius=rolling_radius,
            pen_distance=pen_distance,
            steps=steps,
        )


@pytest.mark.parametrize('curve_type', (SpiroType.HYPOTROCHOID, SpiroType.EPITROCHOID))
def test_both_curve_types_produce_lap_spans(curve_type: SpiroType) -> None:
    request = CircularSpiroRequest(
        fixed_radius=120,
        rolling_radius=45,
        pen_distance=20,
        steps=120,
        curve_type=curve_type,
    )

    curve = CircularSpiroGenerator().generate(request)

    assert any(span.kind is SpanKind.LAP for span in curve.spans)
