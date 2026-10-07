"""Lexical analysis for the safe expression calculator.

The tokenizer converts a raw expression string such as ``"(1+2)*3"`` into a
flat list of :class:`Token` objects. It performs *no* arbitrary code
execution: only a small, fixed set of characters is accepted.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import List

from .errors import TokenizeError

# Token type constants.
NUMBER = "NUMBER"
OPERATOR = "OPERATOR"
LPAREN = "LPAREN"
RPAREN = "RPAREN"

# Maps the characters a user may type to a canonical operator symbol.
# Both ASCII and the "pretty" multiplication/division signs are accepted.
_OPERATOR_MAP = {
    "+": "+",
    "-": "-",
    "*": "*",
    "\u00d7": "*",  # ×
    "/": "/",
    "\u00f7": "/",  # ÷
}

# Full-width characters that users may accidentally type.
_FULLWIDTH_MAP = {
    "\uff08": "(",  # （
    "\uff09": ")",  # ）
    "\uff0b": "+",  # ＋
    "\uff0d": "-",  # －
    "\uff0a": "*",  # ＊
    "\uff0f": "/",  # ／
}

_NUMBER_RE = re.compile(r"(?:\d+\.\d*|\.\d+|\d+)")


class Token:
    """A single lexical unit produced by :func:`tokenize`."""

    __slots__ = ("type", "value", "pos")

    def __init__(self, token_type: str, value, pos: int) -> None:
        self.type = token_type
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"Token({self.type!r}, {self.value!r}, pos={self.pos})"


def tokenize(text: str) -> List[Token]:
    """Split ``text`` into a list of tokens.

    :raises TokenizeError: if an unsupported character is encountered or a
        number literal cannot be parsed.
    """
    if text is None:
        raise TokenizeError("Expression is empty")

    tokens: List[Token] = []
    index = 0
    length = len(text)

    while index < length:
        char = text[index]

        if char.isspace():
            index += 1
            continue

        char = _FULLWIDTH_MAP.get(char, char)

        if char.isdigit() or char == ".":
            match = _NUMBER_RE.match(text, index)
            if not match:
                raise TokenizeError(f"Invalid number at position {index}")
            raw = match.group()
            try:
                value = Decimal(raw)
            except InvalidOperation as exc:  # pragma: no cover - defensive
                raise TokenizeError(f"Invalid number '{raw}'") from exc
            tokens.append(Token(NUMBER, value, index))
            index = match.end()
            continue

        if char in _OPERATOR_MAP:
            tokens.append(Token(OPERATOR, _OPERATOR_MAP[char], index))
            index += 1
            continue

        if char == "(":
            tokens.append(Token(LPAREN, char, index))
            index += 1
            continue

        if char == ")":
            tokens.append(Token(RPAREN, char, index))
            index += 1
            continue

        raise TokenizeError(f"Unexpected character '{char}' at position {index}")

    if not tokens:
        raise TokenizeError("Expression is empty")

    return tokens
