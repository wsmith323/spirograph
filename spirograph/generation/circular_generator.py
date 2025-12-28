import math

from .generator import CurveGenerator
from .requests import CircularSpiroRequest
from .types import GeneratedCurve, Point2D, PointSpan, SpanKind


class CircularSpiroGenerator(CurveGenerator[CircularSpiroRequest]):
    request_type = CircularSpiroRequest

    def validate(self, request: CircularSpiroRequest) -> None:
        if request.fixed_radius <= 0:
            raise ValueError("fixed_radius must be > 0")
        if request.rolling_radius <= 0:
            raise ValueError("rolling_radius must be > 0")
        if request.pen_distance < 0:
            raise ValueError("pen_distance must be >= 0")
        if request.steps <= 0:
            raise ValueError("steps must be > 0")

    def generate(self, request: CircularSpiroRequest) -> GeneratedCurve:
        self.validate(request)

        fixed_radius = request.fixed_radius
        rolling_radius = request.rolling_radius
        pen_distance = request.pen_distance
        step_size = 0.1

        points: list[Point2D] = []
        for step in range(request.steps + 1):
            t = step * step_size
            ratio = (fixed_radius - rolling_radius) / rolling_radius
            x = (fixed_radius - rolling_radius) * math.cos(t) + pen_distance * math.cos(
                ratio * t
            )
            y = (fixed_radius - rolling_radius) * math.sin(t) - pen_distance * math.sin(
                ratio * t
            )
            points.append(Point2D(x=x, y=y))

        span = PointSpan(
            start_index=0,
            end_index=len(points),
            kind=SpanKind.LAP,
            ordinal=0,
        )
        return GeneratedCurve(points=tuple(points), spans=(span,))
