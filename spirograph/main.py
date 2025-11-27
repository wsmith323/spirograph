import turtle
from enum import Enum
from typing import Dict, List, Tuple

import math

NUMBER_OF_STEPS = 3000
SCREEN_SIZE = 1000


class SpiroType(Enum):
    """Enum representing the type of spirograph curve."""

    HYPO = 'hypo'
    EPI = 'epi'


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

            if self.curve_type is SpiroType.HYPO:
                radius_difference = self.fixed_circle_radius - self.rolling_circle_radius
                primary_angle = t_value
                secondary_angle = (radius_difference / self.rolling_circle_radius) * t_value

                x_coordinate = (
                    radius_difference * math.cos(primary_angle)
                    + self.pen_offset * math.cos(secondary_angle)
                )
                y_coordinate = (
                    radius_difference * math.sin(primary_angle)
                    - self.pen_offset * math.sin(secondary_angle)
                )
            else:
                radius_sum = self.fixed_circle_radius + self.rolling_circle_radius
                primary_angle = t_value
                secondary_angle = (radius_sum / self.rolling_circle_radius) * t_value

                x_coordinate = (
                    radius_sum * math.cos(primary_angle)
                    - self.pen_offset * math.cos(secondary_angle)
                )
                y_coordinate = (
                    radius_sum * math.sin(primary_angle)
                    - self.pen_offset * math.sin(secondary_angle)
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
    words = identifier.split('_')
    label = ' '.join(word.capitalize() for word in words)
    return label


def prompt_positive_int(
    identifier: str,
    default_value: int | None = None,
) -> int:
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


def prompt_string_with_default(identifier: str, default_value: str) -> str:
    """Prompt the user for a string value with a default.

    Args:
        identifier: Identifier used to derive the prompt label.
        default_value: Default value used on empty input.

    Returns:
        The entered string, or the default when input is empty.
    """
    label = make_prompt_label(identifier)
    raw_value = input(f'{label} [{default_value}]: ').strip()
    if raw_value == '':
        return default_value
    return raw_value


def prompt_curve_type() -> SpiroType:
    """Prompt the user to select a curve type.

    Returns:
        The selected SpiroType.

    Raises:
        RuntimeError: If the input loop somehow exits unexpectedly.
    """
    label = make_prompt_label('curve_type')
    while True:
        raw_value = input(f'{label} [hypo/epi]: ').strip().lower()
        if raw_value in ('hypo', 'h'):
            return SpiroType.HYPO
        if raw_value in ('epi', 'e'):
            return SpiroType.EPI
        print('Please enter "hypo" or "epi".')


def prompt_drawing_speed(current_speed: int) -> int:
    """Prompt the user for a turtle drawing speed between 1 and 10.

    Args:
        current_speed: The current drawing speed, used as the default.

    Returns:
        A validated drawing speed between 1 (slow) and 10 (fast).
    """
    label = 'Drawing Speed [1 (slow) - 10 (fast)]'

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
        if raw_value in ('y', 'yes'):
            return True
        if raw_value in ('n', 'no'):
            return False
        print('Please enter "y" or "n".')


def build_presets() -> Dict[str, SpiroCurve]:
    """Build and return the preset spirograph configurations.

    Returns:
        A mapping of preset names to SpiroCurve instances.
    """
    presets: Dict[str, SpiroCurve] = {
        'five_petal_flower': SpiroCurve(
            125,
            75,
            50,
            SpiroType.HYPO,
            'blue',
            1,
        ),
        'tight_starburst': SpiroCurve(
            105,
            30,
            60,
            SpiroType.EPI,
            'red',
            1,
        ),
        'gear_ring': SpiroCurve(
            180,
            45,
            20,
            SpiroType.HYPO,
            'green',
            1,
        ),
        'inner_rosette': SpiroCurve(
            150,
            60,
            30,
            SpiroType.HYPO,
            'purple',
            1,
        ),
        'outer_loop_bloom': SpiroCurve(
            160,
            40,
            80,
            SpiroType.EPI,
            'orange',
            1,
        ),
        'nested_loops': SpiroCurve(
            200,
            70,
            40,
            SpiroType.HYPO,
            'brown',
            1,
        ),
        'spiky_wheel': SpiroCurve(
            170,
            30,
            90,
            SpiroType.EPI,
            'darkblue',
            1,
        ),
        'wide_rosette': SpiroCurve(
            220,
            90,
            30,
            SpiroType.HYPO,
            'magenta',
            1,
        ),
        'compact_flower': SpiroCurve(
            120,
            50,
            60,
            SpiroType.EPI,
            'cyan',
            1,
        ),
        'thin_rings': SpiroCurve(
            210,
            35,
            15,
            SpiroType.HYPO,
            'black',
            1,
        ),
    }
    return presets


def choose_preset_or_custom(presets: Dict[str, SpiroCurve]) -> SpiroCurve | None:
    """Allow the user to choose a preset or enter custom values.

    Args:
        presets: Mapping of preset names to SpiroCurve instances.

    Returns:
        A SpiroCurve instance chosen or defined by the user, or None if no valid choice was made.
    """
    preset_items = list(presets.items())

    print('\nAvailable presets:')
    for index, (name, _) in enumerate(preset_items, start=1):
        print(f'{index}. {name}')

    custom_option_index = len(preset_items) + 1
    print(f'{custom_option_index}. Custom values')

    raw_choice = input(
        f'Select an option [1-{custom_option_index}] (empty to exit): ',
    ).strip()

    if raw_choice == '':
        print('No selection entered. Exiting.')
        return None

    try:
        choice_index = int(raw_choice)
    except ValueError:
        print('No valid preset selected. Exiting.')
        return None

    if 1 <= choice_index <= len(preset_items):
        selected_name, selected_curve = preset_items[choice_index - 1]
        print(f'You selected preset: {selected_name}')
        return selected_curve

    if choice_index == custom_option_index:
        print('Entering custom values.')
        return create_custom_curve()

    print('No valid preset selected. Exiting.')
    return None


def create_custom_curve() -> SpiroCurve:
    """Prompt the user for all curve parameters and build a SpiroCurve.

    Returns:
        A new SpiroCurve instance created from user input.
    """
    fixed_circle_radius = prompt_positive_int('fixed_circle_radius')
    rolling_circle_radius = prompt_positive_int('rolling_circle_radius')
    pen_offset = prompt_positive_int('pen_offset')
    curve_type = prompt_curve_type()
    color = prompt_string_with_default('color', 'black')
    line_width = prompt_positive_int('line_width', default_value=1)

    return SpiroCurve(
        fixed_circle_radius,
        rolling_circle_radius,
        pen_offset,
        curve_type,
        color,
        line_width,
    )


def setup_screen() -> tuple[turtle.Screen, turtle.Turtle]:
    """Initialize the turtle screen and drawing turtle.

    Returns:
        A tuple of (screen, turtle_instance) ready for drawing.
    """
    screen = turtle.Screen()
    screen.setup(width=SCREEN_SIZE, height=SCREEN_SIZE)
    screen.title('Spirograph Simulator')
    screen.bgcolor('white')
    screen.tracer(0, 0)

    turtle_obj = turtle.Turtle()
    turtle_obj.hideturtle()
    turtle_obj.speed(0)

    return screen, turtle_obj


def main() -> None:
    """Entry point for the spirograph simulator."""
    presets = build_presets()
    screen, turtle_obj = setup_screen()
    drawing_speed = 1

    while True:
        spiro_curve = choose_preset_or_custom(presets)
        if spiro_curve is None:
            break

        drawing_speed = prompt_drawing_speed(drawing_speed)

        turtle_obj.clear()
        turtle_obj.penup()
        turtle_obj.goto(0.0, 0.0)
        turtle_obj.pendown()

        spiro_curve.draw(turtle_obj, NUMBER_OF_STEPS, drawing_speed)

    print('Done.')
    screen.update()
    screen.bye()


if __name__ == '__main__':
    main()