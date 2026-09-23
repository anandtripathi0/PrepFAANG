"""This program runs inside the disposable sandbox, never in the API server."""
import json
import os
import selectors
import signal
import subprocess
import sys
import time

COMPILE = {'c': ['gcc', '-O2', '/work/main.c', '-o', '/work/program'],
           'cpp': ['g++', '-std=c++17', '-O2', '/work/main.cpp', '-o', '/work/program'],
           'java': ['javac', '/work/Main.java']}
RUN = {'python': ['python3', '-I', '-B', '/work/main.py'], 'javascript': ['node', '--max-old-space-size=128', '/work/main.js'],
       'c': ['/work/program'], 'cpp': ['/work/program'],
       'java': ['java', '-XX:ActiveProcessorCount=1', '-Xmx128m', '-XX:CompressedClassSpaceSize=32m', '-XX:MaxMetaspaceSize=96m', '-cp', '/work', 'Main']}
MAX_OUTPUT = 65536


def bounded(command, source, timeout):
    start = time.monotonic()
    with open('/work/input.txt', 'w') as stream:
        stream.write(source)
    with open('/work/input.txt') as stream:
        process = subprocess.Popen(command, stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd='/work', start_new_session=True, env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/work', 'LANG': 'C.UTF-8'})
        selector = selectors.DefaultSelector()
        for pipe in (process.stdout, process.stderr):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ)
        output = bytearray()
        total = 0
        status = None
        try:
            while selector.get_map():
                if time.monotonic() - start > timeout:
                    status = 'Time Limit Exceeded'
                    break
                for key, _ in selector.select(timeout=0.05):
                    chunk = os.read(key.fileobj.fileno(), 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    if key.fileobj == process.stdout:
                        output.extend(chunk)
                    if total > MAX_OUTPUT:
                        status = 'Output Limit Exceeded'
                        break
                if status:
                    break
            if status:
                os.killpg(process.pid, signal.SIGKILL)
            try:
                code = process.wait(timeout=max(.1, timeout-(time.monotonic()-start)))
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                status, code = 'Time Limit Exceeded', -1
        finally:
            selector.close()
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        return status, code, output.decode('utf-8', errors='replace'), round((time.monotonic()-start)*1000)


def main():
    data = json.load(sys.stdin)
    with open('/work/' + data['filename'], 'w') as stream:
        stream.write(data['code'])
    if data['language'] in COMPILE:
        status, exit_code, _, _ = bounded(COMPILE[data['language']], '', 15)
        if status or exit_code:
            print(json.dumps({'status': 'Compilation Error', 'runtime_ms': 0}))
            return
    status, exit_code, output, runtime = bounded(RUN[data['language']], data['input'], data['timeout'])
    if not status:
        status = 'Runtime Error' if exit_code else 'Executed'
    print(json.dumps({'status': status, 'runtime_ms': runtime, 'output': output[:MAX_OUTPUT]}))


if __name__ == '__main__':
    main()
