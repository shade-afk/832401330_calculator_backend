"""Recursive-descent parser / evaluator for the safe expression calculator.

Grammar (EBNF)::

    expression := term (('+' | '-') term)*
    term       := factor (('*' | '/') factor)*
    factor     := ('+' | '-') factor | primary
    primary    := NUMBER | '(' expression ')'

The parser evaluates the expression while it walks the token list, so no
intermediate AST is required. Computations use :class:`decimal.Decimal` to
avoid binary floating point artifacts such as ``0.1 + 0.2``.

Only the four basic operators, parentheses, unary signs and decimal numbers
are supported. There is deliberately no ``eval`` / ``exec`` anywhere.
"""

from decimal import Decimal, InvalidOperation, getcontext
from typing import List, Optional

from .errors import EvalError, ParseError
from .tokenizer import LPAREN, NUMBER, OPERATOR, RPAREN, Token, tokenize

# Keep enough precision for typical calculator use.
getcontext().prec = 28

# Maximum number of decimal places kept in a result before rounding.
_MAX_DECIMAL_PLACES = 10


class Parser:
    """A recursive-descent parser that evaluates as it parses."""

    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # -- token helpers ----------------------------------------------------
    def _peek(self) -> Optional[Token]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    # -- grammar rules ----------------------------------------------------
    def parse(self) -> Decimal:
        """Parse and evaluate the whole token stream."""
        value = self._expression()
        leftover = self._peek()
        if leftover is not None:
            raise ParseError(f"Unexpected token '{leftover.value}' at position {leftover.pos}")
        return value

    def _expression(self) -> Decimal:
        value = self._term()
        while True:
            token = self._peek()
            if token is not None and token.type == OPERATOR and token.value in ("+", "-"):
                self._advance()
                right = self._term()
                value = value + right if token.value == "+" else value - right
            else:
                return value

    def _term(self) -> Decimal:
        value = self._factor()
        while True:
            token = self._peek()
            if token is not None and token.type == OPERATOR and token.value in ("*", "/"):
                self._advance()
                right = self._factor()
                if token.value == "*":
                    value = value * right
                else:
                    if right == 0:
                        raise EvalError("Division by zero")
                    value = value / right
            else:
                return value

    def _factor(self) -> Decimal:
        token = self._peek()
        if token is None:
            raise ParseError("Unexpected end of expression")

        if token.type == OPERATOR and token.value in ("+", "-"):
            self._advance()
            operand = self._factor()
            return operand if token.value == "+" else -operand

        if token.type == NUMBER:
            self._advance()
            return token.value

        if token.type == LPAREN:
            self._advance()
            value = self._expression()
            closing = self._peek()
            if closing is None or closing.type != RPAREN:
                raise ParseError("Missing closing parenthesis ')'")
            self._advance()
            return value

        raise ParseError(f"Unexpected token '{token.value}' at position {token.pos}")


def evaluate(expression: str) -> Decimal:
    """Tokenize and evaluate ``expression``, returning an exact Decimal.

    :raises CalcError: (a subclass) when the expression is invalid or cannot
        be evaluated.
    """
    tokens = tokenize(expression)
    return Parser(tokens).parse()


def format_result(value: Decimal):
    """Convert a Decimal result into a clean JSON-friendly number.

    Integral values become ``int``; everything else is rounded to at most
    ``_MAX_DECIMAL_PLACES`` decimal places and returned as ``float`` so that
    ``json.dumps`` can serialize it directly.
    """
    if not value.is_finite():
        raise EvalError("Result is not a finite number")

    if value == value.to_integral_value():
        return int(value)

    rounded = value
    try:
        rounded = value.quantize(Decimal(1).scaleb(-_MAX_DECIMAL_PLACES))
    except InvalidOperation:
        # Numbers with a very large magnitude cannot be quantized; fall back
        # to the raw value.
        rounded = value
    return float(rounded)


def format_result_text(value: Decimal) -> str:
    """Render a Decimal as a compact human readable string for persistence."""
    number = format_result(value)
    if isinstance(number, int):
        return str(number)
    return repr(number)
