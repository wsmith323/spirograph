from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenderSettings:
    color: str = "black"
    width: float = 1.0
    speed: int = 0
