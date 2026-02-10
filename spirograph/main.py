import time

import math

from spirograph.generation import SpiroType
from .console_ui.guidance import (
    describe_curve,
    guide_before_fixed_radius,
    guide_before_pen_offset,
    guide_before_rolling_radius,
)
from .console_ui.prompts import (
    compute_steps,
    make_prompt_label,
    parse_color,
    prompt_drawing_speed,
    prompt_enum,
    prompt_lock_value,
    prompt_non_negative_float,
    prompt_positive_float,
    prompt_positive_int,
    prompt_positive_int_or_random,
)
from .console_ui.random import (
    random_fixed_circle_radius,
    random_pen_offset,
    random_rolling_circle_radius,
)
from .console_ui.session import ConsoleUiSessionState
from .generation.circular_generator import CircularSpiroGenerator
from .generation.registry import GeneratorRegistry
from .generation.requests import CircularSpiroRequest
from .orchestration import CurveOrchestrator
from .rendering import (
    RenderPlanBuilder,
    RenderSettings,
    TurtleGraphicsRenderer,
    Color,
    ColorMode,
)

MAX_LAPS_TO_CLOSE = 200

MENU_TEXT = """
Next action:
Geometry:
    m - Manually input R, r, and d
    a - Print analysis of current curve
Session:
    e - Edit Session settings
    p - Print session settings
Random:
    b - Batch: run N random curves with a pause in between
    l - Locks: set fixed values for random runs (R/r/d)
    [Enter] - Generate next random curve (same settings)
Program:
    q - Quit
"""

SESSION_MENU_TEXT = """
Session settings:
    1 - Curve type
    2 - Random constraint mode
    3 - Random evolution mode
    4 - Color mode
    5 - Color (only when mode is fixed)
    6 - Laps per color (only when mode is random_every_n_laps)
    7 - Spins per color (only when mode is random_every_n_spins)
    8 - Line width
    9 - Drawing speed
    p - Print session settings
    [Enter] / q - Done
"""


def compute_laps_to_close(fixed_radius: int, rolling_radius: int) -> int:
    gcd_value = math.gcd(fixed_radius, rolling_radius)
    return max(1, rolling_radius // gcd_value) if gcd_value else 1


def prompt_color_value(current_color: Color) -> Color:
    label = make_prompt_label('color')
    raw_value = input(f'{label} [{current_color.as_hex}]: ').strip()
    if raw_value == '':
        return current_color
    return parse_color(raw_value, current_color)


def print_selected_parameters(request: CircularSpiroRequest, session: ConsoleUiSessionState) -> None:
    print(
        f"""
Selected parameters:
Fixed Circle Radius (R): {int(request.fixed_radius)}
Rolling Circle Radius (r): {int(request.rolling_radius)}
Pen Offset (d): {int(request.pen_distance)}
Curve Type: {request.curve_type.value}
Color Mode: {session.color_mode.value}
Color: {session.color.as_hex}
Line Width: {session.line_width}
    """
    )


def print_session_status(session: ConsoleUiSessionState) -> None:
    r_lock = 'r' if session.locked_fixed_radius is None else session.locked_fixed_radius
    rr_lock = 'r' if session.locked_rolling_radius is None else session.locked_rolling_radius
    d_lock = 'r' if session.locked_pen_distance is None else session.locked_pen_distance

    print(f"""
Current session settings:
Geometry:     
    Curve Type: {session.curve_type.value.title()}
Random:
    Constraint: {session.random_constraint_mode.value.title()}
    Evolution: {session.random_evolution_mode.value.title()}
    Locks:
        R:{r_lock}
        r:{rr_lock}
        d:{d_lock}
Color:
    Mode: {session.color_mode.value}
    Fixed color: {session.color.as_hex}
    Laps per color: {session.laps_per_color}
    Spins per color: {session.spins_per_color}
Drawing:
    Line width: {session.line_width}
    Drawing speed: {session.drawing_speed}
""")


def print_menu(session: ConsoleUiSessionState) -> None:
    print(MENU_TEXT)


def build_request(
    fixed_radius: int,
    rolling_radius: int,
    pen_distance: int,
    curve_type: SpiroType,
) -> CircularSpiroRequest:
    steps = compute_steps(fixed_radius, rolling_radius)
    return CircularSpiroRequest(
        fixed_radius=fixed_radius,
        rolling_radius=rolling_radius,
        pen_distance=pen_distance,
        steps=steps,
        curve_type=curve_type,
    )


def generate_random_request(session: ConsoleUiSessionState) -> CircularSpiroRequest:
    if session.locked_fixed_radius is None:
        fixed_radius = random_fixed_circle_radius(session.last_request, session.random_evolution_mode)
    else:
        fixed_radius = session.locked_fixed_radius

    if session.locked_rolling_radius is None:
        rolling_radius = random_rolling_circle_radius(
            fixed_radius,
            session.last_request,
            session.random_constraint_mode,
            session.random_evolution_mode,
        )
    else:
        rolling_radius = session.locked_rolling_radius

    if session.locked_pen_distance is None:
        pen_distance = random_pen_offset(
            rolling_radius,
            session.last_request,
            session.random_constraint_mode,
            session.random_evolution_mode,
        )
    else:
        pen_distance = session.locked_pen_distance

    if session.locked_rolling_radius is not None:
        laps = compute_laps_to_close(fixed_radius, rolling_radius)
        if laps > MAX_LAPS_TO_CLOSE:
            print(
                f'Warning: locked r produces {laps} laps (> {MAX_LAPS_TO_CLOSE}). '
                'This may be slow. Consider unlocking r or choosing a different value.'
            )

    return build_request(
        fixed_radius,
        rolling_radius,
        pen_distance,
        session.curve_type,
    )


def edit_geometry(session: ConsoleUiSessionState) -> CircularSpiroRequest:
    previous_request = session.last_request

    guide_before_fixed_radius(previous_request)
    fixed_radius = prompt_positive_int_or_random(
        'fixed_circle_radius',
        int(previous_request.fixed_radius) if previous_request else None,
        lambda: random_fixed_circle_radius(previous_request, session.random_evolution_mode),
    )

    guide_before_rolling_radius(fixed_radius, previous_request)
    rolling_radius = prompt_positive_int_or_random(
        'rolling_circle_radius',
        int(previous_request.rolling_radius) if previous_request else None,
        lambda: random_rolling_circle_radius(
            fixed_radius,
            previous_request,
            session.random_constraint_mode,
            session.random_evolution_mode,
        ),
    )

    guide_before_pen_offset(fixed_radius, rolling_radius, previous_request)
    pen_distance = prompt_positive_int_or_random(
        'pen_offset',
        int(previous_request.pen_distance) if previous_request else None,
        lambda: random_pen_offset(
            rolling_radius,
            previous_request,
            session.random_constraint_mode,
            session.random_evolution_mode,
        ),
    )

    return build_request(
        fixed_radius,
        rolling_radius,
        pen_distance,
        session.curve_type,
    )


def edit_session_settings(session: ConsoleUiSessionState) -> None:
    while True:
        print_session_status(session)
        print(SESSION_MENU_TEXT)
        command = input('session> ').strip().lower()

        match command:
            case '' | 'q':
                break

            case 'p':
                print_session_status(session)
                continue

            case '1':
                session.curve_type = prompt_enum('Curve Type', SpiroType, session.curve_type)
                continue

            case '2':
                session.random_constraint_mode = prompt_enum(
                    'Random Constraint Mode',
                    type(session.random_constraint_mode),
                    session.random_constraint_mode,
                )
                continue

            case '3':
                session.random_evolution_mode = prompt_enum(
                    'Random Evolution Mode',
                    type(session.random_evolution_mode),
                    session.random_evolution_mode,
                )
                continue

            case '4':
                session.color_mode = prompt_enum('Color Mode', ColorMode, session.color_mode)
                continue

            case '5':
                if session.color_mode is not ColorMode.FIXED:
                    print(f"Not applicable: Color mode is '{session.color_mode.value}'.")
                    continue
                session.color = prompt_color_value(session.color)
                continue

            case '6':
                if session.color_mode is not ColorMode.RANDOM_EVERY_N_LAPS:
                    print(f"Not applicable: Color mode is '{session.color_mode.value}'.")
                    continue
                session.laps_per_color = prompt_positive_int('laps_per_color', default_value=session.laps_per_color)
                continue

            case '7':
                if session.color_mode is not ColorMode.RANDOM_EVERY_N_SPINS:
                    print(f"Not applicable: Color mode is '{session.color_mode.value}'.")
                    continue
                session.spins_per_color = prompt_positive_int('spins_per_color', default_value=session.spins_per_color)
                continue

            case '8':
                session.line_width = prompt_positive_float('line_width', default_value=session.line_width)
                continue

            case '9':
                session.drawing_speed = prompt_drawing_speed(session.drawing_speed)
                continue

            case _:
                print('Unknown session command.')
                continue


def edit_locks(session: ConsoleUiSessionState) -> None:
    print('\nLocks for random runs:')
    print("  Set a number to lock a value during random runs. Enter 'r' to unlock.")
    print('  Press Enter to keep the current lock setting.\n')

    session.locked_fixed_radius = prompt_lock_value('fixed_circle_radius', session.locked_fixed_radius)
    session.locked_rolling_radius = prompt_lock_value('rolling_circle_radius', session.locked_rolling_radius)
    session.locked_pen_distance = prompt_lock_value('pen_offset', session.locked_pen_distance)


def resolve_interval(session: ConsoleUiSessionState) -> int:
    if session.color_mode is ColorMode.RANDOM_EVERY_N_LAPS:
        return max(1, session.laps_per_color)
    if session.color_mode is ColorMode.RANDOM_EVERY_N_SPINS:
        return max(1, session.spins_per_color)
    return 1


def render_request(
    orchestrator: CurveOrchestrator,
    request: CircularSpiroRequest,
    session: ConsoleUiSessionState,
) -> None:
    interval = resolve_interval(session)
    settings = RenderSettings(
        color=session.color,
        color_mode=session.color_mode,
        interval=interval,
        width=session.line_width,
        speed=session.drawing_speed,
    )
    orchestrator.run(request, settings)


def main() -> None:
    registry = GeneratorRegistry()
    registry.register(CircularSpiroGenerator())

    builder = RenderPlanBuilder()
    renderer = TurtleGraphicsRenderer()
    orchestrator = CurveOrchestrator(registry, builder, renderer)

    session = ConsoleUiSessionState()

    while True:
        print_menu(session)
        command = input('> ').strip().lower()

        match command:
            case 'q':
                break

            case 'a':
                if session.last_request is None:
                    print('No curve yet. Press Enter to generate one, or use e to edit values.')
                else:
                    describe_curve(session.last_request)
                continue

            case 'b':
                count = prompt_positive_int('batch_count', default_value=10)
                pause_seconds = prompt_non_negative_float('pause_seconds', default_value=2.0)

                for _ in range(count):
                    request = generate_random_request(session)
                    session.last_request = request

                    print_selected_parameters(request, session)
                    describe_curve(request)
                    render_request(orchestrator, request, session)
                    time.sleep(pause_seconds)

                continue

            case 'l':
                edit_locks(session)
                continue

            case 'e':
                edit_session_settings(session)
                continue

            case 'm':
                request = edit_geometry(session)
                session.last_request = request
                print_selected_parameters(request, session)
                describe_curve(request)
                render_request(orchestrator, request, session)
                continue

            case 'p':
                print_session_status(session)

            case '':
                request = generate_random_request(session)
                session.last_request = request
                print_selected_parameters(request, session)
                describe_curve(request)
                render_request(orchestrator, request, session)

            case _:
                print('Unknown command')
                continue


if __name__ == '__main__':
    main()
