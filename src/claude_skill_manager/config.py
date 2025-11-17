"""Configuration management for Claude Skill Manager."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from .models import SkillConfig


class ConfigManager:
    """Manages skill configuration files."""

    DEFAULT_CONFIG_PATH = ".claude/skill-sources.yaml"
    DEFAULT_SOURCE = "mojzis/marimo-template"

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the config manager.

        Args:
            project_root: Root directory of the project. If None, searches for .claude directory.
        """
        self.project_root = project_root or self._find_project_root()
        self.config_path = self.project_root / self.DEFAULT_CONFIG_PATH

    @staticmethod
    def _find_project_root() -> Path:
        """Find the project root by looking for .claude directory.

        Returns:
            Path to the project root.

        Raises:
            FileNotFoundError: If no .claude directory is found.
        """
        current = Path.cwd()
        while current != current.parent:
            claude_dir = current / ".claude"
            if claude_dir.exists() and claude_dir.is_dir():
                return current
            current = current.parent

        # If not found, return current working directory
        return Path.cwd()

    def load(self) -> SkillConfig:
        """Load configuration from file.

        Returns:
            SkillConfig object.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValidationError: If config is invalid.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        try:
            return SkillConfig(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}") from e

    def save(self, config: SkillConfig) -> None:
        """Save configuration to file.

        Args:
            config: SkillConfig object to save.
        """
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save as YAML
        data = config.model_dump(exclude_none=True)

        with open(self.config_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def init(self, default_source: Optional[str] = None) -> SkillConfig:
        """Initialize a new configuration file with defaults.

        Args:
            default_source: Default source repository. If None, uses DEFAULT_SOURCE.

        Returns:
            The initialized SkillConfig.

        Raises:
            FileExistsError: If config file already exists.
        """
        if self.config_path.exists():
            raise FileExistsError(f"Config file already exists: {self.config_path}")

        source = default_source or self.DEFAULT_SOURCE
        config = SkillConfig(
            default_source=source,
            allowed_sources=[source],
            aliases={},
        )

        self.save(config)
        return config

    def load_or_init(self, default_source: Optional[str] = None) -> SkillConfig:
        """Load existing config or initialize a new one.

        Args:
            default_source: Default source repository for initialization.

        Returns:
            The loaded or initialized SkillConfig.
        """
        try:
            return self.load()
        except FileNotFoundError:
            return self.init(default_source)

    def add_source(self, source: str) -> SkillConfig:
        """Add a new allowed source to the configuration.

        Args:
            source: Repository source in 'owner/repo' format.

        Returns:
            Updated SkillConfig.
        """
        config = self.load()

        if source not in config.allowed_sources:
            config.allowed_sources.append(source)
            self.save(config)

        return config

    def remove_source(self, source: str) -> SkillConfig:
        """Remove an allowed source from the configuration.

        Args:
            source: Repository source in 'owner/repo' format.

        Returns:
            Updated SkillConfig.

        Raises:
            ValueError: If trying to remove the default source.
        """
        config = self.load()

        if source == config.default_source:
            raise ValueError("Cannot remove the default source")

        if source in config.allowed_sources:
            config.allowed_sources.remove(source)
            self.save(config)

        return config

    def add_alias(self, alias: str, skill_name: str) -> SkillConfig:
        """Add a skill name alias.

        Args:
            alias: The alias name.
            skill_name: The actual skill name.

        Returns:
            Updated SkillConfig.
        """
        config = self.load()
        config.aliases[alias] = skill_name
        self.save(config)
        return config

    def resolve_alias(self, name: str) -> str:
        """Resolve an alias to its actual skill name.

        Args:
            name: Skill name or alias.

        Returns:
            The actual skill name (or the original name if no alias exists).
        """
        try:
            config = self.load()
            return config.aliases.get(name, name)
        except FileNotFoundError:
            return name

    def is_source_allowed(self, source: str) -> bool:
        """Check if a source is in the allowed sources list.

        Args:
            source: Repository source in 'owner/repo' format.

        Returns:
            True if the source is allowed, False otherwise.
        """
        try:
            config = self.load()
            return source in config.allowed_sources
        except FileNotFoundError:
            return False
