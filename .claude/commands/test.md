Run the test-case-writer agent on the target code, then immediately run the test-runner agent on the tests it produced.

If the user specified a file or module (e.g. `/test backend/core/scoring.py`), pass that as the target to test-case-writer. If no argument was given, ask the user which file or module to test before proceeding.

## Step 1 — Write tests
Invoke the **test-case-writer** agent on the target. It will:
- Read the source file
- Author a complete pytest test file in `backend/tests/`
- Follow all project conventions (AsyncMock for DB, mock Groq, parametrize, etc.)

## Step 2 — Run tests
Immediately invoke the **test-runner** agent on the test file just created. It will:
- Execute the tests with `.venv311\Scripts\python.exe -m pytest <test_file> -v --tb=short`
- Diagnose any failures
- Fix them and re-run until the suite is green
- Report final pass/fail counts

Do not declare success until the test-runner confirms all tests pass.
