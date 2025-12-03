---
name: deep-debug
description: Deep debugging workflow combining semantic search, systematic debugging, and fix planning. Use when investigating complex bugs, tracking down root causes, or planning fixes for difficult issues.
---

# Deep Debug

深度问题调试：语义搜索定位 → 系统化调试 → 修复规划。

## 模型配置

### 推荐模型（本 Skill 适用）

本 Skill 串联 3 个工具，需要**强推理能力**：

| 别名 | 推荐原因 |
|------|---------|
| `pro` | ⭐ 首选，深度推理 |
| `kimit` | ⭐ 推理模式 |
| `deepseekr` | ⭐ 推理模式 |
| `flash` | 快速调试 |

### 完整可选列表

**API 模型**：`pro`, `flash`, `glm-4.6`, `kimik`, `kimit`, `deepseekv`, `deepseekr`, `longcatt`, `minimax`

**CLI 模型**：`gcli`, `kcli`, `icli`, `qcli`, `vcli`, `ocli`, `ccli`

> 完整说明见 [README 模型选择指南](../README.md#模型选择指南)

⚠️ **性能提示**：本 Skill 串联 3 个工具，使用 CLI 模型可能需要 3-5 分钟。

### 如何指定模型

```
# 使用默认
Use debug to investigate...

# 指定 API 模型
Use debug with model pro to investigate...

# 指定 CLI 模型
Use debug with model gcli to investigate...
```

## 工具串联

```
search_code → debug → planner
```

## 前置条件

- **search_code 依赖索引**：如果返回"没有索引"，先运行 `index_code`
- 参考 `semantic-code-search` Skill 的索引说明

## Instructions

### 步骤 1：搜索相关代码

```
Use search_code with query="[与错误相关的关键词]"
```

**如果返回"没有索引"**：
```
Use index_code with path="[核心代码目录]" and extensions=[".py"]
```

### 步骤 2：系统化调试

```
Based on the search results, use debug to investigate:
- The error: [错误描述]
- Suspected files: [从搜索结果中得到的文件]
- Context: [错误发生的场景]
```

如果用户指定了模型：
```
Use debug with model [USER_MODEL] to investigate...
```

### 步骤 3：创建修复计划

```
Based on the debug findings, use planner to create an implementation plan for the fix.
```

### 快速定位版（已知问题文件）

```
Use debug to investigate this error:

Error: [错误信息]
File: [已知的问题文件路径]
Symptom: [错误表现]

After identifying the root cause, use planner to create the fix plan.
```

## Examples

### 示例 1：使用默认模型

```
I need to debug a complex issue in this codebase.

Error: "Connection refused" when calling the API
Context: This happens intermittently under high load

Step 1: Use search_code with query="connection pool database retry"

Step 2: Use debug to investigate the connection handling based on search results.

Step 3: Use planner to create the fix plan based on findings.
```

### 示例 2：用户指定模型

```
用户："用 pro 模型调试这个问题"

Step 1: Use search_code with query="connection pool"

Step 2: Use debug with model pro to investigate the issue.

Step 3: Use planner to create the fix plan.
```

### 示例 3：混合模型（每步不同模型）

```
用户："分析用 pro，规划用 flash"

Step 1: Use search_code with query="database connection" to locate code.
        # search_code 不需要模型

Step 2: Use debug with model pro to deeply analyze the connection issue.
        # pro 做深度分析

Step 3: Use planner with model flash to quickly create the fix plan.
        # flash 做快速规划
```

### 示例 4：带共识验证的混合模型

```
Step 1: Use search_code to find the buggy code.

Step 2: Use debug with model pro to analyze root cause.

Step 3: Use consensus with flash and kimik to validate the analysis.
        # 两个模型投票验证

Step 4: Use planner with model pro to create the fix plan.
```

### 示例 5：多模型协作调试

```
Step 1: Use search_code with query="[问题关键词]"

Step 2: Use debug to analyze the issue.

Step 3: Use consensus to validate:
Is the identified root cause correct? Are there other possibilities?

Step 4: Based on consensus, use planner to create the fix plan.
```

## 错误处理

### search_code 返回"没有索引"

先索引核心代码目录：
```
Use index_code with path="tools" and extensions=[".py"]
```

### 模型不可用

将 `model [模型]` 替换为你配置的模型。

## 调试技巧

1. **提供完整错误信息**：包括堆栈跟踪
2. **描述复现步骤**：帮助定位问题
3. **指定怀疑范围**：缩小调查范围
4. **复杂问题用推理模型**：`pro`, `kimit`, `deepseekr`
