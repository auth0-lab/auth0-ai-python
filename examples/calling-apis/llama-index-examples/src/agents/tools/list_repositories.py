from github import Github
from github.GithubException import BadCredentialsException
from llama_index.core.tools import FunctionTool

from auth0_ai_llamaindex.token_vault import TokenVaultError, get_access_token_for_connection
from src.auth0.auth0_ai import with_github_access


def list_repositories_tool_function():
    access_token = get_access_token_for_connection()
    if not access_token:
        raise ValueError(
            "Authorization required to access the Token Vault connection")

    # GitHub SDK
    try:
        g = Github(access_token)
        user = g.get_user()
        repos = user.get_repos()
        repo_names = [repo.name for repo in repos]
        return repo_names
    except BadCredentialsException:
        raise TokenVaultError(
            "Authorization required to access the Token Vault connection")


list_github_repositories_tool = with_github_access(FunctionTool.from_defaults(
    name="list_github_repositories",
    description="List respositories for the current user on GitHub",
    fn=list_repositories_tool_function,
))
