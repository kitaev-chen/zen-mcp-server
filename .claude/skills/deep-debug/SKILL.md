---
name: deep-debug
description: Deep debugging workflow combining semantic search, systematic debugging, and fix planning. Use when investigating complex bugs, tracking down root causes, or planning fixes for difficult issues.
---

# Deep Debug

深度问题调试：语义搜索定位 → 系统化调试 → 修复规划。

## 工具组合

```
search_code → debug → planner
```

## Instructions

### 完整调试流程

1. **搜索相关代码**
```
Use search_code with query="[与错误相关的关键词]"
```

2. **系统化调试**
```
Based on the search results, use debug with model gemini-2.5-pro to investigate:
- The error: [错误描述]
- Suspected files: [从搜索结果中得到的文件]
- Context: [错误发生的场景]
```

3. **创建修复计划**
```
Based on the debug findings, use planner to create an implementation plan for the fix.
```

### 快速定位版（已知问题文件）

```
Use debug with model o3 to investigate this error:

Error: [错误信息]
File: [已知的问题文件路径]
Symptom: [错误表现]

After identifying the root cause, use planner to create the fix plan.
```

## Examples

### 示例 1: 完整调试

```
I need to debug a complex issue in this codebase.

Error: "Connection refused" when calling the API
Context: This happens intermittently under high load

Step 1: Use search_code with query="connection pool database retry"

Step 2: Use debug with model gemini-2.5-pro to investigate the connection handling based on search results.

Step 3: Use planner to create the fix plan based on findings.
```

### 示例 2: 多模型协作调试

```
Step 1: Use search_code with query="[问题关键词]"

Step 2: Use debug with model gemini-2.5-pro to analyze the issue.

Step 3: Use consensus with o3 and gemini-pro to validate:
Is the identified root cause correct? Are there other possibilities?

Step 4: Based on consensus, use planner to create the fix plan.
```

## 调试技巧

1. **提供完整错误信息**：包括堆栈跟踪
2. **描述复现步骤**：帮助定位问题
3. **指定怀疑范围**：缩小调查范围
4. **使用强推理模型**：复杂问题用 o3 或 gemini-2.5-pro
