"""Unit tests for the calculator engine and integration tests for the API.

Run with::

    python -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest

# Make the project root importable when tests are run from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.calculator import CalcError, EvalError, ParseError, evaluate, format_result
from src.config import Config


class CalculatorEngineTest(unittest.TestCase):
    """Pure evaluation tests -- no HTTP, no database."""

    def _result(self, expression):
        return format_result(evaluate(expression))

    def test_basic_addition(self):
        self.assertEqual(self._result("12+8"), 20)

    def test_basic_subtraction(self):
        self.assertEqual(self._result("8-3*2"), 2)

    def test_multiplication_symbols(self):
        self.assertEqual(self._result("5*8"), 40)
        self.assertEqual(self._result("5\u00d78"), 40)  # 5×8

    def test_division_symbols(self):
        self.assertEqual(self._result("10/2"), 5)
        self.assertEqual(self._result("10\u00f72"), 5)  # 10÷2

    def test_operator_precedence(self):
        self.assertEqual(self._result("1+2*3"), 7)

    def test_parentheses(self):
        self.assertEqual(self._result("(1+2)*3"), 9)

    def test_unary_minus(self):
        self.assertEqual(self._result("-5+8"), 3)
        self.assertEqual(self._result("3*-2"), -6)

    def test_unary_plus(self):
        self.assertEqual(self._result("+7"), 7)
        self.assertEqual(self._result("--5"), 5)

    def test_decimal_numbers(self):
        self.assertEqual(self._result("0.1+0.2"), 0.3)
        self.assertEqual(self._result("1.5*2"), 3)

    def test_compound_expression(self):
        self.assertEqual(self._result("10/2+7"), 12)

    def test_division_by_zero(self):
        with self.assertRaises(EvalError):
            evaluate("1/0")

    def test_invalid_expression(self):
        with self.assertRaises(ParseError):
            evaluate("1+*2")
        with self.assertRaises(CalcError):
            evaluate("(1+2")
        with self.assertRaises(CalcError):
            evaluate("1+2)")
        with self.assertRaises(CalcError):
            evaluate("2a+3")
        with self.assertRaises(CalcError):
            evaluate("")

    def test_no_code_execution(self):
        # A tempting payload must be rejected, never executed.
        with self.assertRaises(CalcError):
            evaluate("__import__('os').system('echo hacked')")


class ApiIntegrationTest(unittest.TestCase):
    """End-to-end tests through the Flask test client with a temp database."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        Config.DB_PATH = os.path.join(cls._tmp.name, "test.db")
        from app import create_app

        cls.app = create_app()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    def test_calculate_success(self):
        response = self.client.post("/api/calculate", json={"expression": "(1+2)*3"})
        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["result"], 9)
        self.assertTrue(body["success"])

    def test_calculate_invalid(self):
        response = self.client.post("/api/calculate", json={"expression": "1+*2"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_calculate_division_by_zero(self):
        response = self.client.post("/api/calculate", json={"expression": "1/0"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("zero", response.get_json()["message"].lower())

    def test_calculate_missing_expression(self):
        response = self.client.post("/api/calculate", json={})
        self.assertEqual(response.status_code, 400)

    def test_history_and_delete_flow(self):
        created = self.client.post(
            "/api/calculate", json={"expression": "7*6"}
        ).get_json()
        record_id = created["id"]

        history = self.client.get("/api/history").get_json()["history"]
        self.assertTrue(any(row["id"] == record_id for row in history))

        deleted = self.client.delete(f"/api/history/{record_id}")
        self.assertEqual(deleted.status_code, 200)

        missing = self.client.delete(f"/api/history/{record_id}")
        self.assertEqual(missing.status_code, 404)

    def test_clear_history(self):
        self.client.post("/api/calculate", json={"expression": "2+2"})
        cleared = self.client.delete("/api/history")
        self.assertEqual(cleared.status_code, 200)
        self.assertEqual(self.client.get("/api/history").get_json()["history"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
