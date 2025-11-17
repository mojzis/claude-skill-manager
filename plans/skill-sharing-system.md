# Skill Sharing System - Implementation Plan

## Overview

Create a Python library that enables sharing and managing Claude Code skills across projects, with version control and easy updates.

## Goals

1. **Easy Distribution**: Share skills via GitHub repositories
2. **Simple Installation**: Single command to fetch and install skills
3. **Version Control**: Support for updating skills to newer versions
4. **Security**: Configurable allowed sources to prevent unauthorized skill fetching
5. **Developer Experience**: Clean CLI interface using Typer

## Architecture

### Components

```
claude-skill-manager/
├── src/
│   └── claude_skill_manager/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI commands
│       ├── fetcher.py          # GitHub API/raw content fetching
│       ├── config.py           # Configuration management
│       ├── installer.py        # Skill installation logic
│       └── models.py           # Data models (SkillSource, Skill, etc.)
├── tests/
│   ├── test_cli.py
│   ├── test_fetcher.py
│   ├── test_config.py
│   └── test_installer.py
├── pyproject.toml
└── README.md
```

## Implementation Phases

### Phase 1: Core Library Structure

**Goal**: Set up the Python package with basic structure

**Tasks**:
- [ ] Create new Python package `claude-skill-manager`
- [ ] Set up pyproject.toml with dependencies:
  - `typer` - CLI framework
  - `rich` - Beautiful CLI output
  - `httpx` - HTTP client for fetching
  - `pydantic` - Configuration validation
  - `pyyaml` - Configuration file parsing
- [ ] Create basic package structure with `__init__.py`
- [ ] Set up development dependencies (pytest, mypy, ruff)

### Phase 2: Configuration System

**Goal**: Allow users to configure allowed skill sources

**Configuration File**: `.claude/skill-sources.yaml`

```yaml
# Default configuration
default_source: "mojzis/marimo-template"

# Allowed sources - for security
allowed_sources:
  - "mojzis/marimo-template"
  - "username/other-repo"
  - "org/skills-repo"

# Optional: skill aliases
aliases:
  marimo: "marimo-notebook"
  pandas: "pandas-best-practices"
```

**Tasks**:
- [ ] Create `config.py` with Pydantic models for configuration
- [ ] Implement config file reading/writing
- [ ] Support for default source
- [ ] Validation of allowed sources
- [ ] Optional alias system

**Models**:
```python
class SkillSource(BaseModel):
    owner: str
    repo: str
    branch: str = "main"

    @property
    def full_name(self) -> str:
        return f"{owner}/{repo}"

class SkillConfig(BaseModel):
    default_source: str
    allowed_sources: list[str]
    aliases: dict[str, str] = {}
```

### Phase 3: GitHub Fetcher

**Goal**: Fetch skills from GitHub repositories safely

**Approach**: Use GitHub's raw content API (no authentication needed for public repos)

**URL Pattern**:
```
https://raw.githubusercontent.com/{owner}/{repo}/{branch}/.claude/skills/{skill_name}.md
```

**Tasks**:
- [ ] Create `fetcher.py` with GitHub fetching logic
- [ ] Implement retry logic with exponential backoff
- [ ] Support for both public and private repos (with token)
- [ ] Validate source against allowed_sources list
- [ ] Parse skill metadata from frontmatter
- [ ] Cache fetched skills temporarily

**Security Considerations**:
- Validate source is in allowed_sources before fetching
- Use HTTPS only
- Validate file content is markdown
- Check file size limits (prevent DOS)
- Optional: verify checksums/signatures (future enhancement)

### Phase 4: Skill Installation

**Goal**: Install fetched skills into `.claude/skills/` directory

**Tasks**:
- [ ] Create `installer.py` with installation logic
- [ ] Detect project root (look for `.claude` directory)
- [ ] Create `.claude/skills/` if it doesn't exist
- [ ] Write skill file with proper formatting
- [ ] Handle conflicts (skip, overwrite, or prompt)
- [ ] Track skill metadata (source, version, fetch date)

**Metadata Tracking**: `.claude/skills/.metadata.yaml`
```yaml
skills:
  marimo-notebook.md:
    source: "mojzis/marimo-template"
    fetched_at: "2025-11-17T10:30:00Z"
    branch: "main"
    checksum: "sha256:..."

  pandas-best-practices.md:
    source: "mojzis/marimo-template"
    fetched_at: "2025-11-17T10:31:00Z"
    branch: "main"
    checksum: "sha256:..."
```

### Phase 5: CLI Commands

**Goal**: Provide intuitive CLI using Typer

**Commands**:

```bash
# Fetch a skill from default source
claude-skills fetch marimo-notebook

# Fetch from specific source
claude-skills fetch marimo-notebook mojzis/marimo-template

# Fetch from specific branch
claude-skills fetch marimo-notebook mojzis/marimo-template --branch develop

# List installed skills with metadata
claude-skills list

# Update a skill to latest version
claude-skills update marimo-notebook

# Update all skills
claude-skills update --all

# Remove a skill
claude-skills remove marimo-notebook

# Initialize configuration in a project
claude-skills init

# Add a new allowed source
claude-skills source add username/repo
```

**Tasks**:
- [ ] Create `cli.py` with Typer app
- [ ] Implement `fetch` command
- [ ] Implement `list` command
- [ ] Implement `update` command
- [ ] Implement `remove` command
- [ ] Implement `init` command
- [ ] Implement `source` command group
- [ ] Add rich console output with colors and progress bars
- [ ] Add `--verbose` flag for debugging

### Phase 6: Testing

**Goal**: Comprehensive test coverage

**Tasks**:
- [ ] Unit tests for config parsing
- [ ] Unit tests for GitHub fetching (with mocks)
- [ ] Unit tests for installer
- [ ] Integration tests for CLI commands
- [ ] Test error handling and edge cases
- [ ] Test with both public and private repos

### Phase 7: Documentation

**Goal**: Clear documentation for users and contributors

**Tasks**:
- [ ] README with installation and usage
- [ ] API documentation
- [ ] Examples and tutorials
- [ ] Contributing guide
- [ ] Security guidelines

## Usage Example

### Installation

```bash
# Add as dev dependency
uv add --dev claude-skill-manager

# Or with pip
pip install --dev claude-skill-manager
```

### First-time Setup

```bash
# Initialize in your project
cd my-project
claude-skills init

# This creates .claude/skill-sources.yaml with:
# - default_source: "mojzis/marimo-template"
# - allowed_sources: ["mojzis/marimo-template"]
```

### Fetch Skills

```bash
# Fetch from default source
claude-skills fetch marimo-notebook

# Output:
# ✓ Fetching marimo-notebook from mojzis/marimo-template
# ✓ Validating source...
# ✓ Downloading skill...
# ✓ Installing to .claude/skills/marimo-notebook.md
# ✓ Done!
```

### List Skills

```bash
claude-skills list

# Output:
# Installed Skills:
#
# marimo-notebook.md
#   Source: mojzis/marimo-template
#   Fetched: 2025-11-17 10:30:00
#
# pandas-best-practices.md
#   Source: mojzis/marimo-template
#   Fetched: 2025-11-17 10:31:00
```

### Update Skills

```bash
# Update specific skill
claude-skills update marimo-notebook

# Update all skills
claude-skills update --all
```

## Security Model

### Source Validation

1. **Allowed Sources List**: Only fetch from configured sources
2. **HTTPS Only**: Always use secure connections
3. **Content Validation**: Verify markdown format and frontmatter
4. **Size Limits**: Prevent large file downloads
5. **No Code Execution**: Skills are markdown, not executable code

### Configuration Protection

```yaml
# .claude/skill-sources.yaml
allowed_sources:
  - "mojzis/marimo-template"  # Template repo
  - "myorg/our-skills"        # Organization skills
  # Users must explicitly add sources
```

### Future Enhancements (Optional)

- GPG signature verification
- Checksum verification
- Trusted publisher system
- Skill sandboxing

## Alternative: GitHub API vs Raw Content

### Option 1: Raw Content (Recommended for MVP)

**Pros**:
- No authentication needed for public repos
- Simple HTTP GET requests
- No rate limits for public content
- Fast and straightforward

**Cons**:
- Can't easily list available skills
- No metadata about skill versions
- Requires knowing exact skill names

**URL**: `https://raw.githubusercontent.com/owner/repo/branch/.claude/skills/skill.md`

### Option 2: GitHub API

**Pros**:
- Can list available skills in a repo
- Access to commit history and versions
- Rich metadata

**Cons**:
- Rate limits (60 req/hour unauthenticated, 5000 with token)
- Requires token for private repos
- More complex implementation

**Recommendation**: Start with Raw Content (Option 1), add GitHub API later for enhanced features

## Future Enhancements

### Version 1.1
- [ ] List available skills in a repository
- [ ] Search for skills across multiple sources
- [ ] Skill templates/scaffolding
- [ ] Dry-run mode

### Version 1.2
- [ ] GitHub API integration for metadata
- [ ] Support for GitLab and other platforms
- [ ] Skill dependencies
- [ ] Skill collections/bundles

### Version 2.0
- [ ] Central skill registry/marketplace
- [ ] Skill ratings and reviews
- [ ] Automatic updates
- [ ] Skill analytics

## Dependencies

### Core Dependencies
```toml
[project]
name = "claude-skill-manager"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.7.0",
    "httpx>=0.27.0",
    "pydantic>=2.5.0",
    "pyyaml>=6.0.1",
    "python-frontmatter>=1.1.0",  # Parse skill frontmatter
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.8.0",
    "ruff>=0.1.0",
]

[project.scripts]
claude-skills = "claude_skill_manager.cli:app"
```

## Timeline Estimate

- **Phase 1**: 2-3 hours (basic package structure)
- **Phase 2**: 3-4 hours (configuration system)
- **Phase 3**: 4-5 hours (GitHub fetcher)
- **Phase 4**: 3-4 hours (skill installation)
- **Phase 5**: 5-6 hours (CLI commands)
- **Phase 6**: 4-5 hours (testing)
- **Phase 7**: 2-3 hours (documentation)

**Total**: ~25-30 hours for MVP

## Success Criteria

1. ✅ Users can fetch skills with a single command
2. ✅ Configuration prevents unauthorized sources
3. ✅ Skills can be updated easily
4. ✅ Clear error messages for common issues
5. ✅ Works with both public and private repos
6. ✅ Comprehensive test coverage (>80%)
7. ✅ Clear documentation with examples

## Questions for Clarification

1. **Package Name**: `claude-skill-manager` or something else?
2. **Default Source**: Should `mojzis/marimo-template` be the default?
3. **Private Repos**: Should we support GitHub tokens in first version?
4. **Conflict Resolution**: Skip, overwrite, or prompt when skill exists?
5. **Skill Discovery**: How should users know what skills are available?

## Next Steps

1. Review and approve this plan
2. Create the `claude-skill-manager` package repository
3. Start with Phase 1: Core library structure
4. Iterate through phases sequentially
5. Test with real-world usage in marimo-template project
