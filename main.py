"""AstrBot 鲸元券（WHALE-YUAN TOKEN）票面查看插件。

鲸元券是一个虚构货币视觉设计项目的产物：六档面额、正反两面、纯矢量票面。
本插件把该项目的成品票面打包进 resources/，按面额返回对应票面供聊天展示。

指令：
    /鲸元券 <面额>        发送该面额票面正面（如 /鲸元券 1亿）
    /鲸元券 反面 <面额>    发送票面反面
    /鲸元券 双面 <面额>    正反两面一起发
    /鲸元券 列表          列出全部面额
    /鲸元券 全系列        发送全系列总表长图
    /鲸元券 随机          随机抽一档
    /鲸元券 帮助          查看用法

声明：票面为虚构设定物，非真实货币；票面上的 DeepSeek 标识属第三方商标，
本项目与 DeepSeek 官方无隶属、合作或背书关系。
"""

import random
import re
from pathlib import Path
from typing import Optional

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

PLUGIN_NAME = "astrbot_plugin_whale_token"
RESOURCE_DIR = Path(__file__).resolve().parent / "resources"

# 六档面额，数据取自项目 build/palette.py 与 docs/spec-book.md
TIERS = [
    {
        "key": "010000000",
        "value": 10_000_000,
        "amount": "10,000,000",
        "cn": "壹仟萬",
        "theme": "引航",
        "mm": 132.0,
        "height_mm": 61.6,
        "spot": "#24506B",
        "spot_name": "深青蓝",
        "reverse": "灯浮标",
    },
    {
        "key": "020000000",
        "value": 20_000_000,
        "amount": "20,000,000",
        "cn": "贰仟萬",
        "theme": "夜航",
        "mm": 142.0,
        "height_mm": 66.3,
        "spot": "#1F5A52",
        "spot_name": "深海绿",
        "reverse": "罗盘玫瑰",
    },
    {
        "key": "050000000",
        "value": 50_000_000,
        "amount": "50,000,000",
        "cn": "伍仟萬",
        "theme": "港市",
        "mm": 148.0,
        "height_mm": 69.0,
        "spot": "#4A3A6E",
        "spot_name": "紫罗兰",
        "reverse": "门吊与货箱",
    },
    {
        "key": "100000000",
        "value": 100_000_000,
        "amount": "100,000,000",
        "cn": "壹億",
        "theme": "守望",
        "mm": 150.0,
        "height_mm": 70.0,
        "spot": "#1B2657",
        "spot_name": "藏青",
        "reverse": "灯塔",
    },
    {
        "key": "200000000",
        "value": 200_000_000,
        "amount": "200,000,000",
        "cn": "贰億",
        "theme": "星图",
        "mm": 158.0,
        "height_mm": 73.7,
        "spot": "#8A5A2B",
        "spot_name": "赭金",
        "reverse": "北斗七星",
    },
    {
        "key": "500000000",
        "value": 500_000_000,
        "amount": "500,000,000",
        "cn": "伍億",
        "theme": "远洋",
        "mm": 176.0,
        "height_mm": 82.1,
        "spot": "#2E2717",
        "spot_name": "玄金",
        "reverse": "三十二向罗经花",
    },
]

COMMANDS = ("鲸元券", "词元券", "鲸元", "whaletoken")

HELP_TEXT = (
    "🪙 鲸元券 · WHALE-YUAN TOKEN\n"
    "用法：/鲸元券 <面额>\n"
    "示例：/鲸元券 1亿　/鲸元券 5000万　/鲸元券 200000000\n"
    "其他：/鲸元券 列表 · /鲸元券 全系列 · /鲸元券 随机\n"
    "　　　/鲸元券 反面 <面额> · /鲸元券 双面 <面额>\n"
    "面额支持「1亿 / 一亿 / 壹億 / 100000000」等写法。\n"
    "※ 虚构设定物，非真实货币。"
)

LIST_TEXT = (
    "🪙 鲸元券 · 面额一览（6 档）\n"
    + "\n".join(
        f"{t['amount']}｜{t['theme']}｜{t['mm']:.1f}×{t['height_mm']:.1f}mm｜{t['spot']}"
        for t in TIERS
    )
    + "\n发送 /鲸元券 1亿 查看票面。"
)

# 中文数字与单位（覆盖大写与小写写法）
_CN_DIGITS = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    "壹": 1, "贰": 2, "叁": 3, "肆": 4, "伍": 5, "陆": 6, "柒": 7, "捌": 8, "玖": 9,
}
_CN_UNITS = {"十": 10, "拾": 10, "百": 100, "佰": 100, "千": 1000, "仟": 1000}
_CN_BIG = {"万": 10**4, "萬": 10**4, "亿": 10**8, "億": 10**8}


def _cn_to_number(text: str) -> Optional[int]:
    """把「壹仟萬 / 一亿 / 两千万」这类写法转成整数，无法解析返回 None。"""
    total = section = num = 0
    seen = False
    for ch in text:
        if ch in _CN_DIGITS:
            num = _CN_DIGITS[ch]
            seen = True
        elif ch in _CN_UNITS:
            section += (num or 1) * _CN_UNITS[ch]
            num = 0
            seen = True
        elif ch in _CN_BIG:
            section = (section + num) * _CN_BIG[ch]
            total += section
            section = num = 0
            seen = True
        else:
            return None
    if not seen:
        return None
    value = total + section + num
    return value if value > 0 else None


def parse_amount(text: str) -> Optional[int]:
    """解析用户输入的面额文本，返回数值（TOKEN），无法解析返回 None。"""
    if not text:
        return None
    s = re.sub(r"[\s,_，、]", "", text.strip().lower())
    s = s.replace("token", "").replace("₮", "").replace("个", "")
    if not s:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return int(float(s))
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([亿万萬億])", s)
    if m:
        multiplier = 10**8 if m.group(2) in "亿億" else 10**4
        return int(float(m.group(1)) * multiplier)
    return _cn_to_number(s)


@register(
    PLUGIN_NAME,
    "kuaiyidian123",
    "鲸元券票面查看插件：按面额返回对应票面图，支持列表/随机/全系列/正反面",
    "1.0.0",
)
class WhaleTokenPlugin(Star):
    def __init__(self, context: Context, config: Optional[AstrBotConfig] = None):
        super().__init__(context)
        self.config = config or {}
        if not RESOURCE_DIR.is_dir():
            logger.warning(f"[{PLUGIN_NAME}] 未找到资源目录：{RESOURCE_DIR}")
        logger.info(f"[{PLUGIN_NAME}] 插件初始化完成，共 {len(TIERS)} 档面额")

    # ---------- 指令 ----------

    @filter.command("鲸元券", alias={"词元券", "鲸元"})
    async def cmd_whale_token(self, event: AstrMessageEvent):
        """鲸元券票面查看：/鲸元券 1亿"""
        args = self._split_args(event.message_str)
        if not args:
            # 不带参数：按后台配置的默认面额与默认票面发送
            tier = self._resolve_default_tier()
            for result in await self._send_tier(event, tier, self._resolve_default_faces()):
                yield result
            return

        head = args[0]
        rest = args[1:]

        if head in ("帮助", "help", "?", "？"):
            yield event.plain_result(HELP_TEXT)
            return
        if head in ("列表", "一览", "list"):
            yield event.plain_result(LIST_TEXT)
            return
        if head in ("全系列", "总表", "series", "总览"):
            for result in await self._send_series(event):
                yield result
            return
        if head in ("随机", "random", "抽"):
            tier = random.choice(TIERS)
            for result in await self._send_tier(event, tier, "both"):
                yield result
            return

        faces = "front"
        if head in ("反面", "背面", "back"):
            faces = "back"
        elif head in ("双面", "正反", "both", "两面"):
            faces = "both"
        else:
            rest = args

        if not rest:
            yield event.plain_result(HELP_TEXT)
            return

        value = parse_amount(rest[0])
        tier = next((t for t in TIERS if t["value"] == value), None)
        if tier is None:
            yield event.plain_result(
                f"❌ 未识别面额「{rest[0]}」，本插件共 6 档：\n" + LIST_TEXT
            )
            return

        for result in await self._send_tier(event, tier, faces):
            yield result

    # ---------- 发送 ----------

    async def _send_tier(self, event: AstrMessageEvent, tier: dict, faces: str) -> list:
        """构造某档面额的票面图发送结果（可指定正面/反面/双面）。"""
        results = []
        wanted = ("front", "back") if faces == "both" else (faces,)
        for face in wanted:
            path = RESOURCE_DIR / f"{face}_{tier['key']}.jpg"
            if not path.is_file():
                logger.warning(f"[{PLUGIN_NAME}] 缺少资源文件：{path}")
                continue
            results.append(event.image_result(str(path)))
        if not results:
            return [
                event.plain_result(
                    "❌ 票面图片缺失，请重新安装插件或执行 tools/build_resources.ps1 重新生成。"
                )
            ]
        if self.config.get("send_info_text", True):
            results.append(event.plain_result(self._tier_text(tier)))
        return results

    async def _send_series(self, event: AstrMessageEvent) -> list:
        """构造全系列总表长图的发送结果。"""
        if not self.config.get("enable_series_poster", True):
            return [event.plain_result("❌ 全系列总表已在插件配置中关闭。")]
        path = RESOURCE_DIR / "series-all.jpg"
        if not path.is_file():
            return [event.plain_result("❌ 全系列总表图片缺失。")]
        results = [event.image_result(str(path))]
        if self.config.get("send_info_text", True):
            results.append(
                event.plain_result("六档面额正反面按真实相对尺寸排列，票面为虚构设定物。")
            )
        return results

    # ---------- 工具 ----------

    def _resolve_default_tier(self) -> dict:
        """取后台配置的默认面额；配置为空或 random 时随机抽一档。"""
        raw = str(self.config.get("default_amount") or "").strip()
        if not raw or raw.lower() in ("random", "随机", "抽"):
            return random.choice(TIERS)
        value = parse_amount(raw)
        tier = next((t for t in TIERS if t["value"] == value), None)
        if tier is None:
            logger.warning(
                f"[{PLUGIN_NAME}] 后台配置的默认面额「{raw}」无法识别，已回退到 100,000,000。"
            )
            tier = next(t for t in TIERS if t["value"] == 100_000_000)
        return tier

    def _resolve_default_faces(self) -> str:
        """取后台配置的默认票面：front / back / both。"""
        raw = str(self.config.get("default_faces") or "front").strip().lower()
        if raw in ("back", "reverse", "反面", "背面"):
            return "back"
        if raw in ("both", "两面", "双面", "正反"):
            return "both"
        return "front"

    @staticmethod
    def _split_args(message_str: str) -> list:
        """剥离命令前缀后按空白切分参数。"""
        text = (message_str or "").strip()
        if text.startswith("/"):
            text = text[1:]
        for cmd in COMMANDS:
            if text.startswith(cmd):
                text = text[len(cmd):]
                break
        return text.split()

    @staticmethod
    def _tier_text(tier: dict) -> str:
        return (
            f"🪙 鲸元券 · {tier['cn']} TOKEN（{tier['amount']}）\n"
            f"主题：{tier['theme']}\n"
            f"券幅：{tier['mm']:.1f} × {tier['height_mm']:.1f} mm\n"
            f"专色：{tier['spot']} {tier['spot_name']}\n"
            f"反面主景：{tier['reverse']}\n"
            f"发行：DeepSeek Token银行\n"
            f"※ 虚构设定物，非真实货币。"
        )

    async def terminate(self):
        logger.info(f"[{PLUGIN_NAME}] 插件已卸载。")
