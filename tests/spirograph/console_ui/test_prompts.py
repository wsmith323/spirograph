from spirograph.console_ui.prompts import try_parse_color
from spirograph.rendering import Color


def test_try_parse_color_accepts_named_color() -> None:
    parsed, color = try_parse_color('blue')

    assert parsed is True
    assert color == Color(0, 0, 255)


def test_try_parse_color_accepts_hex() -> None:
    parsed, color = try_parse_color('#1a2b3c')

    assert parsed is True
    assert color == Color(26, 43, 60)


def test_try_parse_color_accepts_rgb_csv() -> None:
    parsed, color = try_parse_color('12, 34, 56')

    assert parsed is True
    assert color == Color(12, 34, 56)


def test_try_parse_color_reports_invalid_input() -> None:
    parsed, _color = try_parse_color('not-a-color')

    assert parsed is False
