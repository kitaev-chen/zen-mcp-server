---
name: architecture-decision
description: Architecture decision workflow combining deep thinking, multi-model consensus, and implementation planning. Use when making major technical decisions, system design evaluations, or technology selection.
---

# Architecture Decision

架构决策流程：深度思考 + 多模型共识 + 实施规划。

---

## ⛔ 执行要求 - EXECUTION REQUIREMENTS

### 🔴 禁止事项

1. **禁止跳过 thinkdeep 深度分析** - 架构决策必须有深度思考
2. **禁止跳过 consensus 验证** - 重大决策需要多模型验证
3. **禁止没有 planner 就给出实施方案** - 必须有结构化的实施计划

### 🟢 必须执行

1. **必须完成全部 3 个步骤**：thinkdeep → consensus → planner
2. **必须使用至少 2 个模型进行 consensus 验证**
3. **必须输出包含以下内容的决策文档**：
   - 推荐方案及理由
   - 风险评估和缓解措施
   - 分阶段实施计划
   - 回滚方案

---

## 模型配置

### 推荐模型（本 Skill 适用）

本 Skill 需要**深度推理和多模型协作**：

| 别名 | 推荐原因 |
|------|---------|
| `pro` | ⭐ 首选，深度分析 |
| `kimit` | ⭐ 推理模式 |
| `deepseekr` | ⭐ 推理模式 |
| `kimik` | 与 pro 互补 |
| `deepseekv` | 与 pro 互补 |

**推荐 consensus 组合**：
- `pro` + `kimik` （推荐）
- `pro` + `deepseekv`
- `kimit` + `deepseekr`

### 完整可选列表

**API 模型**：`pro`, `flash`, `glm-4.6`, `kimik`, `kimit`, `deepseekv`, `deepseekr`, `longcatt`, `minimax`

**CLI 模型**：`gcli`, `kcli`, `icli`, `qcli`, `vcli`, `ocli`, `ccli`

> 完整说明见 [README 模型选择指南](../README.md#模型选择指南)

⚠️ **性能提示**：本 Skill 调用多个模型，使用 CLI 模型可能需要 5-10 分钟。

### 如何指定模型

```
# 使用默认
Use thinkdeep to analyze...

# 指定 API 模型
Use thinkdeep with model pro to analyze...

# 指定 CLI 模型
Use thinkdeep with model gcli to analyze...
```

## 工具串联

```
thinkdeep + consensus + planner
```

## Instructions

### 步骤 1：深度分析

```
Use thinkdeep to analyze this decision thoroughly:
- Evaluate all options
- Consider trade-offs
- Assess risks and benefits
- Identify hidden assumptions
```

如果用户指定了模型：
```
Use thinkdeep with model [USER_MODEL] to analyze...
```

### 步骤 2：多模型共识

```
Use consensus with [MODEL1] and [MODEL2] to validate:
- Do you agree with the analysis?
- Any blind spots?
- What's your recommendation?
```

**推荐模型组合**：
- `pro` + `kimik`
- `pro` + `deepseekv`

### 步骤 3：实施路线图

```
Based on the consensus, use planner to create:
- Phased implementation plan
- Milestones and checkpoints
- Risk mitigation strategies
- Rollback procedures
```

## Examples

### 示例 1: 重大技术决策

```
I need to make an important architecture decision.

Decision: Should we migrate from monolith to microservices?

Context:
- Current state: [当前状态]
- Pain points: [痛点]
- Constraints: [约束条件]
- Success criteria: [成功标准]

Step 1: Use thinkdeep to analyze this decision thoroughly.

Step 2: Use consensus with pro and kimik to validate the analysis.

Step 3: Based on the consensus, use planner to create implementation roadmap.

Please provide a comprehensive decision document.
```

### 示例 2: 技术选型

```
I need to choose between [技术A] and [技术B] for [用途].

Evaluation criteria:
- Performance: [要求]
- Scalability: [要求]
- Team expertise: [现状]
- Maintenance cost: [预算]
- Community support: [重要性]

Step 1: Use thinkdeep to analyze both options.

Step 2: Use consensus with pro and kimik to validate and recommend.

Step 3: Use planner to create adoption plan for the chosen option.
```

### 示例 3: 技术债务清理

```
We have accumulated technical debt in [区域].

Debt inventory:
- [债务1]: Impact [高/中/低]
- [债务2]: Impact [高/中/低]

Step 1: Use thinkdeep to analyze priority ranking and dependencies.

Step 2: Use consensus to validate priority.

Step 3: Use planner for phased cleanup plan.
```

## 决策框架

### 输入要求
- [ ] 清晰的决策问题
- [ ] 当前状态描述
- [ ] 约束条件
- [ ] 成功标准

### 分析维度
- [ ] 技术可行性
- [ ] 团队能力匹配
- [ ] 成本效益
- [ ] 风险评估
- [ ] 长期可维护性

### 输出内容
- [ ] 推荐方案
- [ ] 理由说明
- [ ] 风险缓解
- [ ] 实施路线图
- [ ] 回滚方案

## 快捷版本

### 快速技术评估
```
Use thinkdeep with model flash to quickly evaluate:
[技术选项] for [场景] - pros, cons, recommendation.
```

### 快速共识
```
Use consensus with flash and kimik to decide:
[简单决策问题]
```

---

## ⚡ 并行化优化（可选）

对于需要多模型验证的架构决策，可用 `batch_query` 并行获取意见：

```
# 并行获取多模型对架构方案的评估
Use batch_query with:
  models=["pro", "kimit", "deepseekr"]
  prompt="请评估以下架构决策：

[方案描述]

请分析：
1. 技术可行性
2. 潜在风险
3. 长期维护性
4. 你的态度（支持/中立/反对）及理由"

# 然后综合各模型意见，用 planner 制定实施计划
```

**优势**：并行执行，总耗时 ≈ 最慢模型时间

> ⚠️ **注意**：API 模型别名需与 `listmodels` 输出一致。
