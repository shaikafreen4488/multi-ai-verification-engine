from tools.llm import chat
from tools.sandbox import run_code

SYSTEM = """You are the CODER agent. If the task requires computation, write a short
self-contained Python script that computes the answer and prints ONLY the final
result with print(). If the task is not computational, respond with exactly:
NO_CODE_NEEDED

Output ONLY the Python code (or NO_CODE_NEEDED), no explanation, no markdown fences.
"""

def run(task: str, subtasks: list[str], feedback: str = "") -> dict:
    user_msg = f"Task: {task}\nSubtasks: {subtasks}"
    if feedback:
        user_msg += f"\n\nPrevious attempt was rejected. Feedback to address:\n{feedback}"
    raw = chat(SYSTEM, user_msg)
    code = raw.strip().strip("`").replace("python\n", "", 1) if raw.strip().startswith("```") else raw.strip()

    if code.strip() == "NO_CODE_NEEDED" or not code.strip():
        return {"needed": False, "code": None, "execution": None}

    execution = run_code(code)
    return {"needed": True, "code": code, "execution": execution}
