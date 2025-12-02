# 如何确保 Claude Code 使用当前开发版本的 zen-mcp-server

当您在开发 zen-mcp-server 时，Claude Code 可能会使用缓存的旧版本配置。以下是确保 Claude Code 使用当前开发版本的方法：

## 方法 1: 重新配置 Claude Code

运行以下命令重新配置 Claude Code 使用当前目录下的开发版本：

### Windows:
```powershell
# PowerShell
.\update-claude-config.ps1
```

或

```cmd
# Command Prompt
update-claude-config.bat
```

### 通用方法:
```bash
.\run-server.ps1
```
这个脚本会自动检测并配置所有兼容的 MCP 客户端（包括 Claude Code）来使用当前目录的开发版本。

## 方法 2: 手动更新 Claude CLI 配置

如果您使用 Claude CLI，可以手动更新配置：

```bash
# 移除旧的 zen 配置
claude mcp remove zen

# 添加当前开发版本（确保您在项目根目录下）
claude mcp add -s user zen .zen_venv\Scripts\python.exe server.py
```

## 方法 3: 使用开发运行脚本

您也可以使用以下命令运行开发版本：

```bash
python run_dev_version.py
```

## 重要提示

1. **重启 Claude Code**: 每次更新配置后，必须重启 Claude Code 以应用更改。

2. **检查虚拟环境**: 确保已运行 `.\run-server.ps1` 来设置虚拟环境：
   ```bash
   .\run-server.ps1
   ```

3. **验证当前版本**: 要验证 Claude Code 是否使用了正确的版本，可以在服务器运行时查看日志：
   ```bash
   .\run-server.ps1 -Follow
   ```

4. **使用当前目录**: 确保您始终在 zen-mcp-server 项目的根目录中运行这些命令。

## 故障排除

如果 Claude Code 仍然使用旧配置：

1. 检查 Claude 桌面应用的配置文件：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - 确保其中的 zen 配置指向正确的 Python 和 server.py 路径

2. 完全关闭 Claude Code，包括后台进程，然后重新启动

3. 检查是否有其他地方安装了 zen-mcp-server，可能会干扰当前开发版本

## 开发工作流建议

为了确保您的代码更改能实时反映：

1. 在项目根目录运行 `.\run-server.ps1` 进行初始设置
2. 每当您对 server.py 或相关文件进行重大更改后，运行 `.\update-claude-config.ps1`
3. 重启 Claude Code
4. 测试您的更改是否生效

这样，您对 zen-mcp-server 的任何更改都会立即在 Claude Code 中生效。