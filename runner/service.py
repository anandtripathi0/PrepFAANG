"""Privileged orchestration boundary: deploy ONLY on a dedicated sandbox host.

Untrusted programs run in disposable, non-root, networkless containers.
The API talks to this worker over an authenticated private HTTP connection.
"""
import asyncio
import hmac
import os
import subprocess
import threading
import time
import uuid
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title='PrepForge isolated runner')
LANGUAGES = {
    'python': ('main.py', 'python3 -I -B /work/main.py'),
    'javascript': ('main.js', 'node --max-old-space-size=128 /work/main.js'),
    'c': ('main.c', 'gcc -O2 /work/main.c -o /work/program && /work/program'),
    'cpp': ('main.cpp', 'g++ -std=c++17 -O2 /work/main.cpp -o /work/program && /work/program'),
    'java': ('Main.java', 'javac /work/Main.java && java -XX:ActiveProcessorCount=1 -Xmx128m -XX:CompressedClassSpaceSize=32m -XX:MaxMetaspaceSize=96m -cp /work Main'),
}
capacity = asyncio.Semaphore(2)


def bounded_docker(args, payload, timeout):
    """Bound the entire container output, including a tampered supervisor."""
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    chunks = bytearray()
    exceeded = threading.Event()

    def drain():
        while True:
            chunk = process.stdout.read(8192)
            if not chunk:
                return
            if len(chunks) + len(chunk) > 131072:
                exceeded.set()
                process.kill()
                return
            chunks.extend(chunk)

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    try:
        process.stdin.write(payload.encode())
        process.stdin.close()
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise
    finally:
        reader.join(timeout=2)
    if exceeded.is_set():
        return '{"status":"Output Limit Exceeded","runtime_ms":0}'
    return chunks.decode('utf-8', errors='replace')


class Case(BaseModel):
    input: str = Field(max_length=10000)
    output: str = Field(max_length=10000)
    hidden: bool = False


class Evaluation(BaseModel):
    language: str
    code: str = Field(min_length=1, max_length=50000)
    tests: list[Case] = Field(min_length=1, max_length=20)
    time_limit: float = Field(gt=0, le=5)
    memory_limit: int = Field(ge=64, le=512)


def docker_arguments(name, memory):
    return ['docker', 'run', '--rm', '--name', name, '--network=none', '--read-only', '--user', '65534:65534',
        '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64', '--cpus=1',
        f'--memory={memory}m', f'--memory-swap={memory}m', '--ulimit', 'nofile=64:64',
        '--ulimit', 'fsize=1024:1024', '--tmpfs', '/work:rw,nosuid,nodev,size=32m,mode=1777',
        '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777', '-i',
        os.environ.get('CODE_RUNNER_IMAGE', 'prepforge-sandbox:local'), 'python3', '/opt/execute.py']


def execute_case(data, case):
    import json
    name = 'prepforge-' + uuid.uuid4().hex
    started = time.monotonic()
    try:
        # Only constant Docker arguments are executed on the worker host.
        # Code and test input are passed as JSON over stdin, not interpolated into a command.
        payload = {'filename': LANGUAGES[data.language][0], 'language': data.language, 'code': data.code,
                   'input': case.input, 'timeout': data.time_limit}
        output = bounded_docker(docker_arguments(name, data.memory_limit), json.dumps(payload), data.time_limit + 25)
        try:
            result = json.loads(output)
        except ValueError:
            raise RuntimeError('Sandbox unavailable or terminated by resource limit')
        status = result['status']
        if status == 'Executed':
            status = 'Accepted' if result.get('output', '').split() == case.output.split() else 'Wrong Answer'
        elif status not in ('Time Limit Exceeded', 'Runtime Error', 'Compilation Error', 'Output Limit Exceeded'):
            status = 'Runtime Error'
        return {'status': status, 'runtime_ms': result.get('runtime_ms', 0)}
    except subprocess.TimeoutExpired:
        return {'status': 'Time Limit Exceeded', 'runtime_ms': round((time.monotonic()-started)*1000)}
    finally:
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=False)


@app.post('/evaluate')
async def evaluate(data: Evaluation, authorization: str = Header(default='')):
    token = os.environ.get('CODE_RUNNER_TOKEN', '')
    if not token or not hmac.compare_digest(authorization, 'Bearer ' + token):
        raise HTTPException(401, 'Runner authentication required.')
    if data.language not in LANGUAGES:
        raise HTTPException(422, 'Unsupported language.')
    async with capacity:
        try:
            results = []
            started = time.monotonic()
            for case in data.tests:
                if time.monotonic() - started > 60:
                    raise RuntimeError('Evaluation exceeded the worker job budget')
                results.append(await asyncio.to_thread(execute_case, data, case))
        except (OSError, RuntimeError, subprocess.SubprocessError):
            raise HTTPException(503, 'Sandbox execution unavailable. Check the worker and sandbox image.')
    passed = sum(r['status'] == 'Accepted' for r in results)
    return {'status': next((r['status'] for r in results if r['status'] != 'Accepted'), 'Accepted'),
            'passed': passed, 'runtime_ms': sum(r['runtime_ms'] for r in results), 'tests': results}
