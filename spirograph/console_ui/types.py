from enum import Enum


class RandomConstraintMode(Enum):
    PHYSICAL = 'physical'
    EXTENDED = 'extended'
    WILD = 'wild'


class RandomEvolutionMode(Enum):
    RANDOM = 'random'
    DRIFT = 'drift'
    JUMP = 'jump'
