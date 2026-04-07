# 快速开始

## 1. 获取 OSU API 凭证（5分钟）

### 步骤
1. 访问 https://osu.ppy.sh/home/account/edit
2. 向下滚动，找到 "OAuth" 部分
3. 点击 "New OAuth Application"
4. 填写表单:
   ```
   Application name: AstrBot OSU Plugin
   Redirect URL: http://localhost:7210/
   ```
5. 选择 "Application Type: Client Credentials"
6. 保存好 **Client ID** 和 **Client Secret**

## 2. 安装插件

```bash
# 进入项目目录
cd d:/Github/osu_astrbot

# 安装依赖
pip install -r astrbot_plugin_osuscore/requirements.txt
```

## 3. 配置 AstrBot

在 AstrBot 的配置文件中添加（位置取决于你的 AstrBot 安装方式）：

```json
{
  "osu_client_id": 12345,          // 替换为你的 Client ID
  "osu_client_secret": "abc123xyz", // 替换为你的 Client Secret
  "db_path": "./osuscore.db"
}
```

## 4. 启动 AstrBot

```bash
# 按照 AstrBot 的启动方式启动
# 通常是:
python main.py
```

## 5. 使用插件

在支持的聊天平台上：

### 绑定你的账号
```
/bind peppy
```
响应: `✅ 成功绑定账号: peppy (ID: 2)`

### 查询最近成绩
```
/pr
```

### 查询其他玩家
```
/pr username
/pr peppy :1        // Taiko mode
/pr peppy :0 +HDDT  // HD+DT Mods
```

## 完成！

你现在已经有了一个可用的 OSU 查分插件！

### 下一步可以做什么

1. **查看日志** - 检查命令执行情况
2. **尝试不同的命令** - 测试各种参数组合
3. **阅读代码** - 理解插件架构（参见 DEVELOPMENT.md）
4. **扩展功能** - 实现 /bp、/info 等命令

## 故障排查

### 问题：插件加载失败
**解决方案**：检查 AstrBot 日志，确保 metadata.yaml 格式正确

### 问题：API 认证失败
**解决方案**：检查 Client ID 和 Client Secret 是否正确复制

### 问题：图片发送失败
**解决方案**：检查是否安装了 Pillow，运行 `pip install pillow`

### 问题：数据库访问错误
**解决方案**：检查 db_path 目录是否有写入权限

## 获取帮助

- 查看 README.md - 功能概览
- 查看 DEVELOPMENT.md - 技术细节
- 查看源代码注释 - 代码级文档

## 示例命令

```
# 绑定账号
/bind peppy
/bind 2

# 查询最近成绩
/pr
/pr peppy
/pr peppy :0
/pr peppy :1 +HD
/pr peppy :2 +DTHD

# 查询 mania 成绩
/mania
/mania peppy best 3
/mania peppy recent 1 4k
/mania peppy best 5 +HD

# 模式代码
# 0 = Standard (默认)
# 1 = Taiko
# 2 = Catch
# 3 = Mania
```

祝你使用愉快！ 🎮
