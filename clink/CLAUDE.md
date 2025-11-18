[根目录](../../CLAUDE.md) > [clink](../) > **clink**

## CLink模块

### 模块职责

CLink模块是Zen MCP Server的CLI桥接系统，实现了与外部AI CLI工具的集成和子代理功能。它允许用户在当前CLI会话中启动独立的AI CLI实例，实现上下文隔离和角色专业化。

### 入口和启动

- **主入口文件**: `clink/__init__.py`
- **注册中心**: `clink/registry.py` - CLI代理注册和管理
- **核心工具**: `tools/clink.py` - CLink工具实现

### 外部接口

#### 支持的CLI客户端
```python
# 预配置的CLI客户端
from clink import get_registry, ClinkRegistry

registry = get_registry()
available_clis = registry.list_available_clis()
# ['gemini', 'claude', 'codex', 'cursor', ...]
```

#### CLI代理系统
- **clink/agents/** - 各CLI的代理实现
- **clink/parsers/** - 响应解析器，将CLI输出标准化
- **conf/cli_clients/** - CLI配置文件和角色定义

#### 角色专业化
```python
# 预定义角色
roles = {
    'planner': 'default_planner.txt',
    'codereviewer': 'default_codereviewer.txt',
    'default': 'default.txt'
}
```

### 关键依赖和配置

#### 内部依赖
- `providers/*` - AI提供商抽象层，用于CLI实例的模型选择
- `utils/*` - 工具函数和文件处理
- `systemprompts/clink/*` - CLI专用系统提示词
- `tools/shared/*` - 工具基类和模型定义

#### 配置文件结构
```json
// conf/cli_clients/claude.json
{
    "name": "claude",
    "display_name": "Claude Code",
    "command_template": "claude",
    "supported_roles": ["planner", "codereviewer", "default"],
    "environment": {
        "ANTHROPIC_API_KEY": "{CLAUDE_API_KEY}"
    }
}
```

### 数据模型

#### CLI代理数据结构
```python
class CLIAgent:
    cli_name: str
    role: str
    command: list[str]
    environment: dict[str, str]
    system_prompt: str
    working_directory: Optional[str]

class ClinkRegistry:
    agents: dict[str, CLIAgent]
    config_dir: str
```

#### 响应解析
```python
class BaseParser(ABC):
    def parse_response(self, raw_output: str) -> str:
        """标准化CLI输出格式"""
        pass
```

### 测试和质量

#### 测试策略
- **CLI集成测试**: `tests/test_clink_integration.py` - 端到端CLI调用测试
- **解析器测试**: `tests/test_clink_parsers.py` - 各CLI响应解析测试
- **代理测试**: `tests/test_clink_*.py` - CLI代理行为验证

#### 质量保证
- 进程隔离和超时控制
- 标准化的响应格式和错误处理
- 环境变量安全和密钥管理
- 临时文件清理和资源管理

### 常见问题解答

**Q: CLink如何实现上下文隔离？**
A: 每个CLI子代理在独立进程中运行，拥有自己的上下文窗口，不会污染主会话的上下文。

**Q: 如何添加新的CLI客户端支持？**
A: 在`conf/cli_clients/`中添加配置文件，在`clink/agents/`中实现代理类，在`clink/parsers/`中实现响应解析器。

**Q: 角色专业化是如何工作的？**
A: 每个角色对应特定的系统提示词文件，CLI启动时加载对应的提示词，实现专业化行为。

**Q: 如何处理CLI的API密钥？**
A: 通过环境变量传递，支持从主配置继承或单独配置，确保密钥安全。

### 相关文件列表

#### 核心实现
- `clink/__init__.py` - 模块导出
- `clink/registry.py` - CLI注册中心
- `clink/models.py` - 数据模型定义

#### CLI代理实现
- `clink/agents/__init__.py` - 代理模块导出
- `clink/agents/base.py` - 代理基类
- `clink/agents/claude.py` - Claude Code代理
- `clink/agents/gemini.py` - Gemini CLI代理
- `clink/agents/codex.py` - Codex CLI代理

#### 响应解析器
- `clink/parsers/__init__.py` - 解析器模块导出
- `clink/parsers/base.py` - 解析器基类
- `clink/parsers/gemini.py` - Gemini响应解析
- `clink/parsers/codex.py` - Codex响应解析

#### 配置文件
- `conf/cli_clients/claude.json` - Claude CLI配置
- `conf/cli_clients/gemini.json` - Gemini CLI配置
- `conf/cli_clients/codex.json` - Codex CLI配置

#### 系统提示词
- `systemprompts/clink/default.txt` - 默认角色提示词
- `systemprompts/clink/default_planner.txt` - 规划师角色提示词
- `systemprompts/clink/default_codereviewer.txt` - 代码审查员角色提示词
- `systemprompts/clink/codex_codereviewer.txt` - Codex专用代码审查员

#### 测试文件
- `tests/test_clink_tool.py` - CLink工具测试
- `tests/test_clink_integration.py` - CLI集成测试
- `tests/test_clink_claude_agent.py` - Claude代理测试
- `tests/test_clink_gemini_agent.py` - Gemini代理测试
- `tests/test_clink_codex_agent.py` - Codex代理测试
- `tests/test_clink_parsers.py` - 解析器测试

### 变更日志 (Changelog)

**2025-11-15**: 创建模块文档，整理CLI桥接系统和子代理架构说明

---

CLink模块为Zen MCP Server提供了强大的CLI集成能力，通过标准化的代理系统实现了多CLI协作和上下文隔离，扩展了AI工具的生态系统。