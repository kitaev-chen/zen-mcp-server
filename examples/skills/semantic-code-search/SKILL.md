---
name: semantic-code-search
description: Search code semantically using natural language. Automatically checks if index exists - only indexes if needed. Use when you need to find code by meaning rather than exact text matching.
---

# Semantic Code Search

用自然语言搜索代码库，通过语义理解找到相关代码。

## 使用策略

**智能流程（推荐）**：
1. **先尝试 `search_code`** - 如果索引存在，直接返回结果
2. 如果返回"没有索引"错误，再调用 `index_code`
3. 索引完成后，再次调用 `search_code`

**不要**：
- ❌ 总是先调用 `index_code`（可能已存在索引）
- ❌ 使用 `force: true` 除非确实需要重建索引（会导致超时）
- ❌ 索引整个项目根目录（应该索引核心代码目录）

## Instructions

### 步骤 1：尝试搜索（推荐先做）

```
Use search_code with query="[自然语言搜索词]" and limit=10
```

### 步骤 2：如果索引不存在

如果 search_code 返回"没有索引"错误，再执行：

```
Use index_code with path="[核心代码目录]" and extensions=[".py", ".ts", ".js"]
```

**⚠️ 重要提示**：
- 不要使用 `force: true` 除非确实需要重建索引（会导致超时）
- 不要索引整个项目根目录，只索引核心代码目录
- 默认 `force: false` 会增量索引，只处理新/修改的文件

## 路径选择建议

**推荐索引核心代码目录**：
```
Use index_code with path="tools" and extensions=[".py"]
Use index_code with path="providers" and extensions=[".py"]
Use index_code with path="utils" and extensions=[".py"]
```

**避免索引**：
- ❌ 整个项目根目录（包含测试、文档、临时文件）
- ❌ `tests/`, `simulator_tests/`（除非需要搜索测试代码）
- ❌ `node_modules/`, `build/`, `dist/`（构建产物）

## 错误处理

### 如果 index_code 超时

1. **检查索引是否已存在**：
   ```
   Use search_code with query="test" and limit=1
   ```
   如果返回结果，说明索引已存在，直接使用即可

2. **如果确实需要索引，使用更小的路径**：
   ```
   Use index_code with path="utils" and extensions=[".py"]
   ```

3. **分批索引**：
   ```
   Use index_code with path="tools" and extensions=[".py"]
   Use index_code with path="providers" and extensions=[".py"]
   ```

## 增量索引

`index_code` 默认只索引新文件或修改过的文件（增量索引）。

- ✅ **默认行为**：`force: false` - 只索引新/修改的文件（快速）
- ⚠️ **强制重建**：`force: true` - 重新索引所有文件（慢，可能超时）

**建议**：除非索引损坏，否则不要使用 `force: true`

## Examples

### 示例 1：直接搜索（推荐）

```
Use search_code with query="database connection handling" and limit=10
```

### 示例 2：需要索引时

```
# 先尝试搜索
Use search_code with query="authentication logic"

# 如果返回"没有索引"，再索引核心目录
Use index_code with path="tools" and extensions=[".py"]
Use index_code with path="utils" and extensions=[".py"]

# 然后搜索
Use search_code with query="authentication logic" and limit=10
```

### 示例 3：搜索后深入分析

```
Use search_code with query="error handling"

Based on the results, use analyze to examine the specific file more deeply.
```

## Parameters

### search_code（优先使用）
| 参数 | 说明 | 默认值 |
|------|------|--------|
| query | 自然语言搜索词 | (必填) |
| limit | 返回结果数 | 10 |
| min_score | 最低相关度 | 0.3 |

### index_code（仅在需要时使用）
| 参数 | 说明 | 默认值 |
|------|------|--------|
| path | 要索引的目录 | "." |
| extensions | 文件扩展名 | [".py", ".js", ".ts"] |
| force | 强制重新索引 | false ⚠️ |
| chunk_size | 每块行数 | 50 |
