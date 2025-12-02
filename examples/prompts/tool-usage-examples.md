# Zen MCP 工具使用范例

本文档提供各种工具的使用提示和最佳实践。

---

## ThinkDeep - 深度思考

### 基础用法
```
Use thinkdeep to analyze [问题描述].
```

### 指定模型（推荐）
```
Use thinkdeep with model cli:kimi to analyze [项目/问题].

CRITICAL INSTRUCTIONS:
1. Every step must include model="cli:kimi" parameter
2. **NEVER** report confidence as 'certain'. The maximum allowed confidence is 'almost_certain'.
3. Even if you are 100% sure, you MUST set confidence to 'very_high' or 'almost_certain' in the final step.
4. I explicitly REQUIRE the "Expert Analysis" phase to run. Do not skip it.
5. File paths must use full absolute paths (e.g., C:\Users\...\server.py)
6. Set next_step_required=false for the final step
7. Please reply in Chinese.
```

### 使用场景
- 复杂架构决策分析
- 技术方案评估
- 深度代码理解

---

## Chat - 快速对话

### 基础用法
```
Use chat with gemini-2.5-flash to explain [概念].
```

### 多模型对比
```
Use chat with gpt-4o to explain [概念], then compare with gemini-pro's perspective.
```

---

## Debug - 问题调试

### 基础用法
```
Use debug to investigate [错误描述] in [文件路径].
```

### 带上下文调试
```
Use debug with model o3 to analyze this error:
[粘贴错误信息]

Context: The error occurs when [场景描述].
```

---

## CodeReview - 代码审查

### 基础用法
```
Use codereview to review [文件或目录路径].
```

### 安全聚焦审查
```
Use codereview with security focus to audit [代码路径].
Focus on: authentication, input validation, SQL injection, XSS.
```

---

## Consensus - 多模型共识

### 基础用法
```
Use consensus with gemini-pro and gpt-4o to decide: [决策问题]?
```

### 技术决策
```
Use consensus with gemini-pro, o3, and claude to evaluate:
Should we use [技术A] or [技术B] for [场景]?
Consider: performance, maintainability, team expertise.
```

---

## Planner - 任务规划

### 基础用法
```
Use planner to create implementation plan for [功能描述].
```

### 详细规划
```
Use planner to break down this task:
[任务描述]

Requirements:
- [需求1]
- [需求2]

Constraints:
- [约束条件]
```

---

## Clink - CLI 桥接

### 基础用法
```
Use clink with gemini to [任务描述].
```

### 子代理模式
```
Use clink with codex as codereviewer to audit [模块] for security issues.
```

### 角色指定
```
Use clink with kimi as planner to design the architecture for [项目].
```

---

## 组合使用技巧

### 代码审查 + 规划 + 实施
```
1. Use codereview to review [代码路径]
2. Continue with planner to create fix plan based on the review
3. Implement the fixes, then use precommit to validate
```

### 多模型协作调试
```
1. Use debug with gemini to identify the issue
2. Use consensus with o3 and gemini to validate the root cause
3. Use chat with gpt-4o to generate the fix
```

---

## 最佳实践

1. **指定模型**：明确指定模型可获得更一致的结果
2. **提供上下文**：详细描述问题背景和期望
3. **使用绝对路径**：文件路径使用完整绝对路径
4. **分步执行**：复杂任务分解为多步骤
5. **中文回复**：需要中文时在末尾添加 "Please reply in Chinese."
