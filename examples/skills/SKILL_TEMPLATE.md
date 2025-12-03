# Skill 模板

创建新 Skill 时，使用此模板作为参考。

---

```markdown
---
name: [skill-name]
description: [简短描述]. Use when [使用场景].
---

# [Skill Title]

[一句话描述]

## 模型配置

### 推荐模型（本 Skill 适用）

本 Skill 串联 N 个工具，需要**[根据 Skill 特点填写]**：

| 别名 | 推荐原因 |
|------|---------|
| `pro` | ⭐ 首选，[原因] |
| `[其他推荐]` | ⭐ [原因] |
| `flash` | 快速任务 |

### 完整可选列表

**API 模型**：`pro`, `flash`, `glm-4.6`, `kimik`, `kimit`, `deepseekv`, `deepseekr`, `longcatt`, `minimax`

**CLI 模型**：`gcli`, `kcli`, `icli`, `qcli`, `vcli`, `ocli`, `ccli`

> 完整说明见 [README 模型选择指南](../README.md#模型选择指南)

⚠️ **性能提示**：本 Skill 串联 N 个工具，使用 CLI 模型可能需要 3-5 分钟。

### 如何指定模型

```
# 使用默认
Use [tool] to [action]

# 指定 API 模型
Use [tool] with model pro to [action]

# 指定 CLI 模型
Use [tool] with model gcli to [action]
```

## 工具串联

```
[Tool1] → [Tool2] → [Tool3]
```

## Instructions

### 步骤 1：[步骤名称]

```
Use [tool1] to [action]
```

如果用户指定了模型，传递该参数：
```
Use [tool1] with model [USER_MODEL] to [action]
```

### 步骤 2：[步骤名称]

```
Use [tool2] to [action]
```

## Examples

### 示例 1：使用默认模型

```
Use [tool1] to [action1]
Use [tool2] to [action2]
```

### 示例 2：用户指定模型

```
用户："用 pro 模型审查代码"

Use [tool1] with model pro to [action1]
Use [tool2] with model pro to [action2]
```

### 示例 3：使用 CLI 模型

```
Use [tool1] with model gcli to [action1]
```

## 错误处理

### 模型不可用

将 `model [模型]` 替换为你配置的模型。

### 工具超时

- 减少处理范围
- 使用更快的模型（如 `flash`）

## Parameters

### [tool1]
| 参数 | 说明 | 默认值 |
|------|------|--------|
| model | AI 模型 | auto |
| ... | ... | ... |
```

---

## 模板使用说明

1. 复制上面的模板到 `examples/skills/[skill-name]/SKILL.md`
2. 替换所有 `[placeholder]` 为实际内容
3. 根据实际工具调整"工具串联"和"Parameters"章节
4. 如果 Skill 依赖其他工具（如 `search_code` 依赖索引），添加前置条件说明
