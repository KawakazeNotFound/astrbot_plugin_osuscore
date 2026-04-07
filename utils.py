"""工具函数"""

import re
from typing import Any, Dict, Optional, List

# 模式映射
MODE_MAP = {
    "0": "std",
    "1": "taiko",
    "2": "ctb",
    "3": "mania"
}

MODE_REVERSE = {v: k for k, v in MODE_MAP.items()}

# 兼容 nonebot-plugin-osubot 的模式映射
GM = {
    0: "osu",
    1: "taiko",
    2: "fruits",
    3: "mania",
    4: "osu",
    5: "taiko",
    6: "fruits",
    8: "osu",
}

NGM = {
    "0": "osu",
    "1": "taiko",
    "2": "fruits",
    "3": "mania",
    "4": "rxosu",
    "5": "rxtaiko",
    "6": "rxfruits",
    "8": "aposu",
}

GMN = {
    "osu": "Std",
    "taiko": "Taiko",
    "fruits": "Ctb",
    "mania": "Mania",
    "rxosu": "RX Std",
    "rxtaiko": "RX Taiko",
    "rxfruits": "RX Ctb",
    "aposu": "AP Std",
}

FGM = {
    "osu": 0,
    "taiko": 1,
    "fruits": 2,
    "mania": 3,
    "rxosu": 4,
    "rxtaiko": 5,
    "rxfruits": 6,
    "aposu": 8,
}

# Mod 字典
MODS_DICT = {
    "NF": 1 << 0,
    "EZ": 1 << 1,
    "TD": 1 << 2,
    "HD": 1 << 3,
    "HR": 1 << 4,
    "SD": 1 << 5,
    "DT": 1 << 6,
    "RX": 1 << 7,
    "HT": 1 << 8,
    "NC": 1 << 9,
    "FL": 1 << 10,
    "AT": 1 << 11,
    "SO": 1 << 12,
}


def parse_mods(mod_string: str) -> List[str]:
    """
    解析 Mod 字符串转为列表
    例如: "HDDT" -> ["HD", "DT"]
    """
    if not mod_string:
        return []

    mods = []
    mod_string = mod_string.upper()

    # 分解两个字符的 mod
    i = 0
    while i < len(mod_string):
        if i + 1 < len(mod_string):
            two_char = mod_string[i:i+2]
            if two_char in MODS_DICT:
                mods.append(two_char)
                i += 2
                continue

        # 单个字符可能不合法，跳过
        i += 1

    return mods


def parse_command_args(text: str) -> Dict[str, Any]:
    """
    解析命令参数
    支持格式: /pr [username] [:mode] [+mods]
    例如: /pr myname :1 +HD
    """
    args = {
        "username": None,
        "mode": None,
        "mode_specified": False,
        "mods": [],
    }

    # 统一全角符号，尽量兼容输入习惯。
    text = text.strip().replace("：", ":").replace("＋", "+")

    # 提取模式 :0-3
    mode_match = re.search(r':\s*([0-3])', text)
    if mode_match:
        args["mode"] = mode_match.group(1)
        args["mode_specified"] = True
        text = text[:mode_match.start()] + text[mode_match.end():]

    # 提取 mod +HDDT
    mods_match = re.search(r'\+\s*([A-Za-z]+)', text)
    if mods_match:
        args["mods"] = parse_mods(mods_match.group(1))
        text = text[:mods_match.start()] + text[mods_match.end():]

    # 剩余的作为用户名
    username = text.strip()
    if username:
        args["username"] = username

    return args


def format_score_rank(rank: str) -> str:
    """格式化排名"""
    rank_map = {
        "XH": "SS+",
        "X": "SS",
        "SH": "S+",
        "S": "S",
        "A": "A",
        "B": "B",
        "C": "C",
        "D": "D",
        "F": "F",
    }
    return rank_map.get(rank.upper(), rank)


def format_accuracy(accuracy: float) -> str:
    """格式化准确度"""
    return f"{accuracy * 100:.2f}%"


def format_number(num: int) -> str:
    """格式化数字（带千分位）"""
    return f"{num:,}"


def get_mode_name(mode: str) -> str:
    """获取模式名称"""
    mode_names = {
        "0": "Standard",
        "1": "Taiko",
        "2": "Catch",
        "3": "Mania"
    }
    return mode_names.get(mode, "Unknown")


def get_mods_string(mods: list) -> str:
    """获取 Mod 字符串表示"""
    if not mods:
        return "No Mod"
    return "".join([mod["acronym"] if isinstance(mod, dict) else mod for mod in mods])


def info_calc(n1: Optional[float], n2: Optional[float], rank: bool = False, pp: bool = False):
    """按参考实现计算资料卡变化值与箭头。"""
    if not n1 or not n2:
        return "", 0
    num = n1 - n2
    if num < 0:
        if rank:
            op, value = "↑", num * -1
        elif pp:
            op, value = "↓", num * -1
        else:
            op, value = "-", num * -1
    elif num > 0:
        if rank:
            op, value = "↓", num
        elif pp:
            op, value = "↑", num
        else:
            op, value = "+", num
    else:
        op, value = "", 0
    return [op, value]
