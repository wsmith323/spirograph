from typing import Callable

import math

from spirograph.generation import SpiroType
from spirograph.rendering import Color, ColorMode
from .types import RandomConstraintMode, RandomEvolutionMode


def make_prompt_label(identifier: str) -> str:
    return ' '.join(word.capitalize() for word in identifier.split('_'))


def color_input_examples() -> str:
    return 'named colors, #RRGGBB, or R,G,B (0-255)'


def prompt_enum(label: str, enum_cls, default):
    values = list(enum_cls)
    descriptions_by_enum = {
        RandomConstraintMode: {
            RandomConstraintMode.PHYSICAL: 'Stay close to real spirograph constraints.',
            RandomConstraintMode.EXTENDED: 'Allow r > R and d > r; more loopiness.',
            RandomConstraintMode.WILD: 'Very permissive; frequent self-intersections and chaos.',
        },
        RandomEvolutionMode: {
            RandomEvolutionMode.RANDOM: 'Ignores the previous run; fresh random each time.',
            RandomEvolutionMode.DRIFT: 'Random, but centered near the previous value.',
            RandomEvolutionMode.JUMP: 'Mostly drift with occasional big changes.',
        },
        ColorMode: {
            ColorMode.FIXED: 'Use the configured color for all drawing.',
            ColorMode.RANDOM_PER_RUN: 'Choose a random color for each new curve.',
            ColorMode.RANDOM_PER_LAP: 'Change to a new random color each lap around the track.',
            ColorMode.RANDOM_EVERY_N_LAPS: 'Change to a new random color every N laps around the track.',
            ColorMode.RANDOM_PER_SPIN: 'Change to a new random color each spin of the rolling circle.',
            ColorMode.RANDOM_EVERY_N_SPINS: 'Change to a new random color every N spins of the rolling circle.',
        },
    }
    descriptions = descriptions_by_enum.get(enum_cls, {})

    while True:
        print(f'{label}:')
        for index, value in enumerate(values, start=1):
            description = descriptions.get(value)
            if description:
                print(f'  {index}. {value.value} - {description}')
            else:
                print(f'  {index}. {value.value}')

        default_index = values.index(default) + 1
        raw_value = input(f'Select {label} [1-{len(values)}] [{default_index}]: ').strip()
        if raw_value == '':
            return default

        try:
            idx = int(raw_value) - 1
        except ValueError:
            print('Invalid choice.')
            continue

        if 0 <= idx < len(values):
            return values[idx]

        print('Invalid choice.')


def prompt_positive_int(identifier: str, default_value: int | None = None) -> int:
    label = make_prompt_label(identifier)

    while True:
        if default_value is not None:
            raw_value = input(f'{label} [{default_value}]: ').strip()
            if raw_value == '':
                return default_value
        else:
            raw_value = input(f'{label}: ').strip()

        try:
            parsed_value = int(raw_value)
        except ValueError:
            print('Please enter a valid integer.')
            continue

        if parsed_value <= 0:
            print('Please enter a positive integer.')
            continue

        return parsed_value


def prompt_non_negative_float(identifier: str, default_value: float) -> float:
    label = make_prompt_label(identifier)

    while True:
        raw_value = input(f'{label} [{default_value}]: ').strip()
        if raw_value == '':
            return default_value

        try:
            value = float(raw_value)
        except ValueError:
            print('Please enter a valid number.')
            continue

        if value < 0:
            print('Please enter a non-negative number.')
            continue

        return value


def prompt_positive_float(identifier: str, default_value: float) -> float:
    label = make_prompt_label(identifier)

    while True:
        raw_value = input(f'{label} [{default_value}]: ').strip()
        if raw_value == '':
            return default_value

        try:
            value = float(raw_value)
        except ValueError:
            print('Please enter a valid number.')
            continue

        if value <= 0:
            print('Please enter a positive number.')
            continue

        return value


def prompt_positive_int_or_random(
    identifier: str,
    default_value: int | None,
    random_factory: Callable[[], int],
) -> int:
    label = make_prompt_label(identifier)
    while True:
        suffix = f' [{default_value}]' if default_value is not None else ''
        raw_value = input(f"{label}{suffix} (or 'r'/'rand'/'random'): ").strip()

        if raw_value.lower() in ('r', 'rand'):
            value = random_factory()
            print(f'  Selected random {label}: {value}')
            return value

        if raw_value == '' and default_value is not None:
            return default_value

        try:
            value = int(raw_value)
        except ValueError:
            print("Enter a positive integer or 'r'.")
            continue

        if value <= 0:
            print('Please enter a positive integer.')
            continue

        return value


def prompt_drawing_speed(current_speed: int) -> int:
    label = 'Drawing speed [1 (slow) - 10 (fast)]'

    while True:
        raw_value = input(f'{label} [{current_speed}]: ').strip()
        if raw_value == '':
            return current_speed

        try:
            parsed_value = int(raw_value)
        except ValueError:
            print('Please enter a valid integer between 1 and 10.')
            continue

        if not 1 <= parsed_value <= 10:
            print('Please enter a value between 1 and 10.')
            continue

        return parsed_value


def prompt_lock_value(identifier: str, current_value: int | None) -> int | None:
    label = make_prompt_label(identifier)
    current_display = 'r' if current_value is None else str(current_value)

    while True:
        raw_value = input(f"{label} lock [{current_display}] (number or 'r'/'rand'/'random'): ").strip().lower()
        if raw_value == '':
            return current_value
        if raw_value in ('r', 'rand', 'random'):
            return None

        try:
            parsed_value = int(raw_value)
        except ValueError:
            print("Enter a positive integer, 'r', or press Enter.")
            continue

        if parsed_value <= 0:
            print('Please enter a positive integer.')
            continue

        return parsed_value


def try_parse_color(value: str) -> tuple[bool, Color]:
    cleaned = value.strip().lower()
    if cleaned == '':
        return False, Color(0, 0, 0)

    named_colors = {
        'black': Color(0, 0, 0),
        'white': Color(255, 255, 255),
        'red': Color(255, 0, 0),
        'green': Color(0, 128, 0),
        'blue': Color(0, 0, 255),
        'yellow': Color(255, 255, 0),
        'cyan': Color(0, 255, 255),
        'magenta': Color(255, 0, 255),
        'gray': Color(128, 128, 128),
        'grey': Color(128, 128, 128),
    }
    if cleaned in named_colors:
        return True, named_colors[cleaned]

    if cleaned.startswith('#'):
        cleaned = cleaned[1:]

    if len(cleaned) == 6:
        try:
            r = int(cleaned[0:2], 16)
            g = int(cleaned[2:4], 16)
            b = int(cleaned[4:6], 16)
        except ValueError:
            return False, Color(0, 0, 0)
        return True, Color(r, g, b)

    if ',' in cleaned:
        parts = [part.strip() for part in cleaned.split(',')]
        if len(parts) == 3:
            try:
                r, g, b = (int(part) for part in parts)
            except ValueError:
                return False, Color(0, 0, 0)
            if all(0 <= channel <= 255 for channel in (r, g, b)):
                return True, Color(r, g, b)

    return False, Color(0, 0, 0)


def parse_color(value: str, default: Color) -> Color:
    parsed, color = try_parse_color(value)
    if not parsed:
        return default
    return color


def compute_steps(fixed_radius: int, rolling_radius: int) -> int:
    gcd_value = math.gcd(fixed_radius, rolling_radius)
    laps = rolling_radius // gcd_value if gcd_value else 1
    return min(20000, max(3000, laps * 300))


def toggle_curve_type(current: SpiroType) -> SpiroType:
    if current is SpiroType.HYPOTROCHOID:
        return SpiroType.EPITROCHOID
    return SpiroType.HYPOTROCHOID
