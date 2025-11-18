[根目录](../../CLAUDE.md) > [simulator_tests](../) > **simulator_tests**

## Simulator Tests模块

### 模块职责

Simulator Tests模块为Zen MCP Server提供端到端的功能验证，模拟真实的AI对话工作流。这些测试使用实际的API密钥和模型，验证整个系统的集成性和用户场景覆盖。

### 入口和启动

- **主入口**: `communication_simulator_test.py` - 测试运行器
- **基类**: `simulator_tests/base_test.py` - 测试基础设施
- **日志工具**: `simulator_tests/log_utils.py` - 日志分析和验证

### 外部接口

#### 测试运行模式
```bash
# 运行所有测试 (完整验证)
python communication_simulator_test.py

# 快速模式 (6个核心测试)
python communication_simulator_test.py --quick

# 详细输出模式
python communication_simulator_test.py --verbose

# 单独测试运行
python communication_simulator_test.py --individual <test_name>
```

#### 核心测试集
**快速模式测试** (最高优先级，覆盖核心功能):
- `cross_tool_continuation` - 跨工具对话连续性
- `conversation_chain_validation` - 对话链和内存验证
- `consensus_workflow_accurate` - 共识工作流准确性
- `codereview_validation` - 代码审查工具验证
- `planner_validation` - 规划工具验证
- `token_allocation_validation` - Token分配验证

### 关键依赖和配置

#### 测试环境要求
```bash
# 必需的API密钥 (至少一个)
export GEMINI_API_KEY=your_gemini_key
export OPENAI_API_KEY=your_openai_key
export XAI_API_KEY=your_xai_key

# 可选配置
export LOG_LEVEL=DEBUG
export DEFAULT_MODEL=auto
```

#### 测试基础设施
- **BaseTest**: 提供统一的测试接口和工具方法
- **LogUtils**: 实时日志监控和错误检测
- **ConversationBaseTest**: 对话相关测试的基类

### 数据模型

#### 测试结果结构
```python
class TestResult:
    test_name: str
    status: str  # "PASSED", "FAILED", "SKIPPED"
    duration: float
    error_message: Optional[str]
    details: dict

class SimulationContext:
    thread_id: str
    messages: list[dict]
    files_used: list[str]
    models_tested: list[str]
```

#### 测试配置
```python
# 快速模式配置
QUICK_MODE_TESTS = [
    'cross_tool_continuation',
    'conversation_chain_validation',
    'consensus_workflow_accurate',
    'codereview_validation',
    'planner_validation',
    'token_allocation_validation'
]

# 完整测试列表
ALL_TESTS = [
    'basic_conversation',
    'content_validation',
    'per_tool_deduplication',
    'cross_tool_comprehensive',
    'line_number_validation',
    'memory_validation',
    'model_thinking_config',
    'o3_model_selection',
    'ollama_custom_url',
    'openrouter_fallback',
    'openrouter_models',
    'testgen_validation',
    'refactor_validation',
    'precommit_validation',
    'secaudit_validation',
    'consensus_stance',
    'debug_validation',
    'thinkdeep_validation',
    # ... 更多测试
]
```

### 测试和质量

#### 测试策略
1. **快速验证**: 6个核心测试确保基础功能正常
2. **全面覆盖**: 完整测试集验证所有工具和场景
3. **实时监控**: 通过日志分析检测测试过程中的问题
4. **错误隔离**: 单独运行每个测试以避免相互影响

#### 质量保证特性
- **真实API**: 使用实际API密钥和模型进行测试
- **实时监控**: 测试过程中实时检查服务器日志
- **错误恢复**: 自动重试和优雅的错误处理
- **详细报告**: 提供测试结果的详细分析和建议

#### 测试场景覆盖
**核心功能测试**:
- 对话启动和连续性
- 文件处理和去重
- 模型选择和切换
- 错误处理和恢复

**工作流集成测试**:
- 多工具协作场景
- 跨模型共识流程
- 复杂规划任务
- 代码审查和调试链

**边界和异常测试**:
- Token限制处理
- 网络错误恢复
- 无效输入处理
- 模型不可用情况

### 常见问题解答

**Q: 模拟器测试与单元测试的区别？**
A: 模拟器测试使用真实API密钥和模型，验证端到端功能；单元测试使用Mock，验证单个组件逻辑。

**Q: 快速模式的6个测试是如何选择的？**
A: 基于功能覆盖和重要性，选择代表核心功能的测试：对话内存、跨工具协作、共识、代码审查、规划、Token管理。

**Q: 测试失败时如何调试？**
A: 查看实时日志输出，使用`--verbose`模式获取详细信息，检查`logs/mcp_server.log`中的错误。

**Q: 如何添加新的模拟器测试？**
A: 继承`BaseTest`类，实现`execute_test()`方法，添加到测试注册表，并更新对应文档。

### 相关文件列表

#### 核心测试文件
- `communication_simulator_test.py` - 主测试运行器
- `simulator_tests/__init__.py` - 模块初始化
- `simulator_tests/base_test.py` - 测试基类
- `simulator_tests/log_utils.py` - 日志分析工具
- `simulator_tests/conversation_base_test.py` - 对话测试基类

#### 核心功能测试
- `simulator_tests/test_basic_conversation.py` - 基础对话测试
- `simulator_tests/test_content_validation.py` - 内容验证测试
- `simulator_tests/test_cross_tool_continuation.py` - 跨工具连续性测试
- `simulator_tests/test_conversation_chain_validation.py` - 对话链验证测试
- `simulator_tests/test_memory_validation.py` - 内存验证测试
- `simulator_tests/test_token_allocation_validation.py` - Token分配测试

#### 工具特定测试
- `simulator_tests/test_chat_simple_validation.py` - 聊天工具测试
- `simulator_tests/test_codereview_validation.py` - 代码审查测试
- `simulator_tests/test_debug_validation.py` - 调试工具测试
- `simulator_tests/test_planner_validation.py` - 规划工具测试
- `simulator_tests/test_consensus_workflow_accurate.py` - 共识工作流测试
- `simulator_tests/test_thinkdeep_validation.py` - 深度思考测试

#### 提供商和模型测试
- `simulator_tests/test_o3_model_selection.py` - O3模型选择测试
- `simulator_tests/test_openrouter_models.py` - OpenRouter模型测试
- `simulator_tests/test_openrouter_fallback.py` - OpenRouter降级测试
- `simulator_tests/test_ollama_custom_url.py` - 自定义URL测试
- `simulator_tests/test_xai_models.py` - X.AI模型测试

#### 专项功能测试
- `simulator_tests/test_per_tool_deduplication.py` - 文件去重测试
- `simulator_tests/test_line_number_validation.py` - 行号处理测试
- `simulator_tests/test_model_thinking_config.py` - 思考模式测试
- `simulator_tests/test_consensus_stance.py` - 共识立场测试
- `simulator_tests/test_vision_capability.py` - 视觉能力测试

#### 工作流和集成测试
- `simulator_tests/test_cross_tool_comprehensive.py` - 综合跨工具测试
- `simulator_tests/test_analyze_validation.py` - 分析工具测试
- `simulator_tests/test_refactor_validation.py` - 重构工具测试
- `simulator_tests/test_testgen_validation.py` - 测试生成测试
- `simulator_tests/test_secaudit_validation.py` - 安全审计测试
- `simulator_tests/test_precommit_validation.py` - 提交前验证测试

#### 边界和错误测试
- `simulator_tests/test_debug_certain_confidence.py` - 调试置信度测试
- `simulator_tests/test_prompt_size_limit_bug.py` - 提示词大小限制测试
- `simulator_tests/test_logs_validation.py` - 日志验证测试

### 变更日志 (Changelog)

**2025-11-15**: 创建模块文档，整理模拟器测试框架和策略说明

---

Simulator Tests模块为Zen MCP Server提供了真实环境下的功能验证，通过全面的工作流测试确保了系统的实际可用性和稳定性。