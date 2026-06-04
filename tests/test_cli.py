from get_weather.cli import main, run_weather_process
from get_weather.exceptions import InvalidCityNameError


class FakeClient:
    def __init__(self) -> None:
        self.debug_calls: list[tuple[str, str | None]] = []

    def get_city_code(self, city: str) -> str:
        return {"北京": "101010100"}[city]

    def get_city_name(self) -> tuple[str, str]:
        return "北京", "101010100"

    def get_weather(self, code: str, dump_response_path=None) -> str:
        return f"weather for {code}, dump={dump_response_path}"

    def debug_urls(self, city_code: str, output_file="debug_results.json"):
        self.debug_calls.append((city_code, output_file))
        return [{"url": "https://example.com", "status_code": 200}]


def test_run_weather_process_uses_city_name(capsys) -> None:
    result = run_weather_process(city_name="北京", client=FakeClient())

    captured = capsys.readouterr()
    assert result == "weather for 101010100, dump=None"
    assert "使用指定城市：北京" in captured.out


def test_run_weather_process_rejects_invalid_city() -> None:
    try:
        run_weather_process(city_name="beijing", client=FakeClient())
    except InvalidCityNameError as exc:
        assert "非地名字符" in str(exc)
    else:
        raise AssertionError("expected InvalidCityNameError")


def test_main_returns_nonzero_for_invalid_city(capsys) -> None:
    code = main(["--city", "123"])

    captured = capsys.readouterr()
    assert code == 1
    assert "退出脚本" in captured.out
