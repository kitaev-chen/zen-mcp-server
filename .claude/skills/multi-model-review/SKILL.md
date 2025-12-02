---
name: multi-model-review
description: Multi-model collaborative review combining consensus, code review, and deep thinking. Use when reviewing important code changes, validating architectural decisions, or needing multiple AI perspectives on complex problems.
---

# Multi-Model Review

多模型协作审查：共识决策 + 代码审查 + 深度思考。

## 工具组合

```
consensus + codereview + thinkdeep
```

## Instructions

### 完整多模型审查流程

1. **多模型共识评估**
```
Use consensus with gemini-2.5-pro and o3 to evaluate:
- Is the overall approach correct?
- Are there better alternatives?
- What are the potential risks?
```

2. **详细代码审查**
```
Use codereview with model gemini-2.5-pro to perform thorough review.
Focus on: code quality, maintainability, edge cases, performance.
```

3. **深度分析关注点**
```
For any significant concerns, use thinkdeep with model o3 to analyze:
- Root cause of the concern
- Potential solutions
- Trade-offs of each solution
```

## Examples

### 示例 1: 重要代码变更审查

```
I need a thorough multi-model review of this code change.

Target: [代码文件或目录路径]
Context: [变更背景说明]

Step 1: Use consensus with gemini-2.5-pro and o3 to evaluate the approach.

Step 2: Use codereview with model gemini-2.5-pro for detailed review.

Step 3: For any significant concerns, use thinkdeep with model o3 to analyze deeply.

Please synthesize all findings into actionable recommendations.
```

### 示例 2: PR 审查

```
Step 1: Use codereview to review the PR changes at [路径]

Step 2: For any architectural concerns, use thinkdeep to analyze deeply.

Step 3: Use consensus with gemini-pro and o3 to decide:
- Should this PR be approved?
- What changes are required before merge?

Provide final recommendation with confidence level.
```

### 示例 3: 快速多模型验证

```
Use consensus with gemini-pro, o3, and gpt-4o to evaluate this code:

[粘贴代码或指定文件路径]

Questions:
1. Is this implementation correct?
2. Are there any bugs or edge cases?
3. How would you improve it?

Then use codereview for detailed findings.
```

## 模型选择建议

| 任务类型 | 推荐模型 | 原因 |
|---------|---------|------|
| 快速审查 | gemini-2.5-flash | 速度快，成本低 |
| 深度分析 | o3, gemini-2.5-pro | 强推理能力 |
| 创意方案 | gpt-4o | 多样化思路 |
| 安全审计 | o3 | 细致严谨 |
| 共识决策 | 混合 2-3 个 | 多角度验证 |

## 最佳实践

1. **选择互补模型**：不同模型有不同优势
2. **明确评判标准**：告诉模型关注什么
3. **权衡时间成本**：快速检查 vs 深度审查
4. **整合发现**：综合多模型意见形成结论
