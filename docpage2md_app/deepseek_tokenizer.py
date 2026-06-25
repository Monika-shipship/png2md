from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Iterable

try:
    import regex as _regex
except Exception:  # pragma: no cover - fallback for minimal environments
    _regex = None


TOKENIZER_DIR = Path(__file__).resolve().parent / "deepseek_v3_tokenizer"
TOKENIZER_JSON = TOKENIZER_DIR / "tokenizer.json"

_GPT2_BYTES = (
    list(range(ord("!"), ord("~") + 1))
    + list(range(ord("¡"), ord("¬") + 1))
    + list(range(ord("®"), ord("ÿ") + 1))
)
_BYTE_ENCODER: dict[int, str] = {}
_next_codepoint = 0
for _byte in range(256):
    if _byte in _GPT2_BYTES:
        _BYTE_ENCODER[_byte] = chr(_byte)
    else:
        while _next_codepoint in _GPT2_BYTES:
            _next_codepoint += 1
        _BYTE_ENCODER[_byte] = chr(256 + _next_codepoint)
        _next_codepoint += 1

if _regex is not None:
    _PRETOKEN_RE = _regex.compile(
        r"\p{N}{1,3}"
        r"|[一-龥぀-ゟ゠-ヿ]+"
        r"|[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~][A-Za-z]+"
        r"|[^\r\n\p{L}\p{P}\p{S}]?[\p{L}\p{M}]+"
        r"| ?[\p{P}\p{S}]+[\r\n]*"
        r"|\s*[\r\n]+"
        r"|\s+(?!\S)"
        r"|\s+"
    )
else:
    _PRETOKEN_RE = None


def count_text_tokens(text: str) -> int:
    """Count text tokens with the bundled DeepSeek V3 tokenizer."""
    return len(encode_text(text))


def encode_text(text: str) -> list[int]:
    """Encode text with the bundled DeepSeek V3 byte-level BPE tokenizer.

    This is a lightweight in-app implementation using DeepSeek's published
    `tokenizer.json`. It avoids adding `transformers` as a GUI dependency.
    """
    tokenizer = _get_tokenizer()
    return tokenizer.encode(text or "")


def build_deepseek_chat_text(messages: Iterable[dict], *, add_generation_prompt: bool = True) -> str:
    """Render the subset of DeepSeek's chat template used by this app."""
    system_parts: list[str] = []
    non_system: list[dict] = []
    for message in messages:
        role = str(message.get("role") or "")
        content = _message_content_to_text(message.get("content"))
        if role == "system":
            system_parts.append(content)
        else:
            copied = dict(message)
            copied["content"] = content
            non_system.append(copied)

    text = "<｜begin▁of▁sentence｜>" + "\n\n".join(part for part in system_parts if part)
    for message in non_system:
        role = str(message.get("role") or "")
        content = str(message.get("content") or "")
        if role == "user":
            text += "<｜User｜>" + content
        elif role == "assistant":
            if "</think>" in content:
                content = content.split("</think>")[-1]
            text += "<｜Assistant｜>" + content + "<｜end▁of▁sentence｜>"
        elif role == "tool":
            text += "<｜tool▁outputs▁begin｜><｜tool▁output▁begin｜>" + content + "<｜tool▁output▁end｜><｜tool▁outputs▁end｜>"
        else:
            text += content
    if add_generation_prompt:
        text += "<｜Assistant｜>"
    return text


def count_chat_tokens(messages: Iterable[dict], *, add_generation_prompt: bool = True) -> int:
    """Count DeepSeek chat prompt tokens for the simple chat calls used here."""
    return count_text_tokens(build_deepseek_chat_text(messages, add_generation_prompt=add_generation_prompt))


def heuristic_text_tokens(text: str) -> int:
    """Fallback estimate from DeepSeek docs when tokenizer resources cannot load."""
    text = text or ""
    chinese = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    other = max(0, len(text) - chinese)
    return max(1, math.ceil(chinese * 0.6 + other * 0.3))


def _message_content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item.get("text") or ""))
                elif item.get("type") == "text":
                    parts.append(str(item.get("text") or ""))
        return "\n".join(part for part in parts if part)
    return str(content or "")


@lru_cache(maxsize=1)
def _get_tokenizer() -> "_DeepSeekTokenizer":
    return _DeepSeekTokenizer(TOKENIZER_JSON)


class _DeepSeekTokenizer:
    def __init__(self, tokenizer_path: Path) -> None:
        data = json.loads(tokenizer_path.read_text(encoding="utf-8"))
        model = data["model"]
        self.vocab: dict[str, int] = {str(key): int(value) for key, value in model["vocab"].items()}
        self.merge_ranks: dict[tuple[str, str], int] = {}
        for rank, merge in enumerate(model.get("merges") or []):
            parts = str(merge).split()
            if len(parts) == 2:
                self.merge_ranks[(parts[0], parts[1])] = rank
        self.added_tokens: dict[str, int] = {
            str(item["content"]): int(item["id"])
            for item in data.get("added_tokens") or []
            if item.get("content") is not None and item.get("id") is not None
        }
        self.added_token_starts = {token[0] for token in self.added_tokens if token}
        self.added_tokens_by_length = sorted(self.added_tokens, key=len, reverse=True)

    def encode(self, text: str) -> list[int]:
        token_ids: list[int] = []
        for kind, value in self._split_added_tokens(text):
            if kind == "added":
                token_ids.append(self.added_tokens[value])
                continue
            for piece in _pretokenize(value):
                byte_piece = "".join(_BYTE_ENCODER[byte] for byte in piece.encode("utf-8"))
                for token in self._bpe(byte_piece):
                    token_id = self.vocab.get(token)
                    if token_id is not None:
                        token_ids.append(token_id)
                    else:
                        token_ids.extend(self.vocab[char] for char in token if char in self.vocab)
        return token_ids

    def _split_added_tokens(self, text: str) -> Iterable[tuple[str, str]]:
        pos = 0
        buffer: list[str] = []
        length = len(text)
        while pos < length:
            matched = None
            if text[pos] in self.added_token_starts:
                for token in self.added_tokens_by_length:
                    if text.startswith(token, pos):
                        matched = token
                        break
            if matched is None:
                buffer.append(text[pos])
                pos += 1
                continue
            if buffer:
                yield "text", "".join(buffer)
                buffer.clear()
            yield "added", matched
            pos += len(matched)
        if buffer:
            yield "text", "".join(buffer)

    @lru_cache(maxsize=100_000)
    def _bpe(self, token: str) -> tuple[str, ...]:
        if not token:
            return ()
        word = tuple(token)
        if len(word) == 1:
            return word
        pairs = _pairs(word)
        while pairs:
            bigram = min(pairs, key=lambda pair: self.merge_ranks.get(pair, float("inf")))
            if bigram not in self.merge_ranks:
                break
            first, second = bigram
            merged: list[str] = []
            index = 0
            while index < len(word):
                if index < len(word) - 1 and word[index] == first and word[index + 1] == second:
                    merged.append(first + second)
                    index += 2
                else:
                    merged.append(word[index])
                    index += 1
            word = tuple(merged)
            if len(word) == 1:
                break
            pairs = _pairs(word)
        return word


def _pairs(word: tuple[str, ...]) -> set[tuple[str, str]]:
    return {(word[index], word[index + 1]) for index in range(len(word) - 1)}


def _pretokenize(text: str) -> list[str]:
    if not text:
        return []
    if _PRETOKEN_RE is None:
        return _fallback_pretokenize(text)
    pieces = [match.group(0) for match in _PRETOKEN_RE.finditer(text)]
    return pieces or [text]


def _fallback_pretokenize(text: str) -> list[str]:
    pieces: list[str] = []
    current = []
    current_kind = None
    for char in text:
        if char.isspace():
            kind = "space"
        elif char.isalnum() or "\u4e00" <= char <= "\u9fff":
            kind = "word"
        else:
            kind = "punct"
        if current and kind != current_kind:
            pieces.append("".join(current))
            current = []
        current.append(char)
        current_kind = kind
    if current:
        pieces.append("".join(current))
    return pieces
