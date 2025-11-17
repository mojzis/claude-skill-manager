"""Tests for skill fetcher."""

import pytest

from claude_skill_manager.fetcher import FetchError, SkillFetcher
from claude_skill_manager.models import SkillSource


class TestSkillFetcher:
    """Tests for SkillFetcher."""

    def test_build_url(self):
        """Test URL building."""
        fetcher = SkillFetcher()
        source = SkillSource(owner="owner", repo="repo", branch="main")

        url = fetcher._build_url(source, "skill-name")
        expected = "https://raw.githubusercontent.com/owner/repo/main/.claude/skills/skill-name.md"
        assert url == expected

    def test_build_url_with_md_extension(self):
        """Test URL building with .md extension already present."""
        fetcher = SkillFetcher()
        source = SkillSource(owner="owner", repo="repo", branch="main")

        url = fetcher._build_url(source, "skill-name.md")
        expected = "https://raw.githubusercontent.com/owner/repo/main/.claude/skills/skill-name.md"
        assert url == expected

    def test_compute_checksum(self):
        """Test checksum computation."""
        fetcher = SkillFetcher()
        content = "test content"
        checksum = fetcher.compute_checksum(content)

        # Checksum should be consistent
        assert checksum == fetcher.compute_checksum(content)
        # Should be SHA-256 hex (64 characters)
        assert len(checksum) == 64

    def test_validate_empty_content_raises(self):
        """Test validation raises on empty content."""
        fetcher = SkillFetcher()

        with pytest.raises(FetchError, match="empty"):
            fetcher._validate_content("", "http://example.com")

    def test_validate_large_content_raises(self):
        """Test validation raises on oversized content."""
        fetcher = SkillFetcher()
        large_content = "x" * (fetcher.MAX_FILE_SIZE + 1)

        with pytest.raises(FetchError, match="too large"):
            fetcher._validate_content(large_content, "http://example.com")

    def test_context_manager(self):
        """Test fetcher works as context manager."""
        with SkillFetcher() as fetcher:
            assert fetcher is not None
