from tools.llm import chat
from tools.search import search_evidence

SYSTEM = """You are the RESEARCHER agent. You are given a task and a list of search
results (evidence). Produce a short set of CLAIMS relevant to the task, and for each
claim, cite which evidence item (by number) supports it. If no evidence supports a
claim, mark it UNSUPPORTED.

Format:
CLAIM: <claim text> | SOURCE: <evidence number or "UNSUPPORTED">
"""

def run(task: str, subtasks: list[str]) -> dict:
    evidence = search_evidence(task)
    evidence_block = "\n".join(f"[{i}] {e['title']}: {e['snippet']} ({e['url']})" for i, e in enumerate(evidence))
    user_msg = f"Task: {task}\nSubtasks: {subtasks}\n\nEvidence:\n{evidence_block}"
    raw = chat(SYSTEM, user_msg)

    claims = []
    for line in raw.split("\n"):
        if line.strip().startswith("CLAIM:"):
            try:
                claim_part, source_part = line.split("| SOURCE:")
                claims.append({
                    "claim": claim_part.replace("CLAIM:", "").strip(),
                    "source": source_part.strip(),
                })
            except ValueError:
                continue

    return {"raw": raw, "evidence": evidence, "claims": claims}
