#!/usr/bin/env python3
"""
Release management utilities for HEAL application.
Handles version bumping, changelog generation, and release preparation.
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class ReleaseManager:
    """Manages releases for the HEAL application."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.pyproject_file = project_root / "pyproject.toml"
        self.changelog_file = project_root / "CHANGELOG.md"

    def get_current_version(self) -> str:
        """Get the current version from setuptools-scm."""
        try:
            result = subprocess.run([
                sys.executable, "-c",
                "import setuptools_scm; print(setuptools_scm.get_version())"
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "0.0.0"

    def get_git_tags(self) -> List[str]:
        """Get all git tags sorted by version."""
        try:
            result = subprocess.run([
                "git", "tag", "-l", "--sort=-version:refname"
            ], capture_output=True, text=True, check=True)
            return [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
        except subprocess.CalledProcessError:
            return []

    def get_latest_tag(self) -> Optional[str]:
        """Get the latest git tag."""
        tags = self.get_git_tags()
        return tags[0] if tags else None

    def bump_version(self, bump_type: str) -> str:
        """Bump version based on type (major, minor, patch)."""
        current_version = self.get_current_version()

        # Parse current version
        version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', current_version)
        if not version_match:
            raise ValueError(f"Invalid version format: {current_version}")

        major, minor, patch = map(int, version_match.groups())

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        return f"{major}.{minor}.{patch}"

    def generate_changelog_entry(self, version: str, since_tag: Optional[str] = None) -> str:
        """Generate changelog entry for the new version."""
        print(f"Generating changelog for version {version}...")

        # Get commit range
        if since_tag:
            commit_range = f"{since_tag}..HEAD"
        else:
            commit_range = "HEAD"

        try:
            # Get commits since last tag
            result = subprocess.run([
                "git", "log", commit_range,
                "--pretty=format:%s", "--no-merges"
            ], capture_output=True, text=True, check=True)

            commits = [line.strip()
                       for line in result.stdout.split('\n') if line.strip()]

            if not commits:
                return f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n- No changes\n"

            # Categorize commits
            features = []
            fixes = []
            docs = []
            other = []

            for commit in commits:
                commit_lower = commit.lower()
                if any(keyword in commit_lower for keyword in ['feat:', 'feature:', 'add:']):
                    features.append(commit)
                elif any(keyword in commit_lower for keyword in ['fix:', 'bug:', 'patch:']):
                    fixes.append(commit)
                elif any(keyword in commit_lower for keyword in ['doc:', 'docs:']):
                    docs.append(commit)
                else:
                    other.append(commit)

            # Build changelog entry
            entry = f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n"

            if features:
                entry += "### Added\n"
                for feature in features:
                    entry += f"- {feature}\n"
                entry += "\n"

            if fixes:
                entry += "### Fixed\n"
                for fix in fixes:
                    entry += f"- {fix}\n"
                entry += "\n"

            if docs:
                entry += "### Documentation\n"
                for doc in docs:
                    entry += f"- {doc}\n"
                entry += "\n"

            if other:
                entry += "### Changed\n"
                for change in other:
                    entry += f"- {change}\n"
                entry += "\n"

            return entry

        except subprocess.CalledProcessError as e:
            print(f"Error generating changelog: {e}")
            return f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n- Release {version}\n"

    def update_changelog(self, version: str) -> None:
        """Update the changelog file with new version entry."""
        latest_tag = self.get_latest_tag()
        new_entry = self.generate_changelog_entry(version, latest_tag)

        if self.changelog_file.exists():
            content = self.changelog_file.read_text(encoding='utf-8')

            # Find the position to insert the new entry
            if "# Changelog" in content:
                # Insert after the header
                lines = content.split('\n')
                header_index = next(i for i, line in enumerate(
                    lines) if line.startswith('# Changelog'))

                # Insert new entry after header and any description
                insert_index = header_index + 1
                while insert_index < len(lines) and not lines[insert_index].startswith('## '):
                    insert_index += 1

                lines.insert(insert_index, new_entry)
                updated_content = '\n'.join(lines)
            else:
                # Prepend to existing content
                updated_content = f"# Changelog\n\n{new_entry}\n{content}"
        else:
            # Create new changelog
            updated_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{new_entry}"

        self.changelog_file.write_text(updated_content, encoding='utf-8')
        print(f"Updated {self.changelog_file}")

    def create_git_tag(self, version: str, message: Optional[str] = None) -> None:
        """Create a git tag for the release."""
        tag_name = f"v{version}"
        tag_message = message or f"Release {version}"

        try:
            subprocess.run([
                "git", "tag", "-a", tag_name, "-m", tag_message
            ], check=True)
            print(f"Created git tag: {tag_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating git tag: {e}")
            raise

    def prepare_release(self, bump_type: str, dry_run: bool = False) -> str:
        """Prepare a new release."""
        print(f"Preparing {bump_type} release...")

        # Check if working directory is clean
        try:
            result = subprocess.run([
                "git", "status", "--porcelain"
            ], capture_output=True, text=True, check=True)

            if result.stdout.strip() and not dry_run:
                print("Warning: Working directory is not clean")
                print("Uncommitted changes:")
                print(result.stdout)
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("Release preparation cancelled")
                    return ""
        except subprocess.CalledProcessError:
            print("Warning: Could not check git status")

        # Bump version
        new_version = self.bump_version(bump_type)
        print(f"New version: {new_version}")

        if dry_run:
            print("DRY RUN: Would update changelog and create tag")
            print(f"DRY RUN: New version would be {new_version}")
            return new_version

        # Update changelog
        self.update_changelog(new_version)

        # Stage changelog changes
        try:
            subprocess.run(
                ["git", "add", str(self.changelog_file)], check=True)
            subprocess.run([
                "git", "commit", "-m", f"Update changelog for v{new_version}"
            ], check=True)
            print("Committed changelog changes")
        except subprocess.CalledProcessError as e:
            print(f"Error committing changes: {e}")

        # Create git tag
        self.create_git_tag(new_version)

        print(f"\nRelease {new_version} prepared successfully!")
        print("To publish the release:")
        print(f"  git push origin main")
        print(f"  git push origin v{new_version}")
        print("\nThis will trigger the automated build and release workflow.")

        return new_version

    def list_releases(self) -> None:
        """List all releases."""
        tags = self.get_git_tags()

        if not tags:
            print("No releases found")
            return

        print("Releases:")
        print("-" * 50)

        for tag in tags:
            try:
                # Get tag date
                result = subprocess.run([
                    "git", "log", "-1", "--format=%ai", tag
                ], capture_output=True, text=True, check=True)
                date = result.stdout.strip().split()[0]

                # Get tag message
                result = subprocess.run([
                    "git", "tag", "-l", "--format=%(contents)", tag
                ], capture_output=True, text=True, check=True)
                message = result.stdout.strip() or "No message"

                print(f"{tag:15} {date:12} {message}")

            except subprocess.CalledProcessError:
                print(f"{tag:15} {'Unknown':12} No information")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="HEAL Release Manager")
    parser.add_argument(
        "command",
        choices=["prepare", "list", "version", "changelog"],
        help="Command to execute"
    )
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Version bump type (default: patch)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    manager = ReleaseManager(project_root)

    if args.command == "prepare":
        manager.prepare_release(args.bump, args.dry_run)
    elif args.command == "list":
        manager.list_releases()
    elif args.command == "version":
        print(f"Current version: {manager.get_current_version()}")
    elif args.command == "changelog":
        latest_tag = manager.get_latest_tag()
        entry = manager.generate_changelog_entry("NEXT", latest_tag)
        print("Changelog preview:")
        print(entry)


if __name__ == "__main__":
    main()
