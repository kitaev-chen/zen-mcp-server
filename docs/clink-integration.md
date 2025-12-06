# Clink CLI Integration Guide

Complete guide for integrating external AI CLIs with Zen MCP Server.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Supported CLIs](#supported-clis)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [CLI Details](#cli-details)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

Zen MCP Server's `clink` tool bridges MCP requests to external AI CLI tools. It supports multiple AI providers with automatic format detection, error recovery, and role-based prompts.

### Key Features

- **Multi-CLI Support**: gemini, codex, claude, iflow, kimi, qwen, vecli
- **Auto Parser Detection**: Automatically selects correct output parser
- **Error Recovery**: Graceful handling of non-zero exit codes
- **Role-Based Prompts**: Different system prompts for different roles
- **Configuration Layering**: Internal defaults + user overrides

---

## 🔌 Supported CLIs

| CLI | Provider | Parser | Prompt Mode | Output Format |
|-----|----------|--------|-------------|---------------|
| **gemini** | Google | gemini_json | stdin | JSON |
| **codex** | OpenAI | codex_jsonl | stdin | JSONL |
| **claude** | Anthropic | claude_json | stdin | JSON |
| **iflow** | Alibaba | iflow_plain | --prompt | Plain Text |
| **kimi** | Moonshot | kimi_plain | --command | Mixed (ThinkPart/TextPart) |
| **qwen** | Alibaba | gemini_json | --prompt | JSON |
| **vecli** | Bytedance | vecli_plain | stdin | Plain Text |

### Command Examples

```bash
# gemini - stdin, JSON output
echo "hello" | gemini -o json

# codex - stdin, JSONL output  
echo "hello" | codex exec

# claude - stdin, JSON output
echo "hello" | claude --print --output-format json

# iflow - --prompt arg, plain text
iflow --yolo --prompt "hello"

# kimi - --command arg, mixed format
kimi --yolo --print --command "hello"

# qwen - --prompt arg, JSON output
qwen --yolo --output-format json --prompt "hello"

# vecli - stdin, plain text
echo "hello" | vecli --yolo --model doubao-seed-code-preview-251028
```

---

## 🏗️ Architecture

### Component Layers

```
MCP Tool (tools/clink.py)
    ↓
Registry (clink/registry.py)
    ↓
Agent (clink/agents/*.py)
    ↓
Parser (clink/parsers/*.py)
```

### Data Flow

1. **MCP Request** → CLinkTool validates input
2. **Registry** → Resolves CLI configuration
3. **Agent** → Builds command, executes subprocess
4. **Parser** → Extracts content from stdout/stderr
5. **Response** → Returns formatted result to MCP

---

## ⚙️ Configuration

### Internal Defaults (`clink/constants.py`)

Core configuration for each CLI:

```python
INTERNAL_DEFAULTS = {
    "iflow": CLIInternalDefaults(
        parser="iflow_plain",
        additional_args=["--yolo"],
        default_role_prompt="systemprompts/clink/default.txt",
        runner="iflow",
    ),
    "kimi": CLIInternalDefaults(
        parser="kimi_plain",
        additional_args=["--yolo", "--print"],
        default_role_prompt="systemprompts/clink/default.txt",
        runner="kimi",
    ),
    "qwen": CLIInternalDefaults(
        parser="gemini_json",
        additional_args=["--output-format", "json", "--yolo"],
        default_role_prompt="systemprompts/clink/default.txt",
        runner="qwen",
    ),
    "vecli": CLIInternalDefaults(
        parser="vecli_plain",
        additional_args=["--yolo"],
        default_role_prompt="systemprompts/clink/default.txt",
        runner="vecli",
    ),
}
```

### User Configuration (`conf/cli_clients/*.json`)

Per-user overrides (model selection, features):

**iflow.json**
```json
{
  "name": "iflow",
  "command": "iflow",
  "additional_args": [],
  "env": {},
  "roles": { ... }
}
```

**kimi.json**
```json
{
  "name": "kimi",
  "command": "kimi",
  "additional_args": [],
  "env": {},
  "roles": { ... }
}
```

**qwen.json**
```json
{
  "name": "qwen",
  "command": "qwen",
  "additional_args": [],
  "env": {
    "DASHSCOPE_API_KEY": "your-key-here"
  },
  "roles": { ... }
}
```

**vecli.json**
```json
{
  "name": "vecli",
  "command": "vecli",
  "additional_args": ["--model", "doubao-seed-code-preview-251028"],
  "env": {},
  "roles": { ... }
}
```

### Parameter Merging

Final command = `constants.py` + `config.json` + `role_args`

**Example: kimi**
```bash
kimi --yolo --print --command "hello"
     └──────────────┬────────────────┘ └────┬────┘
        constants.py (internal)      config.json (user)
```

---

## 🔍 CLI Details

### iflow

**Provider**: Alibaba
**Parser**: `iflow_plain`  
**Prompt Mode**: `--prompt` argument  
**Output**: Plain text + `<Execution Info>` JSON block

```python
# Agent: IflowAgent
# - Overrides run() to pass prompt via --prompt
# - stdin = DEVNULL

# Parser: IflowPlainParser
# - Extracts content before <Execution Info>
# - Parses tokenUsage from execution info
```

### kimi

**Provider**: Moonshot  
**Parser**: `kimi_plain`  
**Prompt Mode**: `--command` argument  
**Output**: Mixed format (StepBegin, ThinkPart, TextPart)

```python
# Agent: KimiAgent
# - Overrides run() to pass prompt via --command
# - stdin = DEVNULL

# Parser: KimiPlainParser
# - Extracts TextPart content using regex
# - Captures ThinkPart for metadata
# - Fallback to plain text lines
```

### qwen

**Provider**: Alibaba (Qwen/Tongyi)  
**Parser**: `gemini_json` (reused)  
**Prompt Mode**: `--prompt` argument  
**Output**: JSON (same format as gemini)

```python
# Agent: QwenAgent
# - Overrides run() to pass prompt via --prompt
# - stdin = DEVNULL
# - Error recovery similar to Gemini

# Parser: GeminiJSONParser (reused)
# - Extracts response field
# - Parses stats.models for token usage
```

**Auth Note**: OAuth from `~/.qwen/settings.json` doesn't work in subprocess mode. Use API key in env:

```json
{
  "env": {
    "DASHSCOPE_API_KEY": "your-key"
  }
}
```

### vecli

**Provider**: Bytedance (Doubao)  
**Parser**: `vecli_plain`  
**Prompt Mode**: stdin (positional argument)  
**Output**: Plain text + optional `< SUMMARY >` block

```python
# Agent: VecliAgent
# - Uses base run() method (stdin)
# - No special overrides needed

# Parser: VecliPlainParser
# - Extracts main content
# - Identifies and extracts < SUMMARY > block
# - Handles stderr warnings about non-text parts
```

---

## 🧪 Testing

### Unit Tests

```bash
# Parser tests
pytest tests/test_clink_iflow_parser.py -v
pytest tests/test_clink_kimi_parser.py -v
pytest tests/test_clink_vecli_parser.py -v

# Agent tests
pytest tests/test_clink_iflow_agent.py -v
pytest tests/test_clink_kimi_agent.py -v
pytest tests/test_clink_qwen_agent.py -v
pytest tests/test_clink_vecli_agent.py -v

# Configuration tests
pytest tests/test_clink_cli_constants.py -v
```

### Integration Tests

```bash
# Test with real CLIs (requires CLIs installed)
pytest tests/integration/test_agent_real_cli.py -m integration -v

# Specific CLI
pytest tests/integration/ -m integration -k "kimi" -v
```

### Manual Testing

```bash
# Via MCP (in Claude Desktop)
zen - clink (cli_name: "cli:kimi", prompt: "hello")
zen - clink (cli_name: "cli:iflow", prompt: "what is 2+2")
zen - clink (cli_name: "cli:qwen", prompt: "explain python")
zen - clink (cli_name: "cli:vecli", prompt: "code review tips")
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "CLI not in supported list"

**Cause**: MCP Server hasn't reloaded configuration  
**Solution**: Fully restart Claude Desktop

```powershell
# Windows
Get-Process python | Where-Object {$_.CommandLine -like "*zen-mcp-server*"} | Stop-Process -Force
# Then restart Claude Desktop
```

#### 1a. qwen Windows libuv Crash

**Symptoms**: qwen returns valid JSON but exits with code 3221226505
**Error**: `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING), file c:\ws\deps\uv\src\win\async.c, line 76`
**Cause**: Known qwen CLI bug on Windows - libuv crash after successful execution
**Solution**: 
- ✅ **Automatic recovery** - Zen MCP detects valid JSON output and returns it despite crash
- ⚠️ Warning logged but doesn't affect functionality
- 🔧 If persistent, consider using WSL or Linux environment

#### 1b. iflow Windows Path Warning

**Symptoms**: iflow shows `The system cannot find the path specified` in stderr
**Cause**: iflow tries to load optional configuration files with Windows-incompatible paths
**Solution**:
- ✅ **Automatic filtering** - Warning is filtered from output
- ⚠️ Does not affect functionality, response is always returned correctly
- 📝 Confirmed working in production - all tests pass

#### 1c. vecli Function Call Warnings

**Symptoms**: vecli shows `there are non-text parts functionCall` in stderr
**Cause**: vecli uses tool calls internally and reports them in stderr
**Solution**:
- ✅ **Automatic detection** - Parser detects and marks function calls
- ⚠️ Does not affect functionality, full content is returned
- 💡 **Note**: vecli may take longer (30-200s) for complex analyses as it actively explores the project
- ✅ **Previous Windows signal error is resolved** - No longer occurs!

#### 2. "Failed to decode Gemini CLI JSON output"

**Cause**: Wrong parser for CLI output format  
**Check**: Verify parser in `constants.py` matches actual CLI output

```python
# iflow outputs plain text → use iflow_plain, not gemini_json
"iflow": CLIInternalDefaults(parser="iflow_plain", ...)
```

#### 3. "NoConsoleScreenBufferError" (kimi)

**Cause**: Old implementation used stdin, causing Windows console issues  
**Solution**: Fixed in latest version using `--command` argument

#### 4. qwen 401 API Key Error

**Cause**: OAuth doesn't work in subprocess mode  
**Solution**: Add API key to env in config:

```json
{
  "env": {
    "DASHSCOPE_API_KEY": "your-key"
  }
}
```

#### 5. Parser Returns Empty Content

**Symptoms**: CLI runs successfully but parser extracts nothing  
**Debug**:
1. Check actual CLI output: `kimi --print --command "test"`
2. Verify parser matches output format
3. Add logging to parser to see what's being extracted

---

## 📚 Implementation Checklist

When adding a new CLI:

- [ ] **Test CLI locally** - Verify command works and check output format
- [ ] **Create parser** - `clink/parsers/<cli>.py` matching output format
- [ ] **Register parser** - Add to `clink/parsers/__init__.py`
- [ ] **Add constants** - Add to `INTERNAL_DEFAULTS` in `clink/constants.py`
- [ ] **Create agent (if needed)** - Override `run()` if not using stdin
- [ ] **Create config** - `conf/cli_clients/<cli>.json`
- [ ] **Write parser tests** - `tests/test_clink_<cli>_parser.py`
- [ ] **Write agent tests** - `tests/test_clink_<cli>_agent.py`
- [ ] **Update constants test** - `tests/test_clink_cli_constants.py`
- [ ] **Document** - Update this guide

---

## 📊 Parser Summary

| Parser | Input Format | Key Extraction |
|--------|--------------|----------------|
| **gemini_json** | `{"response": "...", "stats": {...}}` | `response` field |
| **codex_jsonl** | `{"type":"stream","text":"..."}` per line | Concat `text` fields |
| **claude_json** | `{"content": [{"text": "..."}]}` | First text content block |
| **iflow_plain** | `Text\n<Execution Info>\n{...}` | Content before `<Execution Info>` |
| **kimi_plain** | `TextPart(text="...")` or plain text | Extract from TextPart or plain lines |
| **vecli_plain** | `Text\n< SUMMARY >\n...` | Main content + optional summary |

---

## 🚀 Quick Start

1. **Install CLIs**:
   ```bash
   # Example for kimi
   uv tool install kimi-cli
   ```

2. **Configure**:
   Edit `~/.zen/cli_clients/<cli>.json` with model preferences

3. **Test CLI locally**:
   ```bash
   kimi --yolo --print --command "hello"
   ```

4. **Restart MCP Server**:
   Fully quit and restart Claude Desktop

5. **Test via MCP**:
   ```
   zen - clink (cli_name: "cli:kimi", prompt: "hello")
   ```

---

## 📝 Configuration Reference

### Required Fields

All config files must have:
- `name`: CLI identifier (matches INTERNAL_DEFAULTS key)
- `command`: Executable name
- `additional_args`: Array of extra arguments
- `env`: Environment variables object
- `roles`: Object with default/planner/codereviewer roles

### Role Configuration

Each role specifies:
- `prompt_path`: Path to system prompt file (relative to project root)
- `role_args`: Additional CLI arguments for this role

```json
{
  "roles": {
    "default": {
      "prompt_path": "systemprompts/clink/default.txt",
      "role_args": []
    }
  }
}
```

---

## 🔄 Update History

**Latest Changes**:
- ✅ kimi: Changed from `stream-json` to plain text with `--command` argument
- ✅ iflow: Added `--prompt` argument support
- ✅ qwen: Changed from `-o json` to `--output-format json` + `--prompt` argument
- ✅ vecli: Confirmed plain text output format
- ✅ All: Added `--yolo` for non-interactive mode

---

**For detailed implementation history, see git commit log.**

---

## 💡 Tips

- **Use `--yolo`** for all CLIs to avoid interactive prompts
- **Test locally first** before testing via MCP
- **Check logs** at `logs/mcp_server.log` for debugging
- **Parser errors** usually mean output format changed
- **Always restart MCP** after code/config changes

---

**End of Guide**
