---
name: full-feature-cycle
description: Complete feature development cycle with planning, code review, and pre-commit validation. Use when implementing new features, refactoring tasks, or any development work requiring systematic quality assurance.
---

# Full Feature Cycle

完整功能开发周期：规划 → 实现 → 审查 → 验证。

## 工具组合

```
planner → [implement] → codereview → precommit
```

## Instructions

### 完整功能开发流程

1. **创建实施计划**
```
Use planner to break down this feature into implementation steps.
Consider: dependencies, risks, testing strategy.
```

2. **实现**（手动执行）

3. **代码审查**
```
Use codereview with model gemini-2.5-pro to review the implementation.
Focus on: correctness, edge cases, code quality.
```

4. **预提交验证**
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

Step 3: Use codereview with model gemini-2.5-pro to review the implementation.

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

Step 3: Use testgen with model gemini-2.5-pro to generate tests for [实现的文件].

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
