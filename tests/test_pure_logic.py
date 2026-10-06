"""纯逻辑测试：不依赖 AstrBot 运行时。

环境里装有 AstrBot 时直接使用真实模块；否则注入最小 stub 后加载 main.py，
只验证与框架无关的部分（面额解析、参数切分、资源文件对应关系）。

运行：python tests/test_pure_logic.py
"""

import sys
import types
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))


def _install_astrbot_stub() -> bool:
    """没有 astrbot 时注入 stub，返回是否注入。"""
    try:
        import astrbot  # noqa: F401
        return False
    except ImportError:
        pass

    astrbot = types.ModuleType("astrbot")
    api = types.ModuleType("astrbot.api")

    class _Logger:
        def info(self, *a, **k):
            pass

        def warning(self, *a, **k):
            pass

        def error(self, *a, **k):
            pass

        def exception(self, *a, **k):
            pass

    api.logger = _Logger()
    api.AstrBotConfig = dict

    event = types.ModuleType("astrbot.api.event")

    class _Filter:
        @staticmethod
        def _passthrough(*a, **k):
            def deco(fn):
                return fn

            return deco

        command = _passthrough
        permission_type = _passthrough
        regex = _passthrough

    event.filter = _Filter()
    event.AstrMessageEvent = object

    star = types.ModuleType("astrbot.api.star")

    class _Star:
        def __init__(self, context=None):
            self.context = context

    def _register(*a, **k):
        def deco(cls):
            return cls

        return deco

    star.Context = object
    star.Star = _Star
    star.register = _register
    star.StarTools = object

    api.event = event
    api.star = star
    astrbot.api = api
    sys.modules["astrbot"] = astrbot
    sys.modules["astrbot.api"] = api
    sys.modules["astrbot.api.event"] = event
    sys.modules["astrbot.api.star"] = star
    return True


USED_STUB = _install_astrbot_stub()
import main  # noqa: E402

FAILURES = []


def check(label, got, expected):
    if got != expected:
        FAILURES.append(f"{label}: got {got!r}, expected {expected!r}")
        print(f"FAIL  {label}: got {got!r}, expected {expected!r}")
    else:
        print(f"ok    {label}")


def test_parse_amount():
    cases = {
        "1亿": 100_000_000,
        "一亿": 100_000_000,
        "壹億": 100_000_000,
        "2亿": 200_000_000,
        "两亿": 200_000_000,
        "5亿": 500_000_000,
        "伍億": 500_000_000,
        "5000万": 50_000_000,
        "伍仟萬": 50_000_000,
        "1000万": 10_000_000,
        "壹仟萬": 10_000_000,
        "2000万": 20_000_000,
        "100000000": 100_000_000,
        "100,000,000": 100_000_000,
        "100 000 000": 100_000_000,
        "500000000": 500_000_000,
        "1.5亿": 150_000_000,
    }
    for text, expected in cases.items():
        check(f"parse_amount({text!r})", main.parse_amount(text), expected)

    for bad in ("", "abc", "鲸元券", "亿"):
        check(f"parse_amount({bad!r}) -> None", main.parse_amount(bad), None)


def test_split_args():
    cases = {
        "/鲸元券 1亿": ["1亿"],
        "鲸元券 反面 1亿": ["反面", "1亿"],
        "/鲸元券 双面 200000000": ["双面", "200000000"],
        "/鲸元券": [],
        "/词元券 列表": ["列表"],
        "/鲸元 随机": ["随机"],
    }
    for text, expected in cases.items():
        check(f"split_args({text!r})", main.WhaleTokenPlugin._split_args(text), expected)


def test_tiers_and_resources():
    check("tier count", len(main.TIERS), 6)
    for tier in main.TIERS:
        for face in ("front", "back"):
            path = main.RESOURCE_DIR / f"{face}_{tier['key']}.jpg"
            check(f"resource exists {path.name}", path.is_file(), True)
        check(f"unique value {tier['amount']}", isinstance(tier["value"], int), True)
    check(
        "series poster exists",
        (main.RESOURCE_DIR / "series-all.jpg").is_file(),
        True,
    )


def test_default_config():
    """后台配置：默认面额与默认票面。"""
    p = main.WhaleTokenPlugin(None, {"default_amount": "2亿", "default_faces": "双面"})
    check("default_amount=2亿", p._resolve_default_tier()["amount"], "200,000,000")
    check("default_faces=双面", p._resolve_default_faces(), "both")

    empty = main.WhaleTokenPlugin(None, {})
    check("empty default_amount is random", empty._resolve_default_tier() in main.TIERS, True)
    check("empty default_faces -> front", empty._resolve_default_faces(), "front")

    bad = main.WhaleTokenPlugin(None, {"default_amount": "乱写", "default_faces": "back"})
    check("invalid amount -> fallback 1亿", bad._resolve_default_tier()["amount"], "100,000,000")
    check("default_faces=back", bad._resolve_default_faces(), "back")

    for raw, expected in (("正面", "front"), ("反面", "back"), ("both", "both"), ("xyz", "front")):
        plugin = main.WhaleTokenPlugin(None, {"default_faces": raw})
        check(f"default_faces={raw}", plugin._resolve_default_faces(), expected)


def test_all_amounts_resolve_to_tier():
    for tier in main.TIERS:
        for text in (tier["amount"], str(tier["value"]), tier["cn"]):
            value = main.parse_amount(text)
            matched = next((t for t in main.TIERS if t["value"] == value), None)
            check(f"{text!r} -> {tier['amount']}", matched["amount"], tier["amount"])


if __name__ == "__main__":
    print(f"astrbot stub installed: {USED_STUB}")
    test_parse_amount()
    test_split_args()
    test_tiers_and_resources()
    test_default_config()
    test_all_amounts_resolve_to_tier()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED")
        sys.exit(1)
    print("ALL PASSED")
