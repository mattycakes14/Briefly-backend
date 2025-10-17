from typing import Any, Dict
import logging
import json
from arcadepy import Arcade
import os
from dotenv import load_dotenv

load_dotenv()

client = Arcade(os.getenv("ARCADE_API_KEY"))

async def node_github(owner: str, repo: str) -> Dict[str, Any]:
    logging.info("GitHub node started")

    # configuration
    USER_ID = "mlau191@uw.edu"
    TOOL_NAME = "Github.ListPullRequests"
    owner = "mattycakes14"
    repo = "mock_repo_frontend"
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
        "base": None,
        "repo": repo
    }
    response = client.tools.execute(
        tool_name=TOOL_NAME,
        input=tool_input,
        user_id=USER_ID,
    )
    logging.info(f"GitHub response: {response}")
    github_data = response.output.value
    
    # Parse if it's a JSON string
    if isinstance(github_data, str):
        github_data = json.loads(github_data)
    
    logging.info(f"GitHub response: {json.dumps(github_data)}")
    return {
        "github": github_data  # Return the dict
    }
