"""Skill installation and management."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml

from .fetcher import SkillFetcher
from .models import Skill, SkillMetadata, SkillsMetadata


class ConflictResolution(str, Enum):
    """How to handle conflicts when installing skills."""

    SKIP = "skip"
    OVERWRITE = "overwrite"
    PROMPT = "prompt"


class SkillInstaller:
    """Manages installation of skills into .claude/skills directory."""

    SKILLS_DIR = ".claude/skills"
    METADATA_FILE = ".metadata.yaml"

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the installer.

        Args:
            project_root: Root directory of the project. If None, searches for .claude directory.
        """
        self.project_root = project_root or self._find_project_root()
        self.skills_dir = self.project_root / self.SKILLS_DIR
        self.metadata_path = self.skills_dir / self.METADATA_FILE

    @staticmethod
    def _find_project_root() -> Path:
        """Find the project root by looking for .claude directory.

        Returns:
            Path to the project root.
        """
        current = Path.cwd()
        while current != current.parent:
            claude_dir = current / ".claude"
            if claude_dir.exists() and claude_dir.is_dir():
                return current
            current = current.parent

        # If not found, return current working directory
        return Path.cwd()

    def _ensure_skills_dir(self) -> None:
        """Ensure the skills directory exists."""
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> SkillsMetadata:
        """Load metadata from file.

        Returns:
            SkillsMetadata object.
        """
        if not self.metadata_path.exists():
            return SkillsMetadata(skills={})

        with open(self.metadata_path, "r") as f:
            data = yaml.safe_load(f) or {}

        return SkillsMetadata(**data)

    def _save_metadata(self, metadata: SkillsMetadata) -> None:
        """Save metadata to file.

        Args:
            metadata: SkillsMetadata object to save.
        """
        self._ensure_skills_dir()

        # Convert to dict for YAML serialization
        data = metadata.model_dump(mode="json")

        with open(self.metadata_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def install(
        self,
        skill: Skill,
        conflict_resolution: ConflictResolution = ConflictResolution.SKIP,
        fetcher: Optional[SkillFetcher] = None,
    ) -> bool:
        """Install a skill to the skills directory.

        Args:
            skill: The skill to install.
            conflict_resolution: How to handle conflicts.
            fetcher: Optional fetcher for computing checksums.

        Returns:
            True if installed, False if skipped.

        Raises:
            FileExistsError: If file exists and conflict_resolution is SKIP.
        """
        self._ensure_skills_dir()

        skill_path = self.skills_dir / skill.filename

        # Check for conflicts
        if skill_path.exists():
            if conflict_resolution == ConflictResolution.SKIP:
                return False
            elif conflict_resolution == ConflictResolution.PROMPT:
                raise FileExistsError(
                    f"Skill already exists: {skill.filename}. "
                    f"Use --overwrite to replace it."
                )

        # Write skill file
        with open(skill_path, "w") as f:
            f.write(skill.content)

        # Update metadata
        metadata = self._load_metadata()

        # Compute checksum
        checksum = (
            fetcher.compute_checksum(skill.content)
            if fetcher
            else SkillFetcher().compute_checksum(skill.content)
        )

        metadata.skills[skill.filename] = SkillMetadata(
            source=skill.source,
            fetched_at=datetime.now(),
            branch=skill.branch,
            checksum=checksum,
        )

        self._save_metadata(metadata)

        return True

    def remove(self, skill_name: str) -> bool:
        """Remove a skill from the skills directory.

        Args:
            skill_name: Name of the skill to remove (with or without .md extension).

        Returns:
            True if removed, False if not found.
        """
        # Ensure .md extension
        if not skill_name.endswith(".md"):
            skill_name = f"{skill_name}.md"

        skill_path = self.skills_dir / skill_name

        if not skill_path.exists():
            return False

        # Remove the file
        skill_path.unlink()

        # Update metadata
        metadata = self._load_metadata()
        if skill_name in metadata.skills:
            del metadata.skills[skill_name]
            self._save_metadata(metadata)

        return True

    def list_skills(self) -> dict[str, SkillMetadata]:
        """List all installed skills with their metadata.

        Returns:
            Dictionary mapping skill filenames to their metadata.
        """
        metadata = self._load_metadata()
        return metadata.skills

    def get_skill_info(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get metadata for a specific skill.

        Args:
            skill_name: Name of the skill (with or without .md extension).

        Returns:
            SkillMetadata if found, None otherwise.
        """
        # Ensure .md extension
        if not skill_name.endswith(".md"):
            skill_name = f"{skill_name}.md"

        metadata = self._load_metadata()
        return metadata.skills.get(skill_name)

    def is_installed(self, skill_name: str) -> bool:
        """Check if a skill is installed.

        Args:
            skill_name: Name of the skill (with or without .md extension).

        Returns:
            True if installed, False otherwise.
        """
        # Ensure .md extension
        if not skill_name.endswith(".md"):
            skill_name = f"{skill_name}.md"

        skill_path = self.skills_dir / skill_name
        return skill_path.exists()

    def needs_update(self, skill_name: str, new_checksum: str) -> bool:
        """Check if a skill needs updating.

        Args:
            skill_name: Name of the skill (with or without .md extension).
            new_checksum: Checksum of the new version.

        Returns:
            True if the skill exists and has a different checksum.
        """
        info = self.get_skill_info(skill_name)
        if not info:
            return False

        return info.checksum != new_checksum

    def get_all_skill_files(self) -> list[Path]:
        """Get all skill files in the skills directory.

        Returns:
            List of paths to skill files.
        """
        if not self.skills_dir.exists():
            return []

        return [
            f
            for f in self.skills_dir.iterdir()
            if f.is_file() and f.suffix == ".md" and f.name != self.METADATA_FILE
        ]
