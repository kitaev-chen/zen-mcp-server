---
name: test-generation
description: Generate comprehensive test cases for code. Analyzes code structure, identifies edge cases, generates unit tests, and reviews test quality. Use when adding tests to existing code or ensuring test coverage.
---

# Test Generation

测试用例生成：代码分析 → 边界识别 → 测试生成 → 质量审查。

**适用场景**：为现有代码添加测试、提高测试覆盖率、识别边界条件。

## 模型配置

### 推荐模型（本 Skill 适用）

| 别名 | 推荐原因 |
|------|---------|
| `pro` | ⭐ 首选，代码理解强 |
| `kimik` | ⭐ 代码生成 |
| `flash` | 快速生成 |
| `gcli` | CLI 免费 |

### 完整可选列表

**API 模型**：`pro`, `flash`, `glm-4.6`, `kimik`, `kimit`, `deepseekv`, `deepseekr`, `longcatt`, `minimax`

**CLI 模型**：`gcli`, `kcli`, `icli`, `qcli`, `vcli`, `ocli`, `ccli`

> 完整说明见 [README 模型选择指南](../README.md#模型选择指南)

## 工具串联

```
search_code (可选) → testgen → codereview
```

## 与其他 Skills 的区别

| Skill | 特点 |
|-------|------|
| **test-generation** | 专注测试生成和边界识别 |
| full-feature-cycle | 完整开发周期，测试是其中一步 |
| secure-review | 安全审查，不生成测试 |

## Instructions

### 步骤 1：分析目标代码（可选）

如果不确定测试范围：
```
Use search_code with query="[功能关键词]" to find relevant code.
```

### 步骤 2：生成测试用例

```
Use testgen to generate tests for [文件路径]:

Focus areas:
- Normal cases (正常流程)
- Edge cases (边界条件)
- Error handling (错误处理)
- Input validation (输入验证)
```

如果用户指定了模型：
```
Use testgen with model [USER_MODEL] to generate tests.
```

### 步骤 3：审查测试质量

```
Use codereview to review the generated tests:

Check:
- Test coverage completeness
- Edge case coverage
- Mock usage appropriateness
- Test naming conventions
```

## Examples

### 示例 1：为函数生成测试

```
Generate tests for tools/index_code.py

Step 1: Use testgen to generate comprehensive tests for tools/index_code.py.

Focus on:
- File indexing with various extensions
- Path validation
- Error handling for missing files
- Large file handling

Step 2: Use codereview to verify test quality and coverage.
```

### 示例 2：快速测试生成

```
Use testgen to generate tests for [文件路径].

Focus on edge cases and error handling.
```

### 示例 3：带搜索的测试生成

```
Step 1: Use search_code with query="authentication" to find auth code.

Step 2: Use testgen to generate tests for the found authentication modules.

Step 3: Use codereview to verify security-related test coverage.
```

### 示例 4：CLI 模型生成

```
Use testgen with model gcli to generate tests for [文件路径].

Then use codereview with model gcli to review.
```

## 测试生成检查清单

生成后确保覆盖：

- [ ] **正常流程** - Happy path
- [ ] **边界条件** - 空值、最大值、最小值
- [ ] **错误处理** - 异常、无效输入
- [ ] **并发场景** - 如适用
- [ ] **资源清理** - 文件、连接等

## 错误处理

### testgen 生成不完整

指定更具体的 focus areas：
```
Use testgen to generate tests focusing specifically on:
- Input validation for [参数名]
- Error handling when [场景]
```

### 测试无法运行

确保生成的测试：
- 导入正确
- Mock 设置正确
- 与项目测试框架一致
