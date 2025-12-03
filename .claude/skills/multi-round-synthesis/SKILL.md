---
name: multi-round-synthesis
description: Multi-round iterative synthesis workflow. Multiple models (CLI or API) provide perspectives, synthesize critically, iterate until convergence. Use for complex decisions, solution design, evaluation, optimization, or any task requiring high-confidence conclusions.
---

# Multi-Round Synthesis（多轮综合）

多轮迭代综合：多模型意见 → 综合评析 → 再次验证 → 收敛结论。

**适用场景**：
- 复杂决策制定
- 技术方案设计
- 系统评估与评分
- 优化建议生成
- 需要高置信度结论的任何问题

---

## 模型类型与工具选择

### CLI 模型

**使用 `clink` 工具**，`cli_name` 参数用 `cli_client` 值（不带 cli 前缀）：

| 用户说 | clink cli_name | 说明 |
|--------|----------------|------|
| `gcli` | `gemini` | Gemini CLI（首选，免费）|
| `kcli` | `kimi` | Kimi CLI（推理强）|
| `icli` | `iflow` | iFlow CLI |
| `qcli` | `qwen` | Qwen CLI |
| `vcli` | `vecli` | Doubao CLI |
| `ccli` | `claude` | Claude CLI |
| `ocli` | `codex` | Codex CLI |

**调用方式**：
```
Use clink with cli_name="gemini" and prompt="..."
Use clink with cli_name="kimi" and prompt="..."
Use clink with cli_name="iflow" and prompt="..."
```

### API 模型

**使用 `thinkdeep` 工具**，`model` 参数用模型名或别名：

| 别名 | 说明 |
|------|------|
| `pro` | Gemini 2.5 Pro |
| `flash` | Gemini 2.5 Flash |
| `glm` | GLM-4.6 |
| `deepseekr` | DeepSeek R1 |
| `deepseekv` | DeepSeek V3 |
| `kimit` | Kimi K2 Thinking |
| `kimik` | Kimi K2 |

**调用方式**：
```
Use thinkdeep with model="pro" and prompt="..."
Use thinkdeep with model="glm" and prompt="..."
```

### 混合调用（CLI + API）

**thinkdeep 也可调用 CLI 模型**，但需带 `cli:` 前缀或使用别名：

```
Use thinkdeep with model="cli:gemini" and prompt="..."  # 带前缀
Use thinkdeep with model="gemini cli" and prompt="..."  # 别名
Use thinkdeep with model="gcli" and prompt="..."        # 简短别名
```

**推荐**：CLI 模型优先用 `clink`，更直接高效。

---

## 工具选择规则

```
用户指定的每个模型:
  如果是 CLI 别名 (gcli, kcli, icli, qcli, vcli, ccli, ocli):
    → 使用 clink，cli_name 用对应的 cli_client 值
  否则 (pro, flash, glm, deepseekr, kimit 等):
    → 使用 thinkdeep，model 用模型名
```

---

## 状态图谱（每轮必须输出）

```
┌───────────────────────────────────────────────────────────────┐
│                 Multi-Round Synthesis - Round N                │
├───────────┬──────┬─────────┬──────────────────────────────────┤
│ 模型      │ 类型 │ 状态    │ 核心观点 / 态度                  │
├───────────┼──────┼─────────┼──────────────────────────────────┤
│ gcli      │ CLI  │ ✅ 成功 │ [观点摘要] / 支持                │
│ kcli      │ CLI  │ ✅ 成功 │ [观点摘要] / 中立                │
│ pro       │ API  │ ✅ 成功 │ [观点摘要] / 反对                │
├───────────┴──────┴─────────┴──────────────────────────────────┤
│ 共识点: [本轮共同观点]                                         │
│ 分歧点: [本轮不同观点]                                         │
│ 收敛度: 高 ✅ / 中 ⚠️ / 低 ❌                                   │
│ 态度变化: [与上轮对比，谁改变了立场]                            │
└───────────────────────────────────────────────────────────────┘
```

**状态符号**：
- `✅` 成功
- `❌` 失败/超时
- `⬆️` 态度变积极
- `⬇️` 态度变消极

---

## Instructions

### 第一轮：收集多方意见

**对于每个 CLI 模型**（gcli, kcli, icli 等）：
```
Use clink with cli_name="[cli_client值]" and prompt="
[完整的任务/问题描述]

请分析并回答：
1. 你的分析和建议
2. 关键考虑因素
3. 风险和顾虑
4. 你的态度（支持/中立/反对）
"
```

**对于每个 API 模型**（pro, glm, deepseekr 等）：
```
Use thinkdeep with model="[模型名]" and prompt="[同上]"
```

**输出 Round 1 状态图谱**。

### 综合评析

```
Use thinkdeep to synthesize:

1. 共识点 - 所有模型同意的
2. 分歧点 - 观点不同的地方
3. 批判性评估 - 每个独特观点的合理性
4. 初步结论
5. 待验证问题
```

### 第二轮：验证结论

**向每个模型展示初步结论**：
```
Use clink/thinkdeep with prompt="
初步结论：[综合后的结论]

请审查：
1. 是否同意？（态度是否改变？）
2. 遗漏了什么？
3. 推理有什么缺陷？
4. 改进建议？
"
```

**输出 Round 2 状态图谱，标注态度变化**。

### 收敛判断

| 收敛度 | 判断标准 | 行动 |
|--------|---------|------|
| 高 ✅ | 各模型基本一致 | 停止，输出最终结论 |
| 中 ⚠️ | 有分歧但不影响核心 | 记录分歧，停止 |
| 低 ❌ | 核心问题仍有分歧 | 继续第三轮（最多3轮）|

---

## Examples

### 示例 1：纯 CLI 模型

```
用户："use multi-round-synthesis with gcli, kcli, icli to evaluate database migration"

=== Round 1 ===

Step 1.1: Use clink with cli_name="gemini" and prompt="
Evaluate database migration from MySQL to PostgreSQL.
Context: 100K rows, 5 tables, 2 weeks timeline.
1. Analysis  2. Considerations  3. Risks  4. Stance
"

Step 1.2: Use clink with cli_name="kimi" and prompt="[同上]"
Step 1.3: Use clink with cli_name="iflow" and prompt="[同上]"

┌───────────────────────────────────────────────────────────────┐
│                 Multi-Round Synthesis - Round 1                │
├───────────┬──────┬─────────┬──────────────────────────────────┤
│ gcli      │ CLI  │ ✅ 成功 │ 支持迁移，建议分批 / 支持        │
│ kcli      │ CLI  │ ✅ 成功 │ 关注兼容性测试 / 中立            │
│ icli      │ CLI  │ ✅ 成功 │ 时间紧张，建议延期 / 反对        │
├───────────┴──────┴─────────┴──────────────────────────────────┤
│ 共识点: 迁移方向正确                                           │
│ 分歧点: 时间表评估                                             │
│ 收敛度: 中 ⚠️                                                  │
└───────────────────────────────────────────────────────────────┘

=== 综合评析 ===
Use thinkdeep to synthesize...

=== Round 2 ===
[验证初步结论...]

┌───────────────────────────────────────────────────────────────┐
│                 Multi-Round Synthesis - Round 2                │
├───────────┬──────┬─────────┬──────────────────────────────────┤
│ gcli      │ CLI  │ ✅ 成功 │ 同意分批方案 / 支持              │
│ kcli      │ CLI  │ ✅ 成功 │ 同意，补充测试建议 / 支持 ⬆️     │
│ icli      │ CLI  │ ✅ 成功 │ 接受分批，仍建议缓冲 / 中立 ⬆️   │
├───────────┴──────┴─────────┴──────────────────────────────────┤
│ 共识点: 同意分批迁移方案                                       │
│ 分歧点: 无重大分歧                                             │
│ 收敛度: 高 ✅                                                  │
│ 态度变化: kcli 中立→支持, icli 反对→中立                       │
└───────────────────────────────────────────────────────────────┘

=== 最终结论 ===
Use thinkdeep to finalize...
```

### 示例 2：混合模型（CLI + API）

```
用户："use gcli, kcli, pro to score this architecture"

=== Round 1 ===

# CLI 模型
Use clink with cli_name="gemini" and prompt="..."
Use clink with cli_name="kimi" and prompt="..."

# API 模型
Use thinkdeep with model="pro" and prompt="..."

┌───────────────────────────────────────────────────────────────┐
│                 Multi-Round Synthesis - Round 1                │
├───────────┬──────┬─────────┬──────────────────────────────────┤
│ gcli      │ CLI  │ ✅ 成功 │ 评分 8/10，扩展性好              │
│ kcli      │ CLI  │ ✅ 成功 │ 评分 7/10，复杂度高              │
│ pro       │ API  │ ✅ 成功 │ 评分 8/10，建议简化接口          │
├───────────┴──────┴─────────┴──────────────────────────────────┤
│ 共识点: 整体设计合理，7-8分                                    │
│ 分歧点: 复杂度评估                                             │
│ 收敛度: 高 ✅                                                  │
└───────────────────────────────────────────────────────────────┘
```

### 示例 3：纯 API 模型

```
用户："use pro, glm, deepseekr to develop optimization plan"

=== Round 1 ===

Use thinkdeep with model="pro" and prompt="..."
Use thinkdeep with model="glm" and prompt="..."
Use thinkdeep with model="deepseekr" and prompt="..."
```

### 示例 4：处理失败

```
┌───────────────────────────────────────────────────────────────┐
│                 Multi-Round Synthesis - Round 1                │
├───────────┬──────┬─────────┬──────────────────────────────────┤
│ gcli      │ CLI  │ ✅ 成功 │ [观点]                           │
│ kcli      │ CLI  │ ❌ 超时 │ 跳过，继续其他模型               │
│ pro       │ API  │ ✅ 成功 │ [观点]                           │
├───────────┴──────┴─────────┴──────────────────────────────────┤
│ 说明: kcli 超时，基于 2 个成功模型继续                         │
└───────────────────────────────────────────────────────────────┘
```

---

## 错误处理

### CLI 超时
CLI 模型较慢（30-60秒），超时时：
- 记录失败
- 继续其他模型
- 在状态图谱中标注

### API 失败
API 模型可能因配额、网络失败：
- 记录失败原因
- 继续其他模型

### 不收敛
3 轮后仍分歧：
```
Use thinkdeep to document:
1. Areas of consensus
2. Areas of persistent disagreement
3. Recommendation despite disagreement, with caveats
```

---

## 最佳实践

1. **问题要具体** - 越具体越容易收敛
2. **2-3 轮足够** - 避免无限迭代
3. **记录态度变化** - 追踪谁改变了立场
4. **CLI 优先** - 免费且质量足够
5. **混合使用** - CLI 收集 + API 综合效果最好
6. **批判性综合** - 不是简单合并，而是评估每个观点

---

## 与其他 Skills 的区别

| Skill | 特点 | 适用 |
|-------|------|------|
| **multi-round-synthesis** | 多轮迭代，收敛验证，CLI+API 混合 | 复杂决策，需要高置信度 |
| multi-model-review | 一次性多模型审查 | 代码审查，快速验证 |
| architecture-decision | 深度分析 + 单轮共识 | 架构设计，技术选型 |
