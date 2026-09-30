"""main_weather_process 参数路由测试(--city-name/--city-code/--json)。全部离线: 网络函数均被替换, 只验证路由逻辑与输出。"""

import pytest

import GetWeather
from GetWeather import AirQuality, WeatherReport, WeatherSnapshot


def make_report() -> WeatherReport:
    return WeatherReport(
        summary="测试摘要",
        snapshot=WeatherSnapshot(
            city_cn="嘉兴",
            city_en="jiaxing",
            description="多云",
            temp_now="24",
            humidity="86%",
            date="09月29日(星期二)",
            update_time="08:25",
            max_temp="26℃",
            min_temp="22℃",
        ),
        air_quality=AirQuality(aqi="26", level="优", pm25="26"),
        umbrella="不用带伞",
        alarms=[],
    )


@pytest.fixture
def spies(monkeypatch):
    calls = {"city_name": [], "city_code": [], "geo": []}

    monkeypatch.setattr(
        GetWeather,
        "get_city_code",
        lambda city, raw_content=None: calls["city_name"].append(city) or "999000999",
    )
    monkeypatch.setattr(
        GetWeather,
        "get_CityName",
        lambda *a, **k: calls["geo"].append(True) or ("杭州", "101210101"),
    )
    monkeypatch.setattr(
        GetWeather,
        "get_weather",
        lambda code: calls["city_code"].append(code) or make_report(),
    )
    return calls


def test_city_name_skips_geolocation(spies, capsys):
    GetWeather.main_weather_process(output=0, city_name="嘉兴", color_mode="none")

    assert spies["city_name"] == ["嘉兴"]
    assert spies["geo"] == []  # 修复前: 总是调用自动定位, --city-name 无效
    assert spies["city_code"] == ["999000999"]
    out = capsys.readouterr().out
    assert "使用指定城市：嘉兴" in out
    assert "多云" in out  # 输出了天气报告


def test_city_code_used_directly(spies, capsys):
    GetWeather.main_weather_process(output=0, city_code="101210301", color_mode="none")

    assert spies["city_name"] == []  # 不按城市名查代码
    assert spies["geo"] == []
    assert spies["city_code"] == ["101210301"]
    assert "使用指定城市代码：101210301" in capsys.readouterr().out


def test_city_name_takes_precedence_over_city_code(spies):
    GetWeather.main_weather_process(
        output=0, city_name="嘉兴", city_code="101210301", color_mode="none"
    )

    assert spies["city_code"] == ["999000999"]  # 城市名解析出的代码优先


def test_invalid_city_name_exits(spies, capsys):
    with pytest.raises(SystemExit):
        GetWeather.main_weather_process(output=0, city_name="beijing123", color_mode="none")

    assert spies["geo"] == []
    assert spies["city_code"] == []
    assert "非地名字符" in capsys.readouterr().out


def test_fallback_to_geolocation_when_no_args(spies):
    """不传参数时保持原行为: 自动定位。"""
    GetWeather.main_weather_process(output=0, color_mode="none")

    assert spies["geo"] == [True]
    assert spies["city_code"] == ["101210101"]
