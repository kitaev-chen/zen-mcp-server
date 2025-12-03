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
