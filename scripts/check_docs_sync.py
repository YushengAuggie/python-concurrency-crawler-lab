"""Check that paired English and Chinese learning documents stay synchronized."""

from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys


DOCUMENT_PAIRS = (
    (Path("README.md"), Path("README.zh-CN.md")),
    (Path("lessons/README.md"), Path("lessons/README.zh-CN.md")),
    (Path("docs/index.html"), Path("docs/zh-CN.html")),
)
REQUIRED_LINK_TARGETS = {
    Path("README.md"): "(README.zh-CN.md)",
    Path("README.zh-CN.md"): "(README.md)",
    Path("lessons/README.md"): "(README.zh-CN.md)",
    Path("lessons/README.zh-CN.md"): "(README.md)",
    Path("docs/index.html"): 'href="zh-CN.html"',
    Path("docs/zh-CN.html"): 'href="index.html"',
}


def check_language_links() -> list[str]:
    """Return errors for missing documents or language-switch links."""
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
    """Require each translated document pair to change together."""
    changed_files = changed_files_since(base_ref)
    errors = []
    for english_document, chinese_document in DOCUMENT_PAIRS:
        english_changed = str(english_document) in changed_files
        chinese_changed = str(chinese_document) in changed_files
        if english_changed != chinese_changed:
            errors.append(
                f"{english_document} and {chinese_document} must be updated "
                "together when their learning content changes."
            )
    return errors


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
