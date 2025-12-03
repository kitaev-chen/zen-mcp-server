---
name: full-feature-cycle
description: Complete feature development cycle with planning, code review, and pre-commit validation. Use when implementing new features, refactoring tasks, or any development work requiring systematic quality assurance.
---

# Full Feature Cycle

完整功能开发周期：规划 → 实现 → 审查 → 验证。

## 模型配置

### 推荐模型（本 Skill 适用）

本 Skill 覆盖规划、审查、验证，需要**综合能力**：

| 别名 | 推荐原因 |
|------|---------|
| `pro` | ⭐ 首选，综合能力强 |
| `kimik` | ⭐ 通用任务 |
| `flash` | 快速任务 |
| `glm-4.6` | 通用任务 |

### 完整可选列表

**API 模型**：`pro`, `flash`, `glm-4.6`, `kimik`, `kimit`, `deepseekv`, `deepseekr`, `longcatt`, `minimax`

**CLI 模型**：`gcli`, `kcli`, `icli`, `qcli`, `vcli`, `ocli`, `ccli`

> 完整说明见 [README 模型选择指南](../README.md#模型选择指南)

⚠️ **性能提示**：本 Skill 串联多个工具，使用 CLI 模型可能需要 3-5 分钟。

### 如何指定模型

```
# 使用默认
Use planner to create...

# 指定 API 模型
Use planner with model pro to create...

# 指定 CLI 模型
Use planner with model gcli to create...
```

## 工具串联

```
planner → [implement] → codereview → precommit
```

## 前置条件

- **precommit 需要 git 环境**：确保在 git 仓库中运行

## Instructions

### 步骤 1：创建实施计划

```
Use planner to break down this feature into implementation steps.
Consider: dependencies, risks, testing strategy.
```

如果用户指定了模型：
```
Use planner with model [USER_MODEL] to break down this feature.
```

### 步骤 2：实现（手动执行）

### 步骤 3：代码审查

```
Use codereview to review the implementation.
Focus on: correctness, edge cases, code quality.
```

### 步骤 4：预提交验证

```
Use precommit to validate all changes before commit.
```

## Examples

### 示例 1: 新功能开发

```
I need to implement a new feature with full quality assurance.

Feature: [功能描述]
Requirements:
- [需求1]
- [需求2]
- [需求3]

Step 1: Use planner to create implementation plan.

Step 2: [After implementation, continue with step 3]

Step 3: Use codereview to review the implementation.

Step 4: Use precommit to validate all changes before commit.
```

### 示例 2: 重构任务

```
I need to refactor [模块名称] with quality assurance.

Current issues:
- [问题1]
- [问题2]

Goal: [重构目标]

Step 1: Use planner to create refactoring plan with:
- Clear phases
- Rollback strategy
- Testing approach

Step 2: [Execute refactoring]

Step 3: Use codereview to verify the refactoring quality.

Step 4: Use precommit for final validation.
```

### 示例 3: 带测试生成的完整周期

```
Step 1: Use planner for implementation plan.

Step 2: Implement the feature.

Step 3: Use testgen to generate tests for [实现的文件].

Step 4: Use codereview to review both implementation and tests.

Step 5: Use precommit for final validation.
```

## 流程检查点

### 规划阶段 ✓
- [ ] 需求明确
- [ ] 依赖识别
- [ ] 风险评估
- [ ] 测试策略

### 实现阶段 ✓
- [ ] 遵循计划
- [ ] 代码规范
- [ ] 边界处理
- [ ] 错误处理

### 审查阶段 ✓
- [ ] 功能正确性
- [ ] 代码质量
- [ ] 性能考量
- [ ] 安全性

### 验证阶段 ✓
- [ ] 测试通过
- [ ] 代码风格
- [ ] 无回归
- [ ] 文档更新

## 快捷版本

### 小功能快速周期
```
Use planner to plan: [简单功能描述]

[实现后]

Use precommit to validate the changes.
```

### 仅审查和验证
```
Use codereview to review [文件路径]
Then use precommit to validate before commit.
```
