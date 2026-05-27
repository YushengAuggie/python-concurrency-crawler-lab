"""Check that the English and Chinese READMEs stay paired in pull requests."""

from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys


README_ENGLISH = Path("README.md")
README_CHINESE = Path("README.zh-CN.md")
REQUIRED_LINK_TARGETS = {
    README_ENGLISH: "(README.zh-CN.md)",
    README_CHINESE: "(README.md)",
}


def check_language_links() -> list[str]:
    """Return errors for missing README files or language-switch links."""
    errors = []
    for readme_path, required_link_target in REQUIRED_LINK_TARGETS.items():
        if not readme_path.exists():
            errors.append(f"Missing documentation file: {readme_path}")
            continue

        if required_link_target not in readme_path.read_text(encoding="utf-8"):
            errors.append(
                f"{readme_path} must include a language link to "
                f"{required_link_target}."
            )
    return errors


def changed_files_since(base_ref: str) -> set[str]:
    """Return files changed from a pull request base commit to HEAD."""
    output = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        text=True,
    )
    return {line.strip() for line in output.splitlines() if line.strip()}


def check_paired_changes(base_ref: str) -> list[str]:
    """Require both translated READMEs to change in the same pull request."""
    changed_files = changed_files_since(base_ref)
    english_changed = str(README_ENGLISH) in changed_files
    chinese_changed = str(README_CHINESE) in changed_files
    if english_changed != chinese_changed:
        return [
            "README.md and README.zh-CN.md must be updated together "
            "when documentation content changes."
        ]
    return []


def main() -> int:
    """Run local link checks and optional pull-request synchronization checks."""
    parser = ArgumentParser()
    parser.add_argument(
        "--base-ref",
        help="Git commit or ref used to verify paired README changes.",
    )
    arguments = parser.parse_args()

    errors = check_language_links()
    if arguments.base_ref:
        errors.extend(check_paired_changes(arguments.base_ref))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Documentation language checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
