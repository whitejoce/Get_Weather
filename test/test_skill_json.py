"""skill 脚本 --json/--raw 数据模式离线测试(今日 AI 解读的数据契约)。"""

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


def test_skill_script_is_standalone():
    source = SKILL_SCRIPT.read_text(encoding="utf-8")
    assert "from get_weather" not in source
    assert "import get_weather" not in source
    assert "sys.path" not in source


@pytest.fixture
def serve_fixtures(skill, monkeypatch):
    idx = (FIXTURES / "weather_index_jiaxing.html").read_text(encoding="utf-8")
    cal = (FIXTURES / "calendar_new_jiaxing.html").read_text(encoding="utf-8")

    def fake_fetch_text(url, headers=None, *, timeout=10):
        if "weather_index" in url:
            return idx
        if "calendar_new" in url:
            return cal
        raise AssertionError(f"不应请求: {url}")

    monkeypatch.setattr(skill, "fetch_text", fake_fetch_text)
    return skill


def test_get_weather_data_clean_structure(serve_fixtures):
    data = serve_fixtures.get_weather_data("101210301", today="20260929")
    clean = data["clean"]

    assert clean["城市"] == {"名称": "嘉兴", "英文": "jiaxing", "代码": "101210301"}
    assert clean["实况"]["天气"] == "阴"
    assert clean["实况"]["空气质量"] == {"AQI": "26", "等级": "优", "PM2.5": "26"}
    assert clean["今日"] == {"白天": "小雨", "夜晚": "多云", "最高温": "26", "最低温": "22"}
    assert clean["昨日"]["日期"] == "20260928"
    assert clean["昨日"]["最高温"] == "26"
    assert clean["昨日"]["最低温"] == "22"
    assert clean["解读"] == "今天白天有小雨，夜晚多云，温度和昨天差不多，现在24°，空气不错。"
    assert len(clean["生活指数"]) == 30
    assert "雨伞指数" in clean["生活指数"]
    assert len(clean["五日预报"]) == 5
    assert clean["五日预报"][0]["说明"] == "今天"
    assert clean["五日预报"][0]["白天"] == "小雨"
    assert clean["预警"] == []


def test_get_weather_data_raw_structure(serve_fixtures):
    data = serve_fixtures.get_weather_data("101210301", today="20260929")
    raw = data["raw"]

    assert raw["dataSK"]["cityname"] == "嘉兴"
    assert raw["alarmDZ"] == {"w": []}
    assert len(raw["fc"]) == 5
    assert raw["fc40"] and raw["yesterday_obs"]["date"] == "20260928"


def test_clean_data_is_json_serializable(serve_fixtures):
    data = serve_fixtures.get_weather_data("101210301", today="20260929")

    for part in ("clean", "raw"):
        payload = json.dumps(data[part], ensure_ascii=False)
        assert json.loads(payload) == data[part]
