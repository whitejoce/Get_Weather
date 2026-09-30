"""预警数据(alarmDZ)本地样本解析测试。

样本:
- alarm1.json: 北京 2 则预警(森林火险橙色 + 大风黄色)
- alarm2.json: 无预警 {"w":[]}
"""

from pathlib import Path

import GetWeather

FIXTURES = Path(__file__).resolve().parent / "sample"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_alarm1_extract_two_alarms():
    data = GetWeather.extract_json_block(load("alarm1.json"), "alarmDZ")

    assert data is not None
    assert len(data["w"]) == 2


def test_alarm1_format_messages():
    data = GetWeather.extract_json_block(load("alarm1.json"), "alarmDZ")
    messages = GetWeather.build_alarm_messages(data)

    # 结构: ["", 标题, 第1条内容, 第1条详情, 第2条内容, 第2条详情]
    assert len(messages) == 6
    assert "气象部门发布2则预警" in messages[1]
    assert "森林火险橙色预警" in messages[2]
    assert "10101-20250206083905-9403.html" in messages[3]
    assert "大风黄色预警" in messages[4]
    assert "10101-20250205150235-0502.html" in messages[5]


def test_alarm2_no_alarm():
    data = GetWeather.extract_json_block(load("alarm2.json"), "alarmDZ")

    assert data == {"w": []}
    assert GetWeather.build_alarm_messages(data) == []


def test_weather_index_alarm_shape_matches_sample():
    """weather_index 响应内嵌的 alarmDZ 与独立预警样本结构一致。"""
    index = GetWeather.extract_json_block(load("weather_index_jiaxing.html"), "alarmDZ")

    assert index == {"w": []}
