import importlib.util
import pathlib
import shutil
import subprocess

import httpx
import pytest
from fastapi import HTTPException

from app.code_runner import Runner


def test_runner_failure_is_explicit(monkeypatch):
    def failure(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "post", failure)
    with pytest.raises(HTTPException) as exc:
        Runner().evaluate("print(1)", "python", {"tests": [], "time_limit": 1, "memory_limit": 128})
    assert exc.value.status_code == 503


def test_hidden_output_is_not_forwarded(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "status": "Wrong Answer",
                "passed": 0,
                "stdout": "SECRET",
                "tests": [{"status": "Wrong Answer", "input": "SECRET", "output": "SECRET"}],
            }

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Response())
    result = Runner().evaluate(
        "print(1)", "python", {"tests": [{"hidden": True}], "time_limit": 1, "memory_limit": 128}, True
    )
    assert "SECRET" not in str(result)


def service():
    path = pathlib.Path(__file__).parents[2] / "runner" / "service.py"
    spec = importlib.util.spec_from_file_location("runner_service", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_container_restrictions():
    args = service().docker_arguments("test", 128)
    for flag in [
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=64",
        "--cpus=1",
        "--memory=128m",
        "--memory-swap=128m",
    ]:
        assert flag in args
    assert "--privileged" not in args
    assert "/var/run/docker.sock" not in " ".join(args)


def docker_ready():
    if not shutil.which("docker"):
        return False
    return (
        subprocess.run(["docker", "image", "inspect", "prepforge-sandbox:local"], capture_output=True).returncode == 0
    )


@pytest.mark.skipif(
    not docker_ready(),
    reason="Docker and prepforge-sandbox:local image are required for real sandbox integration tests",
)
@pytest.mark.parametrize(
    "language,code,expected,status",
    [
        ("python", "print(7)", "7", "Accepted"),
        ("python", "print(8)", "7", "Wrong Answer"),
        ("python", "raise RuntimeError()", "", "Runtime Error"),
        ("python", "while True: pass", "", "Time Limit Exceeded"),
        ("cpp", "invalid source", "", "Compilation Error"),
        (
            "python",
            "import socket\ntry:\n socket.create_connection(('1.1.1.1',80),timeout=.2)\n print('connected')\nexcept OSError:\n print('blocked')",
            "blocked",
            "Accepted",
        ),
        ("python", "import resource\nprint(resource.getrlimit(resource.RLIMIT_NOFILE)[0])", "64", "Accepted"),
        ("python", "print('x'*100000)", "", "Output Limit Exceeded"),
    ],
)
def test_real_sandbox(language, code, expected, status):
    module = service()
    case = module.Case(input="", output=expected)
    data = module.Evaluation(language=language, code=code, tests=[case], time_limit=1, memory_limit=256)
    assert module.execute_case(data, case)["status"] == status
