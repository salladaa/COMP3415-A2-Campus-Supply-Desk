"""Evaluate a Task 6 candidate in a temporary copy; never edit production code."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']
with tempfile.TemporaryDirectory() as directory:
    work = Path(directory)
    for folder in ('supplydesk', 'tests'):
        shutil.copytree(root / folder, work / folder, ignore=shutil.ignore_patterns('__pycache__'))
    source = work / 'supplydesk/service.py'
    original = source.read_text()
    assert original.count('type(quantity) is not int') == 1
    source.write_text(original.replace('type(quantity) is not int', 'not isinstance(quantity, int)'))
    result = subprocess.run(command, cwd=work, capture_output=True, text=True)
    probe = subprocess.run([sys.executable, '-c',
        "from supplydesk.service import OrderService; "
        "q=OrderService('probe.json').quote('regular',[{'product_id':'notebook','quantity':True}]); "
        "print('isinstance(True, int):',isinstance(True,int)); "
        "print('Accepted boolean quantity:',q['items'][0]['quantity']); "
        "print('Total cents:',q['total_cents'])"], cwd=work, capture_output=True, text=True)
    output = ('Task 6 technical candidate experiment\n'
        'Candidate: replace type(quantity) is not int with not isinstance(quantity, int).\n'
        'Change applied only to a temporary copy, then discarded.\n'
        'Specification: Requests and validation forbids boolean quantities.\n'
        f'Command: {command!r}\n{result.stdout}{result.stderr}\nExit code: {result.returncode}\n'
        f'Focused probe:\n{probe.stdout}{probe.stderr}\nProbe exit code: {probe.returncode}\n')
    (root / 'evidence/07-quantity-candidate.txt').write_text(output)
    print(output)
