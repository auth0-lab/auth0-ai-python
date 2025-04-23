from github import Github
from github.GithubException import BadCredentialsException
from src.auth0.auth0_ai import with_github_access
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from auth0_ai_langchain.federated_connections import FederatedConnectionError, get_credentials_for_connection


class ListRepositoriesSchema(BaseModel):
    pass


def list_repositories_tool_function():
    credentials = get_credentials_for_connection()

    # GitHub SDK
    try:
        g = Github(credentials["access_token"])
        user = g.get_user()
        repos = user.get_repos()
        repo_names = [repo.name for repo in repos]
        return repo_names
    except BadCredentialsException:
        raise FederatedConnectionError(
            "Authorization required to access the Federated Connection API")


list_github_repositories_tool = with_github_access(StructuredTool(
    name="list_github_repositories",
    description="List respositories for the current user on GitHub",
    args_schema=ListRepositoriesSchema,
    func=list_repositories_tool_function,
))
