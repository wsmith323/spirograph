import math
import time

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
    random_fixed_circle_radius,
    random_pen_offset,
    random_rolling_circle_radius,
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


def describe_curve(request: CircularSpiroRequest) -> None:
    fixed = int(request.fixed_radius)
    rolling = int(request.rolling_radius)
    offset = int(request.pen_distance)

    gcd_value = math.gcd(fixed, rolling) if fixed > 0 and rolling > 0 else 1
    ratio = fixed / rolling if rolling else 0.0
    offset_factor = offset / rolling if rolling else 0.0

    approx_petals = fixed // gcd_value if gcd_value else 0
    laps_to_close = rolling // gcd_value if gcd_value else 0

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

    if request.curve_type is SpiroType.HYPOTROCHOID:
        curve_kind = "rolling inside fixed circle (hypotrochoid)"
        spin_numerator = abs(fixed - rolling)
    else:
        curve_kind = "rolling outside fixed circle (epitrochoid)"
        spin_numerator = fixed + rolling

    spins_to_close = max(1, spin_numerator // gcd_value) if gcd_value else 1

    print("\nCurve guidance:")
    print(f"  Radius ratio R/r: {ratio:.3f} -> {ratio_desc}")
    print(f"  Offset factor d/r: {offset_factor:.3f} -> {offset_desc}")
    print(f"  gcd(R, r): {gcd_value} -> approx lobes: {approx_petals}")
    print(f"  Laps around the track until closure: ~{laps_to_close}")
    print(f"  Rolling-circle spins about its center until closure: ~{spins_to_close}")
    print(f"  Curve type: {curve_kind}\n")


def guide_before_fixed_radius(previous_request: CircularSpiroRequest | None) -> None:
    print("\nFixed circle radius (R):")

    if previous_request is None:
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

    prev_R = int(previous_request.fixed_radius)
    print(f"  Default R is {prev_R}.")
    print(f"  Higher than {prev_R} scales the pattern up; lower scales it down.")
    print(
        "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
    )


def guide_before_rolling_radius(
    fixed_radius: int, previous_request: CircularSpiroRequest | None
) -> None:
    print("\nRolling circle radius (r):")
    print(f"  Current R = {fixed_radius}.")

    if previous_request is None:
        print(
            "  In a physical kit, hypotrochoids typically use r < R, but this program allows any positive r.\n"
            "  Smaller r (relative to R) gives more lobes and a denser pattern.\n"
            "  Values near R or above R often create more dramatic loops and self-intersections."
        )
        print(
            "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
        )
        return

    prev_r = int(previous_request.rolling_radius)
    ratio_if_unchanged = fixed_radius / prev_r if prev_r else 0.0
    gcd_if_unchanged = math.gcd(fixed_radius, prev_r) if prev_r else 1
    petals_if_unchanged = fixed_radius // gcd_if_unchanged if gcd_if_unchanged else 0
    laps_if_unchanged = prev_r // gcd_if_unchanged if gcd_if_unchanged else 0

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
    fixed_radius: int,
    rolling_radius: int,
    previous_request: CircularSpiroRequest | None,
) -> None:
    print("\nPen offset (d):")
    print(f"  Current R = {fixed_radius}, r = {rolling_radius}.")

    gcd_value = math.gcd(fixed_radius, rolling_radius) if rolling_radius else 1
    ratio = fixed_radius / rolling_radius if rolling_radius else 0.0
    approx_petals = fixed_radius // gcd_value if gcd_value else 0
    laps_to_close = rolling_radius // gcd_value if gcd_value else 0

    if abs(ratio - round(ratio)) < 1e-9:
        ratio_symmetry = "integer-like ratio -> cleaner symmetry"
    else:
        ratio_symmetry = "non-integer ratio -> denser / more intricate"

    print(f"  So far: R/r ~{ratio:.3f} ({ratio_symmetry}).")
    print(f"  So far: gcd(R, r) = {gcd_value} -> approx lobes ~{approx_petals}.")
    print(f"  So far: closes after ~{laps_to_close} laps around the track.")

    if previous_request is None:
        print(
            "  d/r is the key: small -> soft; near 1 -> spiky; above 1 -> loops and self-intersections."
        )
        print(
            "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
        )
        return

    prev_d = int(previous_request.pen_distance)
    offset_factor_if_unchanged = prev_d / rolling_radius if rolling_radius else 0.0

    print(
        f"  Default d is {prev_d}. With current r, d/r would be ~{offset_factor_if_unchanged:.3f}."
    )
    print(
        f"  Smaller than {prev_d} softens (lower d/r); larger exaggerates spikes/loops (higher d/r)."
    )
    print(
        "  Enter a number, press Enter for the default, or type 'r' for a random suggestion."
    )


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
