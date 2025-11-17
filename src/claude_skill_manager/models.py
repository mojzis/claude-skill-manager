"""Data models for Claude Skill Manager."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillSource(BaseModel):
    """Represents a GitHub repository source for skills."""

    owner: str
    repo: str
    branch: str = "main"

    @property
    def full_name(self) -> str:
        """Return the full repository name."""
        return f"{self.owner}/{self.repo}"

    @classmethod
    def from_string(cls, source: str, branch: str = "main") -> "SkillSource":
        """Parse a source string like 'owner/repo' into a SkillSource."""
        parts = source.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid source format: {source}. Expected 'owner/repo'")
        return cls(owner=parts[0], repo=parts[1], branch=branch)

    def __str__(self) -> str:
        """Return string representation."""
        return self.full_name


class SkillConfig(BaseModel):
    """Configuration for skill sources and aliases."""

    default_source: str = Field(description="Default repository to fetch skills from")
    allowed_sources: list[str] = Field(
        default_factory=list, description="List of allowed repository sources"
    )
    aliases: dict[str, str] = Field(
        default_factory=dict, description="Skill name aliases"
    )

    @field_validator("allowed_sources")
    @classmethod
    def validate_sources(cls, v: list[str]) -> list[str]:
        """Validate that all sources are in 'owner/repo' format."""
        for source in v:
            parts = source.split("/")
            if len(parts) != 2:
                raise ValueError(f"Invalid source format: {source}. Expected 'owner/repo'")
        return v

    @field_validator("default_source")
    @classmethod
    def validate_default_source(cls, v: str) -> str:
        """Validate that default source is in 'owner/repo' format."""
        parts = v.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid source format: {v}. Expected 'owner/repo'")
        return v


class SkillMetadata(BaseModel):
    """Metadata for an installed skill."""

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    source: str = Field(description="Repository source of the skill")
    fetched_at: datetime = Field(description="When the skill was fetched")
    branch: str = Field(default="main", description="Branch the skill was fetched from")
    checksum: str = Field(description="SHA-256 checksum of the skill content")


class SkillsMetadata(BaseModel):
    """Collection of metadata for all installed skills."""

    skills: dict[str, SkillMetadata] = Field(default_factory=dict)


class Skill(BaseModel):
    """Represents a skill with its content and metadata."""

    name: str
    content: str
    source: str
    branch: str = "main"
    metadata: Optional[dict[str, str]] = None

    @property
    def filename(self) -> str:
        """Return the filename for this skill."""
        if self.name.endswith(".md"):
            return self.name
        return f"{self.name}.md"
