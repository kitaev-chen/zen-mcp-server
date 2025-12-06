"""Parser registry for clink."""

from __future__ import annotations

from .base import BaseParser, ParsedCLIResponse, ParserError
from .claude import ClaudeJSONParser
from .codex import CodexJSONLParser
from .gemini import GeminiJSONParser
from .iflow import IflowPlainParser
from .kimi import KimiPlainParser
from .qwen import QwenJSONParser
from .vecli import VecliPlainParser

_PARSER_CLASSES: dict[str, type[BaseParser]] = {
    CodexJSONLParser.name: CodexJSONLParser,
    GeminiJSONParser.name: GeminiJSONParser,
    QwenJSONParser.name: QwenJSONParser,
    ClaudeJSONParser.name: ClaudeJSONParser,
    IflowPlainParser.name: IflowPlainParser,
    KimiPlainParser.name: KimiPlainParser,
    VecliPlainParser.name: VecliPlainParser,
}


def get_parser(name: str) -> BaseParser:
    normalized = (name or "").lower()
    if normalized not in _PARSER_CLASSES:
        raise ParserError(f"No parser registered for '{name}'")
    parser_cls = _PARSER_CLASSES[normalized]
    return parser_cls()


__all__ = [
    "BaseParser",
    "ParsedCLIResponse",
    "ParserError",
    "get_parser",
]
