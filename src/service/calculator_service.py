"""Business logic for calculations and history persistence.

The service layer is the only place that talks to both the calculator engine
and the database. Controllers stay thin: they validate HTTP input and map
exceptions to status codes.
"""

from datetime import datetime

from ..calculator import CalcError, evaluate, format_result, format_result_text
from ..model import Database


class CalculatorService:
    """Coordinates expression evaluation and history storage."""

    def __init__(self, database: Database) -> None:
        self._db = database

    # -- calculation ------------------------------------------------------
    def calculate(self, expression: str) -> dict:
        """Evaluate ``expression`` on the backend and persist the record.

        :raises CalcError: if the expression is invalid or cannot be evaluated.
        :raises ValueError: if the request body has no usable expression.
        """
        if expression is None or not str(expression).strip():
            raise ValueError("Field 'expression' is required")

        normalized = str(expression).strip()
        value = evaluate(normalized)
        result = format_result(value)

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record_id = self._db.insert_history(
            normalized, format_result_text(value), created_at
        )

        return {
            "id": record_id,
            "expression": normalized,
            "result": result,
            "createdAt": created_at,
        }

    # -- history ----------------------------------------------------------
    def list_history(self, limit: int) -> list:
        rows = self._db.list_history(limit)
        return [self._to_dict(row) for row in rows]

    def delete_history(self, record_id: int) -> bool:
        return self._db.delete_history(record_id)

    def clear_history(self) -> int:
        return self._db.clear_history()

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _to_dict(row) -> dict:
        return {
            "id": row["id"],
            "expression": row["expression"],
            "result": row["result"],
            "createdAt": row["created_at"],
        }


__all__ = ["CalculatorService", "CalcError"]
