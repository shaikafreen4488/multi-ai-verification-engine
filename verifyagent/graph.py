"""Orchestrates planner -> researcher -> coder -> verifier -> critic, with a
self-correction loop (max MAX_REVISIONS) when the critic asks for a revision.

Uses a plain LangGraph StateGraph. State is a dict passed between nodes; each
node is a thin wrapper around the corresponding agent module so the agent logic
stays independently testable.
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents import planner, researcher, coder, verifier, critic

MAX_REVISIONS = 2


class GraphState(TypedDict):
    task: str
    plan: Optional[dict]
    research: Optional[dict]
    code_result: Optional[dict]
    verification: Optional[dict]
    critique: Optional[dict]
    revisions: int
    trace: list
    final_status: Optional[str]  # accepted | rejected


def node_plan(state: GraphState) -> GraphState:
    plan = planner.run(state["task"])
    state["plan"] = plan
    state["trace"].append({"agent": "Planner", "output": plan})
    return state


def node_research(state: GraphState) -> GraphState:
    research = researcher.run(state["task"], state["plan"]["subtasks"])
    state["research"] = research
    state["trace"].append({"agent": "Researcher", "output": research})
    return state


def node_code(state: GraphState) -> GraphState:
    feedback = state["critique"]["reason"] if state.get("critique") else ""
    code_result = coder.run(state["task"], state["plan"]["subtasks"], feedback=feedback)
    state["code_result"] = code_result
    state["trace"].append({"agent": "Coder", "output": code_result})
    return state


def node_verify(state: GraphState) -> GraphState:
    v = verifier.run(state["task"], state["research"]["claims"], state["research"]["evidence"], state["code_result"])
    state["verification"] = v
    state["trace"].append({"agent": "Verifier", "output": v})
    return state


def node_critique(state: GraphState) -> GraphState:
    c = critic.run(state["task"], state["verification"])
    state["critique"] = c
    state["trace"].append({"agent": "Critic", "output": c})

    decision = c["decision"]
    if decision == "accept":
        state["final_status"] = "accepted"
    elif decision == "reject" or state["revisions"] >= MAX_REVISIONS:
        state["final_status"] = "rejected"
    else:
        state["revisions"] += 1
        state["final_status"] = None
    return state


def route_after_critique(state: GraphState) -> str:
    return "end" if state["final_status"] is not None else "revise"


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("plan", node_plan)
    g.add_node("research", node_research)
    g.add_node("code", node_code)
    g.add_node("verify", node_verify)
    g.add_node("critique", node_critique)

    g.set_entry_point("plan")
    g.add_edge("plan", "research")
    g.add_edge("research", "code")
    g.add_edge("code", "verify")
    g.add_edge("verify", "critique")
    g.add_conditional_edges("critique", route_after_critique, {"revise": "research", "end": END})

    return g.compile()


def run_pipeline(task: str) -> GraphState:
    graph = build_graph()
    initial_state: GraphState = {
        "task": task,
        "plan": None,
        "research": None,
        "code_result": None,
        "verification": None,
        "critique": None,
        "revisions": 0,
        "trace": [],
        "final_status": None,
    }
    return graph.invoke(initial_state)