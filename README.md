# Claude Skill Manager

A Python library for sharing and managing Claude Code skills across projects.

## Overview

Claude Skill Manager enables easy sharing, installation, and updating of Claude Code skills from GitHub repositories with version control and security features.

### Features

- **Simple CLI**: Single command to fetch and install skills
- **GitHub Integration**: Fetches skills directly from GitHub repositories
- **Secure**: Configurable allowed sources to prevent unauthorized skill fetching
- **Version Control**: Track skill versions and update to latest
- **Metadata Tracking**: Maintains installation metadata with checksums
- **Beautiful Output**: Rich CLI output with colors and tables

## Installation

### Using uv (Recommended)

```bash
# Add as dev dependency
uv add --dev claude-skill-manager

# Or install in current environment
uv pip install claude-skill-manager
```

### Using pip

```bash
pip install claude-skill-manager
```

### From Source

```bash
git clone https://github.com/mojzis/claude-skill-manager.git
cd claude-skill-manager
pip install -e .
```

## Quick Start

### 1. Initialize Configuration

First, initialize the skill configuration in your project:

```bash
cd your-project
claude-skills init
```

This creates `.claude/skill-sources.yaml` with default configuration:

```yaml
default_source: "mojzis/marimo-template"
allowed_sources:
  - "mojzis/marimo-template"
aliases: {}
```

### 2. Fetch a Skill

Fetch a skill from the default source:

```bash
claude-skills fetch marimo-notebook
```

Or from a specific source:

```bash
claude-skills fetch marimo-notebook owner/repo
```

### 3. List Installed Skills

View all installed skills with metadata:

```bash
claude-skills list
```

Output:
```
Installed Skills:

┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Skill                ┃ Source              ┃ Branch ┃ Fetched At          ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ marimo-notebook.md   │ mojzis/marimo-temp… │ main   │ 2025-11-17 10:30:00 │
└──────────────────────┴─────────────────────┴────────┴─────────────────────┘
```

## Usage

### Fetching Skills

```bash
# Fetch from default source
claude-skills fetch <skill-name>

# Fetch from specific source
claude-skills fetch <skill-name> owner/repo

# Fetch from specific branch
claude-skills fetch <skill-name> owner/repo --branch develop

# Overwrite if exists
claude-skills fetch <skill-name> --overwrite
```

### Managing Skills

```bash
# List installed skills
claude-skills list

# Update a specific skill
claude-skills update <skill-name>

# Update all skills
claude-skills update --all

# Remove a skill
claude-skills remove <skill-name>
```

### Managing Sources

```bash
# Add a new allowed source
claude-skills source add owner/repo

# Remove an allowed source
claude-skills source remove owner/repo

# List allowed sources
claude-skills source list
```

### Initializing Projects

```bash
# Initialize with default source
claude-skills init

# Initialize with custom default source
claude-skills init --source owner/repo
```

## Configuration

Configuration is stored in `.claude/skill-sources.yaml`:

```yaml
# Default repository to fetch from
default_source: "mojzis/marimo-template"

# List of allowed repositories (for security)
allowed_sources:
  - "mojzis/marimo-template"
  - "myorg/our-skills"

# Optional: skill name aliases
aliases:
  marimo: "marimo-notebook"
  pandas: "pandas-best-practices"
```

### Security

The `allowed_sources` list acts as a security whitelist. Skills can only be fetched from repositories explicitly listed here. This prevents unauthorized skill fetching.

To add a new source:

```bash
claude-skills source add trusted-org/skills-repo
```

## How It Works

### Skill Storage

Skills are stored in `.claude/skills/` in your project:

```
your-project/
├── .claude/
│   ├── skills/
│   │   ├── marimo-notebook.md
│   │   ├── pandas-best-practices.md
│   │   └── .metadata.yaml
│   └── skill-sources.yaml
└── ...
```

### Metadata Tracking

Installation metadata is stored in `.claude/skills/.metadata.yaml`:

```yaml
skills:
  marimo-notebook.md:
    source: "mojzis/marimo-template"
    fetched_at: "2025-11-17T10:30:00"
    branch: "main"
    checksum: "sha256:abc123..."
```

This enables:
- Tracking where skills came from
- Detecting when updates are available
- Verifying skill integrity

### GitHub Integration

Skills are fetched from GitHub using the raw content API:

```
https://raw.githubusercontent.com/{owner}/{repo}/{branch}/.claude/skills/{skill-name}.md
```

For public repositories, no authentication is needed. For private repositories, set the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN=ghp_your_token_here
claude-skills fetch private-skill owner/private-repo
```

## Publishing Skills

To share your skills with others:

1. Create a `.claude/skills/` directory in your repository
2. Add your skill markdown files
3. Users can fetch with: `claude-skills fetch your-skill your-username/your-repo`

Example repository structure:

```
your-repo/
├── .claude/
│   └── skills/
│       ├── skill-one.md
│       └── skill-two.md
├── README.md
└── ...
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/mojzis/claude-skill-manager.git
cd claude-skill-manager

# Install dependencies
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/claude_skill_manager --cov-report=term-missing

# Run specific test file
pytest tests/test_config.py
```

### Code Quality

```bash
# Run linter
ruff check .

# Run type checker
mypy src/claude_skill_manager

# Auto-format code
ruff format .
```

## Examples

### Example 1: Setting Up a New Project

```bash
# Navigate to your project
cd my-project

# Initialize skill configuration
claude-skills init

# Fetch a skill
claude-skills fetch marimo-notebook

# Verify installation
claude-skills list
```

### Example 2: Using Custom Sources

```bash
# Add your organization's skill repository
claude-skills source add myorg/skill-library

# Fetch from your org
claude-skills fetch custom-skill myorg/skill-library

# List all sources
claude-skills source list
```

### Example 3: Keeping Skills Updated

```bash
# Update a specific skill
claude-skills update marimo-notebook

# Update all skills
claude-skills update --all
```

## Troubleshooting

### Skill Not Found

If you get a "Skill not found" error:

1. Verify the skill exists in the repository at `.claude/skills/<skill-name>.md`
2. Check you're using the correct branch (default is `main`)
3. Ensure the repository is public or you have `GITHUB_TOKEN` set

### Access Forbidden

If you get an "Access forbidden" error:

1. The repository might be private - set `GITHUB_TOKEN`
2. Or the skill doesn't exist at the expected path

### Source Not Allowed

If you get "Source not in allowed sources list":

1. Add the source: `claude-skills source add owner/repo`
2. Or check your `.claude/skill-sources.yaml` configuration

## Roadmap

### Version 1.1
- List available skills in a repository
- Search for skills across multiple sources
- Skill templates/scaffolding
- Dry-run mode

### Version 1.2
- GitHub API integration for enhanced metadata
- Support for GitLab and other platforms
- Skill dependencies
- Skill collections/bundles

### Version 2.0
- Central skill registry/marketplace
- Skill ratings and reviews
- Automatic updates
- Skill analytics

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Implementation Plan](plans/skill-sharing-system.md)
- [GitHub Repository](https://github.com/mojzis/claude-skill-manager)
- [Issue Tracker](https://github.com/mojzis/claude-skill-manager/issues)
