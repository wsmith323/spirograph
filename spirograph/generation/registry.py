from __future__ import annotations

from .generator import CurveGenerator
from .requests import EngineRequest


class GeneratorRegistry:
    def __init__(self) -> None:
        self._by_request_type: dict[type[EngineRequest], CurveGenerator] = {}

    def register(self, generator: CurveGenerator) -> None:
        request_type = generator.request_type
        if request_type in self._by_request_type:
            raise ValueError(f"Generator already registered for {request_type}")
        self._by_request_type[request_type] = generator

    def get(self, request_type: type[EngineRequest]) -> CurveGenerator:
        try:
            return self._by_request_type[request_type]
        except KeyError as exc:
            raise KeyError(f"No generator registered for {request_type}") from exc

    def for_request(self, request: EngineRequest) -> CurveGenerator:
        return self.get(type(request))
