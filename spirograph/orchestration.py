from spirograph.generation.registry import GeneratorRegistry
from spirograph.generation.requests import EngineRequest
from spirograph.rendering.builder import RenderPlanBuilder
from spirograph.rendering.settings import RenderSettings
from spirograph.rendering.types import CurveRenderer


class CurveOrchestrator:
    def __init__(
        self,
        registry: GeneratorRegistry,
        builder: RenderPlanBuilder,
        renderer: CurveRenderer,
    ) -> None:
        self._registry = registry
        self._builder = builder
        self._renderer = renderer

    def run(self, request: EngineRequest, settings: RenderSettings) -> None:
        generator = self._registry.for_request(request)
        curve = generator.generate(request)
        plan = self._builder.build(curve, settings)
        self._renderer.render(plan, settings)
