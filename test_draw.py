"""测试新的图片生成系统"""

import asyncio
from draw import ScoreImageGenerator

async def test_score_image():
    """测试成绩图片生成"""
    generator = ScoreImageGenerator()
    
    # 模拟数据
    user_info = {
        "username": "TestPlayer",
        "id": 12345
    }
    
    score_info = {
        "score": 15234567,
        "accuracy": 0.9856,
        "max_combo": 1234,
        "rank": "S",
        "pp": 456.78,
        "mode": "0",  # std
        "mods": ["HD", "DT", "HR"],
        "created_at": "2024-04-07 12:00:00"
    }
    
    beatmap_info = {
        "title": "Test Beatmap",
        "artist": "Test Artist",
        "version": "Expert",
        "creator": "TestMapper",
        "difficulty_rating": 6.5,
        "beatmapset_id": 1,
        "id": 123456
    }
    
    print("Generating score image...")
    try:
        img_bytes = await generator.generate_score_image(user_info, score_info, beatmap_info)
        
        # 保存测试图片
        output_path = "test_output.png"
        with open(output_path, "wb") as f:
            f.write(img_bytes.read())
        
        print(f"[OK] Image generated successfully: {output_path}")
        print(f"  File size: {len(img_bytes.getvalue())} bytes")
        
        # 检查资源加载情况
        print("\nAssets loaded:")
        
    except Exception as e:
        print(f"[ERROR] Failed to generate image: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_score_image())
