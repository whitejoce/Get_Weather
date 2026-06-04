import runpy
from pathlib import Path


SKILL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "querying-weather"
    / "scripts"
    / "GetWeather.py"
)


def test_skill_script_is_standalone() -> None:
    source = SKILL_SCRIPT.read_text(encoding="utf-8")

    assert "from get_weather" not in source
    assert "import get_weather" not in source
    assert "sys.path" not in source


def test_skill_script_loads_without_project_package_import() -> None:
    namespace = runpy.run_path(str(SKILL_SCRIPT))

    assert namespace["CheckInput"]("123")
    assert namespace["query_weather"]("") == " [!] 城市名称不能为空"
    assert namespace["parse_qweather_summary"](
        '<div class="current-abstract">测试摘要</div>'
        '<p class="city-air-chart__txt text-center">优</p>'
    ) == ("测试摘要", "优")
