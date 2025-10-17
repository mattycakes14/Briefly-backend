from __future__ import annotations
from typing import Any, Dict, TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel
import logging
import asyncio
import json
import operator
from arcadepy import Arcade
from langchain_anthropic import ChatAnthropic

llm_synthesis = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
# initialize dotenv
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# initialize arcadepy client
client = Arcade()  # Automatically finds the `ARCADE_API_KEY` env variable

class GraphState(TypedDict, total=False):
    transcript: str
    github: Annotated[Dict[str, Any], operator.or_]  # Merge concurrent updates
    jira: Annotated[Dict[str, Any], operator.or_]
    summary: str
    classification: Dict[str, Any]
    targets: List[str]
    meeting_notes: Dict[str, Any]
    
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
    
    # determine which nodes to run
    cls = state.get("classification", {}) or {}
    targets = []
    if cls.get("is_git"): targets.append("github")
    if cls.get("is_jira"): targets.append("jira")

    if not targets:
        targets.append("synth")

    state["targets"] = targets

    return state

async def node_github(state: GraphState) -> Dict[str, Any]:
    logging.info("GitHub node started")

    # configuration (facebook repo)
    USER_ID = "mlau191@uw.edu"
    TOOL_NAME = "Github.ListPullRequests"
    owner = "facebook"
    repo = "react"
    state = "open"

    auth_response = client.tools.authorize(
        tool_name=TOOL_NAME,
        user_id=USER_ID,
    )
    if auth_response.status != "completed":
        print(f"Click this link to authorize: {auth_response.url}")
    
    
    client.auth.wait_for_completion(auth_response)
    tool_input = {
        "owner": owner,
        "repo": repo,
        "state": state,
        "per_page": 5,
    }
    response = client.tools.execute(
        tool_name=TOOL_NAME,
        input=tool_input,
        user_id=USER_ID,
    )

    github_data = response.output.value
    
    # Parse if it's a JSON string
    if isinstance(github_data, str):
        github_data = json.loads(github_data)
    
    # Fallback to empty dict if null/None
    if github_data is None:
        github_data = {"pull_requests": []}
    
    logging.info(f"GitHub response parsed successfully")
    logging.info(f"Total PRs found: {len(github_data.get('pull_requests', []))}")
    
    # Log each PR
    for pr in github_data.get('pull_requests', []):
        logging.info(f"PR #{pr['number']}: {pr['title']} (State: {pr['state']})")
    
    return {
        "github": github_data
    }


async def node_jira(state: GraphState) -> Dict[str, Any]:
    logging.info("Jira node started")
    
    # hardcoded for demo (input)
    jira_website = "https://uw-team-eg624ru3.atlassian.net/rest/api/3/search"
    assignee = "mlau191@uw.edu"
    project = "briefly"
    keyword = "bug"
    atlassian_cloud_id = "a3c0ae94-18ac-4e5b-a511-6fa2460c8c35"
    limit = 10
    due_from = "2025-01-01"
    status = "In Progress"

    USER_ID = "mlau191@uw.edu"  # Unique identifier for your user (email, UUID, etc.)
    TOOL_NAME = "Jira.GetIssuesWithoutId"

    auth_response = client.tools.authorize(tool_name=TOOL_NAME, user_id=USER_ID)

    if auth_response.status != "completed":
        print(f"Click this link to authorize: {auth_response.url}")

    # Wait for the authorization to complete
    client.auth.wait_for_completion(auth_response)

    tool_input = {
        "status": status,
        "assignee": assignee,
        "project": project,
        "limit": limit,
        "atlassian_cloud_id": atlassian_cloud_id,
    }

    response = client.tools.execute(
        tool_name=TOOL_NAME,
        input=tool_input,
        user_id=USER_ID,
    )
    final_response = response.output.value  # Already a dict, no need for json.dumps
    logging.info(f"Jira response: {json.dumps(final_response)}")  # Log as JSON string for readability

    # parse the response
    parsed = []

    issues = final_response.get("issues", [])
    for issue in issues:
        # Basic info
        key = issue["key"]                           # "OPS-5"
        title = issue["title"]                       # "(Sample) Credit Card Payment"
        status = issue["status"]["name"]             # "In Progress"
        
        # Priority (can be null)
        priority = issue.get("priority")
        priority_name = priority["name"] if priority else "No Priority"
        
        # Assignee
        assignee = issue["assignee"]
        assignee_name = assignee["name"]             # "Matt Lau"
        assignee_email = assignee["email"]           # "mlau191@uw.edu"
        
        # Description (HTML format)
        description = issue["description"]           # "<p>Create a secure payment...</p>"
        
        # Parent Epic (can be null)
        parent = issue.get("parent")
        parent_key = parent["key"] if parent else None      # "OPS-2"
        parent_title = parent["title"] if parent else None  # "(Sample) Payment Processing"
        
        # Dates
        created = issue["created"]                   # "2025-10-16T18:50:36.559-0700"
        
        # URLs
        jira_url = issue["jira_gui_url"]            # Direct link to issue
        
        # Project
        project_name = issue["project"]["name"]      # "briefly"
        project_key = issue["project"]["key"]        # "OPS"
        
        # Build clean dict
        parsed.append({
            "key": key,
            "title": title,
            "status": status,
            "priority": priority_name,
            "assignee": assignee_name,
            "description": description,
            "parent_epic": parent_key,
            "created": created,
            "url": jira_url
        })
    
    logging.info(f"Parsed {len(parsed)} Jira issues")
    
    return {
        "jira": {"issues": parsed}
    }

async def node_meeting_notes(state: GraphState) -> Dict[str, Any]:
    USER_ID = "mlau191@uw.edu"
    TOOL_NAME = "NotionToolkit.GetPageContentByTitle"

    auth_response = client.tools.authorize(
        tool_name=TOOL_NAME,
        user_id=USER_ID,
    )

    if auth_response.status != "completed":
        print(f"Click this link to authorize: {auth_response.url}")

    # Wait for the authorization to complete
    client.auth.wait_for_completion(auth_response)

    tool_input = {
        "title": "Meeting Notes"
    }

    response = client.tools.execute(
        tool_name=TOOL_NAME,
        input=tool_input,
        user_id=USER_ID,
    )
    meeting_notes = response.output.value
    logging.info(f"Meeting notes: {meeting_notes}")

    return {
        "meeting_notes": meeting_notes
    }

async def node_synth(state: GraphState) -> Dict[str, Any]:
    logging.info("Synthesis node started")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=1)

    github = state.get("github", {})
    jira = state.get("jira", {})
    transcript = state.get("transcript")
    meeting_notes = state.get("meeting_notes")

    # Format GitHub PRs into a readable string
    github_string = ""
    if github:
        pr_list = github.get("pull_requests", [])
        if pr_list:
            lines = [f"GitHub - Found {len(pr_list)} pull request(s):"]
            for idx, pr in enumerate(pr_list, 1):
                lines.append(f"  {idx}. PR #{pr['number']}: {pr['title']}")
                lines.append(f"     State: {pr['state']}, Author: {pr['user']}")
                lines.append(f"     URL: {pr['html_url']}")
            github_string = "\n".join(lines)
        else:
            github_string = "GitHub - No pull requests found."
    else:
        github_string = "GitHub - No data available."
    
    # Format Jira issues into a readable string
    jira_string = ""
    if jira:
        jira_issues = jira.get("issues", [])
        if jira_issues:
            lines = [f"Jira - Found {len(jira_issues)} issue(s):"]
            for idx, issue in enumerate(jira_issues, 1):
                lines.append(f"  {idx}. {issue['key']}: {issue['title']}")
                lines.append(f"     Status: {issue['status']}, Priority: {issue['priority']}")
                lines.append(f"     Assignee: {issue['assignee']}")
                if issue.get('parent_epic'):
                    lines.append(f"     Epic: {issue['parent_epic']}")
                lines.append(f"     URL: {issue['url']}")
            jira_string = "\n".join(lines)
        else:
            jira_string = "Jira - No issues found."
    else:
        jira_string = "Jira - No data available."
    
    # Combine everything into a summary
    summary_parts = []
    summary_parts.append(f"Meeting Prep Summary for: '{transcript}'\n")
    summary_parts.append("=" * 50)
    if github_string:
        summary_parts.append(github_string)
    if jira_string:
        summary_parts.append(jira_string)
    
    if meeting_notes:
        summary_parts.append(meeting_notes)
    else:
        summary_parts.append("Meeting notes - No data available.")
    
    final_summary = "\n\n".join(summary_parts)
    logging.info(f"Generated summary:\n{final_summary}")

    # Aggregate into synthesizer llm
    system_prompt = """
    You are a personal meeting preparation assistant for software developers. Your job is to prepare one individual for their upcoming meeting by turning information from GitHub PRs, Jira issues, and meeting notes into a 30–60 second voice-friendly briefing (120–180 words max).

Your output should:

Speak directly to one person using second person (you, your).

Focus only on what they need to say, ask, or be ready for.

Use short, natural sentences (15–20 words max).

Be clear, personal, and conversational — like a teammate prepping them quickly.

Limit to 3 major topics. Summarize minor details without listing too much.

Structure your briefing in three parts:

Start with the most important update or action item.

Add key supporting items, connecting related Jira tickets, PRs, or notes together.

End with what they should anticipate, bring up, or answer.

Voice Style Rules:

Use contractions (you’re, it’s, they’ll).

Say “your ticket OPS-7” once, then just “that ticket.”

Never say URLs aloud.

Avoid technical jargon unless essential.

No bullet points or formatting.

Tone:

Personal, coaching, and action-oriented.

Use phrases like “Here’s what you need to know,” “You’ll want to mention,” “Be ready to talk about.”

Avoid team-wide language or generic statements.

Examples:
✅ “You’ll want to mention your blocker on OPS-7.”
❌ “We need to discuss the blocker on OPS-7.”

✅ “Be ready to answer questions about the auth PR.”
❌ “The team should review the auth PR.”

✅ “You shipped two PRs yesterday — lead with that.”
❌ “Let’s celebrate shipping two PRs.”
"""
    resp = await llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": final_summary}
    ])
    return {"summary": resp.content}

def select_targets(state: GraphState) -> list[str]:
    """Return list of target nodes based on classification."""
    cls = state.get("classification", {}) or {}
    targets = []
    if cls.get("is_git"):
        targets.append("github")
    if cls.get("is_jira"):
        targets.append("jira")
    if cls.get("is_meeting_notes"):
        targets.append("meeting_notes")

    # If nothing selected, go straight to synth
    if not targets:
        targets.append("synth")
    return targets


def build_meeting_prep_graph():
    graph = StateGraph(GraphState)
    graph.add_node("coordinator", node_coordinator)
    graph.add_node("github", node_github)
    graph.add_node("jira", node_jira)
    graph.add_node("synth", node_synth)
    graph.add_node("meeting_notes", node_meeting_notes)

    graph.set_entry_point("coordinator")
    
    # Conditional fan-out based on classification
    graph.add_conditional_edges(
        "coordinator",
        select_targets,
        {
            "github": "github",
            "jira": "jira",
            "synth": "synth",
            "meeting_notes": "meeting_notes",
        }
    )
    
    # Join at synth
    graph.add_edge("github", "synth")
    graph.add_edge("jira", "synth")
    graph.add_edge("meeting_notes", "synth")
    graph.add_edge("synth", END)
    
    return graph.compile()


