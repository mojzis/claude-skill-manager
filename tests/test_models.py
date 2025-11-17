"""Tests for data models."""

import pytest
from pydantic import ValidationError

from claude_skill_manager.models import SkillConfig, SkillSource


class TestSkillSource:
    """Tests for SkillSource model."""

    def test_from_string_valid(self):
        """Test parsing valid source string."""
        source = SkillSource.from_string("owner/repo")
        assert source.owner == "owner"
        assert source.repo == "repo"
        assert source.branch == "main"

    def test_from_string_with_branch(self):
        """Test parsing source with custom branch."""
        source = SkillSource.from_string("owner/repo", branch="develop")
        assert source.owner == "owner"
        assert source.repo == "repo"
        assert source.branch == "develop"

    def test_from_string_invalid(self):
        """Test parsing invalid source string."""
        with pytest.raises(ValueError, match="Invalid source format"):
            SkillSource.from_string("invalid")

    def test_full_name(self):
        """Test full_name property."""
        source = SkillSource(owner="owner", repo="repo")
        assert source.full_name == "owner/repo"

    def test_str(self):
        """Test string representation."""
        source = SkillSource(owner="owner", repo="repo")
        assert str(source) == "owner/repo"


class TestSkillConfig:
    """Tests for SkillConfig model."""

    def test_valid_config(self):
        """Test creating valid config."""
        config = SkillConfig(
            default_source="owner/repo",
            allowed_sources=["owner/repo", "another/repo"],
        )
        assert config.default_source == "owner/repo"
        assert len(config.allowed_sources) == 2

    def test_invalid_default_source(self):
        """Test invalid default source format."""
        with pytest.raises(ValidationError):
            SkillConfig(
                default_source="invalid",
                allowed_sources=["owner/repo"],
            )

    def test_invalid_allowed_source(self):
        """Test invalid allowed source format."""
        with pytest.raises(ValidationError):
            SkillConfig(
                default_source="owner/repo",
                allowed_sources=["invalid"],
            )

    def test_aliases(self):
        """Test aliases configuration."""
        config = SkillConfig(
            default_source="owner/repo",
            allowed_sources=["owner/repo"],
            aliases={"marimo": "marimo-notebook"},
        )
        assert config.aliases["marimo"] == "marimo-notebook"
