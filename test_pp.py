"""测试PP计算功能"""

import asyncio
from pp_calculator import calculate_all_pp_info

async def test_pp_calculation():
    """测试PP计算"""
    
    print("=" * 60)
    print("Testing PP Calculation")
    print("=" * 60)
    
    # 测试数据（来自之前的真实API响应）
    beatmap_id = 5129766
    beatmapset_id = 2375111
    mods = ['CL']
    accuracy = 0.887334
    max_combo = 123
    statistics = {
        'count_300': 799,
        'count_100': 70,
        'count_50': 12,
        'count_miss': 48
    }
    mode = 0  # osu!std
    
    print(f"\nInput:")
    print(f"  Beatmap ID: {beatmap_id}")
    print(f"  Beatmapset ID: {beatmapset_id}")
    print(f"  Mods: {mods}")
    print(f"  Accuracy: {accuracy * 100:.2f}%")
    print(f"  Max Combo: {max_combo}")
    print(f"  Statistics: {statistics}")
    print(f"  Mode: {mode}")
    
    print("\nCalculating PP...")
    
    try:
        pp_info = await calculate_all_pp_info(
            beatmap_id=beatmap_id,
            beatmapset_id=beatmapset_id,
            mods=mods,
            accuracy=accuracy,
            max_combo=max_combo,
            statistics=statistics,
            mode=mode
        )
        
        print("\nResults:")
        print(f"  PP: {pp_info['pp']:.2f}")
        print(f"  PP Aim: {pp_info['pp_aim']:.2f}")
        print(f"  PP Speed: {pp_info['pp_speed']:.2f}")
        print(f"  PP Acc: {pp_info['pp_acc']:.2f}")
        print(f"  IF FC PP: {pp_info['if_fc_pp']:.2f}")
        print(f"  SS PP: {pp_info['ss_pp']:.2f}")
        print(f"  Stars: {pp_info['stars']:.2f}")
        
        print("\n[OK] PP calculation successful!")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pp_calculation())
