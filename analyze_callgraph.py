#!/usr/bin/env python3
"""Collect the per-function stack usage emitted by GCC.

Builds that use ``-fstack-usage`` (or ``-fcallgraph-info=su``) produce one
``.su`` file for every compiled C translation unit.  This script combines
those files into a deterministic inventory.  Each row is one function frame;
it deliberately does *not* add caller and callee frames.  Call-path and graph
analysis can consume the generated JSON later.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class StackUsage:
    """One function record from a GCC ``.su`` file."""

    source: str
    line: int
    column: int
    function: str
    stack_bytes: int | None
    stack_kind: str
    su_file: str

    @property
    def identity(self) -> tuple[str, int, int, str, int | None, str]:
        return (
            self.source,
            self.line,
            self.column,
            self.function,
            self.stack_bytes,
            self.stack_kind,
        )


def parse_su_line(line: str, su_file: Path) -> StackUsage | None:
    """Parse a GCC stack-usage record.

    GCC writes ``source:line:column:function<TAB>bytes<TAB>kind``.  Split from
    the right so a Windows drive letter and C++-style function names do not
    make the location ambiguous.  A missing byte value (``?``) is preserved as
    unknown instead of silently converted to zero.
    """
    fields = line.rstrip("\n").split("\t")
    if len(fields) != 3:
        return None
    location, bytes_text, stack_kind = fields
    try:
        source_and_line, column_text, function = location.rsplit(":", 2)
        source, line_text = source_and_line.rsplit(":", 1)
        line_number = int(line_text)
        column_number = int(column_text)
    except ValueError:
        return None
    try:
        stack_bytes = int(bytes_text)
    except ValueError:
        stack_bytes = None
    return StackUsage(
        source=source.replace("\\", "/"),
        line=line_number,
        column=column_number,
        function=function,
        stack_bytes=stack_bytes,
        stack_kind=stack_kind,
        su_file=su_file.as_posix(),
    )


def is_within(source: str, directory: Path, source_root: Path) -> bool:
    """Return whether a ``.su`` source path belongs to one source directory."""
    source_path = Path(source)
    candidates = (source_path, source_root / source_path)
    for candidate in candidates:
        try:
            candidate.resolve().relative_to(directory.resolve())
            return True
        except ValueError:
            continue
    return False


def is_cmcell_source(record: StackUsage, source_root: Path) -> bool:
    return any(
        is_within(record.source, source_root / module, source_root)
        for module in ("cellular", "com", "modem")
    )


def collect_stack_usage(
    su_dir: Path, source_root: Path, include_all_sources: bool
) -> tuple[list[StackUsage], int, int, list[str]]:
    """Read GCC ``.su`` files, retain the selected sources, and deduplicate."""
    records: dict[tuple[str, int, int, str, int | None, str], StackUsage] = {}
    malformed: list[str] = []
    raw_count = 0
    outside_scope_count = 0
    for su_file in sorted(su_dir.rglob("*.su")):
        with su_file.open(encoding="utf-8", errors="replace") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if not raw_line.strip():
                    continue
                record = parse_su_line(raw_line, su_file)
                if record is None:
                    malformed.append(f"{su_file}:{line_number}")
                    continue
                raw_count += 1
                if not include_all_sources and not is_cmcell_source(record, source_root):
                    outside_scope_count += 1
                    continue
                records.setdefault(record.identity, record)
    return list(records.values()), raw_count, outside_scope_count, malformed


def sort_key(record: StackUsage) -> tuple[int, str, str, int, int]:
    # Unknown sizes are shown after known sizes.  For known data, put the
    # largest frame first so the initial section is immediately actionable.
    unknown = record.stack_bytes is None
    return (unknown, -(record.stack_bytes or 0), record.function, record.source, record.line)


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def report_source(source: str, source_root: Path) -> str:
    source_path = Path(source)
    for candidate in (source_path, source_root / source_path):
        try:
            return candidate.resolve().relative_to(source_root.resolve()).as_posix()
        except ValueError:
            continue
    return source.replace("\\", "/")


def markdown_report(
    records: list[StackUsage],
    raw_count: int,
    outside_scope_count: int,
    su_file_count: int,
    malformed: list[str],
    source_root: Path,
    include_all_sources: bool,
) -> str:
    known = [record for record in records if record.stack_bytes is not None]
    dynamic = [record for record in records if "dynamic" in record.stack_kind]
    in_scope_count = raw_count - outside_scope_count
    duplicate_count = in_scope_count - len(records)
    lines = [
        "# CMCELL function stack-usage inventory",
        "",
        f"- Stack-usage files: {su_file_count}",
        f"- Source scope: {'all build sources' if include_all_sources else '`cellular/`, `com/`, and `modem/`'}",
        f"- Function records: {len(records)} unique ({in_scope_count} in scope)",
        f"- Records outside source scope ignored: {outside_scope_count}",
        f"- Duplicate records ignored: {duplicate_count}",
        f"- Known stack frames: {len(known)}",
        f"- Dynamic stack frames: {len(dynamic)}",
        "- This is an inventory of individual frames; the values are **not** caller-to-callee totals.",
        "",
        "## Functions",
        "",
        "| Stack (B) | Kind | Function | Source |",
        "|---:|---|---|---|",
    ]
    for record in sorted(records, key=sort_key):
        stack = "unknown" if record.stack_bytes is None else str(record.stack_bytes)
        source = f"{report_source(record.source, source_root)}:{record.line}:{record.column}"
        lines.append(
            "| "
            f"{stack} | {markdown_escape(record.stack_kind)} | "
            f"`{markdown_escape(record.function)}` | "
            f"`{markdown_escape(source)}` |"
        )
    if malformed:
        lines.extend(
            [
                "",
                "## Unparsed records",
                "",
                "These lines do not match GCC's expected `.su` format and were skipped:",
                "",
            ]
        )
        lines.extend(f"- `{item}`" for item in malformed)
    return "\n".join(lines) + "\n"


def json_report(
    records: list[StackUsage], su_dir: Path, source_root: Path, include_all_sources: bool
) -> dict[str, object]:
    return {
        "format": "cmcell-stack-usage-v1",
        "input_directory": str(su_dir),
        "source_scope": "all" if include_all_sources else ["cellular", "com", "modem"],
        "source_root": str(source_root),
        "functions": [asdict(record) for record in sorted(records, key=sort_key)],
    }


def csv_report(records: list[StackUsage], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("stack_bytes", "stack_kind", "function", "source", "line", "column", "su_file"),
        )
        writer.writeheader()
        for record in sorted(records, key=sort_key):
            writer.writerow(asdict(record))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--su-dir",
        "--ci-dir",
        dest="su_dir",
        required=True,
        type=Path,
        help="Build directory containing GCC .su files (--ci-dir is a legacy alias)",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="CMCELL repository root used to select cellular/, com/, and modem/",
    )
    parser.add_argument(
        "--all-sources",
        action="store_true",
        help="Include emulator and third-party sources too (default is only cellular/, com/, modem/)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("stack_functions.md"),
        help="Markdown inventory path (default: stack_functions.md)",
    )
    parser.add_argument("--json", type=Path, help="Optional machine-readable inventory path")
    parser.add_argument("--csv", type=Path, help="Optional CSV inventory path")
    args = parser.parse_args()

    if not args.su_dir.is_dir():
        parser.error(f"Directory does not exist: {args.su_dir}")
    su_file_count = sum(1 for _ in args.su_dir.rglob("*.su"))
    if not su_file_count:
        parser.error(f"No .su files found below {args.su_dir}")
    records, raw_count, outside_scope_count, malformed = collect_stack_usage(
        args.su_dir, args.source_root, args.all_sources
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        markdown_report(
            records,
            raw_count,
            outside_scope_count,
            su_file_count,
            malformed,
            args.source_root,
            args.all_sources,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {args.report} ({len(records)} unique functions)")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                json_report(records, args.su_dir, args.source_root, args.all_sources), indent=2
            ),
            encoding="utf-8",
        )
        print(f"Wrote {args.json}")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        csv_report(records, args.csv)
        print(f"Wrote {args.csv}")
    if malformed:
        print(f"Warning: skipped {len(malformed)} malformed .su record(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
