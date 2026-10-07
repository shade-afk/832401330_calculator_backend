"""Self-contained end-to-end HTTP check for the calculator backend.

This script starts the real Flask/Werkzeug HTTP server in a background
thread, sends genuine HTTP requests to it, prints a PASS/FAIL report, then
shuts the server down and exits. It uses a temporary database so it never
touches the development data.

Run with::

    python scripts/e2e_check.py
"""

import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

# -- isolate the test run ------------------------------------------------
os.environ["CALC_DEBUG"] = "0"
_TMP_DIR = tempfile.mkdtemp(prefix="calc-e2e-")
os.environ["CALC_DB_PATH"] = os.path.join(_TMP_DIR, "e2e.db")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.serving import make_server  # noqa: E402

from app import app  # noqa: E402

PORT = int(os.environ.get("CALC_E2E_PORT", "5057"))
BASE_URL = f"http://127.0.0.1:{PORT}"

_results = []


def call(method, path, payload=None):
    """Send one HTTP request and return (status, body)."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def check(name, condition, detail=""):
    """Record and print one assertion result."""
    status = "PASS" if condition else "FAIL"
    _results.append(status == "PASS")
    print(f"  [{status}] {name}{(' -> ' + detail) if detail else ''}")


def main():
    server = make_server("127.0.0.1", PORT, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Backend started on {BASE_URL} (thread id {thread.ident})")
    time.sleep(0.6)

    try:
        print("\n[1] Health check")
        status, body = call("GET", "/api/health")
        check("GET /api/health returns 200", status == 200, f"HTTP {status}")
        check("health payload success", body.get("success") is True)

        print("\n[2] Basic and compound calculations (computed by backend)")
        cases = [
            ("12+8", 20),
            ("1+2*3", 7),
            ("(1+2)*3", 9),
            ("10/2+7", 12),
            ("8-3*2", 2),
            ("-5+8", 3),
            ("3*-2", -6),
            ("0.1+0.2", 0.3),
            ("5\u00d78", 40),
            ("10\u00f72", 5),
        ]
        for expression, expected in cases:
            status, body = call("POST", "/api/calculate", {"expression": expression})
            ok = status == 201 and body.get("result") == expected
            check(
                f"{expression} = {expected}",
                ok,
                f"HTTP {status}, result={body.get('result')}",
            )

        print("\n[3] Error handling")
        status, body = call("POST", "/api/calculate", {"expression": "1/0"})
        check("division by zero -> 400", status == 400, body.get("message", ""))
        status, body = call("POST", "/api/calculate", {"expression": "1+*2"})
        check("invalid expression -> 400", status == 400, body.get("message", ""))
        status, body = call("POST", "/api/calculate", {"expression": "(1+2"})
        check("unbalanced parenthesis -> 400", status == 400, body.get("message", ""))
        status, body = call("POST", "/api/calculate", {})
        check("missing expression -> 400", status == 400, body.get("message", ""))

        print("\n[4] History persistence")
        status, body = call("GET", "/api/history")
        rows = body.get("history", [])
        check("GET /api/history returns 200", status == 200, f"{len(rows)} rows")
        check("history is non-empty after calculations", len(rows) >= 9)
        check(
            "history rows contain required fields",
            all({"id", "expression", "result", "createdAt"} <= set(r) for r in rows),
        )

        print("\n[5] Delete one record")
        target = rows[0]["id"]
        status, _ = call("DELETE", f"/api/history/{target}")
        check(f"DELETE /api/history/{target} -> 200", status == 200, f"HTTP {status}")
        status, body = call("GET", "/api/history")
        check(
            "deleted record no longer present",
            all(r["id"] != target for r in body.get("history", [])),
        )
        status, body = call("DELETE", f"/api/history/{target}")
        check("deleting missing record -> 404", status == 404, f"HTTP {status}")

        print("\n[6] Clear all history")
        status, body = call("DELETE", "/api/history")
        check("DELETE /api/history -> 200", status == 200, f"removed={body.get('removed')}")
        status, body = call("GET", "/api/history")
        check("history empty after clear", body.get("history") == [])

        print("\n[7] 404 handling")
        status, _ = call("GET", "/api/does-not-exist")
        check("unknown route -> 404", status == 404, f"HTTP {status}")

    finally:
        server.shutdown()
        print("\nBackend stopped.")

    passed = sum(1 for ok in _results if ok)
    total = len(_results)
    print(f"\n=== E2E result: {passed}/{total} passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
