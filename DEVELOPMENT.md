# OSU Score 插件开发说明

## 已实现的功能

### 1. 核心基础设施
- ✅ AstrBot 插件框架集成
- ✅ OSU API OAuth 2.0 认证
- ✅ SQLite 数据库管理
- ✅ 参数解析系统

### 2. 插件命令

#### /bind - 绑定账号
```
使用: /bind <osuid或用户名>
功能: 将用户 ID 与 OSU 账号关联
存储: 保存到本地 SQLite 数据库
```

#### /pr - 查询最近成绩  ⭐ 主要功能
```
使用: /pr [用户名] [:模式] [+mods]
功能:
  1. 获取玩家最近1条成绩
  2. 获取谱面详细信息
  3. 生成成绩截图
  4. 发送给用户

支持的参数:
  - 用户名: 留空使用绑定账号，或指定其他用户
  - 模式[:]: 0=std, 1=taiko, 2=ctb, 3=mania
  - Mod[+]: +HDDT 等组合
```

#### /mania - 查询 mania 成绩
```
使用: /mania [用户名] [recent|best] [数量] [4k|7k] [+mods]
功能:
    1. 查询 mania 最近或最佳成绩
    2. 支持多条成绩连续图片输出（limit > 1，最多前5条）
    3. 单条成绩自动生成图片
    4. 支持 4k/7k 变体信息展示
    5. 通过官方 Beatmap Attributes 接口补全 mania 难度属性
```

### 3. 图片生成系统

**ScoreImageGenerator** 特性:
- 使用 PIL/Pillow 生成 800x600 的成绩卡
- 显示内容:
  - 谱面标题、难度等级
  - 玩家名称和模式
  - 分数、准确度、Combo
  - 等级 (SS+, S, A, 等)
  - PP 值和 Mod
  - 成绩提交时间
- 自适应字体加载（支持 Linux/Windows/macOS）

### 4. 架构对标

相比参考的 Nonebot 插件的改进:

| 方面 | Nonebot | AstrBot 版本 |
|------|--------|----------|
| 框架方式 | on_command | @filter.command |
| 消息处理 | state 字典 | event 对象 |
| 参数解析 | split_msg() | parse_command_args() |
| 数据库 | nonebot-plugin-orm | 原生 SQLite |
| HTTP 客户端 | httpx (池化) | httpx (单例) |
| Token 缓存 | ExpiringDict | TokenCache 类 |

## 文件结构

```
astrbot_plugin_osuscore/
├── metadata.yaml          # 插件元数据（600 字节）
├── _conf_schema.json      # 配置架构（380 字节）
├── requirements.txt       # 依赖项（4 个包）
├── __init__.py           # 包初始化
├── main.py               # 主插件（~350 行）⭐
├── api.py                # API 接口（~280 行）⭐
├── database.py           # 数据库管理（~170 行）
├── draw.py               # 图片生成（~210 行）⭐
├── utils.py              # 工具函数（~100 行）
└── README.md             # 使用说明
```

## 关键设计决策

### 1. 数据库选择
- **SQLite** 代替 ORM
  - 优点：无依赖，轻量级，适合单机
  - 缺点：不支持高并发，迁移困难

### 2. API 认证机制
```python
TokenCache:
  - 24小时自动过期
  - 线程安全锁
  - 自动刷新
```

### 3. 参数解析
```python
# 支持格式:
/pr myname :1 +HD
    ↓
parse_command_args()
    ↓
{"username": "myname", "mode": "1", "mods": ["HD"]}
```

### 4. 图片生成
- 不依赖外部字体（自动加载系统字体）
- 纯 PIL 绘制（无需 matplotlib）
- 支持 BytesIO 直接发送

## 使用流程

### 第一次使用

```
1. 配置插件:
   osu_client_id: <从 osu.ppy.sh 获取>
   osu_client_secret: <从 osu.ppy.sh 获取>

2. 绑定账号:
   /bind peppy

3. 查询最近成绩:
   /pr

4. 查询其他用户:
   /pr username :1 +HD
```

### 数据流

```
用户消息 (/pr)
    ↓
event.message_str 提取文本
    ↓
parse_command_args() 解析参数
    ↓
database.get_user() 查询绑定信息 ← SQLite
    ↓
api_client.get_user() 获取用户信息 ← OSU API
    ↓
api_client.get_user_scores() 获取成绩 ← OSU API
    ↓
api_client.get_beatmap() 获取谱面 ← OSU API
    ↓
img_generator.generate_score_image() 生成贖图
    ↓
event.send(MessageChain([Comp.Image()]))
    ↓
发送给用户
```

## 下一步计划

### 短期（v0.2.0）
- [ ] 实现 /bp（查询最佳成绩）
- [ ] 实现 /bplist（范围查询）
- [ ] 改进图片布局（更美观）
- [ ] 添加错误处理细节

### 中期（v0.3.0）
- [ ] 实现 /info（用户信息卡）
- [ ] 缓存机制优化
- [ ] 支持更多 Mod 显示

### 长期（v1.0.0）
- [ ] 与 osutrack 集成
- [ ] 多语言支持
- [ ] 数据库迁移到 PostgreSQL

## 安装和配置指南

### 1. 安装依赖
```bash
cd astrbot_plugin_osuscore
pip install -r requirements.txt
```

### 2. 获取 OSU API 凭证
1. 访问 https://osu.ppy.sh/home/account/edit
2. 向下滚动到 "OAuth"
3. 点击 "New OAuth Application"
4. 填写表单:
   - Application name: "AstrBot OSU Plugin"
   - Redirect URL: http://localhost:7210/
   - Type: 选择 "Client Credentials"
5. 复制 Client ID 和Client Secret

### 3. 配置 AstrBot
编辑 AstrBot 的配置文件，添加:
```json
{
  "osu_client_id": 12345,
  "osu_client_secret": "your_secret_here",
  "db_path": "./osuscore.db"
}
```

### 4. 启动 AstrBot
```bash
python main.py  # AstrBot 启动命令
```

### 5. 使用插件
```
/bind peppy       # 绑定账号
/pr               # 查询最近成绩
```

## 测试检查清单

- [ ] 插件正常加载（查看日志）
- [ ] API 配置有效（token 获取成功）
- [ ] /bind 命令正常（数据写入数据库）
- [ ] /pr 命令正常（图片生成和发送）
- [ ] 错误处理合理（网络错误时有提示）

## 常见问题

### Q: 如何更换用户账号？
A: 重新运行 `/bind <新用户名>`，会覆盖之前的绑定。

### Q: 为什么图片中文显示不正常？
A: 自动加载系统字体，如需中文支持可下载思源黑体并指定路径。

### Q: 能否支持查询特定 beatmap？
A: 可以，但需要额外实现 /score 命令。参见扩展计划。

## 代码示例

### 添加新命令的步骤

```python
@filter.command("newcmd")
async def new_command(self, event: AstrMessageEvent):
    """命令描述"""
    try:
        # 解析参数
        args = parse_command_args(event.message_str)

        # 调用 API
        data = await self.api_client.get_something()

        # 生成响应
        result = await self.process_data(data)

        # 发送
        await event.send(MessageChain([Comp.Plain(result)]))
    except Exception as e:
        await event.send(MessageChain([Comp.Plain(f"❌ 错误: {e}")]))
```

## 参考文档

- AstrBot 官方文档: https://astrbot.readthedocs.io/
- OSU API v2: https://osu.ppy.sh/docs/index.html
- PIL 文档: https://pillow.readthedocs.io/
- Nonebot 参考实现: d:/Github/osu_astrbot/参考/nonebot-plugin-osubot

---

文档版本: v0.1.0
最后更新: 2026-04-07
