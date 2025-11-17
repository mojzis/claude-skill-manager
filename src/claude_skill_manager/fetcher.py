"""GitHub skill fetcher with retry logic and validation."""

import hashlib
import time
from typing import Optional

import httpx
import frontmatter

from .models import Skill, SkillSource


class FetchError(Exception):
    """Error raised when fetching a skill fails."""

    pass


class SkillFetcher:
    """Fetches skills from GitHub repositories."""

    # Maximum file size: 1MB
    MAX_FILE_SIZE = 1024 * 1024

    # Retry configuration
    MAX_RETRIES = 4
    INITIAL_RETRY_DELAY = 2.0

    def __init__(self, github_token: Optional[str] = None):
        """Initialize the fetcher.

        Args:
            github_token: Optional GitHub personal access token for private repos.
        """
        self.github_token = github_token
        self.client = httpx.Client(
            timeout=30.0,
            headers=self._build_headers(),
            follow_redirects=True,
        )

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for requests."""
        headers = {
            "User-Agent": "claude-skill-manager/0.1.0",
            "Accept": "text/plain, text/markdown, */*",
        }

        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        return headers

    def _build_url(self, source: SkillSource, skill_name: str) -> str:
        """Build the raw GitHub URL for a skill.

        Args:
            source: The skill source repository.
            skill_name: Name of the skill file (with or without .md extension).

        Returns:
            The raw GitHub URL.
        """
        # Ensure skill name has .md extension
        if not skill_name.endswith(".md"):
            skill_name = f"{skill_name}.md"

        return (
            f"https://raw.githubusercontent.com/{source.owner}/{source.repo}/"
            f"{source.branch}/.claude/skills/{skill_name}"
        )

    def _validate_content(self, content: str, url: str) -> None:
        """Validate the fetched content.

        Args:
            content: The fetched content.
            url: The URL the content was fetched from.

        Raises:
            FetchError: If validation fails.
        """
        # Check size
        if len(content) > self.MAX_FILE_SIZE:
            raise FetchError(
                f"File too large: {len(content)} bytes (max {self.MAX_FILE_SIZE})"
            )

        # Check if content is empty
        if not content.strip():
            raise FetchError("Fetched content is empty")

        # Try to parse as markdown with frontmatter
        try:
            frontmatter.loads(content)
        except Exception as e:
            # If frontmatter parsing fails, that's okay - not all skills need frontmatter
            # Just check if it looks like markdown
            if not any(line.strip() for line in content.split("\n")):
                raise FetchError(f"Content does not appear to be valid: {e}") from e

    def fetch(
        self, skill_name: str, source: SkillSource, validate: bool = True
    ) -> Skill:
        """Fetch a skill from GitHub.

        Args:
            skill_name: Name of the skill to fetch.
            source: The source repository.
            validate: Whether to validate the content.

        Returns:
            The fetched Skill object.

        Raises:
            FetchError: If fetching fails.
        """
        url = self._build_url(source, skill_name)

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.get(url)

                # Handle different status codes
                if response.status_code == 200:
                    content = response.text

                    if validate:
                        self._validate_content(content, url)

                    # Parse frontmatter if present
                    parsed = frontmatter.loads(content)
                    metadata = dict(parsed.metadata) if parsed.metadata else None

                    return Skill(
                        name=skill_name,
                        content=content,
                        source=source.full_name,
                        branch=source.branch,
                        metadata=metadata,
                    )

                elif response.status_code == 404:
                    raise FetchError(
                        f"Skill not found: {skill_name} in {source.full_name} "
                        f"(branch: {source.branch})"
                    )

                elif response.status_code == 403:
                    raise FetchError(
                        f"Access forbidden. The repository might be private. "
                        f"Try setting a GitHub token."
                    )

                else:
                    # Retry on server errors
                    if response.status_code >= 500:
                        last_error = FetchError(
                            f"Server error: {response.status_code}"
                        )
                    else:
                        raise FetchError(
                            f"Unexpected status code: {response.status_code}"
                        )

            except httpx.RequestError as e:
                last_error = FetchError(f"Network error: {e}")

            # Wait before retry (exponential backoff)
            if attempt < self.MAX_RETRIES - 1:
                delay = self.INITIAL_RETRY_DELAY * (2**attempt)
                time.sleep(delay)

        # All retries failed
        if last_error:
            raise last_error
        raise FetchError("Failed to fetch skill after all retries")

    def compute_checksum(self, content: str) -> str:
        """Compute SHA-256 checksum of content.

        Args:
            content: The content to hash.

        Returns:
            Hex digest of the SHA-256 hash.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "SkillFetcher":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()
