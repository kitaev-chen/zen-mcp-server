---
name: secure-review
description: Comprehensive security review workflow combining code review, security audit, and pre-commit validation. Use when reviewing security-sensitive code, before releases, or for compliance verification (OWASP Top 10).
---

# Secure Review

安全代码审查：代码审查（安全聚焦）→ 安全审计 → 预提交验证。

## 工具组合

```
codereview (security focus) → secaudit → precommit
```

## Instructions

### 完整安全审查流程

1. **安全聚焦的代码审查**
```
Use codereview with model gemini-2.5-pro to review [路径] with security focus.
Focus areas:
- Authentication & authorization
- Input validation
- SQL injection / XSS
- Sensitive data handling
- Error handling (info leakage)
```

2. **OWASP 安全审计**
```
Use secaudit with model o3 to perform comprehensive security audit.
Compliance: OWASP Top 10
```

3. **预提交验证**
```
Use precommit to ensure all security issues are addressed before commit.
```

## Examples

### 示例 1: 完整安全审查

```
I need a comprehensive security review of this codebase before release.

Target: src/api/

Step 1: Use codereview with model gemini-2.5-pro to review src/api/ with security focus.

Step 2: Use secaudit with model o3 to perform OWASP Top 10 audit.

Step 3: Use precommit to validate all changes.

Please report all findings with severity levels (critical/high/medium/low).
```

### 示例 2: API 安全审查

```
Step 1: Use codereview to review [API 路径] focusing on:
- API authentication
- Rate limiting
- Input sanitization
- Response data filtering

Step 2: Use secaudit to check for injection vulnerabilities and access control issues.

Step 3: Use precommit to validate fixes.
```

### 示例 3: 快速安全检查

```
Use secaudit with model gemini-2.5-pro to audit [目标路径] for security vulnerabilities.

Focus on OWASP Top 10 and common vulnerability patterns.

Then summarize critical and high severity issues.
```

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
