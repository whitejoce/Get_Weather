import pytest

from get_weather.exceptions import ParseError
from get_weather.parser import (
    extract_assigned_json,
    extract_object_after_key,
    parse_alarm_lines,
    parse_qweather_summary,
)


def test_extract_assigned_json_handles_nested_objects() -> None:
    source = 'var dataZS={"zs":{"ys_des_s":"不用带伞","nested":{"x":"}"}},"cn":"北京"};'

    result = extract_assigned_json(source, "dataZS")

    assert result["zs"]["ys_des_s"] == "不用带伞"
    assert result["zs"]["nested"]["x"] == "}"


def test_extract_object_after_key_parses_weatherinfo() -> None:
    source = 'var cityDZ101010100={"weatherinfo":{"temp":"36℃","tempn":"21℃"}};'

    result = extract_object_after_key(source, "weatherinfo")

    assert result == {"temp": "36℃", "tempn": "21℃"}


def test_parse_alarm_lines_returns_empty_when_no_alarm() -> None:
    assert parse_alarm_lines('var alarmDZ = {"w":[]};') == []


def test_parse_alarm_lines_formats_alarm_detail_url() -> None:
    source = (
        'var alarmDZ = {"w":[{"w9":"市气象台发布高温蓝色预警：请注意防范",'
        '"w11":"10101-20210618154146-0701.html"}]};'
    )

    lines = parse_alarm_lines(source)

    assert lines[0] == "\n [!]气象部门发布1则预警,请注意:"
    assert "市气象台发布高温蓝色预警" in lines[1]
    assert "10101-20210618154146-0701.html" in lines[2]


def test_parse_qweather_summary_handles_missing_air_quality() -> None:
    summary, aqi_level = parse_qweather_summary(
        '<div class="current-abstract">今天白天晴。</div>'
    )

    assert summary == "今天白天晴。"
    assert aqi_level == "未知"


def test_extract_assigned_json_raises_clear_error() -> None:
    with pytest.raises(ParseError, match="未找到 dataSK 数据"):
        extract_assigned_json("var other = {};", "dataSK")
