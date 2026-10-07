"""Safe mathematical expression calculator package.

Public API:

* :func:`evaluate` -- evaluate an expression string, raising a
  :class:`~src.calculator.errors.CalcError` subclass on failure.
* :func:`format_result` -- convert a Decimal result into a JSON number.
* :func:`format_result_text` -- convert a Decimal result into a storable str.
"""

from .errors import CalcError, EvalError, ParseError, TokenizeError
from .parser import evaluate, format_result, format_result_text

__all__ = [
    "CalcError",
    "EvalError",
    "ParseError",
    "TokenizeError",
    "evaluate",
    "format_result",
    "format_result_text",
]
