import time

import math

from spirograph.cli.evolution import (
    random_fixed_circle_radius,
    random_pen_offset,
    random_rolling_circle_radius,
)
from spirograph.cli.guidance import (
    describe_curve,
    guide_before_fixed_radius,
    guide_before_pen_offset,
    guide_before_rolling_radius,
)
from spirograph.cli.prompts import (
    compute_steps,
    make_prompt_label,
    parse_color,
    prompt_drawing_speed,
    prompt_enum,
    prompt_lock_value,
    prompt_non_negative_float,
    prompt_positive_int,
    prompt_positive_int_or_random,
    toggle_curve_type,
)
from spirograph.cli.session import CliSessionState
from spirograph.generation.circular_generator import CircularSpiroGenerator
from spirograph.generation.registry import GeneratorRegistry
from spirograph.generation.requests import CircularSpiroRequest, SpiroType
from spirograph.orchestration import CurveOrchestrator
from spirograph.rendering import (
    RenderPlanBuilder,
    RenderSettings,
    TurtleGraphicsRenderer,
)
from spirograph.rendering.settings import ColorMode

MAX_LAPS_TO_CLOSE = 200

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


def compute_laps_to_close(fixed_radius: int, rolling_radius: int) -> int:
    gcd_value = math.gcd(fixed_radius, rolling_radius)
    return max(1, rolling_radius // gcd_value) if gcd_value else 1


def color_to_hex(color: Color) -> str:
    return f"#{color.r:02x}{color.g:02x}{color.b:02x}"


def prompt_color_value(current_color: Color) -> Color:
    label = make_prompt_label("color")
    raw_value = input(f"{label} [{color_to_hex(current_color)}]: ").strip()
    if raw_value == "":
        return current_color
    return parse_color(raw_value, current_color)


def print_selected_parameters(
    request: CircularSpiroRequest, session: CliSessionState
) -> None:
    print("\nSelected parameters:")
    print(f"  Fixed Circle Radius (R): {int(request.fixed_radius)}")
    print(f"  Rolling Circle Radius (r): {int(request.rolling_radius)}")
    print(f"  Pen Offset (d): {int(request.pen_distance)}")
    print(f"  Curve Type: {request.curve_type.value}")
    print(f"  Color Mode: {session.color_mode.value}")
    print(f"  Color: {color_to_hex(session.color)}")
    print(f"  Line Width: {session.line_width}")


def print_session_status(session: CliSessionState) -> None:
    r_lock = "r" if session.locked_fixed_radius is None else session.locked_fixed_radius
    rr_lock = (
        "r" if session.locked_rolling_radius is None else session.locked_rolling_radius
    )
    d_lock = "r" if session.locked_pen_distance is None else session.locked_pen_distance

    print(
        "Current: "
        f"complexity={session.random_complexity.value}, "
        f"constraint={session.random_constraint_mode.value}, "
        f"evolution={session.random_evolution_mode.value}, "
        f"type={session.curve_type.value}, "
        f"color_mode={session.color_mode.value}, "
        f"color={color_to_hex(session.color)}, "
        f"laps_per_color={session.laps_per_color}, "
        f"spins_per_color={session.spins_per_color}, "
        f"width={session.line_width}, "
        f"speed={session.drawing_speed}, "
        f"locks=R:{r_lock} r:{rr_lock} d:{d_lock}"
    )


def print_menu(session: CliSessionState) -> None:
    print()
    print(MENU_TEXT)
    print_session_status(session)


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


def generate_random_request(session: CliSessionState) -> CircularSpiroRequest:
    if session.locked_fixed_radius is None:
        fixed_radius = random_fixed_circle_radius(
            session.last_request, session.random_evolution_mode
        )
    else:
        fixed_radius = session.locked_fixed_radius

    if session.locked_rolling_radius is None:
        rolling_radius = random_rolling_circle_radius(
            fixed_radius,
            session.last_request,
            session.random_complexity,
            session.random_constraint_mode,
            session.random_evolution_mode,
        )
    else:
        rolling_radius = session.locked_rolling_radius

    if session.locked_pen_distance is None:
        pen_distance = random_pen_offset(
            rolling_radius,
            session.last_request,
            session.random_complexity,
            session.random_constraint_mode,
            session.random_evolution_mode,
        )
    else:
        pen_distance = session.locked_pen_distance

    if session.locked_rolling_radius is not None:
        laps = compute_laps_to_close(fixed_radius, rolling_radius)
        if laps > MAX_LAPS_TO_CLOSE:
            print(
                f"Warning: locked r produces {laps} laps (> {MAX_LAPS_TO_CLOSE}). "
                "This may be slow. Consider unlocking r or choosing a different value."
            )

    return build_request(
        fixed_radius,
        rolling_radius,
        pen_distance,
        session.curve_type,
    )


def edit_geometry(session: CliSessionState) -> CircularSpiroRequest:
    previous_request = session.last_request

    guide_before_fixed_radius(previous_request)
    fixed_radius = prompt_positive_int_or_random(
        "fixed_circle_radius",
        int(previous_request.fixed_radius) if previous_request else None,
        lambda: random_fixed_circle_radius(
            previous_request, session.random_evolution_mode
        ),
    )

    guide_before_rolling_radius(fixed_radius, previous_request)
    rolling_radius = prompt_positive_int_or_random(
        "rolling_circle_radius",
        int(previous_request.rolling_radius) if previous_request else None,
        lambda: random_rolling_circle_radius(
            fixed_radius,
            previous_request,
            session.random_complexity,
            session.random_constraint_mode,
            session.random_evolution_mode,
        ),
    )

    guide_before_pen_offset(fixed_radius, rolling_radius, previous_request)
    pen_distance = prompt_positive_int_or_random(
        "pen_offset",
        int(previous_request.pen_distance) if previous_request else None,
        lambda: random_pen_offset(
            rolling_radius,
            previous_request,
            session.random_complexity,
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


def edit_session_settings(session: CliSessionState) -> None:
    session.random_complexity = prompt_enum(
        "Random Complexity", type(session.random_complexity), session.random_complexity
    )
    session.random_constraint_mode = prompt_enum(
        "Constraint Mode",
        type(session.random_constraint_mode),
        session.random_constraint_mode,
    )
    session.random_evolution_mode = prompt_enum(
        "Evolution Mode",
        type(session.random_evolution_mode),
        session.random_evolution_mode,
    )

    session.color_mode = prompt_enum("Color Mode", ColorMode, session.color_mode)
    if session.color_mode is ColorMode.FIXED:
        session.color = prompt_color_value(session.color)
    elif session.color_mode is ColorMode.RANDOM_EVERY_N_LAPS:
        session.laps_per_color = prompt_positive_int(
            "laps_per_color", default_value=session.laps_per_color
        )
    elif session.color_mode is ColorMode.RANDOM_EVERY_N_SPINS:
        session.spins_per_color = prompt_positive_int(
            "spins_per_color", default_value=session.spins_per_color
        )

    session.line_width = prompt_positive_int(
        "line_width", default_value=int(session.line_width)
    )
    session.drawing_speed = prompt_drawing_speed(session.drawing_speed)


def edit_locks(session: CliSessionState) -> None:
    print("\nLocks for random runs:")
    print("  Set a number to lock a value during random runs. Enter 'r' to unlock.")
    print("  Press Enter to keep the current lock setting.\n")

    session.locked_fixed_radius = prompt_lock_value(
        "fixed_circle_radius", session.locked_fixed_radius
    )
    session.locked_rolling_radius = prompt_lock_value(
        "rolling_circle_radius", session.locked_rolling_radius
    )
    session.locked_pen_distance = prompt_lock_value(
        "pen_offset", session.locked_pen_distance
    )


def resolve_interval(session: CliSessionState) -> int:
    if session.color_mode is ColorMode.RANDOM_EVERY_N_LAPS:
        return max(1, session.laps_per_color)
    if session.color_mode is ColorMode.RANDOM_EVERY_N_SPINS:
        return max(1, session.spins_per_color)
    return 1


def render_request(
    orchestrator: CurveOrchestrator,
    request: CircularSpiroRequest,
    session: CliSessionState,
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

    session = CliSessionState()

    while True:
        print_menu(session)
        command = input("> ").strip().lower()

        if command == "q":
            break

        if command == "p":
            if session.last_request is None:
                print(
                    "No curve yet. Press Enter to generate one, or use e to edit values."
                )
            else:
                describe_curve(session.last_request)
            continue

        if command == "b":
            count = prompt_positive_int("batch_count", default_value=10)
            pause_seconds = prompt_non_negative_float(
                "pause_seconds", default_value=2.0
            )

            for _ in range(count):
                request = generate_random_request(session)
                session.last_request = request

                print_selected_parameters(request, session)
                describe_curve(request)
                render_request(orchestrator, request, session)
                time.sleep(pause_seconds)

            continue

        if command == "l":
            edit_locks(session)
            continue

        if command == "t":
            session.curve_type = toggle_curve_type(session.curve_type)
            if session.last_request is not None:
                request = build_request(
                    int(session.last_request.fixed_radius),
                    int(session.last_request.rolling_radius),
                    int(session.last_request.pen_distance),
                    session.curve_type,
                )
                session.last_request = request
                render_request(orchestrator, request, session)
            continue

        if command == "s":
            edit_session_settings(session)
            continue

        if command == "e":
            request = edit_geometry(session)
            session.last_request = request
            print_selected_parameters(request, session)
            describe_curve(request)
            render_request(orchestrator, request, session)
            continue

        if command != "":
            print("Unknown command. Press Enter for next random, or use b/l/e/s/t/p/q.")
            continue

        request = generate_random_request(session)
        session.last_request = request
        print_selected_parameters(request, session)
        describe_curve(request)
        render_request(orchestrator, request, session)


if __name__ == "__main__":
    main()
