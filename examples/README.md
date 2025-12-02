# Zen MCP Examples

本文件夹包含配置示例和使用指南。

## 目录结构

```
examples/
├── README.md                    # 本文件
├── prompts/                     # 工具使用 prompt 示例
│   └── tool-usage-examples.md   # 各工具的使用范例
├── skills/                      # 高价值工具编排（Skills）
│   ├── README.md                # Skills 概览
│   ├── semantic-code-search.md  # 语义代码搜索
│   ├── deep-debug.md            # 深度问题调试
│   ├── secure-review.md         # 安全代码审查
│   ├── multi-model-review.md    # 多模型协作审查
│   ├── full-feature-cycle.md    # 完整功能开发周期
│   └── architecture-decision.md # 架构决策流程
├── claude_config_example.json   # Claude Desktop 通用配置
├── claude_config_macos.json     # macOS 配置示例
└── claude_config_wsl.json       # Windows WSL 配置示例
```

## 快速开始

### 1. 配置 Claude Desktop

运行以下命令获取适合你系统的配置：

```bash
./run-server.sh -c  # 或 .\run-server.ps1 -ConfigOnly
```

### 2. 使用 Skills

浏览 `skills/` 文件夹，选择适合你需求的工作流，复制 prompt 到 Claude Code 中使用。

**推荐 Skills**:
- **语义搜索**: 用自然语言搜索代码
- **深度调试**: 系统化定位和修复 bug
- **安全审查**: 全面的安全检查流程

### 3. 自定义 Prompt

参考 `prompts/tool-usage-examples.md` 了解各工具的使用方式，组合创建自己的工作流。

## 更多资源

- [完整文档](../docs/)
- [工具详解](../docs/tools/)
- [配置指南](../docs/configuration.md)
