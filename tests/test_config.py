"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest

from claude_skill_manager.config import ConfigManager
from claude_skill_manager.models import SkillConfig


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        claude_dir = project_root / ".claude"
        claude_dir.mkdir()
        yield project_root


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_init_creates_config(self, temp_project):
        """Test initializing config creates file."""
        manager = ConfigManager(temp_project)
        config = manager.init()

        assert manager.config_path.exists()
        assert config.default_source == "mojzis/marimo-template"
        assert "mojzis/marimo-template" in config.allowed_sources

    def test_init_with_custom_source(self, temp_project):
        """Test initializing with custom source."""
        manager = ConfigManager(temp_project)
        config = manager.init("custom/repo")

        assert config.default_source == "custom/repo"
        assert "custom/repo" in config.allowed_sources

    def test_init_raises_if_exists(self, temp_project):
        """Test init raises error if config already exists."""
        manager = ConfigManager(temp_project)
        manager.init()

        with pytest.raises(FileExistsError):
            manager.init()

    def test_load_config(self, temp_project):
        """Test loading existing config."""
        manager = ConfigManager(temp_project)
        created_config = manager.init()

        loaded_config = manager.load()
        assert loaded_config.default_source == created_config.default_source

    def test_load_nonexistent_raises(self, temp_project):
        """Test loading nonexistent config raises error."""
        manager = ConfigManager(temp_project)

        with pytest.raises(FileNotFoundError):
            manager.load()

    def test_save_config(self, temp_project):
        """Test saving config."""
        manager = ConfigManager(temp_project)
        config = SkillConfig(
            default_source="owner/repo",
            allowed_sources=["owner/repo"],
        )

        manager.save(config)
        loaded = manager.load()

        assert loaded.default_source == "owner/repo"

    def test_add_source(self, temp_project):
        """Test adding a new source."""
        manager = ConfigManager(temp_project)
        manager.init()

        config = manager.add_source("new/repo")
        assert "new/repo" in config.allowed_sources

    def test_remove_source(self, temp_project):
        """Test removing a source."""
        manager = ConfigManager(temp_project)
        manager.init()
        manager.add_source("new/repo")

        config = manager.remove_source("new/repo")
        assert "new/repo" not in config.allowed_sources

    def test_remove_default_source_raises(self, temp_project):
        """Test removing default source raises error."""
        manager = ConfigManager(temp_project)
        config = manager.init()

        with pytest.raises(ValueError, match="Cannot remove the default source"):
            manager.remove_source(config.default_source)

    def test_add_alias(self, temp_project):
        """Test adding an alias."""
        manager = ConfigManager(temp_project)
        manager.init()

        config = manager.add_alias("marimo", "marimo-notebook")
        assert config.aliases["marimo"] == "marimo-notebook"

    def test_resolve_alias(self, temp_project):
        """Test resolving aliases."""
        manager = ConfigManager(temp_project)
        manager.init()
        manager.add_alias("marimo", "marimo-notebook")

        assert manager.resolve_alias("marimo") == "marimo-notebook"
        assert manager.resolve_alias("unknown") == "unknown"

    def test_is_source_allowed(self, temp_project):
        """Test checking if source is allowed."""
        manager = ConfigManager(temp_project)
        config = manager.init()

        assert manager.is_source_allowed(config.default_source)
        assert not manager.is_source_allowed("unknown/repo")
