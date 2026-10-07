"""HTTP controller layer: the REST API blueprint.

API surface::

    GET    /api/health            -> service status
    POST   /api/calculate         -> evaluate an expression and store it
    GET    /api/history           -> list stored history (newest first)
    DELETE /api/history/<id>      -> delete one history record
    DELETE /api/history           -> delete all history records
"""

from flask import Blueprint, current_app, jsonify, request

from ..calculator import CalcError
from ..config import Config

api = Blueprint("api", __name__, url_prefix="/api")


def _service():
    """Fetch the shared CalculatorService instance from the Flask app."""
    return current_app.extensions["calculator_service"]


@api.get("/health")
def health():
    """Simple liveness probe used by the front end and by deployment checks."""
    return jsonify({"success": True, "status": "ok"})


@api.post("/calculate")
def calculate():
    """Evaluate an expression sent by the front end and persist the record."""
    payload = request.get_json(silent=True) or {}
    expression = payload.get("expression")

    try:
        data = _service().calculate(expression)
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except CalcError as exc:
        return jsonify({"success": False, "message": exc.message}), 400

    return jsonify(
        {
            "success": True,
            "id": data["id"],
            "expression": data["expression"],
            "result": data["result"],
            "createdAt": data["createdAt"],
        }
    ), 201


@api.get("/history")
def history():
    """Return the stored calculation history, newest first."""
    limit = request.args.get("limit", type=int) or Config.HISTORY_LIMIT
    return jsonify({"success": True, "history": _service().list_history(limit)})


@api.delete("/history/<int:record_id>")
def delete_history(record_id: int):
    """Delete a single history record by id."""
    deleted = _service().delete_history(record_id)
    if not deleted:
        return jsonify({"success": False, "message": "Record not found"}), 404
    return jsonify({"success": True, "id": record_id}), 200


@api.delete("/history")
def clear_history():
    """Delete every history record (optional extended feature)."""
    removed = _service().clear_history()
    return jsonify({"success": True, "removed": removed}), 200
