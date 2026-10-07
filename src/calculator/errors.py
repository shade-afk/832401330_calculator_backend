"""Custom exception hierarchy for the safe expression calculator.

All calculator errors derive from :class:`CalcError`, so the controller layer
can catch a single base class and translate it into a standardized HTTP error
response.
"""


class CalcError(Exception):
    """Base class for every error raised by the calculator package."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TokenizeError(CalcError):
    """Raised when the raw text cannot be split into valid tokens."""


class ParseError(CalcError):
    """Raised when the token stream does not form a valid expression."""


class EvalError(CalcError):
    """Raised when a syntactically valid expression cannot be evaluated.

    The most common cause is a division by zero.
    """
