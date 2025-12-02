---
name: architecture-decision
description: Architecture decision workflow combining deep thinking, multi-model consensus, and implementation planning. Use when making major technical decisions, system design evaluations, or technology selection.
---

# Architecture Decision

架构决策流程：深度思考 + 多模型共识 + 实施规划。

## 工具组合

```
thinkdeep + consensus + planner
```

## Instructions

### 完整架构决策流程

1. **深度分析**
```
Use thinkdeep with model o3 to analyze this decision thoroughly:
- Evaluate all options
- Consider trade-offs
- Assess risks and benefits
- Identify hidden assumptions
```

2. **多模型共识**
```
Use consensus with gemini-2.5-pro and gpt-4o to validate:
- Do you agree with the analysis?
- Any blind spots?
- What's your recommendation?
```

3. **实施路线图**
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

Step 1: Use thinkdeep with model o3 to analyze this decision thoroughly.

Step 2: Use consensus with gemini-2.5-pro and gpt-4o to validate the analysis.

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

Step 1: Use thinkdeep with model gemini-2.5-pro to analyze both options.

Step 2: Use consensus with o3 and gpt-4o to validate and recommend.

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
Use thinkdeep with model gemini-2.5-flash to quickly evaluate:
[技术选项] for [场景] - pros, cons, recommendation.
```

### 快速共识
```
Use consensus with gemini-flash and gpt-4o-mini to decide:
[简单决策问题]
```
