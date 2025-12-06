---
name: multi-round-synthesis
description: Multi-round iterative synthesis workflow using batch_query for parallel model execution. Multiple models provide perspectives simultaneously, synthesize critically, iterate until convergence.
---

# Multi-Round Synthesis（多轮综合）

多轮迭代综合：**batch_query 并行调用多模型** → 综合评析 → 再次验证 → 收敛结论。

---

## ⛔ 强制执行协议 - MANDATORY EXECUTION PROTOCOL

### 🔴 严格禁止事项

1. **禁止在 Round 1 和 Round 2 使用 `clink`、`thinkdeep` 或 `chat` 逐个调用模型**
   - ❌ 禁止：`clink with cli_name="gemini"` 然后 `clink with cli_name="kimi"` 然后 `clink with cli_name="qwen"` 
   - ❌ 禁止：`thinkdeep with model="pro"` 然后 `thinkdeep with model="glm"` 
   - ❌ 禁止：`chat with model="pro"` 然后 `chat with model="glm"` 
   - ✅ **必须**：使用 `batch_query with models=["gcli", "kcli", "glm", "qwen3c"]` **一次性并行调用所有模型**

2. **禁止手动循环调用**
   - ❌ 禁止：用 for 循环或多次工具调用来实现"批量"
   - ✅ **必须**：所有模型在一个 `batch_query` 调用中

3. **禁止在 STEP 3 使用 `thinkdeep`**
   - ❌ 禁止：`thinkdeep` 的复杂 schema 不适合简单的观点综合
   - ✅ **必须**：使用方式 A（直接综合）或方式 B（`chat` 工具）

4. **禁止跳过 Round 2**
   - ❌ 禁止：只做 Round 1 就给出最终结论
   - ✅ **必须**：完成 Round 1 → 综合 → Round 2 → 最终结论的完整流程

### 🟢 必须执行事项

1. **STEP 1 必须使用 `batch_query` 并行调用所有模型**
   ```json
   Use batch_query with:
   {
     "models": ["gcli", "kcli", "glm", "qwen3c"],
     "prompt": "..."
   }
   ```

2. **STEP 4 必须使用 `batch_query` 再次并行调用所有模型**
   ```json
   Use batch_query with:
   {
     "models": ["gcli", "kcli", "glm", "qwen3c"],  // 与 Round 1 相同
     "prompt": "请审查以下初步结论：..."
   }
   ```

3. **必须输出状态图谱**
   - STEP 2: Round 1 状态图谱
   - STEP 5: Round 2 状态图谱（含态度变化）

4. **必须完成完整流程**
   - Round 1（batch_query）→ 状态图谱 → 综合 → Round 2（batch_query）→ 状态图谱 → 最终结论

### ⚠️ 违反后果

**如果违反以上规则，将导致：**
- ❌ 串行执行（失去并行优势，总耗时 = 所有模型耗时累加）
- ❌ 性能严重下降（4 个模型串行可能需要 10+ 分钟，并行只需 2-3 分钟）
- ❌ 无法正确生成状态图谱和收敛判断

---

## ⚙️ 核心工具：batch_query

**本 Skill 的核心是 `batch_query` 工具，它实现真正的并行执行。**

batch_query 的优势：
- ✅ **保证执行所有模型** - 循环在工具内部，无法跳过
- ✅ **真正并行** - 使用 `asyncio.gather` 并发执行
- ✅ **混合支持** - CLI 和 API 模型可以混用
- ✅ **统一输出** - 所有结果在一个响应中返回
- ✅ **自动路由** - CLI 模型自动调用 `clink`，API 模型自动调用 provider

### 支持的模型别名

| 类型 | 可用别名 |
|------|---------|
| **CLI** | `gcli`, `kcli`, `icli`, `qcli`, `ccli`, `ocli`, `vcli` |
| **API** | `pro`, `flash`, `glm`, `qwen3c`, `deepseekr`, `kimit`, `deepseekv`, `kimik`, `longcatt`, `gpt-5.1` |

> ⚠️ **重要**：上表中的 API 别名仅为示例。**实际可用模型请优先参考 `listmodels` 工具输出**。
> 当 `batch_query` 报 `No provider found for model 'xxx'` 时，应根据 `listmodels` 重新选择可用的 API 模型，而非降级到 CLI。

### CLI 别名映射（batch_query 内部自动处理）

| 用户别名 | 实际 CLI |
|----------|----------|
| gcli | gemini |
| kcli | kimi |
| icli | iflow |
| qcli | qwen |
| ccli | claude |
| ocli | codex |
| vcli | vecli |

---

## STEP 1: Round 1 - 使用 batch_query 并行调用 (REQUIRED)

**🔴 强制执行：必须使用 batch_query，禁止使用 thinkdeep、clink 或 chat！**

当用户说 `use multi-round-synthesis with gcli, kcli, glm, qwen3c` 时：

**✅ 正确做法：**
```json
Use batch_query with:
{
  "models": ["gcli", "kcli", "glm", "qwen3c"],
  "prompt": "请深入分析以下问题：\n\n[用户的具体问题/任务]\n\n请提供：\n1. 你的分析和建议\n2. 关键考虑因素\n3. 风险和顾虑\n4. 你的态度（支持/中立/反对）\n\n⚠️ 用 <SUMMARY>...</SUMMARY> 包裹核心结论（500字以内）"
}
```

**❌ 错误做法（会导致串行执行）：**
```
// ❌ 禁止：逐个调用 clink
Use clink with cli_name="gemini" ...
Use clink with cli_name="kimi" ...
Use clink with cli_name="qwen" ...

// ❌ 禁止：逐个调用 thinkdeep
Use thinkdeep with model="pro" ...
Use thinkdeep with model="glm" ...

// ❌ 禁止：逐个调用 chat
Use chat with model="pro" ...
Use chat with model="glm" ...
```

**batch_query 会**：
- 并行调用所有模型（同时执行）
- 总耗时 ≈ 最慢模型的时间（而非串行累加）
- 返回所有模型的结果，按完成顺序排列

### 观点提取规则

从 batch_query 返回的每个模型结果中：
1. **优先**：从 `<SUMMARY>` 标记提取核心观点
2. **无 SUMMARY**：从完整响应提取要点
3. **模型失败**：记录错误，继续处理其他模型

---

## STEP 2: 输出 Round 1 状态图谱 (REQUIRED)

**在收集完所有模型的 Round 1 响应后，必须立即输出以下格式的状态图谱：**

```
=== Round 1 状态图谱 ===
┌─────────────────────────────────────────────────────────────────────┐
│                   Multi-Round Synthesis - Round 1                    │
├───────────┬──────┬─────────┬────────────────────────────────────────┤
│ 模型      │ 类型 │ 状态    │ 核心观点 / 态度                        │
├───────────┼──────┼─────────┼────────────────────────────────────────┤
│ gcli      │ CLI  │ ✅/❌   │ [从响应中提取的1-2句核心观点]          │
│ kcli→icli │ CLI  │ ✅ 降级 │ [观点] (kcli不可用，降级到icli)        │
│ glm       │ API  │ ✅/❌   │ [观点]                                 │
│ qwen3c    │ API  │ ✅/❌   │ [观点]                                 │
├───────────┴──────┴─────────┴────────────────────────────────────────┤
│ 共识点: [所有模型同意的观点]                                         │
│ 分歧点: [模型之间的不同意见]                                         │
│ 收敛度: 高 ✅ / 中 ⚠️ / 低 ❌                                         │
└─────────────────────────────────────────────────────────────────────┘
```

**状态符号：** ✅ 成功 | ✅ 降级（模型切换成功）| ❌ 失败/超时

---

## STEP 3: 批判性综合 (REQUIRED)

**在输出 Round 1 状态图谱后，进行批判性综合：**

**方式 A（强烈推荐，默认使用）**：直接综合
基于收集到的所有响应，直接输出：
1. 共识点 - 所有模型都同意的观点
2. 分歧点 - 观点存在差异的地方
3. 批判性评估 - 每个独特观点的合理性和局限性
4. 初步结论 - 基于综合分析的初步建议
5. 待验证问题 - 需要在 Round 2 中验证的不确定性

**方式 B（仅在问题极其复杂时使用，不推荐）**：使用 `chat` 工具进行深度综合
```json
Use chat with:
{
  "model": "deepseekr",
  "prompt": "请批判性综合以下多个模型的观点：\n\n[Round 1 各模型观点摘要]\n\n请提供：\n1. 共识点\n2. 分歧点\n3. 批判性评估\n4. 初步结论\n5. 待验证问题"
}
```

**🔴 禁止在 STEP 3 使用 `thinkdeep`** - `thinkdeep` 的复杂 schema（step, step_number, total_steps, next_step_required, findings）不适合简单的观点综合任务。

**输出初步结论，但不得将其作为最终结论。**

---

## STEP 4: Round 2 - 使用 batch_query 验证初步结论 (REQUIRED)

**🔴 强制执行：必须使用 batch_query，禁止使用 thinkdeep、clink 或 chat！**

```json
Use batch_query with:
{
  "models": ["gcli", "kcli", "glm", "qwen3c"],
  "prompt": "请审查以下初步结论：\n\n[STEP 3 得出的初步结论]\n\n请回答：\n1. 你是否同意这个结论？\n2. 与你第一轮的观点相比，态度是否改变？\n3. 这个结论遗漏了什么重要内容？\n4. 推理过程有什么缺陷？\n5. 你的改进建议是什么？\n\n⚠️ 用 <SUMMARY>...</SUMMARY> 包裹核心观点"
}
```

**batch_query 会并行调用所有模型进行验证。**

---

## STEP 5: 输出 Round 2 状态图谱 (REQUIRED)

**在收集完所有模型的 Round 2 响应后，必须输出状态图谱并标注态度变化：**

```
=== Round 2 状态图谱 ===
┌───────────────────────────────────────────────────────────────┐
│                 Multi-Round Synthesis - Round 2                │
├───────────┬──────┬─────────┬──────────────────────────────────┤
│ 模型      │ 类型 │ 状态    │ 核心观点 / 态度变化              │
├───────────┼──────┼─────────┼──────────────────────────────────┤
│ gcli      │ CLI  │ ✅/❌   │ [观点] / 支持 (无变化)           │
│ kcli      │ CLI  │ ✅/❌   │ [观点] / 支持 ⬆️ (原:中立)       │
│ glm       │ API  │ ✅/❌   │ [观点] / 中立 ⬆️ (原:反对)       │
│ qwen3c    │ API  │ ✅/❌   │ [观点] / 支持 (无变化)           │
├───────────┴──────┴─────────┴──────────────────────────────────┤
│ 共识点: [Round 2 后的共同观点]                                 │
│ 分歧点: [仍存在的分歧]                                         │
│ 收敛度: 高 ✅ / 中 ⚠️ / 低 ❌                                   │
│ 态度变化: [列出谁的态度从什么变成什么]                          │
└───────────────────────────────────────────────────────────────┘
```

---

## STEP 6: 收敛判断与最终结论 (REQUIRED)

### 收敛度判断：

| 收敛度 | 判断标准 | 行动 |
|--------|---------|------|
| 高 ✅ | 各模型基本一致，无重大分歧 | 进入最终综合 |
| 中 ⚠️ | 有分歧但不影响核心结论 | 记录分歧，进入最终综合 |
| 低 ❌ | 核心问题仍有重大分歧 | 继续 Round 3（最多 3 轮）|

### 最终综合：

**直接进行最终综合**（无需调用工具）：

基于 Round 1 和 Round 2 的所有模型观点，直接输出：

1. 吸收有效批评 - 整合 Round 2 中的有效反馈
2. 解决识别的缺口 - 填补初步结论遗漏的问题
3. 最终结论 - 高置信度的最终建议
4. 置信度评估 - 结论的可靠性程度
5. 剩余注意事项 - 尽管达成共识但仍需关注的点

---

## 完整执行流程检查清单

```
□ STEP 1: 使用 batch_query 执行 Round 1（所有模型并行调用）
  □ 确认：没有使用 thinkdeep、clink 或 chat 逐个调用
  □ 确认：所有模型在一个 batch_query 调用中
□ STEP 2: Round 1 状态图谱已输出
□ STEP 3: 批判性综合完成，初步结论已生成
  □ 确认：优先使用方式 A（直接综合）
  □ 确认：如果使用方式 B，使用 chat 而非 thinkdeep
□ STEP 4: 使用 batch_query 执行 Round 2（所有模型并行验证）
  □ 确认：没有使用 thinkdeep、clink 或 chat 逐个调用
□ STEP 5: Round 2 状态图谱已输出（含态度变化）
□ STEP 6: 收敛判断完成，最终结论已输出
```

---

## 常见错误和纠正

### ❌ 错误 1: 使用 clink 逐个调用 CLI 模型
```
❌ 错误：
Use clink with cli_name="gemini" ...
Use clink with cli_name="kimi" ...
Use clink with cli_name="qwen" ...
```

```
✅ 正确：
Use batch_query with models=["gcli", "kcli", "qcli"] ...
```

### ❌ 错误 2: 使用 thinkdeep 调用 API 模型
```
❌ 错误：
Use thinkdeep with model="pro" ...
Use thinkdeep with model="glm" ...
Use thinkdeep with model="qwen3c" ...
```

```
✅ 正确：
Use batch_query with models=["pro", "glm", "qwen3c"] ...
```

### ❌ 错误 3: 在 STEP 3 使用 thinkdeep
```
❌ 错误：
Use thinkdeep with model="deepseekr" to synthesize...
```

```
✅ 正确（方式 A）：
直接基于 Round 1 结果进行综合，无需调用工具

✅ 正确（方式 B，仅在必要时）：
Use chat with model="deepseekr" to synthesize...
```

### ❌ 错误 4: 模型失败后改用 thinkdeep 重试
```
❌ 错误：
batch_query 中 qwen3c 失败
→ 改用 thinkdeep with model="qwen3c" 重试
```

```
✅ 正确：
batch_query 中某个模型失败是正常的
→ 在状态图谱中标注 ❌
→ 继续使用其他成功的模型进行综合
→ Round 2 时 batch_query 会自动重试失败的模型
```

---

## 示例：完整执行流程

```
用户: "use multi-round-synthesis with gcli, kcli, glm, qwen3c to evaluate API error fix"

=== STEP 1: Round 1 - 使用 batch_query 并行调用 ===

Use batch_query with:
  models=["gcli", "kcli", "glm", "qwen3c"]
  prompt="请分析 API 错误处理方案..."

→ batch_query 并行执行所有模型（总耗时 ≈ 最慢模型）
→ 返回：
  [1/4] gcli (CLI, 126.2s) ✅ - 建议添加防御性检查
  [2/4] kcli (CLI, 45.3s) ✅ - 建议更全面的测试
  [3/4] glm (API, 8.1s) ✅ - 关注日志记录
  [4/4] qwen3c (API, 12.8s) ✅ - 推荐重构方案

=== STEP 2: Round 1 状态图谱 ===
[状态图谱输出]

=== STEP 3: 批判性综合 ===
→ 初步结论: 添加响应验证层 + WARNING 日志 + 集成测试

=== STEP 4: Round 2 - 使用 batch_query 验证 ===

Use batch_query with:
  models=["gcli", "kcli", "glm", "qwen3c"]
  prompt="请审查初步结论: 添加响应验证层..."

→ 返回所有模型的验证结果

=== STEP 5: Round 2 状态图谱 ===
[状态图谱输出]

=== STEP 6: 最终结论 ===
→ 最终方案输出
```

---

## 错误处理

### 模型不可用时（自动降级）

当收到 "not available" 错误时，按降级链自动切换：

```
API: pro → kimit → qwen3c → deepseekr → gpt-5.1 → flash → glm → kimik → deepseekv → longcatt → longcatc
CLI: gcli → kcli → icli → qcli → ccli → ocli → vcli
```

**处理流程**：
1. 模型返回 "not available" → 立即尝试下一个候选
2. 最多尝试 3 个候选模型
3. 成功后，Round 2 继续使用降级后的模型
4. 在状态图谱中记录：`原模型→实际模型`

### 模型调用失败时（非可用性问题）：
- 超时/网络错误：在状态图谱中标注 ❌
- 继续调用其他模型
- 基于成功的模型继续流程
- **不要**用 `thinkdeep` 或 `clink` 重试失败的模型，`batch_query` 会在 Round 2 自动重试

### 3 轮后仍不收敛：
- 记录持续存在的分歧点
- 输出"尽管存在分歧但仍推荐的方案"
- 明确标注置信度和注意事项
