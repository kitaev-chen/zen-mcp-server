[根目录](../../CLAUDE.md) > [conf](../) > **conf**

## Conf模块

### 模块职责

Conf模块负责管理Zen MCP Server的所有配置数据，包括AI模型定义、客户端配置和能力元数据。该模块确保系统对所有支持的AI提供商和模型有准确的元数据访问。

### 入口和启动

- **主入口文件**: `conf/__init__.py`
- **配置类型**: JSON格式的模型定义和客户端配置
- **动态加载**: 运行时根据提供商可用性加载配置

### 外部接口

#### 模型配置文件
```json
// OpenAI模型配置
conf/openai_models.json
{
    "gpt-5": {
        "name": "gpt-5",
        "display_name": "GPT-5",
        "context_window": 200000,
        "max_output_tokens": 8000,
        "supports_vision": true,
        "supports_functions": true,
        "pricing": {
            "input_tokens": 0.000015,
            "output_tokens": 0.00006
        }
    }
}

// Gemini模型配置
conf/gemini_models.json
{
    "gemini-2.5-pro": {
        "name": "gemini-2.5-pro",
        "display_name": "Gemini 2.5 Pro",
        "context_window": 1000000,
        "max_output_tokens": 8192,
        "supports_vision": true,
        "supports_functions": true,
        "temperature_range": [0.0, 2.0]
    }
}
```

#### CLI客户端配置
```json
// Claude CLI配置
conf/cli_clients/claude.json
{
    "name": "claude",
    "display_name": "Claude Code",
    "command_template": "claude",
    "supported_roles": ["planner", "codereviewer", "default"],
    "environment": {
        "ANTHROPIC_API_KEY": "{CLAUDE_API_KEY}"
    },
    "capabilities": {
        "supports_files": true,
        "supports_vision": true,
        "supports_web_search": false
    }
}
```

### 关键依赖和配置

#### 内部依赖
- **无硬依赖**: 配置文件主要为静态JSON数据
- **提供商集成**: 被`providers/registries/`模块读取和使用
- **CLink集成**: CLI客户端配置被`clink/`模块使用

#### 配置文件结构
```
conf/
├── __init__.py              # 配置模块初始化
├── openai_models.json        # OpenAI模型定义
├── gemini_models.json        # Gemini模型定义
├── azure_models.json         # Azure OpenAI模型定义
├── xai_models.json          # X.AI模型定义
├── dial_models.json          # DIAL模型定义
├── openrouter_models.json     # OpenRouter模型定义
├── custom_models.json        # 自定义模型定义
└── cli_clients/            # CLI客户端配置
    ├── claude.json          # Claude CLI配置
    ├── gemini.json          # Gemini CLI配置
    ├── codex.json          # Codex CLI配置
    └── ...
```

### 数据模型

#### 模型能力定义
```python
class ModelCapability:
    name: str                    # 模型标识符
    display_name: str             # 显示名称
    context_window: int          # 上下文窗口大小
    max_output_tokens: int       # 最大输出token数
    supports_vision: bool        # 是否支持视觉
    supports_functions: bool      # 是否支持函数调用
    temperature_range: tuple     # 温度范围 [min, max]
    pricing: dict              # 定价信息
    provider: str               # 提供商标识
    aliases: list[str]         # 别名列表
```

#### CLI客户端定义
```python
class CLIClientConfig:
    name: str                   # 客户端标识符
    display_name: str            # 显示名称
    command_template: str         # 命令模板
    supported_roles: list[str]    # 支持的角色
    environment: dict           # 环境变量映射
    capabilities: dict          # 能力声明
    install_docs: str           # 安装文档链接
```

### 测试和质量

#### 配置验证
- **结构验证**: 确保JSON文件格式正确
- **完整性检查**: 验证必填字段和数据类型
- **一致性验证**: 检查模型参数的合理性
- **兼容性测试**: 验证配置与实际提供商API的兼容性

#### 更新和维护
- **版本跟踪**: 配置文件版本化管理
- **自动同步**: 定期同步最新模型信息
- **向后兼容**: 保持对旧版本配置的支持
- **错误恢复**: 损坏配置的自动修复机制

### 常见问题解答

**Q: 如何添加新模型配置？**
A: 在对应的提供商JSON文件中添加模型定义，确保包含所有必填字段：name, display_name, context_window等。

**Q: 模型配置的优先级是如何确定的？**
A: 提供商注册时按优先级加载，原生API优先于聚合平台，模型别名在提供商内部解析。

**Q: CLI客户端配置如何工作？**
A: CLink模块读取配置，根据CLI名称构建命令、设置环境变量和加载对应的系统提示词。

**Q: 如何验证配置文件的正确性？**
A: 运行`listmodels`工具检查模型是否正确加载，或查看服务器日志中的配置加载信息。

### 相关文件列表

#### 模型配置文件
- `conf/__init__.py` - 配置模块初始化
- `conf/openai_models.json` - OpenAI模型定义
- `conf/gemini_models.json` - Gemini模型定义
- `conf/azure_models.json` - Azure OpenAI模型定义
- `conf/xai_models.json` - X.AI模型定义
- `conf/dial_models.json` - DIAL模型定义
- `conf/openrouter_models.json` - OpenRouter模型定义
- `conf/custom_models.json` - 自定义模型模板

#### CLI客户端配置
- `conf/cli_clients/claude.json` - Claude CLI配置
- `conf/cli_clients/gemini.json` - Gemini CLI配置
- `conf/cli_clients/codex.json` - Codex CLI配置

#### 测试和验证
- `tests/test_model_enumeration.py` - 模型枚举测试
- `tests/test_supported_models_aliases.py` - 模型别名测试
- `providers/registries/` - 各提供商的注册表实现

### 变更日志 (Changelog)

**2025-11-15**: 创建模块文档，整理配置管理系统和模型定义说明

---

Conf模块为Zen MCP Server提供了统一的配置管理，通过标准化的JSON配置确保了模型和客户端信息的准确性和可维护性。