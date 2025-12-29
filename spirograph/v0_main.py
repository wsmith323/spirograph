import random
import time
import turtle
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import math

NUMBER_OF_STEPS = 3000
SCREEN_SIZE = 1000

MAX_LAPS_TO_CLOSE = 200


class SpiroType(Enum):
    HYPOTROCHOID = "hypotrochoid"
    EPITROCHOID = "epitrochoid"


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


class ColorMode(Enum):
    FIXED = "fixed"
    RANDOM_PER_RUN = "random_per_run"

    # Lap-based: rolling circle center goes around the track (t advances by 2π per lap).
    RANDOM_PER_LAP = "random_per_lap"
    RANDOM_EVERY_N_LAPS = "random_every_n_laps"

    # Spin-based: rolling circle spins about its own center while rolling.
    RANDOM_PER_SPIN = "random_per_spin"
    RANDOM_EVERY_N_SPINS = "random_every_n_spins"


@dataclass
class SessionState:
    """In-memory session state for a single program run (no persistence)."""

    random_complexity: RandomComplexity = RandomComplexity.SIMPLE
    random_constraint_mode: RandomConstraintMode = RandomConstraintMode.EXTENDED
    random_evolution_mode: RandomEvolutionMode = RandomEvolutionMode.RANDOM
    curve_type: SpiroType = SpiroType.HYPOTROCHOID

    color_mode: ColorMode = ColorMode.RANDOM_EVERY_N_LAPS
    color: str = "black"
    laps_per_color: int = 20
    spins_per_color: int = 20

    line_width: int = 1
    drawing_speed: int = 5

    locked_fixed_circle_radius: int | None = None
    locked_rolling_circle_radius: int | None = None
    locked_pen_offset: int | None = None

    last_curve: "SpiroCurve | None" = None


class SpiroCurve:
    def __init__(
        self,
        fixed_circle_radius: int,
        rolling_circle_radius: int,
        pen_offset: int,
        curve_type: SpiroType,
        color: str | tuple[int, int, int],
        line_width: int,
    ) -> None:
        self.fixed_circle_radius = fixed_circle_radius
        self.rolling_circle_radius = rolling_circle_radius
        self.pen_offset = pen_offset
        self.curve_type = curve_type
        self.color = color
        self.line_width = line_width

    def _compute_period(self) -> float:
        gcd_value = math.gcd(self.fixed_circle_radius, self.rolling_circle_radius)
        return 2.0 * math.pi * (self.rolling_circle_radius // gcd_value)

    def generate_points(self, number_of_steps: int) -> list[tuple[float, float]]:
        period = self._compute_period()
        points: list[tuple[float, float]] = []

        for i in range(number_of_steps + 1):
            t = (i / number_of_steps) * period

            if self.curve_type is SpiroType.HYPOTROCHOID:
                R, r, d = (
                    self.fixed_circle_radius,
                    self.rolling_circle_radius,
                    self.pen_offset,
                )
                diff = R - r
                x = diff * math.cos(t) + d * math.cos((diff / r) * t)
                y = diff * math.sin(t) - d * math.sin((diff / r) * t)
            else:
                R, r, d = (
                    self.fixed_circle_radius,
                    self.rolling_circle_radius,
                    self.pen_offset,
                )
                summ = R + r
                x = summ * math.cos(t) - d * math.cos((summ / r) * t)
                y = summ * math.sin(t) - d * math.sin((summ / r) * t)

            points.append((x, y))

        return points

    def draw(self, turtle_obj: turtle.Turtle, steps: int, speed: int) -> None:
        screen = turtle_obj.getscreen()
        batch = compute_batch_size(speed)
        points = self.generate_points(steps)

        if not points:
            return

        turtle_obj.penup()
        turtle_obj.color(self.color)
        turtle_obj.pensize(self.line_width)

        turtle_obj.goto(points[0])
        turtle_obj.pendown()

        for i, p in enumerate(points[1:], start=1):
            turtle_obj.goto(p)
            if i % batch == 0:
                screen.update()

        screen.update()


# ---------------- prompts ---------------- #


def make_prompt_label(identifier: str) -> str:
    return " ".join(w.capitalize() for w in identifier.split("_"))


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


def prompt_lock_value(identifier: str, current_value: int | None) -> int | None:
    """Prompt for a lock value.

    Enter a positive integer to lock to that value, or 'r' to unlock (random).
    Press Enter to keep the current lock setting.
    """
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


# ---------------- guidance and description ---------------- #


def describe_curve(curve: "SpiroCurve") -> None:
    fixed = curve.fixed_circle_radius
    rolling = curve.rolling_circle_radius
    offset = curve.pen_offset

    gcd_value = math.gcd(fixed, rolling)
    ratio = fixed / rolling
    offset_factor = offset / rolling

    approx_petals = fixed // gcd_value
    laps_to_close = rolling // gcd_value

    if ratio < 2.0:
        ratio_desc = "very simple, large rounded shape"
    elif ratio < 4.0:
        ratio_desc = "moderate complexity with visible lobes"
    else:
        ratio_desc = "many lobes and fine detail; dense pattern"

    if offset_factor < 0.3:
        offset_desc = "pen close to center; very soft, low-amplitude petals"
    elif offset_factor < 0.9:
        offset_desc = "pen inside circle; softer petals"
    elif offset_factor < 1.1:
        offset_desc = "pen near rim; classic spiky look"
    elif offset_factor < 1.6:
        offset_desc = "pen outside circle; complex loops and self-intersections"
    else:
        offset_desc = "pen far outside circle; very loopy and potentially chaotic"

    if curve.curve_type is SpiroType.HYPOTROCHOID:
        curve_kind = "rolling inside fixed circle (hypotrochoid)"
        spin_numerator = abs(fixed - rolling)
    else:
        curve_kind = "rolling outside fixed circle (epitrochoid)"
        spin_numerator = fixed + rolling

    spins_to_close = max(1, spin_numerator // gcd_value)

    print("\nCurve guidance:")
    print(f"  Radius ratio R/r: {ratio:.3f} -> {ratio_desc}")
    print(f"  Offset factor d/r: {offset_factor:.3f} -> {offset_desc}")
    print(f"  gcd(R, r): {gcd_value} -> approx lobes: {approx_petals}")
    print(f"  Laps around the track until closure: ~{laps_to_close}")
    print(f"  Rolling-circle spins about its center until closure: ~{spins_to_close}")
    print(f"  Curve type: {curve_kind}\n")


def guide_before_fixed_radius(previous_curve: "SpiroCurve | None") -> None:
    print("\nFixed circle radius (R):")

    if previous_curve is None:
        print(
            "  R controls overall size. Larger R fills more of the window; smaller R keeps the pattern compact."
        )
        print(
            "  This parameter scales the entire figure uniformly. Typical range: 100-320."
        )
        print(
            "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
        )
        return

    prev_R = previous_curve.fixed_circle_radius
    print(f"  Default R is {prev_R}.")
    print(f"  Higher than {prev_R} scales the pattern up; lower scales it down.")
    print(
        "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
    )


def guide_before_rolling_radius(
    fixed_circle_radius: int, previous_curve: "SpiroCurve | None"
) -> None:
    R = fixed_circle_radius
    print("\nRolling circle radius (r):")
    print(f"  Current R = {R}.")

    if previous_curve is None:
        print(
            "  In a physical kit, hypotrochoids typically use r < R, but this program allows any positive r.\n"
            "  Smaller r (relative to R) gives more lobes and a denser pattern.\n"
            "  Values near R or above R often create more dramatic loops and self-intersections."
        )
        print(
            "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
        )
        return

    prev_r = previous_curve.rolling_circle_radius
    ratio_if_unchanged = R / prev_r
    gcd_if_unchanged = math.gcd(R, prev_r)
    petals_if_unchanged = R // gcd_if_unchanged
    laps_if_unchanged = prev_r // gcd_if_unchanged

    print(
        f"  Default r is {prev_r}. With current R, R/r would be ~{ratio_if_unchanged:.3f}."
    )
    print(
        f"  That implies ~{petals_if_unchanged} lobes and closes after ~{laps_if_unchanged} laps around the track."
    )

    if abs(ratio_if_unchanged - round(ratio_if_unchanged)) < 1e-9:
        print("  Integer-like R/r -> clean symmetry.")
    else:
        print("  Non-integer R/r -> denser, more intricate patterns.")

    print(
        f"  Smaller than {prev_r} increases R/r (more lobes); larger decreases R/r (fewer lobes)."
    )
    print(
        "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
    )


def guide_before_pen_offset(
    fixed_circle_radius: int,
    rolling_circle_radius: int,
    previous_curve: "SpiroCurve | None",
) -> None:
    R = fixed_circle_radius
    r = rolling_circle_radius

    print("\nPen offset (d):")
    print(f"  Current R = {R}, r = {r}.")

    gcd_value = math.gcd(R, r)
    ratio = R / r
    approx_petals = R // gcd_value
    laps_to_close = r // gcd_value

    if abs(ratio - round(ratio)) < 1e-9:
        ratio_symmetry = "integer-like ratio -> cleaner symmetry"
    else:
        ratio_symmetry = "non-integer ratio -> denser / more intricate"

    print(f"  So far: R/r ~{ratio:.3f} ({ratio_symmetry}).")
    print(f"  So far: gcd(R, r) = {gcd_value} -> approx lobes ~{approx_petals}.")
    print(f"  So far: closes after ~{laps_to_close} laps around the track.")

    if previous_curve is None:
        print(
            "  d/r is the key: small -> soft; near 1 -> spiky; above 1 -> loops and self-intersections."
        )
        print(
            "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
        )
        return

    prev_d = previous_curve.pen_offset
    offset_factor_if_unchanged = prev_d / r

    print(
        f"  Default d is {prev_d}. With current r, d/r would be ~{offset_factor_if_unchanged:.3f}."
    )
    print(
        f"  Smaller than {prev_d} softens (lower d/r); larger exaggerates spikes/loops (higher d/r)."
    )
    print(
        "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
    )


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
    prev: SpiroCurve | None, evolution: RandomEvolutionMode
) -> int:
    base_min, base_max = 100, 320
    prev_val = prev.fixed_circle_radius if prev else None
    return evolve_value(prev_val, base_min, base_max, evolution)


def random_rolling_circle_radius(
    R: int,
    prev: SpiroCurve | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_r = prev.rolling_circle_radius if prev else None

    if complexity is RandomComplexity.SIMPLE:
        ratio_min, ratio_max = 2.5, 4.5
    elif complexity is RandomComplexity.DENSE:
        ratio_min, ratio_max = 5.0, 14.0
    else:
        ratio_min, ratio_max = 3.5, 9.0

    if constraint is RandomConstraintMode.PHYSICAL:
        max_r = R - 1
    elif constraint is RandomConstraintMode.EXTENDED:
        max_r = int(R * 2.0)
    else:
        max_r = int(R * 3.0)

    base_min = 2
    base_max = max_r

    def laps_to_close_for(candidate_r: int) -> int:
        return candidate_r // math.gcd(R, candidate_r)

    best_r: int | None = None
    best_laps: int | None = None

    for _ in range(80):
        candidate_r = evolve_value(prev_r, base_min, base_max, evolution)
        candidate_r = max(2, candidate_r)

        laps = laps_to_close_for(candidate_r)

        if best_laps is None or laps < best_laps:
            best_r = candidate_r
            best_laps = laps

        if laps <= MAX_LAPS_TO_CLOSE:
            return candidate_r

    if best_r is None:
        return max(2, evolve_value(prev_r, base_min, base_max, evolution))

    return best_r


def random_pen_offset(
    r: int,
    prev: SpiroCurve | None,
    complexity: RandomComplexity,
    constraint: RandomConstraintMode,
    evolution: RandomEvolutionMode,
) -> int:
    prev_d = prev.pen_offset if prev else None

    if complexity is RandomComplexity.SIMPLE:
        max_factor = 1.2
    elif complexity is RandomComplexity.DENSE:
        max_factor = 2.2
    else:
        max_factor = 1.6

    if constraint is RandomConstraintMode.WILD:
        max_factor *= 1.5

    base_min = 1
    base_max = int(r * max_factor)

    return evolve_value(prev_d, base_min, base_max, evolution)


# ---------------- main flow ---------------- #


MENU_TEXT = (
    "Next action:\n"
    "  [Enter]  Generate next random curve (same settings)\n"
    "  b        Batch: run N random curves with a pause\n"
    "  l        Locks: set fixed values for random runs (R/r/d)\n"
    "  e        Edit R / r / d (with guidance)\n"
    "  s        Session settings (complexity, constraints, evolution, display)\n"
    "  t        Toggle curve type (hypo <-> epi)\n"
    "  p        Print detailed analysis of current curve\n"
    "  q        Quit"
)


def print_session_status(session: SessionState) -> None:
    r_lock = (
        "r"
        if session.locked_fixed_circle_radius is None
        else session.locked_fixed_circle_radius
    )
    rr_lock = (
        "r"
        if session.locked_rolling_circle_radius is None
        else session.locked_rolling_circle_radius
    )
    d_lock = "r" if session.locked_pen_offset is None else session.locked_pen_offset

    print(
        "Current: "
        f"complexity={session.random_complexity.value}, "
        f"constraint={session.random_constraint_mode.value}, "
        f"evolution={session.random_evolution_mode.value}, "
        f"type={session.curve_type.value}, "
        f"color_mode={session.color_mode.value}, "
        f"color={session.color}, "
        f"laps_per_color={session.laps_per_color}, "
        f"spins_per_color={session.spins_per_color}, "
        f"width={session.line_width}, "
        f"speed={session.drawing_speed}, "
        f"locks=R:{r_lock} r:{rr_lock} d:{d_lock}"
    )


def print_menu(session: SessionState) -> None:
    print()
    print(MENU_TEXT)
    print_session_status(session)


def toggle_curve_type(current: SpiroType) -> SpiroType:
    if current is SpiroType.HYPOTROCHOID:
        return SpiroType.EPITROCHOID
    return SpiroType.HYPOTROCHOID


def random_rgb_color() -> tuple[int, int, int]:
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def print_selected_parameters(curve: SpiroCurve) -> None:
    print("\nSelected parameters:")
    print(f"  Fixed Circle Radius (R): {curve.fixed_circle_radius}")
    print(f"  Rolling Circle Radius (r): {curve.rolling_circle_radius}")
    print(f"  Pen Offset (d): {curve.pen_offset}")
    print(f"  Curve Type: {curve.curve_type.value}")
    print(f"  Color: {curve.color}")
    print(f"  Line Width: {curve.line_width}")


def draw_curve(
    turtle_obj: turtle.Turtle,
    curve: SpiroCurve,
    drawing_speed: int,
    color_mode: ColorMode,
    laps_per_color: int,
    spins_per_color: int,
) -> None:
    turtle_obj.clear()
    steps = compute_steps(curve)

    if color_mode not in (
        ColorMode.RANDOM_PER_LAP,
        ColorMode.RANDOM_EVERY_N_LAPS,
        ColorMode.RANDOM_PER_SPIN,
        ColorMode.RANDOM_EVERY_N_SPINS,
    ):
        curve.draw(turtle_obj, steps, drawing_speed)
        return

    screen = turtle_obj.getscreen()
    batch = compute_batch_size(drawing_speed)
    points = curve.generate_points(steps)

    if not points:
        return

    gcd_value = math.gcd(curve.fixed_circle_radius, curve.rolling_circle_radius)

    laps_to_close = max(1, curve.rolling_circle_radius // gcd_value)
    base_lap_segment_size = max(2, len(points) // laps_to_close)

    if curve.curve_type is SpiroType.HYPOTROCHOID:
        spin_numerator = abs(curve.fixed_circle_radius - curve.rolling_circle_radius)
    else:
        spin_numerator = curve.fixed_circle_radius + curve.rolling_circle_radius

    spins_to_close = max(1, spin_numerator // gcd_value)
    base_spin_segment_size = max(2, len(points) // spins_to_close)

    if color_mode is ColorMode.RANDOM_PER_LAP:
        segment_size = base_lap_segment_size
    elif color_mode is ColorMode.RANDOM_EVERY_N_LAPS:
        segment_size = base_lap_segment_size * max(1, laps_per_color)
    elif color_mode is ColorMode.RANDOM_PER_SPIN:
        segment_size = base_spin_segment_size
    else:
        segment_size = base_spin_segment_size * max(1, spins_per_color)

    turtle_obj.penup()
    turtle_obj.pensize(curve.line_width)
    turtle_obj.goto(points[0])
    turtle_obj.pendown()

    index = 1
    while index < len(points):
        turtle_obj.color(random_rgb_color())
        segment_end = min(len(points), index + segment_size)

        while index < segment_end:
            turtle_obj.goto(points[index])
            if index % batch == 0:
                screen.update()
            index += 1

        screen.update()

    screen.update()


def generate_random_curve(session: SessionState) -> SpiroCurve:
    if session.locked_fixed_circle_radius is None:
        R = random_fixed_circle_radius(
            session.last_curve, session.random_evolution_mode
        )
    else:
        R = session.locked_fixed_circle_radius

    if session.locked_rolling_circle_radius is None:
        r = random_rolling_circle_radius(
            R,
            session.last_curve,
            session.random_complexity,
            session.random_constraint_mode,
            session.random_evolution_mode,
        )
    else:
        r = session.locked_rolling_circle_radius

    if session.locked_pen_offset is None:
        d = random_pen_offset(
            r,
            session.last_curve,
            session.random_complexity,
            session.random_constraint_mode,
            session.random_evolution_mode,
        )
    else:
        d = session.locked_pen_offset

    if session.locked_rolling_circle_radius is not None:
        laps = r // math.gcd(R, r)
        if laps > MAX_LAPS_TO_CLOSE:
            print(
                f"Warning: locked r produces {laps} laps (> {MAX_LAPS_TO_CLOSE}). "
                "This may be slow. Consider unlocking r or choosing a different value."
            )

    if session.color_mode is ColorMode.FIXED:
        color = session.color
    else:
        color = random_rgb_color()

    return SpiroCurve(R, r, d, session.curve_type, color, session.line_width)


def edit_geometry(session: SessionState) -> SpiroCurve:
    previous_curve = session.last_curve

    guide_before_fixed_radius(previous_curve)
    R = prompt_positive_int_or_random(
        "fixed_circle_radius",
        previous_curve.fixed_circle_radius if previous_curve else None,
        lambda: random_fixed_circle_radius(
            previous_curve, session.random_evolution_mode
        ),
    )

    guide_before_rolling_radius(R, previous_curve)
    r = prompt_positive_int_or_random(
        "rolling_circle_radius",
        previous_curve.rolling_circle_radius if previous_curve else None,
        lambda: random_rolling_circle_radius(
            R,
            previous_curve,
            session.random_complexity,
            session.random_constraint_mode,
            session.random_evolution_mode,
        ),
    )

    guide_before_pen_offset(R, r, previous_curve)
    d = prompt_positive_int_or_random(
        "pen_offset",
        previous_curve.pen_offset if previous_curve else None,
        lambda: random_pen_offset(
            r,
            previous_curve,
            session.random_complexity,
            session.random_constraint_mode,
            session.random_evolution_mode,
        ),
    )

    # Manual edit uses the session's configured color. (ColorMode still affects random runs.)
    return SpiroCurve(R, r, d, session.curve_type, session.color, session.line_width)


def edit_session_settings(session: SessionState) -> None:
    session.random_complexity = prompt_enum(
        "Random Complexity", RandomComplexity, session.random_complexity
    )
    session.random_constraint_mode = prompt_enum(
        "Constraint Mode", RandomConstraintMode, session.random_constraint_mode
    )
    session.random_evolution_mode = prompt_enum(
        "Evolution Mode", RandomEvolutionMode, session.random_evolution_mode
    )

    session.color_mode = prompt_enum("Color Mode", ColorMode, session.color_mode)
    if session.color_mode is ColorMode.FIXED:
        session.color = prompt_string_with_default("color", session.color)
    elif session.color_mode is ColorMode.RANDOM_EVERY_N_LAPS:
        session.laps_per_color = prompt_positive_int(
            "laps_per_color", default_value=session.laps_per_color
        )
    elif session.color_mode is ColorMode.RANDOM_EVERY_N_SPINS:
        session.spins_per_color = prompt_positive_int(
            "spins_per_color", default_value=session.spins_per_color
        )

    session.line_width = prompt_positive_int(
        "line_width", default_value=session.line_width
    )
    session.drawing_speed = prompt_drawing_speed(session.drawing_speed)


def edit_locks(session: SessionState) -> None:
    print("\nLocks for random runs:")
    print("  Set a number to lock a value during random runs. Enter 'r' to unlock.")
    print("  Press Enter to keep the current lock setting.\n")

    session.locked_fixed_circle_radius = prompt_lock_value(
        "fixed_circle_radius", session.locked_fixed_circle_radius
    )
    session.locked_rolling_circle_radius = prompt_lock_value(
        "rolling_circle_radius", session.locked_rolling_circle_radius
    )
    session.locked_pen_offset = prompt_lock_value(
        "pen_offset", session.locked_pen_offset
    )


def compute_batch_size(speed: int) -> int:
    return 2 ** max(0, speed - 1)


def compute_steps(curve: SpiroCurve) -> int:
    gcd_value = math.gcd(curve.fixed_circle_radius, curve.rolling_circle_radius)
    laps = curve.rolling_circle_radius // gcd_value
    return min(20000, max(NUMBER_OF_STEPS, laps * 300))


def setup_screen():
    screen = turtle.Screen()
    screen.setup(SCREEN_SIZE, SCREEN_SIZE)
    screen.tracer(0, 0)

    turtle.colormode(255)

    t = turtle.Turtle()
    t.hideturtle()
    t.speed(0)

    return screen, t


def main() -> None:
    screen, turtle_obj = setup_screen()
    session = SessionState()

    while True:
        print_menu(session)
        command = input("> ").strip().lower()

        if command == "q":
            break

        if command == "p":
            if session.last_curve is None:
                print(
                    "No curve yet. Press Enter to generate one, or use e to edit values."
                )
            else:
                describe_curve(session.last_curve)
            continue

        if command == "b":
            count = prompt_positive_int("batch_count", default_value=10)
            pause_seconds = prompt_non_negative_float(
                "pause_seconds", default_value=2.0
            )

            for _ in range(count):
                curve = generate_random_curve(session)
                session.last_curve = curve

                print_selected_parameters(curve)
                describe_curve(curve)
                draw_curve(
                    turtle_obj,
                    curve,
                    session.drawing_speed,
                    session.color_mode,
                    session.laps_per_color,
                    session.spins_per_color,
                )
                time.sleep(pause_seconds)

            continue

        if command == "l":
            edit_locks(session)
            continue

        if command == "t":
            session.curve_type = toggle_curve_type(session.curve_type)
            if session.last_curve is not None:
                curve = SpiroCurve(
                    session.last_curve.fixed_circle_radius,
                    session.last_curve.rolling_circle_radius,
                    session.last_curve.pen_offset,
                    session.curve_type,
                    session.color,
                    session.line_width,
                )
                session.last_curve = curve
                draw_curve(
                    turtle_obj,
                    curve,
                    session.drawing_speed,
                    session.color_mode,
                    session.laps_per_color,
                    session.spins_per_color,
                )
            continue

        if command == "s":
            edit_session_settings(session)
            continue

        if command == "e":
            curve = edit_geometry(session)
            session.last_curve = curve
            print_selected_parameters(curve)
            describe_curve(curve)
            draw_curve(
                turtle_obj,
                curve,
                session.drawing_speed,
                session.color_mode,
                session.laps_per_color,
                session.spins_per_color,
            )
            continue

        if command != "":
            print("Unknown command. Press Enter for next random, or use b/l/e/s/t/p/q.")
            continue

        curve = generate_random_curve(session)
        session.last_curve = curve
        print_selected_parameters(curve)
        describe_curve(curve)
        draw_curve(
            turtle_obj,
            curve,
            session.drawing_speed,
            session.color_mode,
            session.laps_per_color,
            session.spins_per_color,
        )

    screen.bye()


if __name__ == "__main__":
    main()
