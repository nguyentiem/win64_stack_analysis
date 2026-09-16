#!/usr/bin/env python3

import json
import re
from collections import defaultdict
from pathlib import Path


STACK_PATTERN = re.compile(
    r"Stack Usage for\s+(.+?)\s+(0x[0-9a-fA-F]+|unknown)\s+bytes\.",
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
    result = []
    current_file = ""

    with open(
        map_file,
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        for line in f:
            match = STACK_PATTERN.search(line)

            if not match:
                continue

            function_name = match.group(1).strip()
            stack_text = match.group(2)

            stack_bytes = (
                0
                if stack_text.lower() == "unknown"
                else int(stack_text, 16)
            )

            sources = function_sources.get(function_name, [])

            if len(sources) == 1:
                # Hàm chỉ có một source trong callgraph.
                source_file = sources[0]
                current_file = source_file

            elif len(sources) > 1:
                # Hàm static trùng tên ở nhiều file.
                source_file = current_file

            else:
                # Standard library, IRQ hoặc không có trong callgraph.
                source_file = ""

            result.append(
                {
                    "name": function_name,
                    "source_file": source_file,
                    "stack_bytes": stack_bytes,
                }
            )

    return result


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    listings_dir = project_root / "uvproj" / "Listings"
    callgraph_file = script_dir / "output" / "callgraph.json"
    output_file = script_dir / "output" / "keil_stack.json"

    if not listings_dir.exists():
        raise FileNotFoundError(
            f"Không tìm thấy Listings: {listings_dir}"
        )

    if not callgraph_file.exists():
        raise FileNotFoundError(
            f"Không tìm thấy callgraph: {callgraph_file}"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    function_sources = build_function_source_index(
        callgraph_file,
        project_root,
    )

    map_files = sorted(listings_dir.glob("*.map"))

    if not map_files:
        raise FileNotFoundError(
            f"Không tìm thấy file .map trong: {listings_dir}"
        )

    all_results = []

    for map_file in map_files:
        print(f"Parsing: {map_file}")

        all_results.extend(
            parse_map_file(
                map_file,
                function_sources,
            )
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            all_results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Functions: {len(all_results)}")
    print(f"Output   : {output_file}")


if __name__ == "__main__":
    main()
