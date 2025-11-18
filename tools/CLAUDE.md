[根目录](../../CLAUDE.md) > [tools](../) > **tools**

## Tools模块

### 模块职责

Tools模块是Zen MCP Server的核心功能组件，实现了18个专用AI工具，涵盖代码分析、规划、调试、安全审计等全方位的开发场景。每个工具都继承自BaseTool抽象基类，提供统一的接口和行为。

### 入口和启动

- **主入口文件**: `tools/__init__.py`
- **核心基类**: `tools/shared/base_tool.py` - 定义所有工具的通用接口
- **模型分类**: `tools/shared/base_models.py` - 定义工具模型类别和输出格式

### 外部接口

#### 核心工具类别

**协作与规划工具** (默认启用):
- `chat` - 交互式开发和头脑风暴
- `clink` - CLI桥接器，支持外部AI CLI集成
- `thinkdeep` - 扩展推理工作流，专家级深度分析
- `planner` - 交互式顺序规划器
- `consensus` - 多模型共识工作流

**代码分析与质量工具** (默认启用):
- `debug` - 系统性调查和根因分析
- `precommit` - 提交前验证工作流
- `codereview` - 专业代码审查，严重性级别分级
- `apilookup` - 快速API/SDK文档查找

**开发工具** (默认禁用，可通过环境变量启用):
- `analyze` - 通用文件和代码分析
- `refactor` - 智能重构分析工作流
- `testgen` - 综合测试生成
- `secaudit` - OWASP Top 10安全审计
- `docgen` - 文档生成和复杂度分析
- `tracer` - 静态调用路径预测
- `challenge` - 关键性分析，防止自动同意

#### 工具配置
- **启用/禁用**: 通过`DISABLED_TOOLS`环境变量控制
- **默认工具**: chat, thinkdeep, planner, consensus, codereview, precommit, debug, apilookup, challenge
- **可选工具**: analyze, refactor, testgen, secaudit, docgen, tracer

### 关键依赖和配置

#### 内部依赖
- `providers/*` - AI提供商抽象层
- `utils/*` - 工具函数和对话内存
- `systemprompts/*` - 系统提示词模板
- `config.py` - 全局配置和常量

#### 配置参数
- `MCP_PROMPT_SIZE_LIMIT` - 提示词大小限制
- `TEMPERATURE_*` - 不同工具类型的温度设置
- `DEFAULT_MODEL` - 默认AI模型
- `IS_AUTO_MODE` - 自动模型选择模式

### 数据模型

#### 核心数据结构
```python
# 工具输出格式
class ToolOutput:
    status: str  # "success", "error", "partial"
    content: str
    content_type: str  # "text", "json", "markdown"
    metadata: dict

# 继续提供
class ContinuationOffer:
    continuation_id: str
    tool_name: str
    suggested_followups: list[str]
    expires_at: datetime

# 模型类别
enum ToolModelCategory:
    CHAT = "chat"
    ANALYSIS = "analysis"
    WORKFLOW = "workflow"
    PLANNING = "planning"
```

### 测试和质量

#### 测试策略
- **单元测试**: `tests/test_*.py` - 每个工具的独立测试
- **集成测试**: 使用真实API密钥的端到端测试
- **模拟器测试**: `simulator_tests/test_*_validation.py` - 工作流验证

#### 质量保证
- 继承自`BaseTool`确保一致性
- 统一的错误处理和响应格式
- 智能文件处理和token预算管理
- 对话连续性支持

### 常见问题解答

**Q: 如何启用默认禁用的工具？**
A: 在`.env`文件中从`DISABLED_TOOLS`列表移除相应工具名，或设置为空字符串启用所有工具。

**Q: 工具如何处理大文件？**
A: 使用智能文件分块、token预算管理和去重机制，确保在上下文限制内处理大代码库。

**Q: 如何实现跨工具对话连续性？**
A: 使用`continuation_id`参数，系统自动重建对话历史和文件上下文，支持analyze→codereview→debug等工具链。

**Q: 工具的模型选择策略是什么？**
A: 支持手动指定模型或自动模式，自动模式下根据工具类别和可用性选择最佳模型。

### 相关文件列表

#### 核心实现
- `tools/__init__.py` - 工具注册和导出
- `tools/shared/base_tool.py` - 抽象基类
- `tools/shared/base_models.py` - 数据模型
- `tools/shared/schema_builders.py` - JSON Schema构建器
- `tools/workflow/workflow_mixin.py` - 工作流混入类

#### 具体工具实现
- `tools/chat.py` - 聊天工具
- `tools/clink.py` - CLI桥接工具
- `tools/thinkdeep.py` - 深度思考工具
- `tools/planner.py` - 规划工具
- `tools/consensus.py` - 共识工具
- `tools/codereview.py` - 代码审查工具
- `tools/debug.py` - 调试工具
- `tools/precommit.py` - 提交前验证工具
- `tools/analyze.py` - 分析工具
- `tools/refactor.py` - 重构工具
- `tools/testgen.py` - 测试生成工具
- `tools/secaudit.py` - 安全审计工具
- `tools/docgen.py` - 文档生成工具
- `tools/tracer.py` - 跟踪工具
- `tools/challenge.py` - 挑战工具
- `tools/apilookup.py` - API查找工具
- `tools/listmodels.py` - 模型列表工具
- `tools/version.py` - 版本工具

#### 测试文件
- `tests/test_chat.py` - 聊天工具测试
- `tests/test_codereview.py` - 代码审查测试
- `tests/test_debug.py` - 调试工具测试
- `tests/test_refactor.py` - 重构工具测试
- `tests/test_consensus.py` - 共识工具测试
- `simulator_tests/test_*_validation.py` - 工作流验证测试

### 变更日志 (Changelog)

**2025-11-15**: 创建模块文档，整理工具分类和接口说明

---

Tools模块为Zen MCP Server提供了丰富的AI功能集合，通过统一的架构确保一致性和可扩展性，支持复杂的多模型协作工作流。