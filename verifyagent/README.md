# Verify Engine — Multi-Agent AI Reasoning & Verification Engine

**Theme 8 submission.** A multi-agent system where specialized agents collaborate
to answer a task, and every important output is independently verified — for
factual grounding, code correctness, and logical consistency — before it's
accepted. Generation and verification are handled by separate agents so the
system can catch its own hallucinations, unsupported claims, and unsafe actions
instead of trusting its first draft.

## Live Deployment

🔗 **Deployment URL:** _[fill in after deploying — see Deployment section]_

## Team

- _[Name(s) / roll numbers / emails — fill in]_

## Architecture

```
User Task
   │
   ▼
[Planner] ── flags ambiguity, breaks task into subtasks
   │
   ▼
[Researcher] ── retrieves evidence (web search), links claims → sources
   │
   ▼
[Coder/Tool] ── writes + runs code in a sandboxed subprocess (if needed)
   │
   ▼
[Verifier] ── INDEPENDENT agent: checks claims against evidence,
   │           re-checks code execution, flags contradictions
   ▼
[Critic] ── contradiction/risk gate: accept / revise / reject,
   │         produces confidence score + risk flags
   ▼
 ┌─────────────┐
 │ accept?     │──yes──▶ Final answer + full audit trail shown to user
 │ revise?     │──────▶ loop back to Researcher/Coder with feedback (max 2x)
 │ reject?     │──────▶ Rejected, with stated reason (no unreliable answer shipped)
 └─────────────┘
```

**Separation of generation vs. verification:** the Researcher and Coder generate
content; the Verifier and Critic never generate new claims — they only check
what's already been produced, using the evidence and (re-run) code execution as
ground truth. This is deliberate: a single agent grading its own homework is
exactly the failure mode this system is built to avoid.

### Agent responsibilities

| Agent | Responsibility |
|---|---|
| Planner | Decomposes task, explicitly flags ambiguous/underspecified requests |
| Researcher | Retrieves evidence (DuckDuckGo search), grounds each claim to a source |
| Coder/Tool | Writes code for computational tasks, executes it in a sandboxed subprocess |
| Verifier | Independently checks claims vs. evidence and re-verifies code output |
| Critic | Detects contradictions/unsupported claims, computes confidence, decides accept/revise/reject |

### Handling ambiguous, incomplete, conflicting, and misleading input

- **Ambiguous** — Planner explicitly flags this before any work starts.
- **Incomplete** — Researcher marks claims `UNSUPPORTED` when no evidence backs them; Critic factors this into the reject/revise decision instead of letting the answer through.
- **Conflicting** — Verifier is prompted to flag `contradicted` when evidence disagrees with a claim (or with itself), surfaced in the audit trail rather than silently picking one side.
- **Misleading** — Because the Verifier is a separate, skeptical-by-default agent (not the one that produced the claim), it's checked against retrieved evidence instead of the generator's own confidence.

### Self-correction loop

If the Critic returns `revise`, the pipeline loops back to Researcher → Coder
with the Critic's reason as feedback, up to **2 revisions**. If still not
reliable, the task is **rejected** with the stated reason rather than shipping
a low-confidence answer — this is the "decline unreliable conclusions"
requirement.

### Decision & Audit Layer

The Streamlit UI (`app.py`) shows, for every run: the plan and ambiguity flag,
all evidence with sources, per-claim verification status, contradiction/
unsupported-claim flags, the confidence score, revision history, and — on
rejection — the exact reason.

## Setup

```bash
git clone <this-repo-url>
cd verifyagent
pip install -r requirements.txt
```

Get a **free** Groq API key at https://console.groq.com/keys (no card required),
then either:

```bash
export GROQ_API_KEY="your-key-here"
```

or add it to `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your-key-here"
```

Run locally:

```bash
streamlit run app.py
```

## Deployment (Streamlit Community Cloud — free)

1. Push this repo to a **public** GitHub repo.
2. Go to https://share.streamlit.io → "New app" → select the repo, branch `main`, file `app.py`.
3. In the app's "Secrets" settings, add `GROQ_API_KEY = "your-key-here"`.
4. Deploy. Copy the resulting URL into this README's "Live Deployment" section above.

## Evaluation Set

`eval_set.json` contains 8 hand-crafted test cases covering ambiguous,
incomplete, conflicting, misleading, computational, factual, code, and
unsafe-action categories. Selectable from a dropdown in the UI for live demo.

## Known limitations (honest, for the judges)

- Evidence retrieval uses free DuckDuckGo search; no paid/authenticated data sources.
- Sandboxing is a subprocess with a timeout, not a full containerized sandbox — sufficient to catch incorrect/unsafe code for this scope, not hardened for production.
- Confidence scoring is LLM-self-reported by the Verifier rather than a calibrated statistical model — noted as a direction for future work.
