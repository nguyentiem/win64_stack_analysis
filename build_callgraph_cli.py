#!/usr/bin/env python3

import json
import shlex
import sys
from pathlib import Path

from build_callgraph_gui import (
    CallGraphEngine,
    collect_source_files,
    discover_include_dirs,
    STUB_INCLUDE_DIR,
)

SCRIPT_DIR = Path(__file__).resolve().parent

# cellular/
CELLULAR_ROOT = SCRIPT_DIR.parents[1]

SOURCE_DIRS = [
    CELLULAR_ROOT / "com",
    CELLULAR_ROOT / "cellular",
    CELLULAR_ROOT / "modem",
]

OUTPUT_DIR = SCRIPT_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON = OUTPUT_DIR / "callgraph.json"


def main():
    extra_args = sys.argv[1:]

    source_dirs = [str(p) for p in SOURCE_DIRS]

    print("Source folders:")
    for d in SOURCE_DIRS:
        print(f"  {d}")

    files = collect_source_files(source_dirs, [])

    if not files:
        print("ERROR: no .c files found")
        return 1

    include_dirs = discover_include_dirs(source_dirs)

    clang_args = [
        "-nostdinc",
        "-I" + STUB_INCLUDE_DIR,
    ]

    clang_args.extend(extra_args)

    clang_args.extend(
        "-I" + d
        for d in sorted(set(include_dirs))
    )

    print(f"Found {len(files)} source files")
    print(f"Found {len(set(include_dirs))} include directories")

    engine = CallGraphEngine()
    engine.parse(files, clang_args)

    indirect_edges, unresolved = engine.resolved_indirect_edges()

    unresolved = [
        x
        for x in unresolved
        if not engine.is_ignored_external_call(x[1])
    ]

    print()
    print("========== SUMMARY ==========")
    print(f"Functions          : {len(engine.known_functions)}")
    print(f"Points-to          : {len(engine.points_to)}")
    print(f"Direct edges       : {len(engine.direct_edges)}")
    print(f"Indirect edges     : {len(indirect_edges)}")
    print(f"Unresolved calls   : {len(unresolved)}")
    print("=============================")

    for diag in engine.diagnostics:
        print(diag)

    edges = engine.all_edges()

    OUTPUT_JSON.parent.mkdir(exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            edges,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(f"Output: {OUTPUT_JSON}")
    print(f"Total edges: {len(edges)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())