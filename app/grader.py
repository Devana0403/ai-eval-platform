from app.sandbox import run_in_sandbox

def classify_failure(result: dict) -> str | None:
    """Looks at a sandbox run result and labels *why* it failed."""
    if result["timed_out"]:
        return "timeout"
    if result["exit_code"] == 0:
        return None  # nothing failed
    stderr = result["stderr"]
    if "SyntaxError" in stderr:
        return "syntax_error"
    if "AssertionError" in stderr:
        return "logic_error"      # code ran, but produced a wrong answer
    if any(err in stderr for err in ["TypeError", "AttributeError", "NameError"]):
        return "api_misuse"       # called something incorrectly
    return "runtime_error"        # catch-all for anything else

def grade_solution(solution_code: str, test_code: str) -> dict:
    combined_code = f"{solution_code}\n\n{test_code}"
    result = run_in_sandbox(combined_code, timeout_seconds=5)

    failure_type = classify_failure(result)
    passed = failure_type is None

    return {
        "passed": passed,
        "failure_type": failure_type,
        "stdout": result["stdout"],
        "stderr": result["stderr"]
    }