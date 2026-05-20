"""Client GitHub REST API v3."""

import httpx

from pman.config import settings


class GitHubClient:
    """Wrapper per GitHub REST API."""

    def __init__(self, token: str | None = None, base_url: str = "https://api.github.com"):
        self.token = token or settings.github_token
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def get_repos(self, username: str | None = None) -> list[dict]:
        """Lista repo dell'utente autenticato o di uno specifico username."""
        target = username or "user"
        url = f"{self.base_url}/users/{target}/repos" if username else f"{self.base_url}/user/repos"
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    async def get_issues(self, owner: str, repo: str, state: str = "open") -> list[dict]:
        """Lista issues di un repo."""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues?state={state}"
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    async def get_pulls(self, owner: str, repo: str, state: str = "open") -> list[dict]:
        """Lista PR di un repo."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls?state={state}"
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
