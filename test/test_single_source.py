"""单一源文件守卫: 根 GetWeather.py 必须与 skill 脚本字节一致。

修改天气逻辑时只改 skills/querying-weather/scripts/GetWeather.py, 然后同步:

    Copy-Item skills/querying-weather/scripts/GetWeather.py GetWeather.py

忘了同步会在此测试失败(CI 拦截), 杜绝双副本分叉。
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT_SCRIPT = REPO / "GetWeather.py"
SKILL_SCRIPT = REPO / "skills" / "querying-weather" / "scripts" / "GetWeather.py"


def test_root_and_skill_script_are_identical():
    assert ROOT_SCRIPT.read_bytes() == SKILL_SCRIPT.read_bytes(), (
        "根 GetWeather.py 与 skill 脚本已分叉! 请同步: "
        "Copy-Item skills/querying-weather/scripts/GetWeather.py GetWeather.py"
    )
