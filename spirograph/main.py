import random
import turtle
from enum import Enum
from typing import Callable, List, Tuple

import math

NUMBER_OF_STEPS = 3000
SCREEN_SIZE = 1000


class SpiroType(Enum):
    """Enum representing the type of spirograph curve."""

    HYPOTROCHOID = "hypotrochoid"
    EPITROCHOID = "epitrochoid"


class RandomComplexity(Enum):
    """Enum representing the desired complexity for randomized suggestions."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    DENSE = "dense"


class RandomConstraintMode(Enum):
    """Enum representing whether random suggestions should stay physical-ish or explore extended space."""

    PHYSICAL = "physical"
    EXTENDED = "extended"
    WILD = "wild"


class SpiroCurve:
    """Represents a single spirograph curve configuration and behavior.

    Attributes:
        fixed_circle_radius: Radius of the stationary (fixed) circle.
        rolling_circle_radius: Radius of the rolling circle.
        pen_offset: Distance from the rolling circle center to the pen.
        curve_type: Type of curve, hypotrochoid or epitrochoid.
        color: Line color for drawing.
        line_width: Line width for drawing.
    """

    def __init__(
        self,
        fixed_circle_radius: int,
        rolling_circle_radius: int,
        pen_offset: int,
        curve_type: SpiroType,
        color: str,
        line_width: int,
    ) -> None:
        self.fixed_circle_radius = fixed_circle_radius
        self.rolling_circle_radius = rolling_circle_radius
        self.pen_offset = pen_offset
        self.curve_type = curve_type
        self.color = color
        self.line_width = line_width

    def _compute_period(self) -> float:
        """Compute the full period in radians for the curve.

        Returns:
            The angular period (in radians) needed to close the curve.
        """
        greatest_common_divisor = math.gcd(
            self.fixed_circle_radius,
            self.rolling_circle_radius,
        )
        rotation_ratio = self.rolling_circle_radius // greatest_common_divisor
        period = 2.0 * math.pi * rotation_ratio
        return period

    def generate_points(self, number_of_steps: int) -> List[Tuple[float, float]]:
        """Generate points along the spirograph curve.

        Args:
            number_of_steps: Number of steps to use for sampling the curve.

        Returns:
            A list of (x, y) coordinate pairs describing the curve.
        """
        period = self._compute_period()
        points: List[Tuple[float, float]] = []

        for step_index in range(number_of_steps + 1):
            t_value = (step_index / number_of_steps) * period

            if self.curve_type is SpiroType.HYPOTROCHOID:
                radius_difference = (
                    self.fixed_circle_radius - self.rolling_circle_radius
                )
                primary_angle = t_value
                secondary_angle = (
                    radius_difference / self.rolling_circle_radius
                ) * t_value

                x_coordinate = (radius_difference * math.cos(primary_angle)) + (
                    self.pen_offset * math.cos(secondary_angle)
                )
                y_coordinate = (radius_difference * math.sin(primary_angle)) - (
                    self.pen_offset * math.sin(secondary_angle)
                )
            else:
                radius_sum = self.fixed_circle_radius + self.rolling_circle_radius
                primary_angle = t_value
                secondary_angle = (radius_sum / self.rolling_circle_radius) * t_value

                x_coordinate = (radius_sum * math.cos(primary_angle)) - (
                    self.pen_offset * math.cos(secondary_angle)
                )
                y_coordinate = (radius_sum * math.sin(primary_angle)) - (
                    self.pen_offset * math.sin(secondary_angle)
                )

            points.append((x_coordinate, y_coordinate))

        return points

    def draw(
        self,
        turtle_obj: turtle.Turtle,
        number_of_steps: int,
        drawing_speed: int,
    ) -> None:
        """Draw the spirograph curve using a turtle object.

        Args:
            turtle_obj: The turtle used to draw the curve.
            number_of_steps: Number of steps to use for sampling the curve.
            drawing_speed: Logical drawing speed chosen by the user (1 slowest, 10 fastest).
        """
        screen = turtle_obj.getscreen()
        batch_size = compute_batch_size(drawing_speed)

        points = self.generate_points(number_of_steps)

        turtle_obj.penup()
        turtle_obj.color(self.color)
        turtle_obj.pensize(self.line_width)

        if not points:
            return

        first_x, first_y = points[0]
        turtle_obj.goto(first_x, first_y)
        turtle_obj.pendown()

        for index, (x_coordinate, y_coordinate) in enumerate(points[1:], start=1):
            turtle_obj.goto(x_coordinate, y_coordinate)
            if index % batch_size == 0:
                screen.update()

        screen.update()


def make_prompt_label(identifier: str) -> str:
    """Convert an identifier into a human-friendly prompt label.

    Args:
        identifier: The identifier to convert.

    Returns:
        A human-readable label derived from the identifier.
    """
    words = identifier.split("_")
    label = " ".join(word.capitalize() for word in words)
    return label


def prompt_positive_int(
    identifier: str,
    default_value: int | None = None,
) -> int:  # type: ignore
    """Prompt the user for a positive integer based on an identifier.

    Args:
        identifier: Identifier used to derive the prompt label.
        default_value: Optional default value returned on empty input.

    Returns:
        A validated positive integer entered by the user.
    """
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


def prompt_positive_int_or_random(
    identifier: str,
    default_value: int | None,
    random_value_factory: Callable[[], int],
) -> int:  # type: ignore
    """Prompt for a positive integer or accept 'r'/'rand' for a random suggestion."""
    label = make_prompt_label(identifier)
    while True:
        if default_value is not None:
            prompt_str = f"{label} [{default_value}] (or 'r' for random): "
        else:
            prompt_str = f"{label} (or 'r' for random): "
        raw_value = input(prompt_str).strip()

        if raw_value.lower() in ("r", "rand"):
            value = random_value_factory()
            print(f"Selected random {label}: {value}")
            return value

        if raw_value == "" and default_value is not None:
            return default_value

        try:
            parsed_value = int(raw_value)
        except ValueError:
            print("Please enter a valid integer or 'r' for random.")
            continue

        if parsed_value <= 0:
            print("Please enter a positive integer.")
            continue

        return parsed_value


def prompt_string_with_default(identifier: str, default_value: str) -> str:
    """Prompt the user for a string value with a default.

    Args:
        identifier: Identifier used to derive the prompt label.
        default_value: Default value used on empty input.

    Returns:
        The entered string, or the default when input is empty.
    """
    label = make_prompt_label(identifier)
    raw_value = input(f"{label} [{default_value}]: ").strip()
    if raw_value == "":
        return default_value
    return raw_value


def prompt_curve_type(default_type: SpiroType | None = None) -> SpiroType:  # type: ignore
    """Prompt the user to select a curve type.

    Args:
        default_type: Optional default curve type returned on empty input.

    Returns:
        The selected SpiroType.
    """
    label = make_prompt_label("curve_type")

    while True:
        print(f"{label}:")
        print("  1. Hypotrochoid (rolling inside fixed circle)")
        print("  2. Epitrochoid (rolling outside fixed circle)")

        if default_type is not None:
            default_index = 1 if default_type is SpiroType.HYPOTROCHOID else 2
        else:
            default_index = 1

        raw_value = input(f"Select {label} [1-2] [{default_index}]: ").strip()

        if raw_value == "":
            if default_type is not None:
                return default_type
            return SpiroType.HYPOTROCHOID

        try:
            choice_index = int(raw_value)
        except ValueError:
            print("Please enter 1 or 2.")
            continue

        if choice_index == 1:
            return SpiroType.HYPOTROCHOID
        if choice_index == 2:
            return SpiroType.EPITROCHOID

        print("Please enter 1 or 2.")


def prompt_random_complexity(
    default_complexity: RandomComplexity | None = None,
) -> RandomComplexity:  # type: ignore
    """Prompt the user to select a complexity level for random suggestions.

    Args:
        default_complexity: Optional default complexity returned on empty input.

    Returns:
        The selected RandomComplexity.
    """
    label = make_prompt_label("random_complexity")

    while True:
        print(f"{label}:")
        print("  1. Simple (clean, fewer lobes)")
        print("  2. Medium (usually pretty)")
        print("  3. Dense (more lobes, more intricate)")

        if default_complexity is RandomComplexity.SIMPLE:
            default_index = 1
        elif default_complexity is RandomComplexity.DENSE:
            default_index = 3
        else:
            default_index = 2

        raw_value = input(f"Select {label} [1-3] [{default_index}]: ").strip()

        if raw_value == "":
            if default_complexity is not None:
                return default_complexity
            return RandomComplexity.MEDIUM

        try:
            choice_index = int(raw_value)
        except ValueError:
            print("Please enter 1, 2, or 3.")
            continue

        if choice_index == 1:
            return RandomComplexity.SIMPLE
        if choice_index == 2:
            return RandomComplexity.MEDIUM
        if choice_index == 3:
            return RandomComplexity.DENSE

        print("Please enter 1, 2, or 3.")


def prompt_random_constraint_mode(
    default_mode: RandomConstraintMode | None = None,
) -> RandomConstraintMode:  # type: ignore
    """Prompt the user to select a constraint mode for random suggestions.

    Args:
        default_mode: Optional default mode returned on empty input.

    Returns:
        The selected RandomConstraintMode.
    """
    label = make_prompt_label("random_constraint_mode")

    while True:
        print(f"{label}:")
        print("  1. Physical-ish (stay close to spirograph kit constraints)")
        print("  2. Extended (allow r > R and d > r; may be chaotic)")
        print("  3. Wild (very permissive; frequently chaotic)")

        if default_mode is RandomConstraintMode.PHYSICAL:
            default_index = 1
        elif default_mode is RandomConstraintMode.WILD:
            default_index = 3
        else:
            default_index = 2

        raw_value = input(f"Select {label} [1-3] [{default_index}]: ").strip()

        if raw_value == "":
            if default_mode is not None:
                return default_mode
            return RandomConstraintMode.EXTENDED

        try:
            choice_index = int(raw_value)
        except ValueError:
            print("Please enter 1, 2, or 3.")
            continue

        if choice_index == 1:
            return RandomConstraintMode.PHYSICAL
        if choice_index == 2:
            return RandomConstraintMode.EXTENDED
        if choice_index == 3:
            return RandomConstraintMode.WILD

        print("Please enter 1, 2, or 3.")


def prompt_drawing_speed(current_speed: int) -> int:  # type: ignore
    """Prompt the user for a turtle drawing speed between 1 and 10.

    Args:
        current_speed: The current drawing speed, used as the default.

    Returns:
        A validated drawing speed between 1 (slow) and 10 (fast).
    """
    label = "Drawing Speed [1 (slow) - 10 (fast)]"

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


def compute_batch_size(drawing_speed: int) -> int:
    """Compute the batch size for screen updates based on drawing speed.

    Args:
        drawing_speed: Logical drawing speed from 1 (slowest) to 10 (fastest).

    Returns:
        The number of points to draw between screen updates.
    """
    if drawing_speed <= 1:
        return 1
    if drawing_speed >= 10:
        return 2**9

    return 2 ** (drawing_speed - 1)


def ask_yes_no(prompt_text: str) -> bool:
    """Ask a yes/no question and return the answer as a boolean.

    Args:
        prompt_text: Text to show when asking the question.

    Returns:
        True if the user answered yes, otherwise False.
    """
    while True:
        raw_value = input(prompt_text).strip().lower()
        if raw_value in ("y", "yes"):
            return True
        if raw_value in ("n", "no"):
            return False
        print('Please enter "y" or "n".')


def random_fixed_circle_radius(previous_curve: "SpiroCurve | None") -> int:
    """Generate a random fixed circle radius in a generally usable range."""
    if previous_curve is None:
        return random.randint(120, 280)
    prev = previous_curve.fixed_circle_radius
    low = max(100, int(round(prev * 0.7)))
    high = min(320, int(round(prev * 1.3)))
    return random.randint(low, high)


def random_rolling_circle_radius(
    fixed_circle_radius: int,
    complexity: RandomComplexity,
    constraint_mode: RandomConstraintMode,
) -> int:
    """Generate a random rolling radius, optionally exploring extended and wild ranges."""
    R = fixed_circle_radius

    if complexity is RandomComplexity.SIMPLE:
        low_ratio, high_ratio = 2.5, 4.5
        min_gcd = 2
    elif complexity is RandomComplexity.DENSE:
        low_ratio, high_ratio = 5.0, 14.0
        min_gcd = 1
    else:
        low_ratio, high_ratio = 3.5, 9.0
        min_gcd = 1 if constraint_mode is not RandomConstraintMode.PHYSICAL else 2

    a = random.uniform(low_ratio, high_ratio)
    b = random.uniform(low_ratio, high_ratio)
    ratio = (a + b) / 2

    r_from_ratio = max(2, int(round(R / ratio)))

    if constraint_mode is RandomConstraintMode.PHYSICAL:
        r = min(R - 1, r_from_ratio)
    else:
        if constraint_mode is RandomConstraintMode.WILD:
            inversion_probability = 0.55
            max_multiplier = 3.0
        else:
            inversion_probability = 0.35
            max_multiplier = 2.0

        if random.random() < inversion_probability:
            high = max(2, int(round(R * max_multiplier)))
            r = random.randint(R, high)
        else:
            r = r_from_ratio

        r = max(2, r)

    search_radius = 20 if constraint_mode is RandomConstraintMode.WILD else 14
    for delta in range(0, search_radius + 1):
        for sign in (-1, 1):
            r_candidate = r + sign * delta
            if r_candidate > 1:
                if math.gcd(R, r_candidate) >= min_gcd:
                    return r_candidate

    return r


def random_pen_offset(
    rolling_circle_radius: int,
    complexity: RandomComplexity,
    constraint_mode: RandomConstraintMode,
) -> int:
    """Generate a random pen offset, optionally allowing d > r in extended and wild modes."""
    r = rolling_circle_radius

    if complexity is RandomComplexity.SIMPLE:
        low_factor, high_factor = 0.45, 1.05
    elif complexity is RandomComplexity.DENSE:
        low_factor, high_factor = 0.9, 2.2
    else:
        low_factor, high_factor = 0.6, 1.6

    if constraint_mode is RandomConstraintMode.PHYSICAL:
        max_factor = 1.3
    elif constraint_mode is RandomConstraintMode.WILD:
        max_factor = 3.0
    else:
        max_factor = 2.0

    a = random.uniform(low_factor, high_factor)
    b = random.uniform(low_factor, high_factor)
    factor = (a + b) / 2

    d = int(round(r * factor))
    d = max(1, min(d, int(round(r * max_factor))))
    return d


def create_custom_curve(
    previous_curve: SpiroCurve | None,
    previous_random_complexity: RandomComplexity | None,
    previous_random_constraint_mode: RandomConstraintMode | None,
) -> tuple[SpiroCurve, RandomComplexity, RandomConstraintMode]:
    """Prompt the user for all curve parameters and build a SpiroCurve.

    Args:
        previous_curve: Last custom curve used for providing default values, or None.
        previous_random_complexity: Last used random complexity, or None.
        previous_random_constraint_mode: Last used random constraint mode, or None.

    Returns:
        A tuple of (SpiroCurve, RandomComplexity, RandomConstraintMode) created from user input.
    """
    if previous_curve is not None:
        fixed_circle_radius_default = previous_curve.fixed_circle_radius
        rolling_circle_radius_default = previous_curve.rolling_circle_radius
        pen_offset_default = previous_curve.pen_offset
        curve_type_default = previous_curve.curve_type
        color_default = previous_curve.color
        line_width_default = previous_curve.line_width
    else:
        fixed_circle_radius_default = None
        rolling_circle_radius_default = None
        pen_offset_default = None
        curve_type_default = None
        color_default = "black"
        line_width_default = 1

    random_complexity = prompt_random_complexity(
        previous_random_complexity or RandomComplexity.MEDIUM
    )
    random_constraint_mode = prompt_random_constraint_mode(
        previous_random_constraint_mode or RandomConstraintMode.EXTENDED
    )

    guide_before_fixed_radius(previous_curve)
    fixed_circle_radius = prompt_positive_int_or_random(
        "fixed_circle_radius",
        default_value=fixed_circle_radius_default,
        random_value_factory=lambda: random_fixed_circle_radius(previous_curve),
    )

    guide_before_rolling_radius(fixed_circle_radius, previous_curve)
    rolling_circle_radius = prompt_positive_int_or_random(
        "rolling_circle_radius",
        default_value=rolling_circle_radius_default,
        random_value_factory=lambda: random_rolling_circle_radius(
            fixed_circle_radius,
            random_complexity,
            random_constraint_mode,
        ),
    )

    guide_before_pen_offset(fixed_circle_radius, rolling_circle_radius, previous_curve)
    pen_offset = prompt_positive_int_or_random(
        "pen_offset",
        default_value=pen_offset_default,
        random_value_factory=lambda: random_pen_offset(
            rolling_circle_radius,
            random_complexity,
            random_constraint_mode,
        ),
    )

    curve_type = prompt_curve_type(curve_type_default)
    color = prompt_string_with_default("color", color_default)
    line_width = prompt_positive_int("line_width", default_value=line_width_default)

    return (
        SpiroCurve(
            fixed_circle_radius,
            rolling_circle_radius,
            pen_offset,
            curve_type,
            color,
            line_width,
        ),
        random_complexity,
        random_constraint_mode,
    )


def describe_curve(curve: SpiroCurve) -> None:
    """Print guidance about how the current parameters shape the curve.

    Args:
        curve: The spirograph curve to describe.
    """
    fixed = curve.fixed_circle_radius
    rolling = curve.rolling_circle_radius
    offset = curve.pen_offset

    gcd_value = math.gcd(fixed, rolling)
    ratio = fixed / rolling
    offset_factor = offset / rolling

    approx_petals = fixed // gcd_value
    rotations_to_close = rolling // gcd_value

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
    else:
        curve_kind = "rolling outside fixed circle (epitrochoid)"

    print("\nCurve guidance:")
    print(f"  Radius ratio R/r: {ratio:.3f} → {ratio_desc}")
    print(f"  Offset factor d/r: {offset_factor:.3f} → {offset_desc}")
    print(f"  gcd(R, r): {gcd_value} → approx petals: {approx_petals}")
    print(f"  Rotations of rolling circle until closure: ~{rotations_to_close}")
    print(f"  Curve type: {curve_kind}\n")


def compute_number_of_steps_for_curve(curve: SpiroCurve) -> int:
    """Compute an adaptive number of steps for sampling based on closure and potential complexity.

    Args:
        curve: Curve to be drawn.

    Returns:
        The number of steps to use for sampling points.
    """
    gcd_value = math.gcd(curve.fixed_circle_radius, curve.rolling_circle_radius)
    closure_rotations = curve.rolling_circle_radius // gcd_value
    scaled_steps = max(NUMBER_OF_STEPS, closure_rotations * 300)
    return min(20000, scaled_steps)


def guide_before_fixed_radius(previous_curve: SpiroCurve | None) -> None:
    """Provide brief guidance before entering the fixed circle radius (R).

    Args:
        previous_curve: The last curve used, if any.
    """
    print("\nFixed circle radius (R):")
    if previous_curve is None:
        print(
            "  R controls overall size. Larger R fills more of the window; smaller R keeps the pattern more compact."
        )
        print(
            "  This parameter scales the entire figure uniformly. Try values in the 100–300 range for a typical window."
        )
        print(
            "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
        )
        return

    prev_R = previous_curve.fixed_circle_radius

    print(f"  Previous run: R = {prev_R}.")
    print(
        "  Using the default value will produce a curve with a similar overall size to the last run."
    )
    print(
        f"  Choosing R larger than {prev_R} will scale the pattern up uniformly; choosing R smaller will scale it down."
    )
    print(
        "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
    )


def guide_before_rolling_radius(
    fixed_circle_radius: int,
    previous_curve: SpiroCurve | None,
) -> None:
    """Provide brief guidance before entering the rolling circle radius (r).

    Args:
        fixed_circle_radius: The selected fixed circle radius R for this run.
        previous_curve: The last curve used, if any.
    """
    R = fixed_circle_radius
    print("\nRolling circle radius (r):")
    print(f"  Current R = {R}.")

    if previous_curve is None:
        print(
            "  In a physical kit, hypotrochoids typically use r < R, but this program allows any positive r.\n"
            "Smaller r (relative to R) gives more lobes and a denser pattern.\n"
            "Values near R or above R often create more dramatic loops and self-intersections."
        )
        print(
            "  Ratios R/r that are non-integers tend to look more intricate and dense than simple integer ratios."
        )
        print(
            "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
        )
        return

    prev_r = previous_curve.rolling_circle_radius

    ratio_if_unchanged = R / prev_r
    gcd_if_unchanged = math.gcd(R, prev_r)
    petals_if_unchanged = R // gcd_if_unchanged
    rotations_if_unchanged = prev_r // gcd_if_unchanged

    print(
        f"  Default r is {prev_r}. With current R, R/r would be ≈ {ratio_if_unchanged:.3f}."
    )
    print(
        f"  That would give roughly {petals_if_unchanged} lobes and close after about {rotations_if_unchanged} rotations."
    )

    if abs(ratio_if_unchanged - round(ratio_if_unchanged)) < 1e-6:
        print("  Integer-like R/r → clean symmetry, less visual noise.")
    else:
        print("  Non-integer R/r → more intricate, visually denser pattern.")

    print(
        f"  Choosing r smaller than {prev_r} increases R/r → more lobes and a denser figure."
    )
    print(
        f"  Choosing r larger than {prev_r} decreases R/r → fewer lobes and a simpler figure."
    )
    print(
        "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
    )


def guide_before_pen_offset(
    fixed_circle_radius: int,
    rolling_circle_radius: int,
    previous_curve: SpiroCurve | None,
) -> None:
    """Provide brief guidance before entering the pen offset (d).

    Args:
        fixed_circle_radius: The selected fixed circle radius R for this run.
        rolling_circle_radius: The selected rolling circle radius r for this run.
        previous_curve: The last curve used, if any.
    """
    R = fixed_circle_radius
    r = rolling_circle_radius

    print("\nPen offset (d):")
    print(f"  Current R = {R}, r = {r}.")

    gcd_value = math.gcd(R, r)
    ratio = R / r
    approx_petals = R // gcd_value
    rotations_to_close = r // gcd_value

    if ratio < 2.0:
        ratio_desc = "very simple (few large lobes)"
    elif ratio < 4.0:
        ratio_desc = "moderate complexity (visible lobes)"
    else:
        ratio_desc = "high complexity (many lobes; dense pattern)"

    if abs(ratio - round(ratio)) < 1e-6:
        ratio_symmetry = "integer-like ratio → cleaner symmetry"
    else:
        ratio_symmetry = "non-integer ratio → more intricate/dense"

    print(f"  So far: R/r ≈ {ratio:.3f} → {ratio_desc}; {ratio_symmetry}.")
    print(f"  So far: gcd(R, r) = {gcd_value} → approx lobes ≈ {approx_petals}.")
    print(f"  So far: closes after ~{rotations_to_close} rolling-circle rotations.\n")

    if previous_curve is None:
        print(
            "  The key quantity is d/r: small d/r → softer, low-amplitude petals;\n"
            "d/r around 1 → classic spiky look; d/r > 1 → loops and more chaotic detail."
        )
        print(
            "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
        )
        return

    prev_d = previous_curve.pen_offset
    offset_factor_if_unchanged = prev_d / r

    print(
        f"  Default d is {prev_d}. With current r, d/r would be ≈ {offset_factor_if_unchanged:.3f}."
    )

    if offset_factor_if_unchanged < 0.3:
        desc = "very soft, low-amplitude petals"
    elif offset_factor_if_unchanged < 0.9:
        desc = "softer petals with less extreme spikes"
    elif offset_factor_if_unchanged < 1.1:
        desc = "a classic spiky outline"
    elif offset_factor_if_unchanged < 1.6:
        desc = "complex loops and self-intersections"
    else:
        desc = "very loopy, chaotic-looking structures"

    print(f"  That setting would give {desc}.")
    print(
        f"  Choosing d smaller than {prev_d} will generally soften the pattern (lower d/r)."
    )
    print(
        f"  Choosing d larger than {prev_d} will exaggerate spikes/loops (higher d/r)."
    )
    print(
        "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
    )


def setup_screen() -> tuple[turtle._Screen, turtle.Turtle]:
    """Initialize the turtle screen and drawing turtle.

    Returns:
        A tuple of (screen, turtle_instance) ready for drawing.
    """
    screen = turtle.Screen()
    screen.setup(width=SCREEN_SIZE, height=SCREEN_SIZE)
    screen.title("Spirograph Simulator")
    screen.bgcolor("white")
    screen.tracer(0, 0)

    turtle_obj = turtle.Turtle()
    turtle_obj.hideturtle()
    turtle_obj.speed(0)

    return screen, turtle_obj


def main() -> None:
    """Entry point for the spirograph simulator."""
    screen, turtle_obj = setup_screen()
    drawing_speed = 1
    last_custom_curve: SpiroCurve | None = None
    last_random_complexity: RandomComplexity | None = None
    last_random_constraint_mode: RandomConstraintMode | None = None

    while True:
        spiro_curve, last_random_complexity, last_random_constraint_mode = (
            create_custom_curve(
                last_custom_curve,
                last_random_complexity,
                last_random_constraint_mode,
            )
        )
        last_custom_curve = spiro_curve

        describe_curve(spiro_curve)

        drawing_speed = prompt_drawing_speed(drawing_speed)

        print("\nSelected parameters:")
        print(f"  Fixed Circle Radius: {spiro_curve.fixed_circle_radius}")
        print(f"  Rolling Circle Radius: {spiro_curve.rolling_circle_radius}")
        print(f"  Pen Offset: {spiro_curve.pen_offset}")
        print(f"  Curve Type: {spiro_curve.curve_type.value}")
        print(f"  Color: {spiro_curve.color}")
        print(f"  Line Width: {spiro_curve.line_width}")
        print(f"  Drawing Speed: {drawing_speed}")

        turtle_obj.clear()
        turtle_obj.penup()
        turtle_obj.goto(0.0, 0.0)
        turtle_obj.pendown()

        number_of_steps = compute_number_of_steps_for_curve(spiro_curve)
        spiro_curve.draw(turtle_obj, number_of_steps, drawing_speed)

        print()
        if not ask_yes_no("Draw a new curve? (y/n): "):
            break

    print("Done.")
    screen.update()
    screen.bye()


if __name__ == "__main__":
    main()
