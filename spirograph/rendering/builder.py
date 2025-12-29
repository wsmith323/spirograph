import random

from spirograph.generation.types import GeneratedCurve, SpanKind

from .settings import ColorMode, RenderSettings
from .types import Color, DrawablePath, RenderPlan


class RenderPlanBuilder:
    def build(self, curve: GeneratedCurve, settings: RenderSettings) -> RenderPlan:
        interval = max(1, settings.interval)

        def random_color() -> Color:
            return Color(
                r=random.randint(0, 255),
                g=random.randint(0, 255),
                b=random.randint(0, 255),
            )

        if settings.color_mode is ColorMode.FIXED:
            color = settings.color
            return RenderPlan(
                paths=(
                    DrawablePath(
                        points=curve.points,
                        color=color,
                        width=settings.width,
                    ),
                )
            )

        if settings.color_mode is ColorMode.RANDOM_PER_RUN:
            color = random_color()
            return RenderPlan(
                paths=(
                    DrawablePath(
                        points=curve.points,
                        color=color,
                        width=settings.width,
                    ),
                )
            )

        if settings.color_mode in (
            ColorMode.RANDOM_PER_LAP,
            ColorMode.RANDOM_EVERY_N_LAPS,
        ):
            span_kind = SpanKind.LAP
        else:
            span_kind = SpanKind.SPIN

        spans = [span for span in curve.spans if span.kind is span_kind]
        spans.sort(key=lambda span: span.ordinal)
        if not spans:
            color = random_color()
            return RenderPlan(
                paths=(
                    DrawablePath(
                        points=curve.points,
                        color=color,
                        width=settings.width,
                    ),
                )
            )

        paths: list[DrawablePath] = []
        index = 0
        while index < len(spans):
            group_end_index = min(index + interval - 1, len(spans) - 1)
            start_index = spans[index].start_index
            end_index = spans[group_end_index].end_index
            slice_end = min(end_index + 1, len(curve.points))
            if slice_end > start_index:
                paths.append(
                    DrawablePath(
                        points=curve.points[start_index:slice_end],
                        color=random_color(),
                        width=settings.width,
                    )
                )
            index = group_end_index + 1

        if not paths:
            color = random_color()
            return RenderPlan(
                paths=(
                    DrawablePath(
                        points=curve.points,
                        color=color,
                        width=settings.width,
                    ),
                )
            )

        return RenderPlan(paths=tuple(paths))
