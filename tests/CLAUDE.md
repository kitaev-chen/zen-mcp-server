[根目录](../../CLAUDE.md) > [tests](../) > **tests**

## Tests模块

### 模块职责

Tests模块为Zen MCP Server提供全面的测试框架，包括单元测试、集成测试和回归测试。该模块确保代码质量、功能正确性和API兼容性，支持开发过程中的持续验证。

### 入口和启动

- **主配置文件**: `tests/conftest.py` - pytest配置和fixture
- **运行入口**: `python -m pytest tests/` - 启动所有测试
- **分类执行**: 通过标记区分单元测试和集成测试

### 外部接口

#### 测试分类系统
```bash
# 单元测试 (快速，不需要API密钥)
python -m pytest tests/ -v -m "not integration"

# 集成测试 (需要API密钥，使用本地模型)
python -m pytest tests/ -v -m "integration"

# 覆盖率报告
python -m pytest tests/ --cov=. --cov-report=html -m "not integration"
```

#### 关键测试领域
- **提供商测试**: AI提供商集成和模型解析
- **工具测试**: 各AI工具的功能和错误处理
- **工具函数测试**: utils模块的核心功能
- **集成测试**: 端到端工作流验证
- **回归测试**: 防止功能退化和bug重现

### 关键依赖和配置

#### 测试依赖
```python
# 核心测试框架
pytest >= 7.0.0
pytest-cov          # 覆盖率报告
pytest-asyncio      # 异步测试支持

# 测试工具和模拟
pytest-mock        # Mock和patch
vcrpy             # HTTP请求录制和回放
responses          # HTTP模拟
```

#### 配置和环境
```python
# conftest.py中的关键fixture
@pytest.fixture
def mock_provider():
    """模拟AI提供商用于单元测试"""

@pytest.fixture
def sample_files():
    """提供测试用的示例文件"""

@pytest.fixture
def temp_dir():
    """临时目录fixture"""
```

#### API密钥和集成测试
```bash
# 集成测试配置
export CUSTOM_API_URL="http://localhost:11434"  # Ollama
export CUSTOM_MODEL_NAME="llama3.2"
# 注意：集成测试使用本地模型，免费无限制
```

### 数据模型

#### 测试数据结构
```python
class TestCase:
    name: str
    description: str
    setup: Callable[[], None]
    execute: Callable[[], Any]
    validate: Callable[[Any], bool]
    cleanup: Callable[[], None]

class MockResponse:
    content: str
    model_name: str
    usage: TokenUsage
    finish_reason: str
```

#### 测试标记系统
```python
pytest_marks = {
    'unit': '单元测试 - 快速，无外部依赖',
    'integration': '集成测试 - 需要API密钥',
    'slow': '慢速测试 - 耗时操作',
    'network': '网络测试 - 需要网络连接'
}
```

### 测试和质量

#### 测试策略
1. **单元测试优先**: 快速反馈，无外部依赖
2. **集成验证**: 使用本地Ollama进行真实API测试
3. **回归保护**: 通过cassettes录制和回放确保稳定性
4. **覆盖率监控**: 持续跟踪测试覆盖率

#### 质量保证措施
- **自动化测试**: CI/CD集成的自动测试流水线
- **测试隔离**: 每个测试独立运行，避免相互影响
- **Mock策略**: 对外部依赖进行合理模拟
- **数据清理**: 测试后自动清理临时文件和状态

#### CI/CD集成
```yaml
# .github/workflows/test.yml (示例)
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run unit tests
        run: python -m pytest tests/ -m "not integration" --cov=.
      - name: Run integration tests
        run: |
          export CUSTOM_API_URL="http://localhost:11434"
          python -m pytest tests/ -m "integration"
```

### 常见问题解答

**Q: 如何运行特定测试？**
A: 使用`python -m pytest tests/test_file.py::TestClass::test_method -v`运行具体测试。

**Q: 集成测试需要什么准备？**
A: 需要安装Ollama并拉取模型，设置`CUSTOM_API_URL`环境变量指向本地端点。

**Q: 如何调试测试失败？**
A: 使用`--verbose`和`--pdb`选项，或查看测试日志和生成的临时文件。

**Q: 测试cassettes是什么？**
A: VCR.py录制的HTTP请求和响应，用于模拟API调用，确保测试的可重复性。

### 相关文件列表

#### 核心测试文件
- `tests/conftest.py` - pytest配置和全局fixture
- `tests/__init__.py` - 测试模块初始化

#### 提供商测试
- `tests/test_openai_provider.py` - OpenAI提供商测试
- `tests/test_gemini_token_usage.py` - Gemini token使用测试
- `tests/test_openrouter_provider.py` - OpenRouter测试
- `tests/test_azure_openai_provider.py` - Azure OpenAI测试
- `tests/test_xai_provider.py` - X.AI提供商测试
- `tests/test_custom_provider.py` - 自定义提供商测试
- `tests/test_dial_provider.py` - DIAL提供商测试

#### 工具测试
- `tests/test_chat.py` - 聊天工具测试
- `tests/test_codereview.py` - 代码审查测试
- `tests/test_debug.py` - 调试工具测试
- `tests/test_refactor.py` - 重构工具测试
- `tests/test_consensus.py` - 共识工具测试
- `tests/test_planner.py` - 规划工具测试
- `tests/test_listmodels.py` - 模型列表工具测试
- `tests/test_version.py` - 版本工具测试

#### 工具函数测试
- `tests/test_utils.py` - utils模块测试
- `tests/test_conversation_memory.py` - 对话内存测试
- `tests/test_file_types.py` - 文件类型测试
- `tests/test_model_restrictions.py` - 模型限制测试

#### CLink测试
- `tests/test_clink_tool.py` - CLink工具测试
- `tests/test_clink_integration.py` - CLI集成测试
- `tests/test_clink_claude_agent.py` - Claude代理测试
- `tests/test_clink_gemini_agent.py` - Gemini代理测试
- `tests/test_clink_codex_agent.py` - Codex代理测试
- `tests/test_clink_parsers.py` - 解析器测试

#### 集成和回归测试
- `tests/test_auto_mode_comprehensive.py` - 自动模式综合测试
- `tests/test_prompt_regression.py` - 提示词回归测试
- `tests/test_integration_utf8.py` - UTF-8集成测试
- `tests/test_model_enumeration.py` - 模型枚举测试

#### 专用测试
- `tests/test_buggy_behavior_prevention.py` - Bug预防测试
- `tests/test_file_protection.py` - 文件保护测试
- `tests/test_disabled_tools.py` - 工具禁用测试
- `tests/test_pii_sanitizer.py` - PII数据处理测试

#### 测试辅助工具
- `tests/mock_helpers.py` - Mock工具和助手
- `tests/http_transport_recorder.py` - HTTP传输录制器
- `tests/transport_helpers.py` - 传输层测试助手
- `tests/pii_sanitizer.py` - PII数据清理工具

#### 测试数据和cassettes
- `tests/openai_cassettes/` - OpenAI API录制数据
- `tests/gemini_cassettes/` - Gemini API录制数据
- `tests/triangle.png` - 测试用图像文件

### 变更日志 (Changelog)

**2025-11-15**: 创建模块文档，整理测试框架和策略说明

---

Tests模块为Zen MCP Server提供了全面的质量保证体系，通过分层测试策略确保了代码的可靠性、性能和兼容性。