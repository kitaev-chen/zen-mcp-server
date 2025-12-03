# Zen MCP Skills for Claude Code

本文件夹包含可直接安装到 Claude Code 的 **Agent Skills**，将多个 Zen MCP 工具串联成高效的业务工作流。

## 安装方式

### 方式 1：项目级安装（推荐团队使用）

将 skills 文件夹复制到项目的 `.claude/` 目录：

```bash
# 在你的项目根目录执行
mkdir -p .claude/skills
cp -r /path/to/zen-mcp-server/examples/skills/* .claude/skills/
```

团队成员 `git pull` 后自动获得这些 Skills。

### 方式 2：个人安装

复制到个人 Claude 目录（所有项目可用）：

```bash
cp -r /path/to/zen-mcp-server/examples/skills/* ~/.claude/skills/
```

### 方式 3：选择性安装

只安装需要的 Skill：

```bash
# 例如只安装 semantic-code-search
cp -r examples/skills/semantic-code-search ~/.claude/skills/
```

## 使用方式

安装后，在 Claude Code 中：

1. **查看可用 Skills**：
   ```
   What Skills are available?
   ```

2. **自动使用**：直接描述需求，Claude 会自动选择相关 Skill
   ```
   I need to find the authentication logic in this codebase
   ```

3. **明确指定**：
   ```
   Use the semantic-code-search skill to find database connection code
   ```

## 可用 Skills

| Skill | 描述 | 工具组合 |
|-------|------|---------|
| [semantic-code-search](./semantic-code-search/) | 语义代码搜索 | index_code → search_code |
| [deep-debug](./deep-debug/) | 深度问题调试 | search_code → debug → planner |
| [secure-review](./secure-review/) | 安全代码审查 | codereview → secaudit → precommit |
| [multi-model-review](./multi-model-review/) | 多模型协作审查 | consensus + codereview + thinkdeep |
| [full-feature-cycle](./full-feature-cycle/) | 完整开发周期 | planner → codereview → precommit |
| [architecture-decision](./architecture-decision/) | 架构决策流程 | thinkdeep + consensus + planner |
| [multi-round-synthesis](./multi-round-synthesis/) | 多轮综合 | clink/thinkdeep → thinkdeep (多轮收敛) |
| [test-generation](./test-generation/) | 测试用例生成 | testgen → codereview |

### Skills 区分度

| 场景 | 推荐 Skill |
|------|-----------|
| 搜索代码 | semantic-code-search |
| 调试问题 | deep-debug |
| 安全审查 | secure-review |
| 快速代码审查 | multi-model-review |
| 功能开发 | full-feature-cycle |
| 架构设计 | architecture-decision |
| 高置信度决策 | multi-round-synthesis（多轮综合） |
| 生成测试 | test-generation |

## Skill 文件结构

每个 Skill 遵循 Claude Code 的标准格式：

```
skill-name/
└── SKILL.md          # 必需：包含 YAML frontmatter 和说明
```

### SKILL.md 格式

```markdown
---
name: skill-name
description: Brief description. Use when...
---

# Skill Title

## Instructions
Step-by-step guidance.

## Examples
Concrete examples.
```

## 前置要求

- **Claude Code 1.0+**
- **Zen MCP Server 已配置** - Skills 会调用 Zen 的 MCP 工具

## 模型选择指南

### 可用 API 模型（推荐用于 Skills）

Skills 串联多个 tools，**推荐使用 API 模型**（速度快）：

| 别名 | 模型 | 适用场景 |
|------|------|---------|
| `pro` | gemini-2.5-pro | ⭐ 深度推理，1M 上下文 |
| `flash` | gemini-2.5-flash | ⭐ 快速任务 |
| `glm-4.6` | glm-4-plus | 通用任务 |
| `kimik` | kimi-k2 | 通用任务 |
| `kimit` | kimi-k2-thinking | ⭐ 推理任务 |
| `deepseekv` | deepseek-v3.2 | 通用任务 |
| `deepseekr` | deepseek-r1 | ⭐ 推理任务 |
| `longcatt` | longcat-thinking | 推理任务 |
| `minimax` | minimax | 通用任务 |

> ⭐ 标记为特别推荐

### 可用 CLI 模型（较慢，仅在需要时使用）

| 别名 | clink cli_name | thinkdeep model | 说明 |
|------|----------------|-----------------|------|
| `gcli` | `gemini` | `cli:gemini` | Gemini CLI |
| `kcli` | `kimi` | `cli:kimi` | Kimi CLI |
| `icli` | `iflow` | `cli:iflow` | iFlow CLI |
| `qcli` | `qwen` | `cli:qwen` | Qwen CLI |
| `vcli` | `vecli` | `cli:vecli` | Doubao CLI |
| `ocli` | `codex` | `cli:codex` | Codex CLI |
| `ccli` | `claude` | `cli:claude` | Claude CLI |

### 在 Skills 中指定模型

**方式 1：使用默认**
```
Use [tool] to [action]
```

**方式 2：统一模型**
```
Use debug with model pro to analyze...
Use planner with model pro to create...
```

**方式 3：混合模型（每步不同）**
```
Step 1: Use debug with model pro to analyze...       # pro 深度分析
Step 2: Use consensus with flash and kimik to...    # 两个模型投票
Step 3: Use planner with model flash to...          # flash 快速规划
```

**方式 4：CLI 模型**
```
Use [tool] with model gcli to [action]
```

### 场景推荐

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| Skills 串联多个 tools | API 模型 | 速度快，适合批量处理 |
| 深度推理 | `pro`, `kimit`, `deepseekr` | 强推理能力 |
| 快速响应 | `flash`, `glm-4.6` | 低延迟 |
| 多模型共识 | `pro` + `kimik` 或 `pro` + `deepseekv` | 多角度验证 |
| 需要 CLI 特性 | `gcli`, `kcli`, `icli` | 访问 CLI 特有功能 |

## 自定义 Skill

基于现有 Skill 创建自己的工作流：

```bash
mkdir -p .claude/skills/my-custom-skill
```

创建 `SKILL.md`：

```markdown
---
name: my-custom-skill
description: My custom workflow. Use when...
---

# My Custom Skill

## Instructions
1. Use [tool1] to [action1]
2. Use [tool2] to [action2]
3. Use [tool3] to [final_action]
```

## 更多资源

- [Claude Code Skills 官方文档](https://code.claude.com/docs/en/skills)
- [Zen MCP 工具文档](../../docs/tools/)
- [配置指南](../../docs/configuration.md)
