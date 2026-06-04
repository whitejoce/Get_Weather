import argparse
import sys
from pathlib import Path

from .client import WeatherClient
from .core_validation import is_invalid_city_name
from .exceptions import InvalidCityNameError, WeatherError


def run_weather_process(
    output: int = 0,
    city_name: str | None = None,
    dump_response_path: str | Path | None = None,
    client: WeatherClient | None = None,
) -> str:
    client = client or WeatherClient()

    if city_name:
        city_name = city_name.strip()
        if is_invalid_city_name(city_name):
            raise InvalidCityNameError("检测到非地名字符")
        print(" [+] 使用指定城市：" + city_name)
        code = client.get_city_code(city_name)
    else:
        address, code = client.get_city_name()
        if not address:
            address = input(" [?] 请手动输入所在地（例：广州）[输入为空即退出]：").strip()
            if not address:
                raise InvalidCityNameError("未输入城市名称")
            if is_invalid_city_name(address):
                raise InvalidCityNameError("检测到非地名字符")
            print(" [+] 使用手动输入定位位置：" + address)
            code = client.get_city_code(address)
        else:
            print(" [+] 自动定位位置：" + address)

    weather_text = client.get_weather(code, dump_response_path=dump_response_path)
    if output == 0:
        print("\n" + weather_text + "\n")
    elif output == 1:
        _show_window(weather_text)
    else:
        raise InvalidCityNameError("--output 仅支持 0 或 1")
    return weather_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weather Script with Debug Mode")
    parser.add_argument("--debug", action="store_true", help="启用 Debug 模式，仅检查状态码")
    parser.add_argument("--city", type=str, default=None, help="城市名称 (例：北京)")
    parser.add_argument(
        "--output",
        type=int,
        default=0,
        help="输出模式，0 为 shell 输出，1 为窗口输出",
    )
    parser.add_argument(
        "--dump-response",
        action="store_true",
        help="调试时保存 weather_index 原始响应到 response.html",
    )
    parser.add_argument(
        "--debug-output",
        default="debug_results.json",
        help="Debug 模式状态码结果输出文件；传入空字符串可禁用写入",
    )
    args = parser.parse_args(argv)

    client = WeatherClient()
    try:
        if args.debug:
            city_code = client.get_city_code(args.city) if args.city else "101280601"
            output_file = args.debug_output or None
            results = client.debug_urls(city_code, output_file=output_file)
            for item in results:
                if "status_code" in item:
                    print(f"URL: {item['url']}, Status Code: {item['status_code']}")
                else:
                    print(f"Error fetching URL: {item['url']}, Exception: {item['error']}")
            if output_file:
                print(f"Debug results saved to {output_file}")
            return 0

        dump_path = "response.html" if args.dump_response else None
        run_weather_process(
            output=args.output,
            city_name=args.city,
            dump_response_path=dump_path,
            client=client,
        )
        return 0
    except WeatherError as exc:
        print(f" [!] {exc}")
        print(" [#] 退出脚本")
        return 1


def _show_window(weather_text: str) -> None:
    from tkinter import INSERT, Text, Tk

    windows = Tk()
    windows.title("GetWeather")
    text1 = Text(windows)
    text1.insert(INSERT, weather_text)
    text1.pack()
    windows.mainloop()


if __name__ == "__main__":
    sys.exit(main())
