---
name: multi-model-review
description: Multi-model collaborative review combining consensus, code review, and deep thinking. Use when reviewing important code changes, validating architectural decisions, or needing multiple AI perspectives on complex problems.
---

# Multi-Model Review

多模型协作审查：共识决策 + 代码审查 + 深度思考。

## 模型配置

### 推荐模型（本 Skill 适用）

本 Skill 需要**多个模型协作**，推荐选择不同特点的模型组合：

| 别名 | 推荐原因 |
|------|---------|
| `pro` | ⭐ 首选，深度分析 |
| `kimik` | ⭐ 与 pro 互补 |
| `deepseekv` | ⭐ 与 pro 互补 |
| `flash` | 快速审查 |
| `kimit` | 推理模式 |

**推荐 consensus 组合**：
- `pro` + `kimik` （推荐）
- `pro` + `deepseekv`
- `flash` + `kimik`

### 完整可选列表

**API 模型**：`pro`, `flash`, `glm-4.6`, `kimik`, `kimit`, `deepseekv`, `deepseekr`, `longcatt`, `minimax`

**CLI 模型**：`gcli`, `kcli`, `icli`, `qcli`, `vcli`, `ocli`, `ccli`

> 完整说明见 [README 模型选择指南](../README.md#模型选择指南)

⚠️ **性能提示**：本 Skill 调用多个模型，使用 CLI 模型可能需要 5-10 分钟。

### 如何指定模型

```
# consensus 需要多个模型
Use consensus with pro and kimik to evaluate...

# 其他工具
Use codereview with model pro to review...
```

## 工具串联

```
consensus + codereview + thinkdeep
```

## Instructions

### 步骤 1：多模型共识评估

```
Use consensus with [MODEL1] and [MODEL2] to evaluate:
- Is the overall approach correct?
- Are there better alternatives?
- What are the potential risks?
```

**推荐模型组合**：
- `pro` + `kimik`
- `pro` + `deepseekv`
- `flash` + `kimik`

### 步骤 2：详细代码审查

```
Use codereview to perform thorough review.
Focus on: code quality, maintainability, edge cases, performance.
```

如果用户指定了模型：
```
Use codereview with model [USER_MODEL] to perform thorough review.
```

### 步骤 3：深度分析关注点

```
For any significant concerns, use thinkdeep to analyze:
- Root cause of the concern
- Potential solutions
- Trade-offs of each solution
```

## Examples

### 示例 1：使用默认模型

```
I need a thorough multi-model review of this code change.

Target: [代码文件或目录路径]
Context: [变更背景说明]

Step 1: Use consensus with pro and kimik to evaluate the approach.

Step 2: Use codereview for detailed review.

Step 3: For any significant concerns, use thinkdeep to analyze deeply.

Please synthesize all findings into actionable recommendations.
```

### 示例 2：用户指定模型

```
用户："用 pro 和 deepseekv 做多模型审查"

Step 1: Use consensus with pro and deepseekv to evaluate the approach.

Step 2: Use codereview with model pro for detailed review.

Step 3: Use thinkdeep with model pro to analyze concerns.
```

### 示例 3：PR 审查

```
Step 1: Use codereview to review the PR changes at [路径]

Step 2: For any architectural concerns, use thinkdeep to analyze deeply.

Step 3: Use consensus with pro and kimik to decide:
- Should this PR be approved?
- What changes are required before merge?

Provide final recommendation with confidence level.
```

## 错误处理

### 模型不可用

将模型替换为你配置的模型，确保 consensus 至少有 2 个可用模型。

### 工具超时

- 减少代码审查范围
- 使用更快的模型（如 `flash`）

## 模型选择建议

| 任务类型 | 推荐模型 | 原因 |
|---------|---------|------|
| 快速审查 | `flash` | 速度快，成本低 |
| 深度分析 | `pro`, `kimit` | 强推理能力 |
| 共识决策 | 混合 2-3 个 | 多角度验证 |

## 最佳实践

1. **选择互补模型**：不同模型有不同优势
2. **明确评判标准**：告诉模型关注什么
3. **权衡时间成本**：快速检查 vs 深度审查
4. **整合发现**：综合多模型意见形成结论
