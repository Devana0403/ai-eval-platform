import os
from app.sandbox_local import run_in_sandbox_local
from app.sandbox_azure import run_in_sandbox_azure, AzureSandboxUnavailable

SANDBOX_BACKEND = os.getenv("SANDBOX_BACKEND", "azure").lower()


def run_in_sandbox(code: str, timeout_seconds: int = 5) -> dict:
    if SANDBOX_BACKEND == "local":
        return run_in_sandbox_local(code, timeout_seconds)

    try:
        return run_in_sandbox_azure(code, timeout_seconds)
    except AzureSandboxUnavailable as e:
        return {
            "stdout": "",
            "stderr": (
                "Azure sandbox is currently unavailable (this is expected once the "
                "Azure free-tier trial period ends). "
                f"Details: {e}\n\n"
                "To test this project locally, clone the repo, set SANDBOX_BACKEND=local "
                "in your .env file, and make sure Docker Desktop is running. "
                "See the README for full setup instructions."
            ),
            "exit_code": -1,
            "timed_out": False
        }