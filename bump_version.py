#!/usr/bin/env python3
"""
Simple version bumper for OHM MCP package.
Usage: python bump_version.py [patch|minor|major]
"""

import sys
import re
from pathlib import Path

def bump_version(current_version, bump_type):
    """Bump version according to semantic versioning."""
    major, minor, patch = map(int, current_version.split('.'))

    if bump_type == 'patch':
        patch += 1
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError("Bump type must be 'patch', 'minor', or 'major'")

    return f"{major}.{minor}.{patch}"

def update_pyproject_toml(version):
    """Update version in pyproject.toml."""
    pyproject_path = Path(__file__).parent / "pyproject.toml"

    with open(pyproject_path, 'r') as f:
        content = f.read()

    # Update version line
    pattern = r'(version = ")[^"]*(")'
    new_content = re.sub(pattern, rf'\g<1>{version}\g<2>', content)

    with open(pyproject_path, 'w') as f:
        f.write(new_content)

    print(f"✅ Updated pyproject.toml to version {version}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py [patch|minor|major]")
        sys.exit(1)

    bump_type = sys.argv[1].lower()
    if bump_type not in ['patch', 'minor', 'major']:
        print("Error: Bump type must be 'patch', 'minor', or 'major'")
        sys.exit(1)

    # Read current version
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    with open(pyproject_path, 'r') as f:
        content = f.read()

    version_match = re.search(r'version = "([^"]*)"', content)
    if not version_match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)

    current_version = version_match.group(1)
    new_version = bump_version(current_version, bump_type)

    print(f"🔄 Bumping version: {current_version} → {new_version}")

    # Update version
    update_pyproject_toml(new_version)

    print("📦 Ready to build and publish!")
    print(f"   cd {Path(__file__).parent}")
    print("   python -m build")
    print("   twine upload dist/*")

if __name__ == "__main__":
    main()
