[根目录](../../CLAUDE.md) > [systemprompts](../) > **systemprompts**

## SystemPrompts模块

### 模块职责

SystemPrompts模块负责管理和提供所有AI工具的系统提示词模板。这些提示词定义了每个工具的行为模式、输出格式和专业角色，确保AI模型在不同任务中表现出一致性和专业性。

### 入口和启动

- **主入口文件**: `systemprompts/__init__.py`
- **提示词类型**: 涵盖18个工具的专用提示词
- **CLink专用**: `systemprompts/clink/` - CLI代理角色提示词

### 外部接口

#### 核心工具提示词
```python
# 导入所有提示词模板
from systemprompts import (
    CHAT_PROMPT,           # 聊天和协作
    THINKDEEP_PROMPT,       # 深度思考和推理
    PLANNER_PROMPT,         # 项目规划和分解
    CONSENSUS_PROMPT,        # 多模型共识
    CODEREVIEW_PROMPT,      # 代码审查和分析
    DEBUG_ISSUE_PROMPT,      # 问题调试和根因分析
    PRECOMMIT_PROMPT,       # 提交前验证
    ANALYZE_PROMPT,         # 通用代码分析
    REFACTOR_PROMPT,        # 代码重构建议
    TESTGEN_PROMPT,         # 测试用例生成
    SECAUDIT_PROMPT,       # 安全审计
    DOCGEN_PROMPT,          # 文档生成
    TRACER_PROMPT,          # 代码路径跟踪
    GENERATE_CODE_PROMPT,    # 代码生成
    CHALLENGE_PROMPT,       # 批判性思维
)
```

#### CLink角色提示词
```python
# CLI代理角色专用提示词
systemprompts/clink/
├── default.txt              # 默认通用角色
├── default_planner.txt      # 规划师角色
├── default_codereviewer.txt  # 代码审查员角色
└── codex_codereviewer.txt  # Codex专用审查员
```

### 关键依赖和配置

#### 内部依赖
- **无硬依赖**: 提示词主要为字符串常量，独立于其他模块
- **工具集成**: 通过`tools/`模块导入和使用
- **CLink集成**: 通过`clink/`模块加载角色提示词

#### 提示词设计原则
- **一致性**: 所有提示词遵循统一的格式和结构
- **专业性**: 针对不同任务设计专业角色和行为
- **可扩展性**: 支持参数化和条件逻辑
- **多语言**: 支持通过LOCALE配置的语言本地化

### 数据模型

#### 提示词结构模式
```python
# 标准提示词结构
PROMPT_TEMPLATE = """
你是一个专业的{角色名称}。

任务描述:
{任务详情}

要求:
1. {要求1}
2. {要求2}
3. {要求3}

输出格式:
{输出格式说明}

注意事项:
- {注意事项1}
- {注意事项2}
"""
```

#### 参数化支持
```python
# 支持的参数化变量
{
    'role': '角色名称',
    'task_description': '任务描述',
    'temperature': '创造性级别',
    'locale': '语言设置',
    'model_capabilities': '模型能力'
}
```

### 测试和质量

#### 质量保证策略
- **格式验证**: 确保所有提示词遵循统一格式
- **效果测试**: 通过模拟器测试验证提示词效果
- **多语言测试**: 验证本地化支持的正确性
- **性能测试**: 监控提示词对响应时间和质量的影响

#### 提示词分类
**分析类提示词** (客观、结构化):
- `ANALYZE_PROMPT` - 通用代码分析
- `CODEREVIEW_PROMPT` - 代码审查
- `DEBUG_ISSUE_PROMPT` - 问题调试
- `SECAUDIT_PROMPT` - 安全审计
- `TRACER_PROMPT` - 路径跟踪

**创作类提示词** (创造性、生成性):
- `CHAT_PROMPT` - 对话和头脑风暴
- `THINKDEEP_PROMPT` - 深度思考
- `PLANNER_PROMPT` - 项目规划
- `REFACTOR_PROMPT` - 重构建议
- `TESTGEN_PROMPT` - 测试生成
- `DOCGEN_PROMPT` - 文档生成
- `GENERATE_CODE_PROMPT` - 代码生成

**协作类提示词** (交互性、协调性):
- `CONSENSUS_PROMPT` - 多模型共识
- `PRECOMMIT_PROMPT` - 验证和检查
- `CHALLENGE_PROMPT` - 批判性分析

### 常见问题解答

**Q: 提示词如何支持多语言？**
A: 通过`LOCALE`环境变量配置，在提示词中包含语言指令，确保AI模型以指定语言响应。

**Q: 如何自定义提示词？**
A: 可以直接修改`systemprompts/`中的对应文件，或通过环境变量覆盖特定提示词内容。

**Q: 提示词参数化是如何工作的？**
A: 提示词模板包含占位符，在运行时由工具类填充具体值，如角色、任务描述等。

**Q: CLink提示词与标准提示词有何区别？**
A: CLink提示词专门为CLI代理设计，强调角色专业化和输出格式标准化，确保与外部CLI的一致性。

### 相关文件列表

#### 核心提示词文件
- `systemprompts/__init__.py` - 模块导出和提示词常量
- `systemprompts/chat_prompt.py` - 聊天提示词
- `systemprompts/thinkdeep_prompt.py` - 深度思考提示词
- `systemprompts/planner_prompt.py` - 规划提示词
- `systemprompts/consensus_prompt.py` - 共识提示词
- `systemprompts/codereview_prompt.py` - 代码审查提示词
- `systemprompts/debug_prompt.py` - 调试提示词
- `systemprompts/precommit_prompt.py` - 提交前验证提示词
- `systemprompts/analyze_prompt.py` - 分析提示词
- `systemprompts/refactor_prompt.py` - 重构提示词
- `systemprompts/testgen_prompt.py` - 测试生成提示词
- `systemprompts/secaudit_prompt.py` - 安全审计提示词
- `systemprompts/docgen_prompt.py` - 文档生成提示词
- `systemprompts/tracer_prompt.py` - 跟踪提示词
- `systemprompts/generate_code_prompt.py` - 代码生成提示词
- `systemprompts/challenge_prompt.py` - 批判性思维提示词

#### CLink专用提示词
- `systemprompts/clink/default.txt` - 默认CLI代理角色
- `systemprompts/clink/default_planner.txt` - CLI规划师角色
- `systemprompts/clink/default_codereviewer.txt` - CLI代码审查员角色
- `systemprompts/clink/codex_codereviewer.txt` - Codex专用审查员

#### 测试相关
- `tests/test_prompt_regression.py` - 提示词回归测试
- `simulator_tests/test_prompt_size_limit_bug.py` - 提示词大小限制测试

### 变更日志 (Changelog)

**2025-11-15**: 创建模块文档，整理提示词管理系统和设计原则说明

---

SystemPrompts模块为Zen MCP Server提供了专业的AI行为指导，通过精心设计的提示词确保了各工具的一致性、专业性和多语言支持。