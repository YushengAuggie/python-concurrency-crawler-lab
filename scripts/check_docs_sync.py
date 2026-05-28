"""Check that paired English and Chinese learning documents stay synchronized."""

from argparse import ArgumentParser
from html.parser import HTMLParser
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
GENERATED_SOURCE_PAYLOAD = Path("docs/assets/source-files.js")


class SourceHighlightParser(HTMLParser):
    """Collect source-reader highlight ranges from the static course pages."""

    def __init__(self) -> None:
        super().__init__()
        self.highlights: list[tuple[str, str, str]] = []

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        attribute_map = dict(attributes)
        source_path = attribute_map.get("data-source-path")
        source_highlight = attribute_map.get("data-highlight")
        if source_path and source_highlight:
            self.highlights.append(("tree", source_path, source_highlight))

        source_target = attribute_map.get("data-source-target")
        target_highlight = attribute_map.get("data-source-highlight")
        if source_target and target_highlight:
            self.highlights.append(("jump", source_target, target_highlight))


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


def check_generated_source_payload() -> list[str]:
    """Require the website source-code payload to match repository files."""
    repository_root = Path(__file__).resolve().parents[1]
    if str(repository_root) not in sys.path:
        sys.path.insert(0, str(repository_root))

    import scripts.generate_site_sources as source_generator

    if not GENERATED_SOURCE_PAYLOAD.exists():
        return [f"Missing generated source payload: {GENERATED_SOURCE_PAYLOAD}"]

    expected_payload = source_generator.render_javascript(
        source_generator.build_payload()
    )
    actual_payload = GENERATED_SOURCE_PAYLOAD.read_text(encoding="utf-8")
    if actual_payload != expected_payload:
        return [
            "docs/assets/source-files.js is out of date. Run "
            "python3 scripts/generate_site_sources.py."
        ]

    return []


def parse_highlight_range(range_text: str) -> list[tuple[int, int]]:
    """Parse comma-separated source line ranges such as 8-16 or 42."""
    parsed_ranges = []
    for raw_range in range_text.split(","):
        range_item = raw_range.strip()
        if not range_item:
            continue

        start_text, separator, end_text = range_item.partition("-")
        if not start_text.isdecimal() or (separator and not end_text.isdecimal()):
            raise ValueError(f"Invalid line range: {range_item}")

        start_line = int(start_text)
        end_line = int(end_text) if separator else start_line
        if start_line < 1 or end_line < start_line:
            raise ValueError(f"Invalid line range: {range_item}")

        parsed_ranges.append((start_line, end_line))

    return parsed_ranges


def collect_source_highlights(document_path: Path) -> list[tuple[str, str, str]]:
    """Return all source-reader highlights from one HTML document."""
    parser = SourceHighlightParser()
    parser.feed(document_path.read_text(encoding="utf-8"))
    return parser.highlights


def check_source_highlights() -> list[str]:
    """Verify source-reader highlights point at real lines and stay bilingual."""
    errors = []
    english_highlights = collect_source_highlights(Path("docs/index.html"))
    chinese_highlights = collect_source_highlights(Path("docs/zh-CN.html"))
    if english_highlights != chinese_highlights:
        errors.append(
            "docs/index.html and docs/zh-CN.html must use matching source "
            "highlight ranges."
        )

    for document_path in (Path("docs/index.html"), Path("docs/zh-CN.html")):
        for _source_kind, source_path, range_text in collect_source_highlights(
            document_path
        ):
            code_path = Path(source_path)
            if not code_path.exists():
                errors.append(f"{document_path} highlights missing file {source_path}.")
                continue

            line_count = len(code_path.read_text(encoding="utf-8").splitlines())
            try:
                highlighted_ranges = parse_highlight_range(range_text)
            except ValueError as error:
                errors.append(f"{document_path} has {error} for {source_path}.")
                continue

            for start_line, end_line in highlighted_ranges:
                if end_line > line_count:
                    errors.append(
                        f"{document_path} highlights {source_path}:{start_line}-"
                        f"{end_line}, but the file has {line_count} lines."
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
    errors.extend(check_generated_source_payload())
    errors.extend(check_source_highlights())
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
