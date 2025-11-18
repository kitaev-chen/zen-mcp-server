# Clink CLI Parsers Configuration

This document explains the parser configurations for all supported CLI clients in the clink functionality.

## Overview

The clink system supports multiple LLM CLI clients, each with its own output format. The parser system translates these various output formats into a unified `ParsedCLIResponse` structure.

## Parser Configurations

### 1. Gemini (`gemini`)

- **Command Args**: `-o json`
- **Parser**: `gemini_json` (`GeminiJSONParser`)
- **Output Format**: JSON with `response` and `stats` fields
- **Example Output**:
  ```json
  {
    "response": "The answer is 42",
    "stats": {
      "models": {
        "gemini-2.5-pro": {
          "tokens": {"prompt": 10, "candidates": 5, "total": 15},
          "api": {"totalLatencyMs": 1234}
        }
      }
    }
  }
  ```

### 2. Codex (`codex`)

- **Command Args**: `exec`
- **Parser**: `codex_jsonl` (`CodexJSONLParser`)
- **Output Format**: JSONL events stream (one JSON object per line)
- **Example Output**:
  ```jsonl
  {"type":"item.completed","item":{"type":"agent_message","text":"Hello"}}
  {"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}
  ```
- **Note**: Uses the `exec` subcommand (not an option flag) to run non-interactively

### 3. Claude (`claude`)

- **Command Args**: `--print --output-format json`
- **Parser**: `claude_json` (`ClaudeJSONParser`)
- **Output Format**: JSON with `result` field and metadata
- **Example Output**:
  ```json
  {
    "type": "result",
    "result": "42",
    "usage": {"input_tokens": 10, "output_tokens": 5},
    "modelUsage": {"claude-sonnet-4-5-20250929": {"inputTokens": 10}}
  }
  ```

### 4. iflow (`iflow`)

- **Command Args**: _(none)_
- **Parser**: `iflow_plain` (`IflowPlainParser`)
- **Output Format**: Plain text with optional execution metadata
- **Example Output**:
  ```
  The answer is 4

  What else can I do for you?

  <Execution Info>
  {
    "session-id": "session-xxx",
    "tokenUsage": {"input": 100, "output": 20}
  }
  </Execution Info>
  ```
- **Note**: iflow does NOT support JSON output format. It outputs plain text to stdout with execution metadata at the bottom.

### 5. Kimi (`kimi`)

- **Command Args**: `--yolo --print --thinking --command`
- **Parser**: `kimi_plain` (`KimiPlainParser`)
- **Output Format**: Mixed format with TextPart, ThinkPart, and plain text
- **Example Output**:
  ```
  hello
  StepBegin(n=1)
  ThinkPart(type='think', think='The user said "hello"...')
  TextPart(type='text', text="Hello! I'm Kimi CLI, ready to help you.")
  StatusUpdate(status=StatusSnapshot(context_usage=0.02))
  ```
- **Note**: Kimi outputs mixed format with structured parts (TextPart, ThinkPart) and plain text

### 6. Qwen (`qwen`)

- **Command Args**: `--yolo --output-format json --prompt`
- **Parser**: `gemini_json` (`GeminiJSONParser`)
- **Output Format**: Same as Gemini (JSON with `response` and `stats`)
- **Example Output**:
  ```json
  {
    "response": "The answer is 42",
    "stats": {
      "models": {
        "qwen3-coder-plus": {
          "tokens": {"prompt": 10, "candidates": 5, "total": 15}
        }
      }
    }
  }
  ```
- **Note**: Qwen uses the same output format as Gemini, so it reuses the `gemini_json` parser

### 7. Vecli (`vecli`)

- **Command Args**: _(none)_
- **Parser**: `vecli_plain` (`VecliPlainParser`)
- **Output Format**: Plain text with optional `< SUMMARY >` tags
- **Example Output**:
  ```
  The answer is 4.
  
  < SUMMARY >
  Provided answer to simple math question.
  </SUMMARY >
  ```
- **Note**: vecli outputs plain text by default. It may include SUMMARY tags with spaces.

## Why Different `additional_args`?

The `additional_args` in `constants.py` reflect how each CLI tool exposes its output format options:

1. **gemini** and **qwen**: Use `-o json` flag to specify JSON output format
2. **claude**: Uses `--print` (non-interactive mode) + `--output-format json` flags
3. **codex**: Uses `exec` subcommand (not a flag) to run non-interactively with JSONL output
4. **iflow** and **vecli**: Output in plain text by default without special flags
5. **kimi**: Uses `--print --output-format stream-json` + `-c` for prompt (requires command-line prompt)

## Parser Implementation

All parsers extend `BaseParser` and implement the `parse(stdout: str, stderr: str) -> ParsedCLIResponse` method.

### Common Patterns

1. **JSON Parsing**: Most parsers parse JSON from stdout
2. **Content Extraction**: Extract the main response text from different formats:
   - Gemini/Qwen: `response` field from JSON
   - Claude: `result` field from JSON
   - Codex: `agent_message` events from JSONL
   - iflow: Plain text before `<Execution Info>`
   - Kimi: `assistant` role messages from JSONL
   - vecli: Full plain text with optional `< SUMMARY >` extraction

3. **Metadata Extraction**: Extract usage, model info, timing, etc. into metadata dict
4. **Error Handling**: Raise `ParserError` for invalid/empty output

## Testing

Each parser has a corresponding test file:
- `tests/test_clink_gemini_parser.py`
- `tests/test_clink_parsers.py` (codex)
- `tests/test_clink_claude_parser.py`
- `tests/test_clink_iflow_parser.py`
- `tests/test_clink_kimi_parser.py`
- `tests/test_clink_vecli_parser.py`

Test validation:
```bash
python -c "from clink.parsers import get_parser; \
  for name in ['gemini_json', 'codex_jsonl', 'claude_json', 'iflow_plain', 'kimi_plain', 'vecli_plain']: \
    p = get_parser(name); print(f'✓ {name}')"
```

## Adding New CLI Clients

To add a new CLI client:

1. **Test the CLI**: Run `<cli> --help` to understand its output format options
2. **Determine Parser**: 
   - If it matches an existing format (like gemini/qwen), reuse the parser
   - Otherwise, create a new parser in `clink/parsers/<cli>.py`
3. **Add to Constants**: Update `INTERNAL_DEFAULTS` in `clink/constants.py`
4. **Register Parser**: Add to `_PARSER_CLASSES` in `clink/parsers/__init__.py`
5. **Create Tests**: Add test file in `tests/test_clink_<cli>_parser.py`
6. **Verify**: Run the validation tests to ensure everything works

## Configuration Files

- **Constants**: `clink/constants.py` - CLI client configurations
- **Parser Registry**: `clink/parsers/__init__.py` - Parser registration
- **Parser Implementations**: `clink/parsers/*.py` - Individual parser classes
- **Tests**: `tests/test_clink_*_parser.py` - Parser test suites
