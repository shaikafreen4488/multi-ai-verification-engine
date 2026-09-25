from tools.llm import chat

SYSTEM = """You are the PLANNER agent in a multi-agent verification system.
Your job: break the user's task into concrete subtasks, and explicitly flag if the
task is ambiguous, underspecified, or requires information that may not be available.

Respond in this exact format:
AMBIGUOUS: yes|no
AMBIGUITY_NOTE: <one line, or "none">
SUBTASKS:
- <subtask 1>
- <subtask 2>
(2-4 subtasks max)
TASK_TYPE: factual|computational|code|mixed
"""

def run(task: str) -> dict:
    raw = chat(SYSTEM, f"Task: {task}")
    ambiguous = "yes" in raw.split("AMBIGUOUS:")[1].split("\n")[0].lower() if "AMBIGUOUS:" in raw else False
    note = raw.split("AMBIGUITY_NOTE:")[1].split("\n")[0].strip() if "AMBIGUITY_NOTE:" in raw else ""
    task_type = raw.split("TASK_TYPE:")[1].split("\n")[0].strip().lower() if "TASK_TYPE:" in raw else "mixed"
    subtasks = []
    if "SUBTASKS:" in raw:
        block = raw.split("SUBTASKS:")[1].split("TASK_TYPE:")[0]
        subtasks = [l.strip("- ").strip() for l in block.strip().split("\n") if l.strip()]
    return {
        "raw": raw,
        "ambiguous": ambiguous,
        "ambiguity_note": note,
        "subtasks": subtasks or [task],
        "task_type": task_type,
    }
