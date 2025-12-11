import turtle
from enum import Enum
from typing import List, Tuple

import math

NUMBER_OF_STEPS = 3000
SCREEN_SIZE = 1000


class SpiroType(Enum):
    """Enum representing the type of spirograph curve."""

    HYPOTROCHOID = "hypotrochoid"
    EPITROCHOID = "epitrochoid"


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

                x_coordinate = radius_difference * math.cos(
                    primary_angle
                ) + self.pen_offset * math.cos(secondary_angle)
                y_coordinate = radius_difference * math.sin(
                    primary_angle
                ) - self.pen_offset * math.sin(secondary_angle)
            else:
                radius_sum = self.fixed_circle_radius + self.rolling_circle_radius
                primary_angle = t_value
                secondary_angle = (radius_sum / self.rolling_circle_radius) * t_value

                x_coordinate = radius_sum * math.cos(
                    primary_angle
                ) - self.pen_offset * math.cos(secondary_angle)
                y_coordinate = radius_sum * math.sin(
                    primary_angle
                ) - self.pen_offset * math.sin(secondary_angle)

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

        raw_value = input(
            f"Select {label} [1-2] [{default_index}]: ",
        ).strip()

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
    # Clamp just in case.
    if drawing_speed <= 1:
        return 1
    if drawing_speed >= 10:
        return 2**9  # 512

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


def create_custom_curve(previous_curve: SpiroCurve | None) -> SpiroCurve:
    """Prompt the user for all curve parameters and build a SpiroCurve.

    Args:
        previous_curve: Last custom curve used for providing default values, or None.

    Returns:
        A new SpiroCurve instance created from user input.
    """
    print("\nConfigure your spirograph curve.")
    print(
        "  Fixed circle radius (R) controls overall size; try 100-300 for a 1000x1000 window."
    )
    print(
        "  Rolling circle radius (r) controls lobes and detail; try 20-150 and keep r < R."
    )
    print("  Pen offset (d) controls spikiness:")
    print("    - d << r: very soft, low-amplitude petals")
    print("    - d ≈ r: classic spiky flower")
    print("    - d > r: complex, loopy patterns\n")

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

    print("Fixed circle radius (R): overall size of the pattern.")
    fixed_circle_radius = prompt_positive_int(
        "fixed_circle_radius",
        default_value=fixed_circle_radius_default,
    )
    print("Rolling circle radius (r): smaller r ⇒ more lobes and finer detail.")
    rolling_circle_radius = prompt_positive_int(
        "rolling_circle_radius",
        default_value=rolling_circle_radius_default,
    )
    print("Pen offset (d): distance from the rolling circle center to the pen.")
    pen_offset = prompt_positive_int(
        "pen_offset",
        default_value=pen_offset_default,
    )
    curve_type = prompt_curve_type(curve_type_default)
    color = prompt_string_with_default("color", color_default)
    line_width = prompt_positive_int("line_width", default_value=line_width_default)

    return SpiroCurve(
        fixed_circle_radius,
        rolling_circle_radius,
        pen_offset,
        curve_type,
        color,
        line_width,
    )


# Helper to describe the curve's properties
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

    while True:
        print()
        if not ask_yes_no("Draw a new curve? (y/n): "):
            break

        spiro_curve = create_custom_curve(last_custom_curve)
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

        spiro_curve.draw(turtle_obj, NUMBER_OF_STEPS, drawing_speed)

    print("Done.")
    screen.update()
    screen.bye()


if __name__ == "__main__":
    main()
