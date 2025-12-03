---
name: secure-review
description: Comprehensive security review workflow combining code review, security audit, and pre-commit validation. Use when reviewing security-sensitive code, before releases, or for compliance verification (OWASP Top 10).
---

# Secure Review

安全代码审查：代码审查（安全聚焦）→ 安全审计 → 预提交验证。

## 模型配置

### 推荐模型（本 Skill 适用）

本 Skill 串联 3 个工具，需要**细致的安全分析能力**：

| 别名 | 推荐原因 |
|------|---------|
| `pro` | ⭐ 首选，深度安全分析 |
| `kimit` | ⭐ 推理模式，细致严谨 |
| `deepseekr` | ⭐ 推理模式 |
| `flash` | 快速检查 |

### 完整可选列表

**API 模型**：`pro`, `flash`, `glm-4.6`, `kimik`, `kimit`, `deepseekv`, `deepseekr`, `longcatt`, `minimax`

**CLI 模型**：`gcli`, `kcli`, `icli`, `qcli`, `vcli`, `ocli`, `ccli`

> 完整说明见 [README 模型选择指南](../README.md#模型选择指南)

⚠️ **性能提示**：本 Skill 串联 3 个工具，使用 CLI 模型可能需要 3-5 分钟。

### 如何指定模型

```
# 使用默认
Use codereview to review...

# 指定 API 模型
Use codereview with model pro to review...

# 指定 CLI 模型
Use codereview with model gcli to review...
```

## 工具串联

```
codereview (security focus) → secaudit → precommit
```

## 前置条件

- **precommit 需要 git 环境**：确保在 git 仓库中运行

## Instructions

### 步骤 1：安全聚焦的代码审查

```
Use codereview to review [路径] with security focus.
Focus areas:
- Authentication & authorization
- Input validation
- SQL injection / XSS
- Sensitive data handling
- Error handling (info leakage)
```

如果用户指定了模型：
```
Use codereview with model [USER_MODEL] to review [路径] with security focus.
```

### 步骤 2：OWASP 安全审计

```
Use secaudit to perform comprehensive security audit.
Compliance: OWASP Top 10
```

### 步骤 3：预提交验证

```
Use precommit to ensure all security issues are addressed before commit.
```

## Examples

### 示例 1：使用默认模型

```
I need a comprehensive security review of this codebase before release.

Target: src/api/

Step 1: Use codereview to review src/api/ with security focus.

Step 2: Use secaudit to perform OWASP Top 10 audit.

Step 3: Use precommit to validate all changes.

Please report all findings with severity levels (critical/high/medium/low).
```

### 示例 2：用户指定模型

```
用户："用 pro 模型做安全审查"

Step 1: Use codereview with model pro to review src/api/ with security focus.

Step 2: Use secaudit with model pro to perform OWASP Top 10 audit.

Step 3: Use precommit to validate all changes.
```

### 示例 3：快速安全检查

```
Use secaudit to audit [目标路径] for security vulnerabilities.

Focus on OWASP Top 10 and common vulnerability patterns.

Then summarize critical and high severity issues.
```

## 错误处理

### precommit 失败

确保在 git 仓库中运行，且有待提交的更改。

### 模型不可用

将 `model [模型]` 替换为你配置的模型。

## 安全检查清单 (OWASP Top 10)

审查完成后，确保覆盖以下方面：

- [ ] **A01: Broken Access Control** - 权限验证
- [ ] **A02: Cryptographic Failures** - 加密实现
- [ ] **A03: Injection** - SQL/NoSQL/OS 注入
- [ ] **A04: Insecure Design** - 设计缺陷
- [ ] **A05: Security Misconfiguration** - 配置问题
- [ ] **A06: Vulnerable Components** - 依赖漏洞
- [ ] **A07: Authentication Failures** - 认证缺陷
- [ ] **A08: Data Integrity Failures** - 数据完整性
- [ ] **A09: Logging Failures** - 日志监控
- [ ] **A10: SSRF** - 服务端请求伪造
