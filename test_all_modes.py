"""测试所有4个游戏模式的图片生成"""

import asyncio
from draw import ScoreImageGenerator

async def test_all_modes():
    generator = ScoreImageGenerator()
    
    # 基础数据
    user_info = {"username": "TestPlayer", "id": 12345}
    
    # 测试4个模式
    modes = [
        ("0", "std", "Standard"),
        ("1", "taiko", "Taiko"),
        ("2", "ctb", "Catch"),
        ("3", "mania", "Mania")
    ]
    
    print("=" * 50)
    print("Testing All Game Modes")
    print("=" * 50)
    
    for mode_id, mode_name, mode_full in modes:
        print(f"\n[{mode_full}] Generating...")
        
        score_info = {
            "score": 15234567,
            "accuracy": 0.9856,
            "max_combo": 1234,
            "rank": "S",
            "pp": 456.78,
            "mode": mode_id,
            "mods": ["HD", "DT"],
            "created_at": "2024-04-07 12:00:00"
        }
        
        beatmap_info = {
            "title": f"Test Beatmap",
            "version": f"{mode_full} Expert",
            "creator": "TestMapper",
            "difficulty_rating": 6.5,
            "beatmapset_id": 1  # 使用真实ID测试背景下载
        }
        
        try:
            img_bytes = await generator.generate_score_image(
                user_info, score_info, beatmap_info
            )
            
            output_path = f"test_output_{mode_name}.png"
            with open(output_path, "wb") as f:
                f.write(img_bytes.read())
            
            size_kb = len(img_bytes.getvalue()) / 1024
            print(f"  [OK] {output_path} ({size_kb:.1f} KB)")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_all_modes())
