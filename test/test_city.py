"""城市码查找测试: 轻量搜索(toy1) + 完整城市列表(city.js)回退。全部离线。"""

import json
from pathlib import Path

import pytest

import GetWeather

FIXTURES = Path(__file__).resolve().parent / "sample"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, body: str) -> None:
        self.content = body.encode("utf-8")
        self.text = body

    def raise_for_status(self) -> None:
        pass


@pytest.fixture(scope="module")
def city_js() -> str:
    return (FIXTURES / "city.js").read_text(encoding="utf-8")


def test_get_city_code_with_local_raw_content(city_js):
    assert GetWeather.get_city_code("北京", raw_content=city_js) == "101010100"
    assert GetWeather.get_city_code("嘉兴", raw_content=city_js) == "101210301"
    assert GetWeather.get_city_code("广州", raw_content=city_js) == "101280101"
    assert GetWeather.get_city_code("深圳", raw_content=city_js) == "101280601"


def test_get_city_code_accepts_stripped_json(city_js):
    """旧样本 city.json(去掉 `var city_data = ` 前缀的纯 JSON)同样可用。"""
    stripped = (FIXTURES / "city.json").read_text(encoding="utf-8")

    assert GetWeather.get_city_code("北京", raw_content=stripped) == "101010100"


def test_get_city_code_unknown_city_exits(city_js, capsys):
    with pytest.raises(SystemExit):
        GetWeather.get_city_code("不存在的城市", raw_content=city_js)

    assert "未能找到该地区信息" in capsys.readouterr().err


def test_find_city_by_name_direct(city_js):
    data = json.loads(city_js[city_js.find("{") :])

    hit = GetWeather.find_city_by_name("嘉兴", data)
    assert hit is not None
    assert hit["AREAID"] == "101210301"
    assert GetWeather.find_city_by_name("不存在的城市", data) is None


# ---------- 轻量城市搜索(toy1) ----------


def test_search_city_code_exact_match(monkeypatch):
    body = load("toy1_search_jiaxing.txt")
    monkeypatch.setattr(GetWeather.httpx, "get", lambda *a, **k: FakeResponse(body))

    assert GetWeather.search_city_code("嘉兴") == "101210301"


def test_search_city_code_filters_fuzzy_matches(monkeypatch):
    """模糊命中(如"嘉兴路街道")不能当作"嘉兴"。"""
    body = '[{"ref":"101020100002~shanghai~嘉兴路街道~jiaxinglujiedao~虹口~hongkou~021~200000~shx~上海"}]'
    monkeypatch.setattr(GetWeather.httpx, "get", lambda *a, **k: FakeResponse(body))

    assert GetWeather.search_city_code("嘉兴") is None


def test_search_city_code_returns_none_on_network_error(monkeypatch):
    def boom(*args, **kwargs):
        raise ConnectionError("offline")

    monkeypatch.setattr(GetWeather.httpx, "get", boom)

    assert GetWeather.search_city_code("嘉兴") is None


def test_get_city_code_falls_back_to_city_js(monkeypatch, city_js):
    """轻量搜索未命中时回退完整城市列表(约345KB)。"""
    monkeypatch.setattr(GetWeather, "search_city_code", lambda city: None)
    monkeypatch.setattr(GetWeather.httpx, "get", lambda *a, **k: FakeResponse(city_js))

    assert GetWeather.get_city_code("嘉兴") == "101210301"
