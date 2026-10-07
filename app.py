"""Application entry point for the calculator backend.

Run it directly::

    python app.py

or with a WSGI server::

    waitress-serve --port=5000 app:app
"""

from flask import Flask, jsonify
from flask_cors import CORS

from src.config import Config
from src.controller import api
from src.model import Database
from src.service import CalculatorService


def create_app() -> Flask:
    """Application factory: wire together config, database and routes."""
    app = Flask(__name__)

    # CORS is required because the front end is served from a different origin.
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    # Database: create the schema on startup so evaluation always works.
    database = Database(Config.DB_PATH)
    database.init_schema()

    # Share a single service instance through the app extensions.
    app.extensions["calculator_service"] = CalculatorService(database)

    app.register_blueprint(api)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"success": False, "message": "Internal server error"}), 500

    @app.get("/")
    def index():
        return jsonify(
            {
                "success": True,
                "service": "calculator-backend",
                "version": "1.0.0",
                "endpoints": [
                    "GET    /api/health",
                    "POST   /api/calculate",
                    "GET    /api/history",
                    "DELETE /api/history/<id>",
                    "DELETE /api/history",
                ],
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
