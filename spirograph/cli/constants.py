from enum import Enum


class RandomComplexity(Enum):
    SIMPLE = 'simple'
    MEDIUM = 'medium'
    COMPLEX = 'complex'
    DENSE = 'dense'


class RandomConstraintMode(Enum):
    PHYSICAL = 'physical'
    EXTENDED = 'extended'
    WILD = 'wild'


class RandomEvolutionMode(Enum):
    RANDOM = 'random'
    DRIFT = 'drift'
    JUMP = 'jump'
