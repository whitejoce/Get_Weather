"""摘要合成单元测试: 确定性输入, 不发网络请求。

阈值依据见 test/README.md「和风摘要句式」。
"""

from pathlib import Path

import GetWeather

FIXTURES = Path(__file__).resolve().parent / "sample"


def test_build_temp_compare_thresholds():
    f = GetWeather.build_temp_compare
    # |Δ|<=1 差不多
    assert f("26", "26") == "温度和昨天差不多"
    assert f("26", "25") == "温度和昨天差不多"
    # 2~4 一些, >=5 很多
    assert f("26", "24") == "比昨天热一些"
    assert f("30", "25") == "比昨天热很多"
    # 最高温 >=25 用"热", <25 用"暖和"
    assert f("23", "21") == "比昨天暖和一些"
    assert f("19", "14") == "比昨天暖和很多"
    # 降温用"凉爽"
    assert f("20", "24") == "比昨天凉爽一些"
    assert f("19", "24") == "比昨天凉爽很多"
    # 缺数据
    assert f("", "26") == ""
    assert f("26", "") == ""


def test_wind_phrase():
    f = GetWeather.wind_phrase
    assert f("4级") == "风很大"
    assert f("2级") == "有风"
    assert f("<3级") == "有风"  # 3 级
    assert f("1级") == ""
    assert f("") == ""


def test_aqi_level_and_phrase():
    assert GetWeather.aqi_level_text("26") == "优"
    assert GetWeather.aqi_level_text("52") == "良"
    assert GetWeather.aqi_level_text("120") == "轻度污染"
    assert GetWeather.aqi_level_text("250") == "重度污染"
    assert GetWeather.aqi_level_text("") == ""
    assert GetWeather.air_phrase("26") == "不错"
    assert GetWeather.air_phrase("52") == "一般"
    assert GetWeather.air_phrase("120") == "较差"


def test_weather_code_table():
    assert GetWeather.weather_text_from_code("00") == "晴"
    assert GetWeather.weather_text_from_code("07") == "小雨"
    assert GetWeather.weather_text_from_code("d02") == "阴"  # dataSK.weathercode 带 d 前缀
    assert GetWeather.weather_text_from_code("99") == ""


def test_day_night_weather_prefers_citydz_text():
    index = (FIXTURES / "weather_index_jiaxing.html").read_text(encoding="utf-8")
    assert GetWeather.day_night_weather(index) == ("小雨", "多云")


def test_day_night_weather_fallback_to_fc_codes():
    source = 'var cityDZ ={"weatherinfo":{}};var fc ={"f":[{"fa":"00","fb":"02"}]};'
    assert GetWeather.day_night_weather(source) == ("晴", "阴")


def test_find_yesterday_obs_with_fixture():
    cal = (FIXTURES / "calendar_new_jiaxing.html").read_text(encoding="utf-8")
    fc40 = GetWeather.extract_fc40(cal)
    assert fc40 is not None and len(fc40) >= 30

    yday = GetWeather.find_yesterday_obs(fc40, today="20260929")
    assert yday["date"] == "20260928"
    assert yday["maxobs"] == "26"
    assert yday["minobs"] == "22"
    # 超出近 5 天实测窗口 -> None
    assert GetWeather.find_yesterday_obs(fc40, today="20261010") is None


def test_build_summary_full_sentence():
    index = (FIXTURES / "weather_index_jiaxing.html").read_text(encoding="utf-8")
    cal = (FIXTURES / "calendar_new_jiaxing.html").read_text(encoding="utf-8")
    fc40 = GetWeather.extract_fc40(cal)
    yday = GetWeather.find_yesterday_obs(fc40, today="20260929")

    summary = GetWeather.build_summary({"temp": "24", "WS": "2级", "aqi": "26"}, index, yday)
    assert summary == "今天白天有小雨，夜晚多云，温度和昨天差不多，现在24°，有风，空气不错。"


def test_build_summary_degrades_without_yesterday():
    index = (FIXTURES / "weather_index_jiaxing.html").read_text(encoding="utf-8")
    summary = GetWeather.build_summary({"temp": "24", "WS": "1级", "aqi": "26"}, index, None)
    # 无昨日数据 -> 省略温度比较段; 风力 1 级 -> 省略风段
    assert summary == "今天白天有小雨，夜晚多云，现在24°，空气不错。"


def test_build_summary_rain_gets_you_prefix():
    source = 'var cityDZ ={"weatherinfo":{"weather":"晴转阵雨"}};var fc ={"f":[{"fa":"00","fb":"03","fc":"26","fd":"18"}]};'
    summary = GetWeather.build_summary({"temp": "20", "WS": "1级", "aqi": "30"}, source, None)
    assert summary.startswith("今天白天晴，夜晚有阵雨")  # 降水加"有", 晴不加
