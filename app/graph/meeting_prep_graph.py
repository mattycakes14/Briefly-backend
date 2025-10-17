from __future__ import annotations
from typing import Any, Dict, TypedDict
from langgraph.graph import StateGraph, END
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel
import logging
import asyncio
import json

# initialize dotenv
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# initialize openai client

class GraphState(TypedDict, total=False):
    transcript: str
    github: Dict[str, Any]
    jira: Dict[str, Any]
    summary: str
    classification: Dict[str, Any]

# TBD 
# class ClassifyRequest(TypedDict, total=False):
    
async def node_coordinator(state: GraphState) -> GraphState:
    # classify the request and execute certain nodes based on the classification
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    transcript = state.get("transcript", "")

    system_prompt = """You are a routing coordinator. Analyze the query and determine which data sources are needed. values are booleans.
        DATA SOURCES:
        - GitHub (is_git): PRs, commits, code reviews, deployments
        - Jira (is_jira): Tickets, blockers, tasks, sprint status
        - Meeting Notes (is_meeting_notes): Past discussions, decisions, agendas

        RULES:
        - Code/technical work → is_git
        - Tasks/blockers/status → is_jira
        - Past meetings/discussions → is_meeting_notes
        - General prep (e.g., "prep for standup") → ALL true
        - Multiple sources can be true

        EXAMPLES:
        "Prep me for standup" → all true
        "What PRs did I ship?" → is_git only
        "What's blocking us?" → is_jira only
        "What did Sarah mention?" → is_meeting_notes only
        "Status on auth feature?" → is_git + is_jira

        Output ONLY valid JSON:
        {
        "is_git": boolean,
        "is_jira": boolean,
        "is_meeting_notes": boolean,
        }
    """

    resp = await llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcript}
    ])
    state["classification"] = resp.content

    # Parse JSON; fall back safely
    try:
        parsed = json.loads(resp.content)
        logging.info(f"Parsed: {parsed}")
        result = {
            "is_git": bool(parsed.get("is_git", False)),
            "is_jira": bool(parsed.get("is_jira", False)),
            "is_meeting_notes": bool(parsed.get("is_meeting_notes", False)),
        }
    except Exception:
        result = {"is_git": False, "is_jira": False, "is_meeting_notes": False}
        logging.error(f"Error parsing JSON: {e}")
    state["classification"] = result
    return state

async def node_github(state: GraphState) -> GraphState:
    await asyncio.sleep(0.05)
    state["github"] = {
        "pull_requests": [
            {"title": "Add summarizer endpoint", "status": "merged", "number": 42},
            {"title": "Refactor auth middleware", "status": "open", "number": 57},
        ],
    }
    return state


async def node_jira(state: GraphState) -> GraphState:
    await asyncio.sleep(0.05)
    state["jira"] = {
        "assigned": [
            {"key": "BRF-101", "title": "Voice wake word bug", "status": "In Progress"},
            {"key": "BRF-88", "title": "Add meeting prep flow", "status": "Review"},
        ],
        "blockers": [
            {"key": "BRF-77", "title": "Auth feature blocked by OAuth redirect", "owner": "sarah"},
        ],
    }
    return state


async def node_synth(state: GraphState) -> GraphState:
    github = state.get("github", {})
    jira = state.get("jira", {})
    transcript = state.get("transcript")
    recent_prs = ", ".join(pr["title"] for pr in github.get("pull_requests", [])[:2])
    assigned = ", ".join(i["key"] for i in jira.get("assigned", [])[:2])
    top_blocker = (jira.get("blockers", [{}]) or [{}])[0].get("title", "None")
    base = (
        f"GitHub PRs: {recent_prs or 'none'}. "
        f"Jira assigned: {assigned or 'none'}. Top blocker: {top_blocker}."
    )
    if transcript:
        base += f" Transcript: {transcript}"
    state["summary"] = base
    return state


def build_meeting_prep_graph():
    graph = StateGraph(GraphState)
    graph.add_node("coordinator", node_coordinator)
    # graph.add_node("github", node_github)
    # graph.add_node("jira", node_jira)
    # graph.add_node("synth", node_synth)

    # # Run data fetch nodes in parallel, then synth
    graph.set_entry_point("coordinator")
    # graph.add_edge("coordinator", "github")
    # graph.add_edge("coordinator", "jira")
    # graph.add_edge("github", "synth")
    # graph.add_edge("jira", "synth")
    # graph.add_edge("synth", END)
    graph.add_edge("coordinator", END)
    return graph.compile()


