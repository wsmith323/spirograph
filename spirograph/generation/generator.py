from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .requests import EngineRequest
from .data_types import GeneratedCurve

RequestT = TypeVar('RequestT', bound=EngineRequest)


class CurveGenerator(ABC, Generic[RequestT]):
    request_type: type[RequestT]

    @abstractmethod
    def validate(self, request: RequestT) -> None:
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: RequestT) -> GeneratedCurve:
        raise NotImplementedError
