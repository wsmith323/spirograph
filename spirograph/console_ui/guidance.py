import math

from spirograph.generation import SpiroType
from spirograph.generation.requests import CircularSpiroRequest


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
        ratio_desc = 'very simple, large rounded shape'
    elif ratio < 4.0:
        ratio_desc = 'moderate complexity with visible lobes'
    else:
        ratio_desc = 'many lobes and fine detail; dense pattern'

    if offset_factor < 0.3:
        offset_desc = 'pen close to center; very soft, low-amplitude petals'
    elif offset_factor < 0.9:
        offset_desc = 'pen inside circle; softer petals'
    elif offset_factor < 1.1:
        offset_desc = 'pen near rim; classic spiky look'
    elif offset_factor < 1.6:
        offset_desc = 'pen outside circle; complex loops and self-intersections'
    else:
        offset_desc = 'pen far outside circle; very loopy and potentially chaotic'

    if request.curve_type is SpiroType.HYPOTROCHOID:
        curve_kind = 'rolling inside fixed circle (hypotrochoid)'
        spin_numerator = abs(fixed - rolling)
    else:
        curve_kind = 'rolling outside fixed circle (epitrochoid)'
        spin_numerator = fixed + rolling

    spins_to_close = max(1, spin_numerator // gcd_value) if gcd_value else 1

    print('\nCurve guidance:')
    print(f'  Radius ratio R/r: {ratio:.3f} -> {ratio_desc}')
    print(f'  Offset factor d/r: {offset_factor:.3f} -> {offset_desc}')
    print(f'  gcd(R, r): {gcd_value} -> approx lobes: {approx_petals}')
    print(f'  Laps around the track until closure: ~{laps_to_close}')
    print(f'  Rolling-circle spins about its center until closure: ~{spins_to_close}')
    print(f'  Curve type: {curve_kind}\n')


def guide_before_fixed_radius(previous_request: CircularSpiroRequest | None) -> None:
    print('\nFixed circle radius (R):')

    if previous_request is None:
        print('  R controls overall size. Larger R fills more of the window; smaller R keeps the pattern compact.')
        print('  This parameter scales the entire figure uniformly. Typical range: 100-320.')
        print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")
        return

    prev_R = int(previous_request.fixed_radius)
    print(f'  Default R is {prev_R}.')
    print(f'  Higher than {prev_R} scales the pattern up; lower scales it down.')
    print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")


def guide_before_rolling_radius(fixed_radius: int, previous_request: CircularSpiroRequest | None) -> None:
    print('\nRolling circle radius (r):')
    print(f'  Current R = {fixed_radius}.')

    if previous_request is None:
        print(
            '  In a physical kit, hypotrochoids typically use r < R, but this program allows any positive r.\n'
            '  Smaller r (relative to R) gives more lobes and a denser pattern.\n'
            '  Values near R or above R often create more dramatic loops and self-intersections.'
        )
        print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")
        return

    prev_r = int(previous_request.rolling_radius)
    ratio_if_unchanged = fixed_radius / prev_r if prev_r else 0.0
    gcd_if_unchanged = math.gcd(fixed_radius, prev_r) if prev_r else 1
    petals_if_unchanged = fixed_radius // gcd_if_unchanged if gcd_if_unchanged else 0
    laps_if_unchanged = prev_r // gcd_if_unchanged if gcd_if_unchanged else 0

    print(f'  Default r is {prev_r}. With current R, R/r would be ~{ratio_if_unchanged:.3f}.')
    print(f'  That implies ~{petals_if_unchanged} lobes and closes after ~{laps_if_unchanged} laps around the track.')

    if abs(ratio_if_unchanged - round(ratio_if_unchanged)) < 1e-9:
        print('  Integer-like R/r -> clean symmetry.')
    else:
        print('  Non-integer R/r -> denser, more intricate patterns.')

    print(f'  Smaller than {prev_r} increases R/r (more lobes); larger decreases R/r (fewer lobes).')
    print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")


def guide_before_pen_offset(
    fixed_radius: int,
    rolling_radius: int,
    previous_request: CircularSpiroRequest | None,
) -> None:
    print('\nPen offset (d):')
    print(f'  Current R = {fixed_radius}, r = {rolling_radius}.')

    gcd_value = math.gcd(fixed_radius, rolling_radius) if rolling_radius else 1
    ratio = fixed_radius / rolling_radius if rolling_radius else 0.0
    approx_petals = fixed_radius // gcd_value if gcd_value else 0
    laps_to_close = rolling_radius // gcd_value if gcd_value else 0

    if abs(ratio - round(ratio)) < 1e-9:
        ratio_symmetry = 'integer-like ratio -> cleaner symmetry'
    else:
        ratio_symmetry = 'non-integer ratio -> denser / more intricate'

    print(f'  So far: R/r ~{ratio:.3f} ({ratio_symmetry}).')
    print(f'  So far: gcd(R, r) = {gcd_value} -> approx lobes ~{approx_petals}.')
    print(f'  So far: closes after ~{laps_to_close} laps around the track.')

    if previous_request is None:
        print('  d/r is the key: small -> soft; near 1 -> spiky; above 1 -> loops and self-intersections.')
        print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")
        return

    prev_d = int(previous_request.pen_distance)
    offset_factor_if_unchanged = prev_d / rolling_radius if rolling_radius else 0.0

    print(f'  Default d is {prev_d}. With current r, d/r would be ~{offset_factor_if_unchanged:.3f}.')
    print(f'  Smaller than {prev_d} softens (lower d/r); larger exaggerates spikes/loops (higher d/r).')
    print("  Enter a number, press Enter for the default, or type 'r' for a random suggestion.")
