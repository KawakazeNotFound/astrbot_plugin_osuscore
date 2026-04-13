"""使用真实API数据测试图片生成"""

import asyncio
from draw import ScoreImageGenerator
from data_adapter import adapt_api_data_for_image
from pp_calculator import calculate_all_pp_info

async def test_with_real_api_data():
    """使用用户提供的真实API数据测试"""
    generator = ScoreImageGenerator()
    
    # 用户提供的真实API数据
    api_data = {
        'classic_total_score': 9771034,
        'preserve': True,
        'processed': True,
        'ranked': True,
        'maximum_statistics': {'great': 929, 'legacy_combo_increase': 329},
        'mods': [{'acronym': 'CL'}],
        'statistics': {'ok': 70, 'meh': 12, 'miss': 48, 'great': 799},
        'total_score_without_mods': 360809,
        'beatmap_id': 5129766,
        'best_id': None,
        'id': 6490271943,
        'rank': 'B',
        'type': 'solo_score',
        'user_id': 36148327,
        'accuracy': 0.887334,
        'build_id': None,
        'ended_at': '2026-04-07T06:59:06Z',
        'has_replay': True,
        'is_perfect_combo': False,
        'legacy_perfect': False,
        'legacy_score_id': 5007593614,
        'legacy_total_score': 1745940,
        'max_combo': 123,
        'passed': True,
        'pp': 40.5499,
        'ruleset_id': 0,
        'started_at': None,
        'total_score': 346377,
        'replay': True,
        'current_user_attributes': {'pin': None},
        'beatmap': {
            'beatmapset_id': 2375111,
            'difficulty_rating': 6.08558,
            'id': 5129766,
            'mode': 'osu',
            'status': 'ranked',
            'total_length': 220,
            'user_id': 9397193,
            'version': 'Dreaming',
            'accuracy': 9,
            'ar': 9.3,
            'bpm': 183,
            'convert': False,
            'count_circles': 604,
            'count_sliders': 323,
            'count_spinners': 2,
            'cs': 4,
            'deleted_at': None,
            'drain': 6,
            'hit_length': 215,
            'is_scoreable': True,
            'last_updated': '2026-03-09T04:03:46Z',
            'mode_int': 0,
            'passcount': 1125,
            'playcount': 5158,
            'ranked': 1,
            'url': 'https://osu.ppy.sh/beatmaps/5129766',
            'checksum': 'aa4916eb16d0c040c2256b486262efd0'
        },
        'beatmapset': {
            'anime_cover': True,
            'artist': 'Hikari no Naka ni',
            'artist_unicode': 'ひかりのなかに',
            'covers': {
                'cover': 'https://assets.ppy.sh/beatmaps/2375111/covers/cover.jpg?1773029042',
                'cover@2x': 'https://assets.ppy.sh/beatmaps/2375111/covers/cover@2x.jpg?1773029042',
                'card': 'https://assets.ppy.sh/beatmaps/2375111/covers/card.jpg?1773029042',
                'card@2x': 'https://assets.ppy.sh/beatmaps/2375111/covers/card@2x.jpg?1773029042',
                'list': 'https://assets.ppy.sh/beatmaps/2375111/covers/list.jpg?1773029042',
                'list@2x': 'https://assets.ppy.sh/beatmaps/2375111/covers/list@2x.jpg?1773029042',
                'slimcover': 'https://assets.ppy.sh/beatmaps/2375111/covers/slimcover.jpg?1773029042',
                'slimcover@2x': 'https://assets.ppy.sh/beatmaps/2375111/covers/slimcover@2x.jpg?1773029042'
            },
            'creator': '-digital',
            'favourite_count': 65,
            'genre_id': 4,
            'hype': None,
            'id': 2375111,
            'language_id': 3,
            'nsfw': False,
            'offset': 0,
            'play_count': 10033,
            'preview_url': 'https://b.ppy.sh/preview/2375111.mp3',
            'source': '',
            'spotlight': False,
            'status': 'ranked',
            'title': 'Moonlight',
            'title_unicode': 'ムーンライト',
            'track_id': None,
            'user_id': 9397193,
            'video': False
        },
        'user': {
            'avatar_url': 'https://a.ppy.sh/36148327?1718416056.jpeg',
            'country_code': 'HK',
            'default_group': 'default',
            'id': 36148327,
            'is_active': True,
            'is_bot': False,
            'is_deleted': False,
            'is_online': True,
            'is_supporter': True,
            'last_visit': '2026-04-07T06:59:06+00:00',
            'pm_friends_only': False,
            'profile_colour': None,
            'username': '-Lilac-',
            'cover': {
                'custom_url': 'https://assets.ppy.sh/user-profile-covers/36148327/939e6aedc5b59a60e0a5ccae2a87a742ce790320ee802f06dfab72f8fdc8303f.jpeg',
                'url': 'https://assets.ppy.sh/user-profile-covers/36148327/939e6aedc5b59a60e0a5ccae2a87a742ce790320ee802f06dfab72f8fdc8303f.jpeg',
                'id': '36148327'
            },
            # 手动添加统计信息（模拟get_user API返回）
            'statistics': {
                'global_rank': 123456,
                'country_rank': 1234,
                'pp': 3456.78
            }
        }
    }
    
    print("=" * 60)
    print("Testing with Real API Data + PP Calculation")
    print("=" * 60)
    
    # 使用适配器转换数据
    user_info, score_info, beatmap_info = adapt_api_data_for_image(api_data)
    
    # 计算PP信息
    print("\nCalculating PP...")
    pp_info = await calculate_all_pp_info(
        beatmap_id=beatmap_info['id'],
        beatmapset_id=beatmap_info['beatmapset_id'],
        mods=score_info['mods'],
        accuracy=score_info['accuracy'],
        max_combo=score_info['max_combo'],
        statistics=score_info['statistics'],
        mode=int(score_info['mode'])
    )
    
    # 合并PP信息
    score_info.update(pp_info)
    
    print("\nData Summary:")
    print(f"  User: {user_info['username']} (#{user_info.get('global_rank', 'N/A')})")
    print(f"  Beatmap: {beatmap_info['title']} - {beatmap_info['version']}")
    print(f"  PP: {score_info['pp']:.2f}")
    print(f"  PP Aim: {score_info['pp_aim']:.2f}")
    print(f"  PP Speed: {score_info['pp_speed']:.2f}")
    print(f"  PP Acc: {score_info['pp_acc']:.2f}")
    print(f"  IF FC PP: {score_info['if_fc_pp']:.2f}")
    print(f"  SS PP: {score_info['ss_pp']:.2f}")
    
    print("\nGenerating image with all features...")
    try:
        img_bytes = await generator.generate_score_image(
            user_info, score_info, beatmap_info
        )
        
        output_path = "test_final_with_pp.png"
        with open(output_path, "wb") as f:
            f.write(img_bytes.read())
        
        size_kb = len(img_bytes.getvalue()) / 1024
        print(f"\n[OK] Image generated: {output_path} ({size_kb:.1f} KB)")
        print("\nFeatures included:")
        print("  ✓ Avatar at (27, 532)")
        print("  ✓ Global rank at (985, 260)")
        print("  ✓ Country rank at (283, 630)")
        print("  ✓ IF FC PP at (933, 393)")
        print("  ✓ SS PP at (1066, 393)")
        print("  ✓ AIM PP at (933, 482)")
        print("  ✓ SPEED PP at (1066, 482)")
        print("  ✓ ACC PP at (1200, 482)")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_with_real_api_data())
