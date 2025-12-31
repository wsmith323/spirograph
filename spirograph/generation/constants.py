from enum import Enum


class SpanKind(Enum):
    LAP = 'LAP'
    SPIN = 'SPIN'


class SpiroType(Enum):
    HYPOTROCHOID = 'hypotrochoid'
    EPITROCHOID = 'epitrochoid'
