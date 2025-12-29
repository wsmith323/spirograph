import math
import random
from enum import Enum
from typing import Callable

from spirograph.generation.requests import CircularSpiroRequest, SpiroType
from spirograph.rendering.settings import ColorMode
from spirograph.rendering.types import Color


class RandomComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    DENSE = "dense"


class RandomConstraintMode(Enum):
    PHYSICAL = "physical"
    EXTENDED = "extended"
    WILD = "wild"


class RandomEvolutionMode(Enum):
    RANDOM = "random"
    DRIFT = "drift"
    JUMP = "jump"


def make_prompt_label(identifier: str) -> str:
    return " ".join(word.capitalize() for word in identifier.split("_"))


def prompt_enum(label: str, enum_cls, default):
    values = list(enum_cls)
    descriptions_by_enum = {
        RandomComplexity: {
            RandomComplexity.SIMPLE: "Cleaner, fewer lobes; tends to look more symmetric.",
            RandomComplexity.MEDIUM: "Balanced defaults; usually pretty.",
            RandomComplexity.DENSE: "More lobes and detail; tends to close slower and look busier.",
        },
        RandomConstraintMode: {
            RandomConstraintMode.PHYSICAL: "Stay close to real spirograph constraints.",
            RandomConstraintMode.EXTENDED: "Allow r > R and d > r; more loopiness.",
            RandomConstraintMode.WILD: "Very permissive; frequent self-intersections and chaos.",
        },
        RandomEvolutionMode: {
            RandomEvolutionMode.RANDOM: "Ignores the previous run; fresh random each time.",
            RandomEvolutionMode.DRIFT: "Random, but centered near the previous value.",
            RandomEvolutionMode.JUMP: "Mostly drift with occasional big changes.",
        },
        ColorMode: {
            ColorMode.FIXED: "Use the configured color for all drawing.",
            ColorMode.RANDOM_PER_RUN: "Choose a random color for each new curve.",
            ColorMode.RANDOM_PER_LAP: "Change to a new random color each lap around the track.",
            ColorMode.RANDOM_EVERY_N_LAPS: "Change to a new random color every N laps around the track.",
            ColorMode.RANDOM_PER_SPIN: "Change to a new random color each spin of the rolling circle.",
            ColorMode.RANDOM_EVERY_N_SPINS: "Change to a new random color every N spins of the rolling circle.",
        },
    }
    descriptions = descriptions_by_enum.get(enum_cls, {})

    while True:
        print(f"{label}:")
        for index, value in enumerate(values, start=1):
            description = descriptions.get(value)
            if description:
                print(f"  {index}. {value.value} - {description}")
            else:
                print(f"  {index}. {value.value}")

        default_index = values.index(default) + 1
        raw_value = input(
            f"Select {label} [1-{len(values)}] [{default_index}]: "
        ).strip()
        if raw_value == "":
            return default

        try:
            idx = int(raw_value) - 1
        except ValueError:
            print("Invalid choice.")
            continue

        if 0 <= idx < len(values):
            return values[idx]

        print("Invalid choice.")


def prompt_positive_int(identifier: str, default_value: int | None = None) -> int:
    label = make_prompt_label(identifier)

    while True:
        if default_value is not None:
            raw_value = input(f"{label} [{default_value}]: ").strip()
            if raw_value == "":
                return default_value
        else:
            raw_value = input(f"{label}: ").strip()

        try:
            parsed_value = int(raw_value)
        except ValueError:
            print("Please enter a valid integer.")
            continue

        if parsed_value <= 0:
            print("Please enter a positive integer.")
            continue

        return parsed_value


def prompt_non_negative_float(identifier: str, default_value: float) -> float:
    label = make_prompt_label(identifier)

    while True:
        raw_value = input(f"{label} [{default_value}]: ").strip()
        if raw_value == "":
            return default_value

        try:
            value = float(raw_value)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if value < 0:
            print("Please enter a non-negative number.")
            continue

        return value


def prompt_string_with_default(identifier: str, default_value: str) -> str:
    label = make_prompt_label(identifier)
    raw_value = input(f"{label} [{default_value}]: ").strip()
    if raw_value == "":
        return default_value
    return raw_value


def prompt_positive_int_or_random(
    identifier: str,
    default_value: int | None,
    random_factory: Callable[[], int],
) -> int:
    label = make_prompt_label(identifier)
    while True:
        suffix = f" [{default_value}]" if default_value is not None else ""
        raw_value = input(f"{label}{suffix} (or 'r'): ").strip()

        if raw_value.lower() in ("r", "rand"):
            value = random_factory()
            print(f"  Selected random {label}: {value}")
            return value

        if raw_value == "" and default_value is not None:
            return default_value

        try:
            value = int(raw_value)
        except ValueError:
            print("Enter a positive integer or 'r'.")
            continue

        if value <= 0:
            print("Please enter a positive integer.")
            continue

        return value


def prompt_drawing_speed(current_speed: int) -> int:
    label = "Drawing speed [1 (slow) - 10 (fast)]"

    while True:
        raw_value = input(f"{label} [{current_speed}]: ").strip()
        if raw_value == "":
            return current_speed

        try:
            parsed_value = int(raw_value)
        except ValueError:
            print("Please enter a valid integer between 1 and 10.")
            continue

        if not 1 <= parsed_value <= 10:
            print("Please enter a value between 1 and 10.")
            continue

        return parsed_value


def prompt_lock_value(identifier: str, current_value: int | None) -> int | None:
    label = make_prompt_label(identifier)
    current_display = "r" if current_value is None else str(current_value)

    while True:
        raw_value = (
            input(f"{label} lock [{current_display}] (number or 'r'): ").strip().lower()
        )
        if raw_value == "":
            return current_value
        if raw_value in ("r", "rand", "random"):
            return None

        try:
            parsed_value = int(raw_value)
        except ValueError:
            print("Enter a positive integer, 'r', or press Enter.")
            continue

        if parsed_value <= 0:
            print("Please enter a positive integer.")
            continue

        return parsed_value


def parse_color(value: str, default: Color) -> Color:
    cleaned = value.strip().lower()
    if cleaned == "":
        return default

    named_colors = {
        "black": Color(0, 0, 0),
        "white": Color(255, 255, 255),
        "red": Color(255, 0, 0),
        "green": Color(0, 128, 0),
        "blue": Color(0, 0, 255),
        "yellow": Color(255, 255, 0),
        "cyan": Color(0, 255, 255),
        "magenta": Color(255, 0, 255),
        "gray": Color(128, 128, 128),
        "grey": Color(128, 128, 128),
    }
    if cleaned in named_colors:
        return named_colors[cleaned]

    if cleaned.startswith("#"):
        cleaned = cleaned[1:]

    if len(cleaned) == 6:
        try:
            r = int(cleaned[0:2], 16)
            g = int(cleaned[2:4], 16)
            b = int(cleaned[4:6], 16)
        except ValueError:
            return default
        return Color(r, g, b)

    if "," in cleaned:
        parts = [part.strip() for part in cleaned.split(",")]
        if len(parts) == 3:
            try:
                r, g, b = (int(part) for part in parts)
            except ValueError:
                return default
            if all(0 <= channel <= 255 for channel in (r, g, b)):
                return Color(r, g, b)

    return default


# ---------------- randomness helpers ---------------- #


def evolve_value(
    previous: int | None,
    base_min: int,
    base_max: int,
    evolution: RandomEvolutionMode,
    jump_scale: float = 0.5,
) -> int:
    if previous is None or evolution is RandomEvolutionMode.RANDOM:
        return random.randint(base_min, base_max)

    if evolution is RandomEvolutionMode.JUMP and random.random() < 0.25:
        span = base_max - base_min
        jump = int(span * jump_scale)
        return max(base_min, min(base_max, previous + random.randint(-jump, jump)))

    span = base_max - base_min
    drift = max(3, int(span * 0.25))
    return max(base_min, min(base_max, previous + random.randint(-drift, drift)))


def random_fixed_circle_radius(
    prev: CircularSpiroRequest | None, evolution: RandomEvolutionMode
) -> int:
    base_min, base_max = 100, 320
    prev_val = int(prev.fixed_radius) if prev else None
    return evolve_value(prev_val, base_min, base_max, evolution)


def random_rolling_circle_radius(
    fixed_radius: int,
    prev: CircularSpiroRequest | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_r = int(prev.rolling_radius) if prev else None

    if complexity is RandomComplexity.SIMPLE:
        ratio_min, ratio_max = 2.5, 4.5
    elif complexity is RandomComplexity.DENSE:
        ratio_min, ratio_max = 5.0, 14.0
    else:
        ratio_min, ratio_max = 3.5, 9.0

    if constraint is RandomConstraintMode.PHYSICAL:
        max_r = fixed_radius - 1
    elif constraint is RandomConstraintMode.EXTENDED:
        max_r = int(fixed_radius * 2.0)
    else:
        max_r = int(fixed_radius * 3.0)

    base_min = 2
    base_max = max_r

    def laps_to_close_for(candidate_r: int) -> int:
        return candidate_r // math.gcd(fixed_radius, candidate_r)

    best_r: int | None = None
    best_laps: int | None = None

    for _ in range(80):
        candidate_r = evolve_value(prev_r, base_min, base_max, evolution)
        candidate_r = max(2, candidate_r)

        laps = laps_to_close_for(candidate_r)

        if best_laps is None or laps < best_laps:
            best_r = candidate_r
            best_laps = laps

        if laps <= 200:
            return candidate_r

    if best_r is None:
        return max(2, evolve_value(prev_r, base_min, base_max, evolution))

    return best_r


def random_pen_offset(
    rolling_radius: int,
    prev: CircularSpiroRequest | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_d = int(prev.pen_distance) if prev else None

    if complexity is RandomComplexity.SIMPLE:
        max_factor = 1.2
    elif complexity is RandomComplexity.DENSE:
        max_factor = 2.2
    else:
        max_factor = 1.6

    if constraint is RandomConstraintMode.WILD:
        max_factor *= 1.5

    base_min = 1
    base_max = int(rolling_radius * max_factor)

    return evolve_value(prev_d, base_min, base_max, evolution)


def compute_steps(fixed_radius: int, rolling_radius: int) -> int:
    gcd_value = math.gcd(fixed_radius, rolling_radius)
    laps = rolling_radius // gcd_value if gcd_value else 1
    return min(20000, max(3000, laps * 300))


def toggle_curve_type(current: SpiroType) -> SpiroType:
    if current is SpiroType.HYPOTROCHOID:
        return SpiroType.EPITROCHOID
    return SpiroType.HYPOTROCHOID
