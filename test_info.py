"""个人信息卡(/info)链路测试脚本。

用法:
    python test_info.py <client_id> <client_secret> <username> [mode] [day] [source]

示例:
    python test_info.py 12345 abcdef peppy 0 0 osu
    python test_info.py 12345 abcdef peppy 3 7 osu
    python test_info.py 12345 abcdef some_sb_user 4 0 ppysb
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import sys
import types
from pathlib import Path


def _import_plugin_module(module_name: str):
    """在不依赖 AstrBot 运行时的情况下导入插件子模块。"""
    package_name = "astrbot_plugin_osuscore"
    if package_name not in sys.modules:
        pkg = types.ModuleType(package_name)
        pkg.__path__ = [str(Path(__file__).resolve().parent)]
        sys.modules[package_name] = pkg
    return importlib.import_module(f"{package_name}.{module_name}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="测试 /info 个人信息卡生成")
    parser.add_argument("client_id", type=int, help="OSU OAuth client id")
    parser.add_argument("client_secret", type=str, help="OSU OAuth client secret")
    parser.add_argument("username", type=str, help="用户名")
    parser.add_argument("mode", nargs="?", default="0", help="模式代码，默认 0")
    parser.add_argument("day", nargs="?", type=int, default=0, help="对比天数，默认 0")
    parser.add_argument("source", nargs="?", default="osu", help="服务器: osu 或 ppysb")
    return parser


async def _run(args: argparse.Namespace) -> int:
    api_mod = _import_plugin_module("api")
    db_mod = _import_plugin_module("database")
    renderer_mod = _import_plugin_module("info_renderer")
    utils_mod = _import_plugin_module("utils")

    if args.mode not in utils_mod.NGM:
        print(f"[ERROR] 不支持的模式代码: {args.mode}")
        print("可用模式: " + ", ".join(sorted(utils_mod.NGM.keys(), key=lambda x: int(x))))
        return 2

    mode_name = utils_mod.NGM[args.mode]
    db = db_mod.Database("./osuscore.db")
    api_client = api_mod.OsuApiClient(args.client_id, args.client_secret)

    try:
        uid = await api_client.get_uid_by_name(args.username, args.source)
        image_bytes = await renderer_mod.draw_info(
            api_client,
            db,
            uid,
            mode_name,
            args.day,
            args.source,
            ["https://api.nerinyan.moe/profile-background"],
        )

        safe_name = args.username.replace("/", "_").replace("\\", "_")
        output = Path(f"test_info_{safe_name}_{args.source}_{mode_name}.jpg")
        output.write_bytes(image_bytes)

        print("[OK] 个人信息卡生成成功")
        print(f"  输出文件: {output}")
        print(f"  文件大小: {output.stat().st_size} bytes")
        return 0
    except Exception as e:
        print(f"[ERROR] 个人信息卡生成失败: {e}")
        return 1
    finally:
        await api_client.close()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
