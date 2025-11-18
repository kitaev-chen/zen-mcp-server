[根目录](../../CLAUDE.md) > [providers](../) > **providers**

## Providers模块

### 模块职责

Providers模块为Zen MCP Server提供统一的AI提供商抽象层，支持8个主流AI服务提供商的集成。该模块定义了标准化的模型访问接口，实现提供商注册、模型能力管理和请求路由功能。

### 入口和启动

- **主入口文件**: `providers/__init__.py`
- **核心基类**: `providers/base.py` - 定义提供商抽象接口
- **注册中心**: `providers/registry.py` - 提供商注册和模型解析

### 外部接口

#### 支持的AI提供商

**原生API提供商**:
- `providers/gemini.py` - Google Gemini API集成
- `providers/openai.py` - OpenAI API集成 (GPT-5, O3等)
- `providers/azure_openai.py` - Azure OpenAI服务集成
- `providers/xai.py` - X.AI (Grok) API集成
- `providers/dial.py` - DIAL平台集成

**聚合和自定义提供商**:
- `providers/openrouter.py` - OpenRouter多模型聚合平台
- `providers/custom.py` - 自定义API端点 (Ollama, vLLM等)
- `providers/openai_compatible.py` - OpenAI兼容API通用适配器

#### 提供商注册系统

**注册优先级** (按配置优先级):
1. **原生API** (最高优先级) - 最直接和高效
2. **自定义端点** - 本地/私有模型
3. **OpenRouter** (兜底) - 覆盖其他所有模型

**提供商发现**:
```python
# 自动检测API密钥并注册对应提供商
ModelProviderRegistry.register_provider(ProviderType.GOOGLE, GeminiModelProvider)
ModelProviderRegistry.register_provider(ProviderType.OPENAI, OpenAIModelProvider)
ModelProviderRegistry.register_provider(ProviderType.OPENROUTER, OpenRouterProvider)
```

### 关键依赖和配置

#### 核心依赖
- `providers/shared/*` - 共享数据模型和能力定义
- `providers/registries/*` - 各提供商的模型注册表
- `utils/*` - 工具函数和环境变量处理
- `conf/*_models.json` - 模型配置文件

#### API密钥配置
```bash
# 环境变量配置
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_API_KEY=your_azure_key
XAI_API_KEY=your_xai_key
DIAL_API_KEY=your_dial_key
OPENROUTER_API_KEY=your_openrouter_key
CUSTOM_API_URL=http://localhost:11434  # Ollama
CUSTOM_API_KEY=  # 可选，某些本地模型不需要
```

#### 模型能力系统
```python
class ModelCapabilities:
    model_name: str
    context_window: int
    max_output_tokens: int
    supports_vision: bool
    supports_functions: bool
    pricing: dict
    provider_type: ProviderType
    temperature_range: tuple[float, float]
```

### 数据模型

#### 提供商类型
```python
enum ProviderType:
    GOOGLE = "google"
    OPENAI = "openai"
    AZURE = "azure"
    XAI = "xai"
    DIAL = "dial"
    OPENROUTER = "openrouter"
    CUSTOM = "custom"
```

#### 模型响应格式
```python
class ModelResponse:
    content: str
    model_name: str
    usage: TokenUsage
    finish_reason: str
    metadata: dict
```

#### 共享数据结构
- `ModelCapabilities` - 模型能力元数据
- `ModelResponse` - 统一的响应格式
- `ProviderType` - 提供商类型枚举
- `Temperature` - 温度参数验证和处理

### 测试和质量

#### 测试覆盖
- **单元测试**: 每个提供商的独立测试 (`tests/test_*provider*.py`)
- **集成测试**: 真实API调用测试 (`tests/test_*_integration.py`)
- **模型解析测试**: 别名解析和模型验证
- **错误处理测试**: API失败和降级策略

#### 质量保证
- 统一的错误处理和重试逻辑
- 速率限制和配额管理
- 模型能力验证和限制检查
- 优雅的降级和回退机制

### 常见问题解答

**Q: 如何添加新的AI提供商？**
A: 继承`ModelProvider`基类，实现`MODEL_CAPABILITIES`和必要方法，然后通过`ModelProviderRegistry.register_provider()`注册。

**Q: 提供商优先级是如何确定的？**
A: 原生API优先于自定义端点，OpenRouter作为兜底。可通过API密钥配置自动调整优先级。

**Q: 如何处理模型限制和配额？**
A: 每个提供商内部实现速率限制、token计数和配额检查，超出限制时提供清晰的错误消息。

**Q: 模型能力是如何定义的？**
A: 每个提供商在`MODEL_CAPABILITIES`字典中定义支持的模型及其能力，包括上下文窗口、视觉支持等。

**Q: 如何配置自定义模型端点？**
A: 设置`CUSTOM_API_URL`环境变量，可选提供`CUSTOM_API_KEY`和`CUSTOM_MODEL_NAME`。

### 相关文件列表

#### 核心实现
- `providers/__init__.py` - 模块导出
- `providers/base.py` - 抽象基类
- `providers/registry.py` - 注册中心
- `providers/registry_provider_mixin.py` - 注册混入类

#### 具体提供商实现
- `providers/gemini.py` - Google Gemini实现
- `providers/openai.py` - OpenAI实现
- `providers/azure_openai.py` - Azure OpenAI实现
- `providers/xai.py` - X.AI实现
- `providers/dial.py` - DIAL实现
- `providers/openrouter.py` - OpenRouter实现
- `providers/custom.py` - 自定义端点实现
- `providers/openai_compatible.py` - 通用适配器

#### 共享组件
- `providers/shared/__init__.py` - 共享组件导出
- `providers/shared/model_capabilities.py` - 模型能力定义
- `providers/shared/model_response.py` - 响应格式定义
- `providers/shared/provider_type.py` - 提供商类型枚举
- `providers/shared/temperature.py` - 温度参数处理

#### 注册表实现
- `providers/registries/base.py` - 注册表基类
- `providers/registries/openai.py` - OpenAI模型注册表
- `providers/registries/gemini.py` - Gemini模型注册表
- `providers/registries/azure.py` - Azure模型注册表
- `providers/registries/xai.py` - X.AI模型注册表
- `providers/registries/dial.py` - DIAL模型注册表
- `providers/registries/openrouter.py` - OpenRouter模型注册表
- `providers/registries/custom.py` - 自定义模型注册表

#### 测试文件
- `tests/test_openai_provider.py` - OpenAI提供商测试
- `tests/test_gemini_token_usage.py` - Gemini Token使用测试
- `tests/test_openrouter_provider.py` - OpenRouter测试
- `tests/test_custom_provider.py` - 自定义提供商测试
- `tests/test_auto_mode_provider_selection.py` - 自动模式测试

### 变更日志 (Changelog)

**2025-11-15**: 创建模块文档，整理提供商架构和接口说明

---

Providers模块为Zen MCP Server提供了强大的多模型支持能力，通过统一的抽象层实现了AI提供商的插件化架构，确保了系统的可扩展性和灵活性。