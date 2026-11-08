"""Run the full suite and preserve command, runtime, revision, output and exit code."""
from pathlib import Path
import platform
import subprocess
import sys

name = sys.argv[1]
command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']
result = subprocess.run(command, capture_output=True, text=True)
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
status = subprocess.check_output(['git', 'status', '--short'], text=True)
Path('evidence', name).write_text(
    f'Command: {command!r}\nPython: {platform.python_version()}\nHEAD before run: {revision}\n'
    f'Working changes at run:\n{status}\n{result.stdout}{result.stderr}\nExit code: {result.returncode}\n')
print(result.stdout + result.stderr)
sys.exit(result.returncode)
