# Test evidence

Runtime: bundled CPython 3.12.14 (system python3 is 3.9.6 and below the README requirement).
Executable: `/Users/santhoshallada/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`
Portable command, with Python 3.10+: `python -m unittest discover -s tests -v`.
Capture command: `python evidence/run_tests.py LOG_NAME.txt`. It records exit code and worktree status.

- 01-starter-tests.txt: original 4 tests; expected 4 pass, actual 4 pass, exit 0.
- 02-before-refactoring.txt: 23 tests on untouched application; expected conformance to FUNCTIONAL_SPEC, actual 5 failed assertions across 3 test methods, exit 1.
- 03-after-refactoring.txt: same suite; expected unchanged baseline, including known failures.
- 04-after-defect-fixes.txt: same suite; expected all pass after separately identified corrections.
- 05-after-cr01.txt: full expanded suite; expected all pass.

Baseline failures are deliberately real failures, not skipped tests or adjusted expectations:
1. Duplicate product requests exceeding combined stock are accepted by quote and placement (2 failures).
2. A second cancellation restores stock twice, giving 22 instead of 20 notebooks (1 failure).
3. Students receive no discount at exactly 5000 cents instead of 500 cents (2 failures).

No application code was edited before capturing the baseline. Original starter commit:
82ed75e0714e50c086a13ee491f51b349814d8a4 (tag assignment-starter).
All tests use temporary state paths; ordinary saved user data is untouched.
