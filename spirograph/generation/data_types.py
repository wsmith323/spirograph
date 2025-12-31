from dataclasses import dataclass, field

from .constants import SpanKind


@dataclass(frozen=True, slots=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class PointSpan:
    start_index: int
    end_index: int
    kind: SpanKind
    ordinal: int

    def __post_init__(self) -> None:
        if self.start_index < 0:
            raise ValueError('start_index must be >= 0')
        if self.end_index <= self.start_index:
            raise ValueError('end_index must be > start_index')
        if self.ordinal < 0:
            raise ValueError('ordinal must be >= 0')


@dataclass(frozen=True, slots=True)
class GeneratedCurve:
    points: tuple[Point2D, ...]
    spans: tuple[PointSpan, ...]
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.points) <= 1:
            raise ValueError('points must contain at least 2 entries')
        max_index = len(self.points)
        for span in self.spans:
            if span.start_index < 0 or span.end_index > max_index:
                raise ValueError('span indices must be within points bounds')
