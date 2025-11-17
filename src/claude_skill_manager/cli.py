"""Command-line interface for Claude Skill Manager."""

import os
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import ConfigManager
from .fetcher import FetchError, SkillFetcher
from .installer import ConflictResolution, SkillInstaller
from .models import SkillSource

app = typer.Typer(
    name="claude-skills",
    help="Manage and share Claude Code skills across projects",
    add_completion=False,
)

source_app = typer.Typer(help="Manage allowed skill sources")
app.add_typer(source_app, name="source")

console = Console()


@app.command()
def init(
    default_source: Optional[str] = typer.Option(
        None,
        "--source",
        "-s",
        help="Default source repository (e.g., 'owner/repo')",
    ),
) -> None:
    """Initialize skill configuration in the current project."""
    try:
        config_manager = ConfigManager()
        config = config_manager.init(default_source)

        console.print(
            f"✓ Initialized configuration at {config_manager.config_path}",
            style="green",
        )
        console.print(f"  Default source: {config.default_source}", style="dim")
        console.print(
            f"  Allowed sources: {', '.join(config.allowed_sources)}", style="dim"
        )

    except FileExistsError as e:
        console.print(f"✗ {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def fetch(
    skill_name: str = typer.Argument(..., help="Name of the skill to fetch"),
    source: Optional[str] = typer.Argument(
        None, help="Source repository (e.g., 'owner/repo'). Uses default if not specified."
    ),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch to fetch from"),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-f", help="Overwrite if skill already exists"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Fetch a skill from a GitHub repository."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        try:
            config = config_manager.load()
        except FileNotFoundError:
            console.print(
                "✗ No configuration found. Run 'claude-skills init' first.",
                style="red",
            )
            raise typer.Exit(1)

        # Resolve skill name (check for aliases)
        actual_skill_name = config_manager.resolve_alias(skill_name)
        if actual_skill_name != skill_name and verbose:
            console.print(f"  Resolved alias '{skill_name}' → '{actual_skill_name}'", style="dim")

        # Determine source
        if source is None:
            source = config.default_source
            if verbose:
                console.print(f"  Using default source: {source}", style="dim")

        # Validate source is allowed
        if not config_manager.is_source_allowed(source):
            console.print(
                f"✗ Source '{source}' is not in allowed sources list", style="red"
            )
            console.print(
                "  Add it with: claude-skills source add {source}", style="yellow"
            )
            raise typer.Exit(1)

        # Parse source
        try:
            skill_source = SkillSource.from_string(source, branch)
        except ValueError as e:
            console.print(f"✗ {e}", style="red")
            raise typer.Exit(1)

        console.print(
            f"Fetching {actual_skill_name} from {skill_source.full_name}...",
            style="cyan",
        )

        # Fetch the skill
        github_token = os.environ.get("GITHUB_TOKEN")
        with SkillFetcher(github_token) as fetcher:
            try:
                skill = fetcher.fetch(actual_skill_name, skill_source)
            except FetchError as e:
                console.print(f"✗ Failed to fetch skill: {e}", style="red")
                raise typer.Exit(1)

            # Install the skill
            installer = SkillInstaller()
            conflict_resolution = (
                ConflictResolution.OVERWRITE
                if overwrite
                else ConflictResolution.PROMPT
            )

            try:
                installed = installer.install(skill, conflict_resolution, fetcher)

                if installed:
                    console.print(
                        f"✓ Installed {skill.filename} to {installer.skills_dir / skill.filename}",
                        style="green",
                    )
                else:
                    console.print(
                        f"  Skill {skill.filename} already exists (skipped)",
                        style="yellow",
                    )
                    console.print(
                        "  Use --overwrite to replace it", style="dim"
                    )

            except FileExistsError as e:
                console.print(f"✗ {e}", style="red")
                raise typer.Exit(1)

    except Exception as e:
        if verbose:
            console.print_exception()
        else:
            console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def list() -> None:
    """List all installed skills with metadata."""
    try:
        installer = SkillInstaller()
        skills = installer.list_skills()

        if not skills:
            console.print("No skills installed yet.", style="yellow")
            console.print("  Use 'claude-skills fetch <skill-name>' to install skills", style="dim")
            return

        console.print("Installed Skills:", style="bold cyan")
        console.print()

        table = Table(show_header=True, header_style="bold")
        table.add_column("Skill", style="cyan")
        table.add_column("Source", style="green")
        table.add_column("Branch", style="blue")
        table.add_column("Fetched At", style="yellow")

        for filename, metadata in skills.items():
            table.add_row(
                filename,
                metadata.source,
                metadata.branch,
                metadata.fetched_at.strftime("%Y-%m-%d %H:%M:%S"),
            )

        console.print(table)

    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def update(
    skill_name: Optional[str] = typer.Argument(
        None, help="Name of the skill to update. Omit to update all."
    ),
    all: bool = typer.Option(False, "--all", "-a", help="Update all skills"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Update a skill or all skills to their latest versions."""
    try:
        installer = SkillInstaller()
        config_manager = ConfigManager()

        # Get skills to update
        if all or skill_name is None:
            skills_to_update = list(installer.list_skills().keys())
            if not skills_to_update:
                console.print("No skills to update.", style="yellow")
                return
            console.print(f"Updating {len(skills_to_update)} skill(s)...", style="cyan")
        else:
            # Ensure .md extension
            if not skill_name.endswith(".md"):
                skill_name = f"{skill_name}.md"

            if not installer.is_installed(skill_name):
                console.print(f"✗ Skill not installed: {skill_name}", style="red")
                raise typer.Exit(1)

            skills_to_update = [skill_name]

        # Update each skill
        updated_count = 0
        skipped_count = 0

        github_token = os.environ.get("GITHUB_TOKEN")
        with SkillFetcher(github_token) as fetcher:
            for skill_file in skills_to_update:
                # Get current metadata
                metadata = installer.get_skill_info(skill_file)
                if not metadata:
                    console.print(f"  Skipping {skill_file} (no metadata)", style="yellow")
                    skipped_count += 1
                    continue

                # Fetch the latest version
                try:
                    skill_source = SkillSource.from_string(
                        metadata.source, metadata.branch
                    )
                    skill = fetcher.fetch(skill_file.replace(".md", ""), skill_source)

                    # Check if update is needed
                    new_checksum = fetcher.compute_checksum(skill.content)
                    if not installer.needs_update(skill_file, new_checksum):
                        if verbose:
                            console.print(f"  {skill_file} is already up to date", style="dim")
                        skipped_count += 1
                        continue

                    # Install the update
                    installer.install(skill, ConflictResolution.OVERWRITE, fetcher)
                    console.print(f"✓ Updated {skill_file}", style="green")
                    updated_count += 1

                except FetchError as e:
                    console.print(f"✗ Failed to update {skill_file}: {e}", style="red")
                    skipped_count += 1

        # Summary
        console.print()
        console.print(f"Updated: {updated_count}, Skipped: {skipped_count}", style="cyan")

    except Exception as e:
        if verbose:
            console.print_exception()
        else:
            console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def remove(
    skill_name: str = typer.Argument(..., help="Name of the skill to remove"),
) -> None:
    """Remove an installed skill."""
    try:
        installer = SkillInstaller()

        if installer.remove(skill_name):
            console.print(f"✓ Removed {skill_name}", style="green")
        else:
            console.print(f"✗ Skill not found: {skill_name}", style="red")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1)


@source_app.command("add")
def source_add(
    source: str = typer.Argument(..., help="Source repository to add (e.g., 'owner/repo')"),
) -> None:
    """Add a new allowed source repository."""
    try:
        config_manager = ConfigManager()
        config = config_manager.add_source(source)

        console.print(f"✓ Added source: {source}", style="green")
        console.print(
            f"  Allowed sources: {', '.join(config.allowed_sources)}", style="dim"
        )

    except FileNotFoundError:
        console.print(
            "✗ No configuration found. Run 'claude-skills init' first.", style="red"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1)


@source_app.command("remove")
def source_remove(
    source: str = typer.Argument(..., help="Source repository to remove"),
) -> None:
    """Remove an allowed source repository."""
    try:
        config_manager = ConfigManager()
        config = config_manager.remove_source(source)

        console.print(f"✓ Removed source: {source}", style="green")
        console.print(
            f"  Allowed sources: {', '.join(config.allowed_sources)}", style="dim"
        )

    except FileNotFoundError:
        console.print(
            "✗ No configuration found. Run 'claude-skills init' first.", style="red"
        )
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"✗ {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1)


@source_app.command("list")
def source_list() -> None:
    """List all allowed source repositories."""
    try:
        config_manager = ConfigManager()
        config = config_manager.load()

        console.print("Allowed Sources:", style="bold cyan")
        console.print()

        for source in config.allowed_sources:
            if source == config.default_source:
                console.print(f"  • {source} (default)", style="green bold")
            else:
                console.print(f"  • {source}", style="green")

    except FileNotFoundError:
        console.print(
            "✗ No configuration found. Run 'claude-skills init' first.", style="red"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
