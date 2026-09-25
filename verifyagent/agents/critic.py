from tools.llm import chat

SYSTEM = """You are the CRITIC agent, the final quality gate before an answer ships.
Given the verifier's findings, decide if the overall output is reliable enough to
accept. Accept confidently-verified, well-established facts even with modest
evidence, as long as there is no contradiction and confidence is reasonable
(60+). Reserve "revise" or "reject" for cases with an actual contradiction,
a failed code check, or very low confidence (under 40) on a specific/surprising
claim. Do not reject well-known facts just because search evidence is thin.

Respond in this exact format:
DECISION: accept|revise|reject
RISK_FLAGS: <comma-separated list, or "none">
REASON: <one or two sentences, this will be shown to the end user if rejected>
"""
def run(task: str, verifier_result: dict) -> dict:
    user_msg = (
        f"Task: {task}\n"
        f"Verifier confidence: {verifier_result['confidence']}\n"
        f"Contradicted: {verifier_result['contradicted']}\n"
        f"Unsupported claim count: {verifier_result['unsupported_count']}\n"
        f"Code check: {verifier_result['code_check']}\n"
        f"Raw verifier notes:\n{verifier_result['raw']}"
    )
    raw = chat(SYSTEM, user_msg, temperature=0.0)

    decision = "revise"
    if "DECISION:" in raw:
        decision = raw.split("DECISION:")[1].split("\n")[0].strip().lower()
    reason = raw.split("REASON:")[1].strip() if "REASON:" in raw else "No reason provided."
    risk_flags = raw.split("RISK_FLAGS:")[1].split("\n")[0].strip() if "RISK_FLAGS:" in raw else "none"

    return {"raw": raw, "decision": decision, "reason": reason, "risk_flags": risk_flags}
