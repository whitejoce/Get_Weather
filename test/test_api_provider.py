"""官方 API 数据源(可选 provider)离线测试: 使用 api_*.json 样本, 不发网络请求/不消耗配额。"""

import importlib.util
import json
from pathlib import Path

import pytest

SKILL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "querying-weather"
    / "scripts"
    / "GetWeather.py"
)
FIXTURES = Path(__file__).resolve().parent / "sample"


@pytest.fixture(scope="module")
def skill():
    spec = importlib.util.spec_from_file_location("skill_getweather", SKILL_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fx():
    def load(name):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    return load


@pytest.fixture
def fake_api(skill, monkeypatch, fx):
    def fake_api_get(path, key, **params):
        if "translate" in path:
            return fx("api_translate_jiaxing.json")
        if "currentconditions" in path:
            return fx("api_current_jiaxing.json")
        if "daily/5day" in path:
            return fx("api_daily5_jiaxing.json")
        if "hourly/12hour" in path:
            return fx("api_hourly12_jiaxing.json")
        if "airquality" in path:
            return fx("api_air_jiaxing.json")
        if "alerts" in path:
            return fx("api_alerts_jiaxing.json")
        if "nowcast_cn" in path:
            return fx("api_nowcast_jiaxing.json")
        raise AssertionError(f"意外路径: {path}")

    monkeypatch.setattr(skill, "_api_get", fake_api_get)
    return skill


def test_api_location_key_exact_match(fake_api, fx):
    loc_key, item = fake_api.api_location_key("嘉兴", "k")
    assert loc_key == "61618"
    assert item["LocalizedName"] == "嘉兴"
    assert item["AdministrativeArea"]["LocalizedName"] == "浙江省"


def test_get_weather_data_api_clean(fake_api, fx):
    data = fake_api.get_weather_data_api("嘉兴", "k")
    assert data["source"] == "openapi"

    clean = data["clean"]
    assert clean["数据源"].startswith("华风爱科")
    assert clean["城市"]["LocationKey"] == "61618"
    # 实况(样本冻结值)
    assert clean["实况"]["天气"] == "阴"
    assert clean["实况"]["气温"] == 24.0
    assert clean["实况"]["风力"].endswith("级")
    assert clean["实况"]["紫外线描述"] == "很弱"
    assert clean["实况"]["气压趋势"] == "稳定"
    assert clean["实况"]["白天"] is True
    assert clean["实况"]["阵风风速"] == 18.7
    assert clean["实况"]["过去24小时温度"] == {"最高": 25.5, "最低": 22.4}
    assert clean["实况"]["过去24小时降水mm"] == 10.0
    air_fx = fx("api_air_jiaxing.json")
    assert clean["实况"]["空气质量"]["AQI"] == air_fx["Index"]
    assert clean["实况"]["空气质量"]["PM2.5"] == air_fx["ParticulateMatter2_5"]
    assert clean["实况"]["更新时间"]  # YYYY-MM-DD HH:MM
    # 今日(扁平温度结构已正确读取)
    assert clean["今日"]["最高温"] == 26.0
    assert clean["今日"]["最低温"] == 22.0
    assert clean["今日"]["日出"] == "05:49"
    assert clean["今日"]["日落"] == "17:46"
    assert clean["今日"]["月相"]
    assert clean["今日"]["月出"] == "19:06"
    assert clean["今日"]["月落"] == "09:25"
    assert clean["今日"]["空气质量预报"] == {"AQI": 25, "等级": "优", "首要污染物": "臭氧"}
    daily_fx = fx("api_daily5_jiaxing.json")
    d0 = daily_fx["DailyForecasts"][0]
    assert clean["今日"]["白天降水概率"] == d0["Day"]["PrecipitationProbability"]
    assert clean["今日"]["夜晚降水概率"] == d0["Night"]["PrecipitationProbability"]
    # 官方 Headline 原生摘要(含"比昨天")
    assert "比昨天" in clean["解读"]
    assert clean["实况"]["过去24小时温度变化"] is not None
    # 五日/逐小时/预警
    assert len(clean["五日预报"]) == 5
    row0 = clean["五日预报"][0]
    assert "降水概率" not in row0  # 已拆分为白天/夜晚
    assert row0["夜晚降水概率"] == d0["Night"]["PrecipitationProbability"]
    assert row0["白天风向"] == "东"
    assert row0["白天风速"] == 3.2
    hourly_fx = fx("api_hourly12_jiaxing.json")
    assert len(clean["逐小时预报"]) == 12
    h0 = clean["逐小时预报"][0]
    assert h0["时间"] == str(hourly_fx[0]["DateTime"])[11:16]
    assert h0["体感温度"] == hourly_fx[0]["RealFeelTemperature"]["Value"]  # details=true 扩展
    assert h0["白天"] is hourly_fx[0]["IsDaylight"]
    assert "降水强度" not in h0  # 平台无此字段(死读取已移除)
    assert clean["逐小时预报"][6]["白天"] is hourly_fx[6]["IsDaylight"]
    alerts_fx = fx("api_alerts_jiaxing.json")
    assert len(clean["预警"]) == len(alerts_fx)
    if alerts_fx:
        assert clean["预警"][0]["标题"]
        assert "嘉兴" in "".join(clean["预警"][0]["区域"])
        assert "生效" in clean["预警"][0]["摘要"]
        assert clean["预警"][0]["链接"].startswith("http")
    # 短临降水(嘉兴样本: 无雨, 官方描述透传, 序列不输出)
    assert clean["短临降水"] == {
        "两小时内有雨": False,
        "摘要": "未来2小时无降水",
        "降水类型": "",
        "官方描述": "未来2小时无降水",
    }


def test_get_weather_data_api_raw(fake_api):
    data = fake_api.get_weather_data_api("嘉兴", "k")
    raw = data["raw"]
    for key in ("location", "currentconditions", "daily_forecast", "hourly_forecast", "airquality", "alerts", "minutecast"):
        assert key in raw
    # 两级均可 JSON 序列化
    for part in ("clean", "raw"):
        assert json.loads(json.dumps(data[part], ensure_ascii=False))


def test_nowcast_failure_is_silent(skill, monkeypatch):
    """短临失败(非中国区域/接口异常)返回 None, 由调用方静默跳过(字段不出现)。"""
    def boom(path, key, **params):
        raise skill.httpx.ConnectError("offline")

    monkeypatch.setattr(skill, "_api_get", boom)
    assert skill.fetch_minute_cast(30.75, 120.75, "k") is None
    assert skill.fetch_city_minute_cast("嘉兴", "k") is None


def test_nowcast_failure_omits_field_in_clean(fake_api, monkeypatch):
    """短临不可用时 clean 中不出现"短临降水"字段, 与"两小时内有雨=false"区分。"""
    inner = fake_api._api_get

    def wrapped(path, key, **params):
        if "nowcast_cn" in path:
            raise fake_api.httpx.ConnectError("offline")
        return inner(path, key, **params)

    monkeypatch.setattr(fake_api, "_api_get", wrapped)
    clean = fake_api.get_weather_data_api("嘉兴", "k")["clean"]
    assert "短临降水" not in clean


def test_api_failure_returns_none(skill, monkeypatch):
    def boom(path, key, **params):
        raise skill.httpx.ConnectError("offline")

    monkeypatch.setattr(skill, "_api_get", boom)
    assert skill.get_weather_data_api("嘉兴", "k") is None


def test_load_api_key_env_has_priority(skill, monkeypatch):
    monkeypatch.setenv("WEATHERCN_API_KEY", "test-key-123")
    assert skill._load_api_key() == "test-key-123"  # 环境变量优先于磁盘 .env


def test_api_metric_handles_both_shapes(skill):
    assert skill._api_metric({"Metric": {"Value": 24.0}}) == 24.0
    assert skill._api_metric({"Value": 26.0}) == 26.0
    assert skill._api_metric(None) is None
    assert skill._api_metric({}) is None
