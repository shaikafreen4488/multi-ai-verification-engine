from tools.llm import chat

SYSTEM = """You are the VERIFIER agent, independent from the agents that generated
this content. Be skeptical of specific, checkable, or surprising claims — but for
claims that are basic, well-established facts (elementary science, well-known
geography, famous historical facts), mark them "supported" if the evidence is
broadly on-topic and does not contradict the claim, even if the evidence doesn't
use identical wording. Only mark "unsupported" when the evidence is genuinely
irrelevant or silent on the topic, and only mark "contradicted" when evidence
actively disagrees with the claim.

For each claim, output:
VERIFY: <claim> | STATUS: supported|unsupported|contradicted | REASON: <short reason>

Then output:
CODE_CHECK: correct|incorrect|not_applicable | REASON: <short reason>
OVERALL_CONFIDENCE: <0-100>
"""

def run(task: str, claims: list[dict], evidence: list[dict], coder_result: dict) -> dict:
    evidence_block = "\n".join(f"[{i}] {e['title']}: {e['snippet']}" for i, e in enumerate(evidence))
    claims_block = "\n".join(f"- {c['claim']} (claimed source: {c['source']})" for c in claims) or "none"
    code_block = "NO_CODE_NEEDED"
    if coder_result and coder_result.get("needed"):
        ex = coder_result["execution"]
        code_block = f"CODE:\n{coder_result['code']}\nEXECUTION RESULT: success={ex['success']} stdout={ex['stdout']} stderr={ex['stderr']} error={ex['error']}"

    user_msg = f"Task: {task}\n\nEvidence:\n{evidence_block}\n\nClaims:\n{claims_block}\n\n{code_block}"
    raw = chat(SYSTEM, user_msg, temperature=0.0)

    verifications = []
    for line in raw.split("\n"):
        if line.strip().startswith("VERIFY:"):
            verifications.append(line.replace("VERIFY:", "").strip())

    code_check = "not_applicable"
    if "CODE_CHECK:" in raw:
        code_check = raw.split("CODE_CHECK:")[1].split("|")[0].strip()

    confidence = 50
    if "OVERALL_CONFIDENCE:" in raw:
        try:
            confidence = int("".join(c for c in raw.split("OVERALL_CONFIDENCE:")[1].split("\n")[0] if c.isdigit()))
        except ValueError:
            pass

    contradicted = any("contradicted" in v.lower() for v in verifications)
    unsupported_count = sum(1 for v in verifications if "unsupported" in v.lower())

    return {
        "raw": raw,
        "verifications": verifications,
        "code_check": code_check,
        "confidence": confidence,
        "contradicted": contradicted,
        "unsupported_count": unsupported_count,
    }
