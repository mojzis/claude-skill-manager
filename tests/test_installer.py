"""Tests for skill installer."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from claude_skill_manager.installer import ConflictResolution, SkillInstaller
from claude_skill_manager.models import Skill


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        claude_dir = project_root / ".claude"
        claude_dir.mkdir()
        yield project_root


@pytest.fixture
def sample_skill():
    """Create a sample skill for testing."""
    return Skill(
        name="test-skill",
        content="# Test Skill\n\nThis is a test skill.",
        source="owner/repo",
        branch="main",
    )


class TestSkillInstaller:
    """Tests for SkillInstaller."""

    def test_install_creates_directory(self, temp_project, sample_skill):
        """Test installation creates skills directory."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        assert installer.skills_dir.exists()
        assert (installer.skills_dir / "test-skill.md").exists()

    def test_install_writes_content(self, temp_project, sample_skill):
        """Test installation writes correct content."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        content = (installer.skills_dir / "test-skill.md").read_text()
        assert content == sample_skill.content

    def test_install_creates_metadata(self, temp_project, sample_skill):
        """Test installation creates metadata file."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        assert installer.metadata_path.exists()
        metadata = installer._load_metadata()
        assert "test-skill.md" in metadata.skills

    def test_install_skip_on_conflict(self, temp_project, sample_skill):
        """Test skip behavior on conflict."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        # Try to install again with skip
        installed = installer.install(sample_skill, ConflictResolution.SKIP)
        assert not installed

    def test_install_overwrite_on_conflict(self, temp_project, sample_skill):
        """Test overwrite behavior on conflict."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        # Modify and reinstall with overwrite
        modified_skill = Skill(
            name="test-skill",
            content="# Modified Content",
            source="owner/repo",
            branch="main",
        )
        installed = installer.install(modified_skill, ConflictResolution.OVERWRITE)
        assert installed

        content = (installer.skills_dir / "test-skill.md").read_text()
        assert content == "# Modified Content"

    def test_remove_skill(self, temp_project, sample_skill):
        """Test removing a skill."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        assert installer.remove("test-skill")
        assert not (installer.skills_dir / "test-skill.md").exists()

    def test_remove_nonexistent(self, temp_project):
        """Test removing nonexistent skill."""
        installer = SkillInstaller(temp_project)
        assert not installer.remove("nonexistent")

    def test_list_skills(self, temp_project, sample_skill):
        """Test listing installed skills."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        skills = installer.list_skills()
        assert "test-skill.md" in skills
        assert skills["test-skill.md"].source == "owner/repo"

    def test_is_installed(self, temp_project, sample_skill):
        """Test checking if skill is installed."""
        installer = SkillInstaller(temp_project)

        assert not installer.is_installed("test-skill")
        installer.install(sample_skill)
        assert installer.is_installed("test-skill")

    def test_get_skill_info(self, temp_project, sample_skill):
        """Test getting skill metadata."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        info = installer.get_skill_info("test-skill")
        assert info is not None
        assert info.source == "owner/repo"
        assert info.branch == "main"

    def test_needs_update(self, temp_project, sample_skill):
        """Test checking if skill needs update."""
        installer = SkillInstaller(temp_project)
        installer.install(sample_skill)

        # Same checksum - no update needed
        info = installer.get_skill_info("test-skill")
        assert not installer.needs_update("test-skill", info.checksum)

        # Different checksum - update needed
        assert installer.needs_update("test-skill", "different-checksum")
