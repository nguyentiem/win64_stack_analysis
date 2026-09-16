#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


STACK_PATTERN = re.compile(
    r"^\s*Stack Usage for\s+(.+?)\s+(0x[0-9a-fA-F]+|unknown)\s+bytes\.\s*$",
    re.IGNORECASE,
)


def normalize_path(path: str, project_root: Path) -> str:
    if not path:
        return ""

    source_path = Path(path)

    try:
        return source_path.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except ValueError:
        return source_path.as_posix()


def build_function_source_index(
    callgraph_file: Path,
    project_root: Path,
) -> dict[str, list[str]]:
    """
    Output:
    {
        "initialize": [
            "cellular/src/cell_connect.c",
            "cellular/src/cell_dfota.c"
        ],
        "perform_action": [
            "cellular/src/cell_connect.c"
        ]
    }
    """
    with open(callgraph_file, "r", encoding="utf-8") as f:
        callgraph = json.load(f)

    function_sources: dict[str, set[str]] = defaultdict(set)

    for edge in callgraph:
        for node_name in ("caller", "callee"):
            node = edge.get(node_name, {})

            function_name = node.get("name", "").strip()
            source_file = node.get("file", "").strip()

            if not function_name or not source_file:
                continue

            normalized_file = normalize_path(
                source_file,
                project_root,
            )

            function_sources[function_name].add(normalized_file)

    return {
        name: sorted(sources)
        for name, sources in function_sources.items()
    }


def parse_map_file(
    map_file: Path,
    function_sources: dict[str, list[str]],
) -> list[dict]:
    """Read individual frames and infer duplicate symbols from nearby sources.

    Prefer the current source when it is a candidate. Otherwise use the nearest
    uniquely mapped function whose source is a candidate, including lookahead.
    This is a source-order heuristic, not compiler symbol identity information.
    """
    entries = []
    in_section = False
    section_started = False
    section_ended = False
    with map_file.open(encoding="utf-8", errors="replace") as stream:
        for line_number, line in enumerate(stream, 1):
            heading = line.strip().lower()
            if heading == "stack usage for functions.":
                in_section = True
                section_started = True
                continue
            if in_section and heading == "potential stack usage inaccuracies.":
                section_ended = True
                break
            if not in_section:
                continue
            match = STACK_PATTERN.fullmatch(line)
            if match:
                name, value = match.groups()
                entries.append({
                    "name": name.strip(),
                    "source_file": "",
                    "stack_bytes": 0 if value.lower() == "unknown" else int(value, 16),
                })
            elif heading.startswith("stack usage for "):
                raise ValueError(f"Unsupported stack entry in {map_file}:{line_number}: {line.strip()}")
    if not section_started or not section_ended:
        raise ValueError(f"Missing stack section boundaries in {map_file}")

    anchors = []
    for index, entry in enumerate(entries):
        sources = function_sources.get(entry["name"], [])
        if len(sources) == 1:
            entry["source_file"] = sources[0]
            anchors.append((index, sources[0]))

    current_file = ""
    unresolved = []
    for index, entry in enumerate(entries):
        sources = function_sources.get(entry["name"], [])
        if len(sources) == 1:
            current_file = sources[0]
        elif len(sources) > 1:
            if current_file in sources:
                entry["source_file"] = current_file
            else:
                nearby = [(abs(position - index), position > index, source)
                          for position, source in anchors if source in sources]
                if nearby:
                    entry["source_file"] = min(nearby)[2]
                    current_file = entry["source_file"]
                else:
                    unresolved.append(entry["name"])
    if unresolved:
        print(f"Warning: {map_file}: source unresolved for {len(unresolved)} duplicate entries: "
              + ", ".join(sorted(set(unresolved))))
    return entries


def main():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Extract individual Keil function stack frames from map files.")
    parser.add_argument("--map", type=Path, action="append", dest="map_files",
                        help="Map file to parse; repeat to combine files. Default: FLASH_RAM/CMCELL_AC5_O0.map")
    parser.add_argument("--callgraph", type=Path, default=script_dir / "output" / "callgraph.json")
    parser.add_argument("--output", type=Path, default=script_dir / "output" / "keil_stack.json")
    parser.add_argument("--source-root", type=Path, default=script_dir.parent.parent)
    args = parser.parse_args()
    map_files = args.map_files or [script_dir / "FLASH_RAM" / "CMCELL_AC5_O0.map"]
    try:
        function_sources = build_function_source_index(args.callgraph, args.source_root)
        results = []
        for map_file in map_files:
            print(f"Parsing: {map_file}")
            results.extend(parse_map_file(map_file, function_sources))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Functions: {len(results)}")
    print(f"Output   : {args.output}")


if __name__ == "__main__":
    main()
