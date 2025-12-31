from enum import Enum


class ColorMode(Enum):
    FIXED = 'fixed'
    RANDOM_PER_RUN = 'random_per_run'
    RANDOM_PER_LAP = 'random_per_lap'
    RANDOM_EVERY_N_LAPS = 'random_every_n_laps'
    RANDOM_PER_SPIN = 'random_per_spin'
    RANDOM_EVERY_N_SPINS = 'random_every_n_spins'
