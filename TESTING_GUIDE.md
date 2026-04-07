"""
OSU成绩图片生成系统 - 测试指南
====================================

本指南提供多种测试方法，从简单的单元测试到完整的插件集成测试。
"""

## 方法1: 独立脚本测试（推荐新手）

已经提供了 `test_draw.py`，可以直接运行：

```bash
# 进入项目目录
cd d:\Github\osu_astrbot\astrbot_plugin_osuscore

# 运行测试脚本
python test_draw.py
```

**预期输出：**
```
Generating score image...
[OK] Image generated successfully: test_output.png
  File size: 513417 bytes

Assets loaded:
  Fonts: 13 loaded
  Mod icons: 69 loaded
  Rank icons: 9 loaded
  Mode backgrounds: 4 loaded
```

**生成的图片：** `test_output.png`


## 方法2: 测试不同游戏模式

创建 `test_all_modes.py`：

```python
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
    
    for mode_id, mode_name, mode_full in modes:
        print(f"\nTesting {mode_full} mode...")
        
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
            "title": f"Test Beatmap ({mode_full})",
            "version": "Expert",
            "creator": "TestMapper",
            "difficulty_rating": 6.5,
            "beatmapset_id": 1
        }
        
        try:
            img_bytes = await generator.generate_score_image(
                user_info, score_info, beatmap_info
            )
            
            output_path = f"test_output_{mode_name}.png"
            with open(output_path, "wb") as f:
                f.write(img_bytes.read())
            
            print(f"  [OK] Generated: {output_path}")
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_modes())
```


## 方法3: 测试不同星级难度的颜色

创建 `test_star_colors.py`：

```python
"""测试星级难度颜色映射"""

import asyncio
from draw import ScoreImageGenerator

async def test_star_colors():
    generator = ScoreImageGenerator()
    
    user_info = {"username": "ColorTest", "id": 1}
    
    # 测试不同星级（0.1 到 10）
    star_ratings = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]
    
    for stars in star_ratings:
        print(f"\nTesting {stars}★...")
        
        score_info = {
            "score": 10000000,
            "accuracy": 1.0,
            "max_combo": 1000,
            "rank": "X",
            "pp": 500,
            "mode": "0",
            "mods": [],
            "created_at": "2024-04-07"
        }
        
        beatmap_info = {
            "title": f"Star Color Test",
            "version": f"{stars} Stars",
            "creator": "Tester",
            "difficulty_rating": stars,
            "beatmapset_id": None  # 不下载背景，测试降级
        }
        
        try:
            img_bytes = await generator.generate_score_image(
                user_info, score_info, beatmap_info
            )
            
            output_path = f"test_stars_{stars:.1f}.png"
            with open(output_path, "wb") as f:
                f.write(img_bytes.read())
            
            print(f"  [OK] Color for {stars}★")
        except Exception as e:
            print(f"  [ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(test_star_colors())
```


## 方法4: 在实际插件中测试

### 4.1 安装依赖

```bash
pip install -r requirements.txt
```

### 4.2 配置插件

在 AstrBot 配置文件中添加：

```json
{
  "osu_client_id": "your_client_id",
  "osu_client_secret": "your_client_secret",
  "db_path": "./osuscore.db"
}
```

### 4.3 使用命令测试

```
/bind your_osu_username    # 绑定账号
/pr                        # 查询最近成绩（会生成图片）
/score 1234567             # 查询指定谱面成绩
```

### 4.4 检查图片生成

成绩图片会被发送到聊天中，检查是否：
- ✅ 有谱面背景（模糊效果）
- ✅ 有游戏模式模板
- ✅ 显示Mod图标
- ✅ 显示排名图标
- ✅ 文字有描边
- ✅ 星级有颜色


## 方法5: 压力测试

创建 `test_performance.py`：

```python
"""性能和并发测试"""

import asyncio
import time
from draw import ScoreImageGenerator

async def test_performance():
    generator = ScoreImageGenerator()
    
    user_info = {"username": "PerfTest", "id": 1}
    score_info = {
        "score": 10000000,
        "accuracy": 0.99,
        "max_combo": 1000,
        "rank": "S",
        "pp": 400,
        "mode": "0",
        "mods": ["HD", "DT", "HR"],
        "created_at": "2024-04-07"
    }
    beatmap_info = {
        "title": "Performance Test",
        "version": "Expert",
        "creator": "Tester",
        "difficulty_rating": 6.0,
        "beatmapset_id": 1
    }
    
    # 测试1: 单次生成时间
    print("Test 1: Single generation time")
    start = time.time()
    await generator.generate_score_image(user_info, score_info, beatmap_info)
    elapsed = time.time() - start
    print(f"  Time: {elapsed:.2f}s")
    
    # 测试2: 连续生成（测试缓存效果）
    print("\nTest 2: Consecutive generations (with cache)")
    times = []
    for i in range(5):
        start = time.time()
        await generator.generate_score_image(user_info, score_info, beatmap_info)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.2f}s")
    
    print(f"\n  Average: {sum(times)/len(times):.2f}s")
    print(f"  Min: {min(times):.2f}s")
    print(f"  Max: {max(times):.2f}s")
    
    # 测试3: 并发生成
    print("\nTest 3: Concurrent generation (10 tasks)")
    start = time.time()
    tasks = [
        generator.generate_score_image(user_info, score_info, beatmap_info)
        for _ in range(10)
    ]
    await asyncio.gather(*tasks)
    elapsed = time.time() - start
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Per image: {elapsed/10:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_performance())
```


## 方法6: 降级方案测试

创建 `test_fallback.py`：

```python
"""测试降级方案（资源缺失时）"""

import asyncio
import shutil
from pathlib import Path
from draw import ScoreImageGenerator

async def test_fallback():
    # 临时移动assets目录
    assets_dir = Path("assets")
    backup_dir = Path("assets_backup")
    
    if assets_dir.exists():
        print("Backing up assets...")
        shutil.move(str(assets_dir), str(backup_dir))
    
    try:
        print("\nTesting fallback mode (no assets)...")
        generator = ScoreImageGenerator()
        
        user_info = {"username": "FallbackTest", "id": 1}
        score_info = {
            "score": 10000000,
            "accuracy": 0.99,
            "max_combo": 1000,
            "rank": "S",
            "pp": 400,
            "mode": "0",
            "mods": ["HD"],
            "created_at": "2024-04-07"
        }
        beatmap_info = {
            "title": "Fallback Test",
            "version": "Expert",
            "creator": "Tester",
            "difficulty_rating": 6.0,
            "beatmapset_id": None
        }
        
        img_bytes = await generator.generate_score_image(
            user_info, score_info, beatmap_info
        )
        
        with open("test_fallback.png", "wb") as f:
            f.write(img_bytes.read())
        
        print("[OK] Fallback mode works! Generated: test_fallback.png")
        
    finally:
        # 恢复assets目录
        if backup_dir.exists():
            print("\nRestoring assets...")
            shutil.move(str(backup_dir), str(assets_dir))

if __name__ == "__main__":
    asyncio.run(test_fallback())
```


## 常见问题排查

### 问题1: ModuleNotFoundError: No module named 'matplotlib'

**解决：**
```bash
pip install matplotlib aiofiles httpx
```

### 问题2: 图片没有背景

**原因：** beatmapset_id 无效或网络问题

**检查：**
```python
# 查看日志
print("Downloading cover...")
bg_img = await download_beatmap_cover(beatmapset_id)
if bg_img:
    print("Cover downloaded!")
else:
    print("Cover download failed, using simple mode")
```

### 问题3: 字体显示异常

**原因：** 字体文件缺失

**检查：**
```python
import os
print("Fonts exist:", os.path.exists("assets/fonts/Torus Regular.otf"))
```

### 问题4: Mod图标不显示

**原因：** Mod名称不匹配

**检查：**
```python
# 在 draw.py 中添加调试
print(f"Mod name: {mod_name}")
print(f"Available mods: {list(self.assets.mod_icons.keys())}")
```

### 问题5: UnicodeEncodeError

**原因：** Windows控制台编码问题

**解决：** 避免在print中使用特殊字符，或设置环境变量：
```bash
set PYTHONIOENCODING=utf-8
```


## 推荐测试流程

1. **基础测试** → 运行 `test_draw.py`
2. **模式测试** → 运行 `test_all_modes.py`
3. **颜色测试** → 运行 `test_star_colors.py`
4. **性能测试** → 运行 `test_performance.py`
5. **降级测试** → 运行 `test_fallback.py`
6. **实战测试** → 在AstrBot中使用 `/pr` 命令


## 验收标准

✅ **合格的图片应该包含：**
- 模糊的谱面背景
- 游戏模式专属UI模板
- Mod图标（如果有Mod）
- 排名图标（右侧大图）
- 文字有黑色描边
- 星级数字有颜色（非白色）
- 文件大小 200KB - 1MB

✅ **资源加载正常：**
- Fonts: 13 loaded
- Mod icons: 69 loaded
- Rank icons: 9 loaded
- Mode backgrounds: 4 loaded

---

**测试愉快！** 🎨✨
