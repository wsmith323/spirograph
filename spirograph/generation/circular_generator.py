import math

from .generator import CurveGenerator
from .requests import CircularSpiroRequest
from .types import GeneratedCurve, Point2D, PointSpan, SpanKind, SpiroType


class CircularSpiroGenerator(CurveGenerator[CircularSpiroRequest]):
    request_type = CircularSpiroRequest

    def validate(self, request: CircularSpiroRequest) -> None:
        if request.fixed_radius <= 0:
            raise ValueError('fixed_radius must be > 0')
        if request.rolling_radius <= 0:
            raise ValueError('rolling_radius must be > 0')
        if request.pen_distance < 0:
            raise ValueError('pen_distance must be >= 0')
        if request.steps <= 0:
            raise ValueError('steps must be > 0')

    def generate(self, request: CircularSpiroRequest) -> GeneratedCurve:
        self.validate(request)

        fixed_radius = request.fixed_radius
        rolling_radius = request.rolling_radius
        pen_distance = request.pen_distance
        fixed_int = int(fixed_radius)
        rolling_int = int(rolling_radius)
        gcd_value = math.gcd(fixed_int, rolling_int)
        laps_to_close = rolling_int // gcd_value
        period = 2.0 * math.pi * laps_to_close

        if request.curve_type is SpiroType.HYPOTROCHOID:
            ratio = (fixed_radius - rolling_radius) / rolling_radius
            spin_ratio = ratio
        else:
            ratio = (fixed_radius + rolling_radius) / rolling_radius
            spin_ratio = ratio

        points: list[Point2D] = []
        lap_spans: list[PointSpan] = []
        spin_spans: list[PointSpan] = []

        current_lap = 0
        current_spin = 0
        lap_start = 0
        spin_start = 0

        for step in range(request.steps + 1):
            t = (step / request.steps) * period
            if request.curve_type is SpiroType.HYPOTROCHOID:
                diff = fixed_radius - rolling_radius
                x = diff * math.cos(t) + pen_distance * math.cos(ratio * t)
                y = diff * math.sin(t) - pen_distance * math.sin(ratio * t)
            else:
                summ = fixed_radius + rolling_radius
                x = summ * math.cos(t) - pen_distance * math.cos(ratio * t)
                y = summ * math.sin(t) - pen_distance * math.sin(ratio * t)
            points.append(Point2D(x=x, y=y))

            lap_index = (step * laps_to_close) // request.steps
            spin_progress = abs(spin_ratio * t) / (2.0 * math.pi) if spin_ratio else 0.0
            spin_index = int(spin_progress)

            if lap_index > current_lap:
                lap_spans.append(
                    PointSpan(
                        start_index=lap_start,
                        end_index=step + 1,
                        kind=SpanKind.LAP,
                        ordinal=current_lap,
                    )
                )
                lap_start = step + 1
                current_lap = lap_index

            if spin_index > current_spin:
                spin_spans.append(
                    PointSpan(
                        start_index=spin_start,
                        end_index=step + 1,
                        kind=SpanKind.SPIN,
                        ordinal=current_spin,
                    )
                )
                spin_start = step + 1
                current_spin = spin_index

        final_index = len(points)
        if lap_start < final_index:
            lap_spans.append(
                PointSpan(
                    start_index=lap_start,
                    end_index=final_index,
                    kind=SpanKind.LAP,
                    ordinal=current_lap,
                )
            )
        if spin_start < final_index:
            spin_spans.append(
                PointSpan(
                    start_index=spin_start,
                    end_index=final_index,
                    kind=SpanKind.SPIN,
                    ordinal=current_spin,
                )
            )
        return GeneratedCurve(
            points=tuple(points),
            spans=tuple(lap_spans + spin_spans),
            metadata={'laps_to_close': laps_to_close},
        )
