---
name: semantic-code-search
description: Search code semantically using natural language. First indexes codebase with index_code MCP tool, then searches with search_code. Use when you need to find code by meaning rather than exact text matching.
---

# Semantic Code Search

用自然语言搜索代码库，通过语义理解找到相关代码。

## 工具组合

使用 Zen MCP 的两个工具串联：
```
index_code → search_code
```

## Instructions

### 首次使用（需要先索引）

1. 先索引代码库：
```
Use index_code with path="[项目根目录绝对路径]" and extensions=[".py", ".ts", ".js"]
```

2. 然后搜索：
```
Use search_code with query="[用自然语言描述你要找的代码]" and limit=10
```

### 后续使用（已有索引）

直接搜索：
```
Use search_code with query="[自然语言搜索词]" and limit=10
```

## Examples

### 好的搜索查询示例

- "authentication and login logic"
- "database connection handling"
- "error handling in API routes"
- "file upload processing"
- "user permission validation"

### 完整使用示例

```
I need to find the authentication logic in this project.

Use search_code with query="user authentication login password" and limit=5
```

### 索引后深入分析

```
Use search_code with query="error handling"

Based on the results, use analyze to examine the specific file more deeply.
```

## Parameters

### index_code
| 参数 | 说明 | 默认值 |
|------|------|--------|
| path | 要索引的目录 | "." |
| extensions | 文件扩展名 | [".py", ".js", ".ts", ...] |
| force | 强制重新索引 | false |
| chunk_size | 每块行数 | 50 |

### search_code
| 参数 | 说明 | 默认值 |
|------|------|--------|
| query | 自然语言搜索词 | (必填) |
| limit | 返回结果数 | 10 |
| min_score | 最低相关度 | 0.3 |
