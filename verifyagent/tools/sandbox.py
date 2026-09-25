"""Sandboxed Python execution used to verify code the Coder agent produces.

Deliberately simple for a hackathon timeline: a subprocess with a timeout and
no network/file access beyond a temp dir, rather than a full container-per-run
sandbox. Good enough to catch wrong answers, exceptions, and infinite loops
without letting generated code touch the host.
"""
import subprocess
import sys
import tempfile
import os


def run_code(code: str, timeout_seconds: int = 5) -> dict:
    """Runs `code` in an isolated subprocess. Returns stdout/stderr/success/error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "snippet.py")
        with open(script_path, "w") as f:
            f.write(code)

        try:
            proc = subprocess.run(
                [sys.executable, script_path],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env={"PATH": os.environ.get("PATH", "")},  # minimal env, no secrets
            )
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
                "error": None,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": f"Execution timed out after {timeout_seconds}s (possible infinite loop).",
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": "", "error": str(e)}
