from karaoke_player.infra.lrc_parser import parse_lrc_text


def test_parse_basic_lrc_text() -> None:
    lines = parse_lrc_text("[00:01.00]Hello\n[00:02.50]World")

    assert len(lines) == 2
    assert lines[0].timestamp_ms == 1000
    assert lines[0].text == "Hello"
    assert lines[1].timestamp_ms == 2500
    assert lines[1].text == "World"


def test_parse_multiple_tags_in_one_line() -> None:
    lines = parse_lrc_text("[00:01.00][00:02.00]Echo")

    assert [line.timestamp_ms for line in lines] == [1000, 2000]
    assert all(line.text == "Echo" for line in lines)
