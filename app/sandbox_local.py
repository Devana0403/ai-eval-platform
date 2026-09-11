import subprocess
import tempfile
import os

def run_in_sandbox_local(code: str, timeout_seconds: int = 5) -> dict:
    """
    Runs untrusted Python code inside an isolated, locked-down Docker
    container and returns what happened (output, errors, exit code).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "solution.py")
        with open(script_path, "w") as f:
            f.write(code)

        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",       # no internet/network access
            "--memory", "128m",        # hard memory cap
            "--cpus", "0.5",           # hard CPU cap
            "--user", "nobody",        # non-root inside the container
            "-v", f"{tmpdir}:/code:ro",  # mount code as READ-ONLY
            "eval-sandbox:latest",          # the image that has python 3.11 slim
            "timeout", str(timeout_seconds),  # kill if it runs too long
            "python", "/code/solution.py"
        ]

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 10
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "timed_out": result.returncode == 124   
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Execution timed out",
                "exit_code": -1,
                "timed_out": True
            }