from spirograph.generation.types import GeneratedCurve

from .settings import RenderSettings
from .types import DrawablePath, RenderPlan


class RenderPlanBuilder:
    def build(self, curve: GeneratedCurve, settings: RenderSettings) -> RenderPlan:
        path = DrawablePath(
            points=curve.points,
            color=settings.color,
            width=settings.width,
        )
        return RenderPlan(paths=(path,))
