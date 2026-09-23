import httpx
from fastapi import HTTPException

from .config import settings


class Runner:
    """Only the isolated worker receives code. No execution in the API process."""

    def evaluate(self, code, language, coding, hidden=False):
        tests = coding["tests"] if hidden else [t for t in coding["tests"] if not t["hidden"]]
        try:
            response = httpx.post(
                settings().code_runner_url + "/evaluate",
                headers={"Authorization": "Bearer " + settings().code_runner_token},
                json={
                    "code": code,
                    "language": language,
                    "tests": tests,
                    "time_limit": coding["time_limit"],
                    "memory_limit": coding["memory_limit"],
                },
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(
                503, "The isolated code runner is unavailable. Your code is saved; start the runner and try again."
            )
        # Never forward worker stdout/stderr or inputs from hidden tests.
        return {
            "status": result["status"],
            "passed": result["passed"],
            "total": len(tests),
            "runtime_ms": result.get("runtime_ms", 0),
            "tests": [
                {"index": i + 1, "status": t["status"], "runtime_ms": t.get("runtime_ms", 0)}
                for i, t in enumerate(result.get("tests", []))
            ],
        }


runner = Runner()
