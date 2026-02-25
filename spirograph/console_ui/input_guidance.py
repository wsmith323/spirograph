import math

from spirograph.generation.requests import CircularSpiroRequest


def guide_before_fixed_radius(previous_request: CircularSpiroRequest | None) -> None:
    print('\nFixed circle radius (R):')

    if previous_request is None:
        print('  R controls overall size. Larger R fills more of the window; smaller R keeps the pattern compact.')
        print('  R also affects the later R/r ratio and closure repeats once you choose r.')
        print('  This parameter scales the figure and sets up later symmetry/density tendencies. Typical range: 100-320.')
        print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")
        return

    prev_fixed_radius = int(previous_request.fixed_radius)
    print(f'  Default R is {prev_fixed_radius}.')
    print(f'  Higher than {prev_fixed_radius} scales the pattern up; lower scales it down.')
    print('  Your later r choice will determine closure repeats and symmetry tendencies.')
    print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")


def guide_before_rolling_radius(fixed_radius: int, previous_request: CircularSpiroRequest | None) -> None:
    print('\nRolling circle radius (r):')
    print(f'  Current R = {fixed_radius}.')

    if previous_request is None:
        print(
            '  In a physical kit, hypotrochoids typically use r < R, but this program allows any positive r.\n'
            '  R/r affects the scale of repeating detail, but visual density is also shaped by closure repeats\n'
            '  (from gcd(R, r)) and later by d/r when you choose the pen offset.'
        )
        print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")
        return

    previous_rolling_radius = int(previous_request.rolling_radius)
    ratio_if_unchanged = fixed_radius / previous_rolling_radius if previous_rolling_radius else 0.0
    gcd_if_unchanged = math.gcd(max(1, fixed_radius), max(1, previous_rolling_radius))
    laps_if_unchanged = max(1, previous_rolling_radius // gcd_if_unchanged)

    print(f'  Default r is {previous_rolling_radius}. With current R, R/r would be ~{ratio_if_unchanged:.3f}.')
    print(f'  Preview closure repeats (from R and r): laps~{laps_if_unchanged}.')
    print('  Final visual density depends on both closure repeats and the d/r value you choose next.')

    if abs(ratio_if_unchanged - round(ratio_if_unchanged)) < 1e-9:
        print('  Integer-like R/r -> stronger symmetry tendency (not necessarily denser).')
    else:
        print('  Non-integer R/r -> weaker symmetry tendency; density still depends on closure repeats + d/r.')

    print('  Smaller r usually increases repeat detail; larger r usually simplifies the repeating structure.')
    print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")


def guide_before_pen_offset(
    fixed_radius: int,
    rolling_radius: int,
    previous_request: CircularSpiroRequest | None,
) -> None:
    print('\nPen offset (d):')
    print(f'  Current R = {fixed_radius}, r = {rolling_radius}.')

    safe_fixed_radius = max(1, fixed_radius)
    safe_rolling_radius = max(1, rolling_radius)
    gcd_value = max(1, math.gcd(safe_fixed_radius, safe_rolling_radius))
    ratio = fixed_radius / rolling_radius if rolling_radius else 0.0
    laps_to_close = max(1, safe_rolling_radius // gcd_value)
    if abs(ratio - round(ratio)) < 1e-9:
        ratio_symmetry = 'integer-like ratio -> stronger symmetry tendency'
    else:
        ratio_symmetry = 'non-integer ratio -> weaker symmetry tendency'

    print(f'  So far: R/r ~{ratio:.3f} ({ratio_symmetry}).')
    print(f'  So far: closure repeats (from R and r) -> laps~{laps_to_close}.')
    print('  d/r now controls visual style: small -> soft, near 1 -> spiky, above 1 -> loopy/intersecting.')
    print('  Final visual density is a combination of closure repeats and d/r, not ratio alone.')

    if previous_request is None:
        print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")
        return

    previous_pen_distance = int(previous_request.pen_distance)
    offset_factor_if_unchanged = previous_pen_distance / rolling_radius if rolling_radius else 0.0

    print(f'  Default d is {previous_pen_distance}. With current r, d/r would be ~{offset_factor_if_unchanged:.3f}.')
    print(f'  Smaller than {previous_pen_distance} softens (lower d/r); larger increases spikes/loops (higher d/r).')
    print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")
