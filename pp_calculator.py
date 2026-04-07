"""PP计算模块 - 使用rosu-pp-py计算PP及其分解"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import httpx

try:
    from rosu_pp_py import Beatmap, Performance
except ImportError:
    print("警告: rosu-pp-py未安装，PP计算功能将不可用")
    Beatmap = None
    Performance = None


# .osu文件存储路径
OSU_FILES_DIR = Path(__file__).parent / "data" / "osu" / "map"
OSU_FILES_DIR.mkdir(parents=True, exist_ok=True)


async def download_osu_file(beatmapset_id: int, beatmap_id: int) -> Optional[Path]:
    """下载.osu文件
    
    Args:
        beatmapset_id: 谱面集ID
        beatmap_id: 谱面ID
        
    Returns:
        下载的文件路径，失败返回None
    """
    # 检查文件是否已存在
    file_path = OSU_FILES_DIR / str(beatmapset_id) / f"{beatmap_id}.osu"
    if file_path.exists():
        return file_path
    
    # 下载源（带回退）
    urls = [
        f"https://osu.ppy.sh/osu/{beatmap_id}",
        f"https://osu.direct/api/osu/{beatmap_id}",
        f"https://catboy.best/osu/{beatmap_id}",
    ]
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    for url in urls:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                
                # 保存文件
                with open(file_path, "wb") as f:
                    f.write(resp.content)
                
                print(f"Downloaded .osu file: {file_path}")
                return file_path
        except Exception as e:
            print(f"Failed to download from {url}: {e}")
            continue
    
    print(f"Failed to download .osu file for beatmap {beatmap_id}")
    return None


def calculate_pp(
    osu_file_path: Path,
    mods: list,
    accuracy: float,
    max_combo: int,
    n300: int,
    n100: int,
    n50: int,
    nmiss: int,
    mode: int = 0
) -> Dict[str, float]:
    """计算PP及其分解
    
    Args:
        osu_file_path: .osu文件路径
        mods: Mod列表 (如 ['HD', 'DT'])
        accuracy: 准确率 (0-1范围)
        max_combo: 最大连击
        n300: 300数量
        n100: 100数量
        n50: 50数量
        nmiss: Miss数量
        mode: 游戏模式 (0=std, 1=taiko, 2=ctb, 3=mania)
        
    Returns:
        包含pp, pp_aim, pp_speed, pp_acc, stars的字典
    """
    if not Beatmap or not Performance:
        return {
            'pp': 0.0,
            'pp_aim': 0.0,
            'pp_speed': 0.0,
            'pp_acc': 0.0,
            'stars': 0.0
        }
    
    try:
        # 读取谱面
        beatmap = Beatmap(path=str(osu_file_path))
        
        # 创建Performance计算器并直接传入统计数据
        perf = Performance(
            mods=_convert_mods_to_int(mods),
            combo=max_combo,
            n300=n300,
            n100=n100,
            n50=n50,
            misses=nmiss
        )
        
        # 计算PP
        result = perf.calculate(beatmap)
        
        return {
            'pp': result.pp,
            'pp_aim': getattr(result, 'pp_aim', 0.0),
            'pp_speed': getattr(result, 'pp_speed', 0.0),
            'pp_acc': getattr(result, 'pp_acc', 0.0),
            'stars': result.difficulty.stars
        }
    except Exception as e:
        print(f"PP calculation error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'pp': 0.0,
            'pp_aim': 0.0,
            'pp_speed': 0.0,
            'pp_acc': 0.0,
            'stars': 0.0
        }


def calculate_if_fc_pp(
    osu_file_path: Path,
    mods: list,
    n300: int,
    n100: int,
    n50: int,
    nmiss: int,
    mode: int = 0
) -> float:
    """计算如果是FC的PP
    
    Args:
        osu_file_path: .osu文件路径
        mods: Mod列表
        n300: 300数量
        n100: 100数量  
        n50: 50数量
        nmiss: Miss数量
        mode: 游戏模式
        
    Returns:
        IF FC的PP值
    """
    if not Beatmap or not Performance:
        return 0.0
    
    try:
        beatmap = Beatmap(path=str(osu_file_path))
        
        # 将miss重新分配为100来保持相似的准确率
        total_hits = n300 + n100 + n50 + nmiss
        if total_hits == 0:
            return 0.0
        
        # 计算如果是FC的统计数据
        # 将miss按比例转换为100和300
        ratio = 1 - n300 / (total_hits - nmiss) if (total_hits - nmiss) > 0 else 0
        new_n100 = int(ratio * nmiss)
        new_n300 = n300 + (nmiss - new_n100)
        new_n100 += n100
        
        # 创建Performance计算器并直接传入统计数据
        perf = Performance(
            mods=_convert_mods_to_int(mods),
            n300=new_n300,
            n100=new_n100,
            n50=n50,
            misses=0
        )
        
        result = perf.calculate(beatmap)
        return result.pp
    except Exception as e:
        print(f"IF FC PP calculation error: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


def calculate_ss_pp(
    osu_file_path: Path,
    mods: list,
    mode: int = 0
) -> float:
    """计算SS成绩的PP
    
    Args:
        osu_file_path: .osu文件路径
        mods: Mod列表
        mode: 游戏模式
        
    Returns:
        SS PP值
    """
    if not Beatmap or not Performance:
        return 0.0
    
    try:
        beatmap = Beatmap(path=str(osu_file_path))
        
        # 创建Performance计算器，不设置state意味着满分
        perf = Performance(mods=_convert_mods_to_int(mods))
        
        result = perf.calculate(beatmap)
        return result.pp
    except Exception as e:
        print(f"SS PP calculation error: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


def _convert_mods_to_int(mods: list) -> int:
    """将Mod列表转换为rosu-pp-py的位掩码格式
    
    Args:
        mods: Mod字符串列表，如 ['HD', 'DT']
        
    Returns:
        Mod位掩码整数
    """
    # rosu-pp-py的Mod位掩码
    MOD_BITS = {
        'NF': 1,
        'EZ': 2,
        'TD': 4,  # Touch Device
        'HD': 8,
        'HR': 16,
        'SD': 32,
        'DT': 64,
        'RX': 128,  # Relax
        'HT': 256,
        'NC': 512,  # Nightcore (包含DT)
        'FL': 1024,
        'SO': 4096,
        'PF': 16384,
        'FI': 1048576,  # Fade In
        'MR': 536870912,  # Mirror
    }
    
    result = 0
    for mod in mods:
        mod_upper = mod.upper()
        if mod_upper in MOD_BITS:
            result |= MOD_BITS[mod_upper]
            # NC自动包含DT
            if mod_upper == 'NC':
                result |= MOD_BITS['DT']
    
    return result


async def calculate_all_pp_info(
    beatmap_id: int,
    beatmapset_id: int,
    mods: list,
    accuracy: float,
    max_combo: int,
    statistics: Dict[str, int],
    mode: int = 0
) -> Dict[str, Any]:
    """计算所有PP信息（当前PP、IF FC、SS PP及分解）
    
    Args:
        beatmap_id: 谱面ID
        beatmapset_id: 谱面集ID
        mods: Mod列表
        accuracy: 准确率(0-1)
        max_combo: 最大连击
        statistics: 统计数据字典 {'count_300': x, 'count_100': y, ...}
        mode: 游戏模式
        
    Returns:
        包含所有PP信息的字典
    """
    # 下载.osu文件
    osu_file = await download_osu_file(beatmapset_id, beatmap_id)
    if not osu_file:
        return {
            'pp': 0.0,
            'pp_aim': 0.0,
            'pp_speed': 0.0,
            'pp_acc': 0.0,
            'if_fc_pp': 0.0,
            'ss_pp': 0.0,
            'stars': 0.0
        }
    
    # 提取统计数据
    n300 = statistics.get('count_300', 0)
    n100 = statistics.get('count_100', 0)
    n50 = statistics.get('count_50', 0)
    nmiss = statistics.get('count_miss', 0)
    
    # 计算当前PP
    current_pp = calculate_pp(
        osu_file, mods, accuracy, max_combo,
        n300, n100, n50, nmiss, mode
    )
    
    # 计算IF FC PP
    if_fc_pp = calculate_if_fc_pp(
        osu_file, mods, n300, n100, n50, nmiss, mode
    )
    
    # 计算SS PP
    ss_pp = calculate_ss_pp(osu_file, mods, mode)
    
    return {
        'pp': current_pp['pp'],
        'pp_aim': current_pp['pp_aim'],
        'pp_speed': current_pp['pp_speed'],
        'pp_acc': current_pp['pp_acc'],
        'if_fc_pp': if_fc_pp,
        'ss_pp': ss_pp,
        'stars': current_pp['stars']
    }
