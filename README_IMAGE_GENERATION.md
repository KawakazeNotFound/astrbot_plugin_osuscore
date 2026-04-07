# osu! 成绩图片生成系统 - 完整实现说明

## 🎨 视觉效果升级

基于 nonebot-plugin-osubot 的完整实现，提供专业级的成绩截图。

### 核心特性

1. **多层图像合成**
   - 谱面封面自动下载（支持多CDN源）
   - 高斯模糊 + 亮度调整
   - 游戏模式专属背景模板
   - Alpha透明度混合

2. **视觉资源**
   - 4种游戏模式背景（std/taiko/ctb/mania）
   - 69个Mod图标（HD、DT、HR、FL等）
   - 9个排名图标（XH、X、SH、S、A、B、C、D、F）
   - 专业字体（Torus Regular/SemiBold、Venera）

3. **特殊效果**
   - 文字描边（提高可读性）
   - 星级难度彩色渐变（0.1★-9★）
   - 圆角边框
   - 图标自适应大小

4. **智能降级**
   - 资源缺失时自动降级到简单模式
   - 网络失败时使用纯色背景
   - 确保任何情况下都能生成图片

## 📁 资源结构

```
assets/
├── fonts/              # 字体文件
│   ├── Torus Regular.otf
│   ├── Torus SemiBold.otf
│   └── Venera.otf
├── mods/               # Mod图标 (69个)
│   ├── HD.png
│   ├── DT.png
│   └── ...
├── ranking/            # 排名图标 (9个)
│   ├── ranking-X.png
│   └── ...
├── work/               # 工作资源
│   └── *.png
├── cache/              # 谱面封面缓存
├── pfm_std.png         # Standard背景
├── pfm_taiko.png       # Taiko背景
├── pfm_ctb.png         # Catch背景
└── pfm_mania.png       # Mania背景
```

## 🔧 技术实现

### 星级颜色映射

使用 matplotlib 的 LinearSegmentedColormap 实现平滑渐变：
- 0.1★ → 蓝色 (#4290FB)
- 3.3★ → 黄色 (#F6F05C)
- 6.7★ → 靛蓝 (#6563DE)
- 9★ → 黑色 (#000000)

### 图像处理流程

```python
1. 下载谱面封面
   ↓
2. 智能裁剪（保持宽高比）
   ↓
3. 高斯模糊（10px）
   ↓
4. 降低亮度（50%）
   ↓
5. 叠加模式背景
   ↓
6. 绘制文本（带描边）
   ↓
7. 合成图标
```

### 缓存策略

- 谱面封面：本地缓存为 `cache/cover_{beatmapset_id}.jpg`
- 自动清理：可扩展为TTL机制（如1天自动刷新）

## 📦 依赖包

```
pillow>=9.2.0          # 图像处理
matplotlib>=3.5.0      # 星级颜色映射
httpx>=0.23.3          # 异步HTTP请求
aiofiles>=0.8.0        # 异步文件IO
```

## 🚀 使用方法

```python
from draw import ScoreImageGenerator

generator = ScoreImageGenerator()

img_bytes = await generator.generate_score_image(
    user_info={...},
    score_info={...},
    beatmap_info={...}
)

# 保存图片
with open("score.png", "wb") as f:
    f.write(img_bytes.read())
```

## 🎯 对比测试

**旧版本：**
- 纯色背景
- 简单文本排版
- 无视觉装饰
- ~50KB

**新版本：**
- 谱面封面背景
- 多层合成
- Mod/排名图标
- 文字描边
- ~500KB（包含高质量图片）

## 📝 注意事项

1. **首次运行**：确保 `assets/` 目录包含所有资源文件
2. **网络连接**：下载谱面封面需要访问 osu.ppy.sh
3. **降级方案**：如果资源缺失，会自动使用简单模式
4. **字体支持**：如果专业字体加载失败，会使用系统默认字体

## 🔗 参考资源

- nonebot-plugin-osubot: https://github.com/yaowan233/nonebot-plugin-osubot
- osu! web 星级颜色标准：https://github.com/ppy/osu-web

---

**生成时间：2024-04-07**
**版本：2.0 (完整nonebot风格)**
