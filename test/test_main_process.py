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
    calls = {"city_name": [], "city_code": [], "geo": [], "nowcast": []}

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
    # 文本模式短临钩子离线守卫: 固定有 key + 拦截网络调用, 只记录解析出的城市名
    monkeypatch.setattr(GetWeather, "_load_api_key", lambda: "test-key")
    monkeypatch.setattr(
        GetWeather,
        "fetch_city_minute_cast",
        lambda city, key: calls["nowcast"].append(city) or None,
    )
    return calls


def test_city_name_skips_geolocation(spies, capsys):
    GetWeather.main_weather_process(output=0, city_name="嘉兴", color_mode="none")

    assert spies["city_name"] == ["嘉兴"]
    assert spies["geo"] == []  # 修复前: 总是调用自动定位, --city-name 无效
    assert spies["city_code"] == ["999000999"]
    captured = capsys.readouterr()  # 进度走 stderr(_note), 报告本体在 stdout
    assert "使用指定城市：嘉兴" in captured.err
    assert "多云" in captured.out  # 输出了天气报告


def test_city_code_used_directly(spies, capsys):
    GetWeather.main_weather_process(output=0, city_code="101210301", color_mode="none")

    assert spies["city_name"] == []  # 不按城市名查代码
    assert spies["geo"] == []
    assert spies["city_code"] == ["101210301"]
    assert "使用指定城市代码：101210301" in capsys.readouterr().err


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
    assert "非地名字符" in capsys.readouterr().err


def test_fallback_to_geolocation_when_no_args(spies):
    """不传参数时保持原行为: 自动定位。"""
    GetWeather.main_weather_process(output=0, color_mode="none")

    assert spies["geo"] == [True]
    assert spies["city_code"] == ["101210101"]


def test_minute_cast_city_resolution(spies):
    """文本模式短临的城市名解析: 显式城市名 > 自动定位地址 > 报告里的城市名。"""
    GetWeather.main_weather_process(output=0, city_name="嘉兴", color_mode="none")
    assert spies["nowcast"] == ["嘉兴"]

    GetWeather.main_weather_process(output=0, color_mode="none")
    assert spies["nowcast"] == ["嘉兴", "杭州"]  # 自动定位返回地址"杭州"

    GetWeather.main_weather_process(output=0, city_code="101210301", color_mode="none")
    assert spies["nowcast"][-1] == "嘉兴"  # 仅城市代码: 取 dataSK 城市名


def test_minute_cast_attached_renders_in_output(spies, monkeypatch, capsys):
    """fetch_city_minute_cast 返回摘要时, 文本输出渲染雨具行与短临区块(钟点为当前时刻)。"""
    import re

    seq = [0.0] * 5 + [0.12, 0.3, 0.42, 0.3, 0.12] + [0.0] * 14
    monkeypatch.setattr(
        GetWeather,
        "fetch_city_minute_cast",
        lambda city, key: GetWeather.synthesize_nowcast({"Intensity": seq, "PreType": "雨"}),
    )
    GetWeather.main_weather_process(output=0, city_name="嘉兴", color_mode="none")

    out = capsys.readouterr().out
    assert "前后有雨，建议带伞" in out
    assert re.search(r"约 \d{2}:\d{2} 开始降雨，持续约25分钟", out)
    assert "短临降水(未来2小时)" in out
    assert "+2h" in out
