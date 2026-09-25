import json
import os
import streamlit as st
from graph import run_pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Verify Engine — Multi-Agent Reasoning & Verification", layout="wide")

st.title("🔎 Multi-Agent AI Reasoning & Verification Engine")
st.caption("Generation and verification are separated: independent agents fact-check, "
           "code-check, and contradiction-check every claim before it's accepted.")

with open(os.path.join(BASE_DIR, "eval_set.json")) as f:
    eval_set = json.load(f)

col1, col2 = st.columns([3, 1])
with col1:
    task_input = st.text_area("Task", placeholder="Type a task, or pick a preset from the eval set →")
with col2:
    preset_labels = ["(none)"] + [f"{e['category']}: {e['task'][:40]}..." for e in eval_set]
    choice = st.selectbox("Eval set presets", preset_labels)
    if choice != "(none)":
        task_input = eval_set[preset_labels.index(choice) - 1]["task"]

run_button = st.button("Run pipeline", type="primary")

if run_button and task_input.strip():
    with st.spinner("Running planner → researcher → coder → verifier → critic..."):
        try:
            result = run_pipeline(task_input)
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()

    status = result["final_status"]
    if status == "accepted":
        st.success(f"✅ ACCEPTED — confidence {result['verification']['confidence']}/100")
    else:
        st.error(f"❌ REJECTED after {result['revisions']} revision(s)")
        st.write(f"**Reason:** {result['critique']['reason']}")

    st.subheader("Decision & Audit Trail")
    tabs = st.tabs(["Summary", "Evidence", "Verification", "Revision History", "Raw Agent Trace"])

    with tabs[0]:
        st.markdown(f"**Plan ambiguity flagged:** {result['plan']['ambiguous']} — {result['plan']['ambiguity_note']}")
        st.markdown(f"**Subtasks:** {', '.join(result['plan']['subtasks'])}")
        st.markdown(f"**Task type:** {result['plan']['task_type']}")
        st.markdown(f"**Critic risk flags:** {result['critique']['risk_flags']}")
        st.markdown(f"**Critic decision:** `{result['critique']['decision']}`")

    with tabs[1]:
        st.markdown("**Claims and their sources:**")
        for c in result["research"]["claims"]:
            st.write(f"- {c['claim']}  \n  *source: {c['source']}*")
        st.markdown("**Raw evidence retrieved:**")
        for i, e in enumerate(result["research"]["evidence"]):
            st.write(f"[{i}] [{e['title']}]({e['url']}) — {e['snippet']}")

    with tabs[2]:
        st.markdown(f"**Overall confidence:** {result['verification']['confidence']}/100")
        st.markdown(f"**Contradiction detected:** {result['verification']['contradicted']}")
        st.markdown(f"**Unsupported claims:** {result['verification']['unsupported_count']}")
        st.markdown(f"**Code check:** {result['verification']['code_check']}")
        if result["code_result"] and result["code_result"]["needed"]:
            st.code(result["code_result"]["code"], language="python")
            st.json(result["code_result"]["execution"])
        st.markdown("**Per-claim verification:**")
        for v in result["verification"]["verifications"]:
            st.write(f"- {v}")

    with tabs[3]:
        st.markdown(f"**Revisions used:** {result['revisions']} / 2 max")
        for i, t in enumerate(result["trace"]):
            st.write(f"**Step {i+1}: {t['agent']}**")

    with tabs[4]:
        for t in result["trace"]:
            with st.expander(t["agent"]):
                st.json(t["output"] if isinstance(t["output"], dict) else {"raw": t["output"]})

elif run_button:
    st.warning("Enter a task or pick a preset first.")

st.divider()
st.caption("Architecture: Planner → Researcher (evidence grounding) → Coder (sandboxed exec) "
           "→ Verifier (independent check) → Critic (contradiction/risk gate) → self-correction loop (max 2).")