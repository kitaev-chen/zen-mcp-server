# Integration Tests for Clink CLI

## 概述

这个目录包含对真实 CLI 工具的集成测试，分为两层：

1. **Agent 层测试** (`test_agent_real_cli.py`) - 测试 Agent → CLI → Parser 链路
2. **Tool 层测试** (`test_tool_real_cli.py`) - 测试完整的 MCP Tool → Registry → Agent 链路

## 前置条件

### 1. CLI 工具安装

所有 7 个 CLI 必须安装并在 PATH 中可用：

```bash
# 检查 CLI 是否可用
gemini --version
codex --version
claude --version
iflow --version
kimi --version
qwen --version
vecli --version
```

### 2. CLI 认证配置

每个 CLI 需要在**自己的配置**中设置 API key 或 auth：

- **gemini**: `~/.gemini/config` 或环境变量
- **codex**: `~/.codex/credentials`
- **claude**: `~/.claude/config.json`
- **iflow**: 按 iflow 文档配置
- **kimi**: 按 kimi 文档配置
- **qwen**: 按 qwen 文档配置
- **vecli**: 按 vecli 文档配置

**重要**：本项目的 `.env` 文件**不需要**配置这些 API key，因为测试直接调用 CLI 工具。

### 3. Python 依赖

```bash
pip install -r requirements-dev.txt
```

## 运行测试

### 运行所有集成测试

```bash
python -m pytest tests/integration/ -m integration -v
```

### 只运行 Agent 层测试

```bash
python -m pytest tests/integration/test_agent_real_cli.py -m integration -v
```

### 只运行 Tool 层测试

```bash
python -m pytest tests/integration/test_tool_real_cli.py -m integration -v
```

### 测试特定的 CLI

```bash
# 只测试 iflow
python -m pytest tests/integration/ -m integration -k iflow -v

# 只测试新增的 4 个 CLI
python -m pytest tests/integration/ -m integration -k "iflow or kimi or qwen or vecli" -v

# 只测试原有的 3 个 CLI（回归测试）
python -m pytest tests/integration/ -m integration -k "gemini or codex or claude" -v
```

### 测试特定的功能

```bash
# 只测试基本执行
python -m pytest tests/integration/ -m integration -k "basic_execution" -v

# 只测试元数据提取
python -m pytest tests/integration/ -m integration -k "metadata" -v

# 只测试新 CLI 的功能
python -m pytest tests/integration/ -m integration -k "new_cli" -v
```

## 测试层次说明

### Agent 层测试 (`test_agent_real_cli.py`)

**测试目标**：
- ✅ CLI 子进程执行
- ✅ stdout/stderr 捕获
- ✅ Parser 正确解析
- ✅ Agent 错误恢复

**测试用例**：
1. `test_real_cli_basic_execution` - 基本执行测试（7个CLI参数化）
2. `test_real_cli_metadata_extraction` - 元数据提取（7个CLI参数化）
3. `test_new_cli_agents_functional` - 新CLI功能验证（4个CLI参数化）
4. `test_real_cli_timeout_handling` - 超时处理
5. `test_original_cli_still_works` - 原有CLI回归测试（3个CLI参数化）

**优点**：
- 快速定位问题（更底层）
- 不依赖 registry/tool 配置
- 适合调试单个 CLI

**缺点**：
- 不验证完整链路
- 不测试配置加载

### Tool 层测试 (`test_tool_real_cli.py`)

**测试目标**：
- ✅ MCP Tool API 完整性
- ✅ Registry 配置加载
- ✅ CLI 客户端解析
- ✅ 响应格式化
- ✅ 端到端流程

**测试用例**：
1. `test_clink_tool_real_cli_execution` - 完整流程测试（7个CLI参数化）
2. `test_new_cli_tool_integration` - 新CLI集成验证（4个CLI参数化）
3. `test_tool_defaults_to_first_cli` - 默认CLI测试
4. `test_original_cli_tool_integration` - 原有CLI回归测试（3个CLI参数化）
5. `test_tool_with_different_roles` - 角色切换测试
6. `test_tool_response_truncation_with_real_cli` - 长输出处理
7. `test_all_cli_configs_loadable` - 配置加载冒烟测试

**优点**：
- 验证真实使用场景
- 测试配置正确性
- 端到端信心

**缺点**：
- 故障面更大
- 定位问题需要排查多层

## 测试策略

### 递进式测试

```
1. Parser 单元测试 (tests/test_clink_*_parser.py)
   ↓ 通过
2. Agent 集成测试 (tests/integration/test_agent_real_cli.py)
   ↓ 通过
3. Tool 端到端测试 (tests/integration/test_tool_real_cli.py)
   ↓ 通过
4. 生产环境部署 ✅
```

### 故障诊断流程

```
Tool 层测试失败
    ↓
检查 Agent 层测试
    ↓
    ├─ Agent 层也失败 → CLI/Parser/Agent 问题
    └─ Agent 层成功 → Registry/Tool/Config 问题
```

## 预期测试时间

- **Agent 层**：每个 CLI ~5-30秒（取决于 CLI 响应速度）
- **Tool 层**：每个 CLI ~5-30秒
- **总计**：全部运行约 3-10 分钟

**提示**：可以并行运行测试（使用 `-n auto` 需要 pytest-xdist）：

```bash
python -m pytest tests/integration/ -m integration -n auto
```

## 持续集成 (CI)

集成测试**默认不在 CI 中运行**，因为：
- 需要外部 CLI 工具
- 需要 API 认证
- 运行时间较长

如需在 CI 中运行：
1. 在 CI 环境安装所有 CLI
2. 配置 secret/credential
3. 显式运行：`pytest -m integration`

## 常见问题

### Q: 某个 CLI 测试失败了怎么办？

A: 按顺序检查：
1. CLI 是否在 PATH 中？`which <cli_name>`
2. CLI 是否配置了认证？手动执行 `<cli_name> "test"`
3. Agent 层测试是否通过？`pytest -m integration -k "<cli_name> and agent"`
4. Parser 单元测试是否通过？`pytest tests/test_clink_<cli_name>_parser.py`

### Q: 所有测试都很慢？

A: 这是正常的，因为在真实调用 LLM API。可以：
- 只运行特定 CLI：`-k iflow`
- 使用更快的模型（在 CLI 配置中调整）
- 并行运行：`-n auto`

### Q: 测试时会产生费用吗？

A: 是的，每次调用 CLI 都会消耗 API 配额/产生费用。建议：
- 在开发时有选择地运行测试
- 使用简短的 prompt
- 考虑使用免费额度的模型

### Q: 能否 mock 掉真实调用？

A: 可以，但那就不是"集成测试"了。Mock 测试已经在 `tests/test_clink_*` 中覆盖。

## 测试覆盖总览

| 测试层 | 文件数 | 测试用例 | CLI覆盖 | 真实调用 |
|--------|--------|----------|---------|----------|
| Parser 单元 | 7 | ~40 | 7/7 | ❌ |
| Agent 集成 | 1 | ~20 | 7/7 | ✅ |
| Tool 端到端 | 1 | ~15 | 7/7 | ✅ |
| **总计** | **9** | **~75** | **7/7** | **35个** |

## 贡献指南

添加新的集成测试时：

1. **必须标记** `@pytest.mark.integration`
2. **必须参数化** 如果逻辑适用于多个 CLI
3. **必须有文档** 说明测试目的和前置条件
4. **必须快速** 使用简短的 prompt，避免长时间运行
5. **必须健壮** 不假设 LLM 输出的具体内容（只验证结构）

## 参考文档

- [CLINK_CLI_IMPLEMENTATION.md](../../CLINK_CLI_IMPLEMENTATION.md) - 实施总结
- [CLINK_IMPLEMENTATION_CHECKLIST.md](../../CLINK_IMPLEMENTATION_CHECKLIST.md) - 完整清单
- [docs/clink_cli_parsers.md](../../docs/clink_cli_parsers.md) - Parser 配置文档
