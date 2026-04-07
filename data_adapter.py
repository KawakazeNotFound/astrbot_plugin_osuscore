"""数据适配器 - 将OSU API v2的数据格式转换为图片生成器需要的格式"""

from typing import Dict, Any, List


def adapt_api_data_for_image(api_score_data: Dict[str, Any]) -> tuple:
    """
    将OSU API v2返回的数据转换为图片生成器需要的格式
    
    Args:
        api_score_data: API返回的完整成绩数据
    
    Returns:
        (user_info, score_info, beatmap_info) 三元组
    """
    
    # 提取user信息
    user_data = api_score_data.get('user', {})
    user_info = {
        'id': user_data.get('id'),
        'username': user_data.get('username', '???'),
        'country_code': user_data.get('country_code', 'XX'),
        'avatar_url': user_data.get('avatar_url', ''),
        'cover_url': user_data.get('cover_url', ''),
        'is_supporter': user_data.get('is_supporter', False),
        # 从user的statistics中获取排名信息（如果有）
        'global_rank': user_data.get('statistics', {}).get('global_rank', 0) if 'statistics' in user_data else 0,
        'country_rank': user_data.get('statistics', {}).get('country_rank', 0) if 'statistics' in user_data else 0,
        'pp': user_data.get('statistics', {}).get('pp', 0) if 'statistics' in user_data else 0,
    }
    
    # 提取score信息
    score_info = {
        # 分数 - 优先使用legacy_total_score
        'score': api_score_data.get('legacy_total_score') or api_score_data.get('total_score', 0),
        
        # 准确率 - API返回0-1之间，不需要转换（图片生成器会自动乘100）
        'accuracy': api_score_data.get('accuracy', 0),
        
        # 最大连击
        'max_combo': api_score_data.get('max_combo', 0),
        
        # 排名
        'rank': api_score_data.get('rank', 'F'),
        
        # PP值
        'pp': api_score_data.get('pp', 0),
        
        # 模式 - ruleset_id转为字符串
        'mode': str(api_score_data.get('ruleset_id', 0)),
        
        # Mods - 从字典数组提取acronym
        'mods': _extract_mods(api_score_data.get('mods', [])),
        
        # 统计数据 - 转换字段名
        'statistics': _convert_statistics(
            api_score_data.get('statistics', {}),
            api_score_data.get('ruleset_id', 0)
        ),
        
        # 时间
        'created_at': api_score_data.get('ended_at', '').replace('T', ' ').replace('Z', ''),
        
        # 其他信息
        'passed': api_score_data.get('passed', True),
        'perfect': api_score_data.get('is_perfect_combo', False)
    }
    
    # 提取beatmap信息
    beatmap_data = api_score_data.get('beatmap', {})
    beatmapset_data = api_score_data.get('beatmapset', {})
    
    beatmap_info = {
        # 谱面ID
        'id': beatmap_data.get('id'),
        'beatmap_id': beatmap_data.get('id'),  # 兼容字段
        'beatmapset_id': beatmap_data.get('beatmapset_id'),
        
        # 谱面元数据
        'title': beatmapset_data.get('title', '???'),
        'title_unicode': beatmapset_data.get('title_unicode'),
        'artist': beatmapset_data.get('artist', '???'),
        'artist_unicode': beatmapset_data.get('artist_unicode'),
        'creator': beatmapset_data.get('creator', '???'),
        'version': beatmap_data.get('version', '???'),
        
        # 难度信息
        'difficulty_rating': beatmap_data.get('difficulty_rating', 0),
        'cs': beatmap_data.get('cs', 0),
        'ar': beatmap_data.get('ar', 0),
        'od': beatmap_data.get('accuracy', 0),  # API中accuracy字段是OD
        'hp': beatmap_data.get('drain', 0),     # API中drain字段是HP
        
        # 谱面统计
        'bpm': beatmap_data.get('bpm', 0),
        'total_length': beatmap_data.get('total_length', 0),
        'hit_length': beatmap_data.get('hit_length', 0),
        'count_circles': beatmap_data.get('count_circles', 0),
        'count_sliders': beatmap_data.get('count_sliders', 0),
        'count_spinners': beatmap_data.get('count_spinners', 0),
        
        # 状态
        'status': beatmap_data.get('status', 'unknown'),
        'ranked': beatmap_data.get('ranked', 0),
        
        # 封面图
        'covers': beatmapset_data.get('covers', {}),
        
        # 模式
        'mode': beatmap_data.get('mode', 'osu'),
        'mode_int': beatmap_data.get('mode_int', 0)
    }
    
    return user_info, score_info, beatmap_info


def _extract_mods(mods_list: List[Dict[str, Any]]) -> List[str]:
    """
    从mods数组中提取mod缩写
    
    API格式: [{'acronym': 'HD'}, {'acronym': 'DT'}]
    转换为: ['HD', 'DT']
    """
    if not mods_list:
        return []
    
    result = []
    for mod in mods_list:
        if isinstance(mod, dict):
            acronym = mod.get('acronym', '')
            if acronym:
                result.append(acronym)
        elif isinstance(mod, str):
            # 如果已经是字符串，直接使用
            result.append(mod)
    
    return result


def _convert_statistics(stats: Dict[str, Any], ruleset_id: int) -> Dict[str, Any]:
    """
    转换统计数据字段名
    
    API格式因模式而异：
    - Standard: great, ok, meh, miss
    - Taiko: great, ok, miss
    - Catch: great, large_tick_hit, small_tick_miss, miss
    - Mania: perfect, great, good, ok, meh, miss
    
    转换为统一格式：count_300, count_100, count_50, count_miss等
    """
    if ruleset_id == 0:  # Standard (osu!)
        return {
            'count_300': stats.get('great', 0),
            'count_100': stats.get('ok', 0),
            'count_50': stats.get('meh', 0),
            'count_miss': stats.get('miss', 0)
        }
    
    elif ruleset_id == 1:  # Taiko
        return {
            'count_300': stats.get('great', 0),
            'count_100': stats.get('ok', 0),
            'count_miss': stats.get('miss', 0)
        }
    
    elif ruleset_id == 2:  # Catch (osu!catch)
        return {
            'count_300': stats.get('great', 0),
            'count_100': stats.get('large_tick_hit', 0),
            'count_50': stats.get('small_tick_miss', 0),
            'count_miss': stats.get('miss', 0)
        }
    
    elif ruleset_id == 3:  # Mania (osu!mania)
        return {
            'count_geki': stats.get('perfect', 0),  # MAX/Rainbow 300
            'count_300': stats.get('great', 0),
            'count_katu': stats.get('good', 0),     # 200
            'count_100': stats.get('ok', 0),
            'count_50': stats.get('meh', 0),
            'count_miss': stats.get('miss', 0)
        }
    
    else:
        # 未知模式，返回原始数据
        return stats


def test_adapter():
    """测试适配器"""
    # 使用用户提供的真实API数据
    api_data = {
        'classic_total_score': 9771034,
        'mods': [{'acronym': 'CL'}],
        'statistics': {'ok': 70, 'meh': 12, 'miss': 48, 'great': 799},
        'beatmap_id': 5129766,
        'rank': 'B',
        'ruleset_id': 0,
        'accuracy': 0.887334,
        'max_combo': 123,
        'pp': 40.5499,
        'legacy_total_score': 1745940,
        'total_score': 346377,
        'ended_at': '2026-04-07T06:59:06Z',
        'beatmap': {
            'beatmapset_id': 2375111,
            'difficulty_rating': 6.08558,
            'id': 5129766,
            'version': 'Dreaming',
            'accuracy': 9,
            'ar': 9.3,
            'bpm': 183,
            'cs': 4,
            'drain': 6,
        },
        'beatmapset': {
            'artist': 'Hikari no Naka ni',
            'title': 'Moonlight',
            'creator': '-digital',
            'id': 2375111,
        },
        'user': {
            'username': '-Lilac-',
            'id': 36148327,
            'country_code': 'HK',
        }
    }
    
    user_info, score_info, beatmap_info = adapt_api_data_for_image(api_data)
    
    print("User Info:")
    print(f"  Username: {user_info['username']}")
    print(f"  ID: {user_info['id']}")
    
    print("\nScore Info:")
    print(f"  Score: {score_info['score']}")
    print(f"  Accuracy: {score_info['accuracy']:.4f}")
    print(f"  Rank: {score_info['rank']}")
    print(f"  PP: {score_info['pp']}")
    print(f"  Combo: {score_info['max_combo']}")
    print(f"  Mode: {score_info['mode']}")
    print(f"  Mods: {score_info['mods']}")
    print(f"  Statistics: {score_info['statistics']}")
    
    print("\nBeatmap Info:")
    print(f"  Title: {beatmap_info['title']}")
    print(f"  Artist: {beatmap_info['artist']}")
    print(f"  Version: {beatmap_info['version']}")
    print(f"  Creator: {beatmap_info['creator']}")
    print(f"  Difficulty: {beatmap_info['difficulty_rating']}")
    print(f"  BeatmapID: {beatmap_info['id']}")
    print(f"  BeatmapsetID: {beatmap_info['beatmapset_id']}")


if __name__ == '__main__':
    test_adapter()
