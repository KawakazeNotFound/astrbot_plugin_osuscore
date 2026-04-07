# OSU Score 查分插件

一个适用于 AstrBot 的 OSU! 查分插件，支持查询玩家的最近成绩（PR）。

## 功能特性

- ✅ 绑定 OSU 账号
- ✅ 查询最近成绩（/pr）
- ✅ 查询 osu!mania 成绩（/mania）
- ✅ 支持多种游玩模式（Standard, Taiko, Catch, Mania）
- ✅ 生成成绩截图

## 安装

1. 复制此目录到 AstrBot 的插件目录
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 配置

在 AstrBot 的配置中添加以下项：

```json
{
  "osu_client_id": 12345,
  "osu_client_secret": "your_secret_key",
  "db_path": "./osuscore.db"
}
```

### 获取 OSU API 凭证

1. 访问 https://osu.ppy.sh/home/account/edit
2. 在 "OAuth" 部分创建新应用
3. 复制 Client ID 和 Client Secret

## 使用

### 绑定账号

```
/bind <osuid或用户名>
```

**示例**:
```
/bind peppy
/bind 2
```

### 查询最近成绩

```
/pr [用户名] [:模式] [+mods]
```

**示例**:
```
/pr                    # 使用绑定的账号查询
/pr peppy              # 查询指定用户
/pr peppy :1           # 查询 Taiko 模式
/pr peppy :0 +HD       # 查询 HD Mod
```

### 查询 mania 成绩

```
/mania [用户名] [recent|best] [数量] [4k|7k] [+mods]
```

**示例**:
```
/mania                     # 查询绑定账号的 mania 最近成绩
/mania peppy best 3        # 查询 peppy 的 mania BEST 前 3
/mania peppy recent 1 4k   # 查询 peppy 的 mania 最近成绩，并附带 4K 变体信息
/mania peppy best 5 +HD    # 仅筛选包含 HD 的 mania BEST 成绩
```

### 模式代码

- `0` - Standard (默认)
- `1` - Taiko
- `2` - Catch
- `3` - Mania

## 项目结构

```
astrbot_plugin_osuscore/
├── metadata.yaml          # 插件元数据
├── _conf_schema.json      # 配置架构
├── requirements.txt       # 依赖项
├── main.py               # 主插件文件
├── api.py                # OSU API 接口
├── database.py           # 数据库管理
├── draw.py               # 图片生成
├── utils.py              # 工具函数
└── __init__.py
```

## 技术细节

### 核心组件

1. **OsuApiClient** - OSU API 客户端，处理 OAuth 认证和 API 调用
2. **Database** - SQLite 数据库管理器，存储用户绑定信息
3. **ScoreImageGenerator** - 成绩截图生成（使用 PIL）
4. **OsuScorePlugin** - 主插件类，处理命令和事件

### 数据流

```
用户输入 /pr peppy
    ↓
parse_command_args() 解析参数
    ↓
api_client.get_user() 获取用户信息
    ↓
api_client.get_user_scores() 获取最近成绩
    ↓
api_client.get_beatmap() 获取谱面信息
    ↓
img_generator.generate_score_image() 生成图片
    ↓
发送给用户
```

## 扩展计划

- [ ] BP 查询（最佳成绩）
- [ ] 多条成绩查询（范围查询）
- [ ] 成绩分析和统计
- [ ] 用户信息卡片
- [ ] 与 osutrack 服务器集成

## 许可证

MIT License

## 作者

Claude
