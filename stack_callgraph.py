#!/usr/bin/env python3
"""Find maximum stack-usage simple call paths using Keil stack JSON.

The JSON format is the one exported by callgraph_gui.py::

    {"caller": {"name": "...", "file": "..."},
     "callee": {"name": "...", "file": "..."}, "type": "direct"}

Direct and resolved indirect calls are included by default. Missing stack
values contribute zero. Recursive functions are counted once per simple path.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from functools import lru_cache
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import re



Node = tuple[str, str]  # (function name, normalized source file)


_GCC_CLONE_SUFFIX_RE = re.compile(
    r"""
    (?:
        \.(?:constprop|isra|part|clone)(?:\.\d+)?
        |
        \.cold(?:\.\d+)?
        |
        \.hot(?:\.\d+)?
        |
        \.lto_priv(?:\.\d+)?
    )$
    """,
    re.VERBOSE,
)


def load_keil_stack(
    filename: Path,
    source_root: Path,
) -> tuple[dict[Node, int], set[Node], list[str]]:
    """
    Read stack usage from keil_stack.json.

    Format:
    [
      {
        "name": "perform_action",
        "source_file": "cellular/src/cell_connect.c",
        "stack_bytes": 456
      }
    ]
    """
    try:
        content = json.loads(
            filename.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Cannot read Keil stack JSON {filename}: {exc}"
        ) from exc

    if not isinstance(content, list):
        raise ValueError(
            "Keil stack JSON root must be a list"
        )

    frames: dict[Node, int] = {}
    unknown: set[Node] = set()
    warnings: list[str] = []

    for index, item in enumerate(content, start=1):
        if not isinstance(item, dict):
            warnings.append(
                f"Keil stack entry {index}: not an object"
            )
            continue

        name = item.get("name")
        file_name = item.get(
            "source_file",
            item.get("file", ""),
        )
        stack_bytes = item.get("stack_bytes")

        if not isinstance(name, str) or not name.strip():
            warnings.append(
                f"Keil stack entry {index}: missing function name"
            )
            continue

        # Keep functions without a known source file
        # for matching by a unique function name.
        if not isinstance(file_name, str):
            file_name = ""

        if not isinstance(stack_bytes, int) or stack_bytes < 0:
            warnings.append(
                f"Keil stack entry {index}: invalid stack_bytes "
                f"for {name}"
            )
            continue

        node = (
            canonical_function(name),
            canonical_file(file_name, source_root),
        )

        # Keep the largest stack value for duplicate function + source entries.
        frames[node] = max(
            frames.get(node, 0),
            stack_bytes,
        )

    return frames, unknown, warnings

def canonical_function(name: str) -> str:
    """Map GCC-generated function clones back to the original function name."""
    result = name.strip()

    # A function can have multiple optimization suffixes, for example:
    # foo.constprop.0.isra.1
    while True:
        normalized = _GCC_CLONE_SUFFIX_RE.sub("", result)
        if normalized == result:
            return result
        result = normalized

@dataclass(frozen=True)
class PathResult:
    nodes: tuple[Node, ...]
    stack_bytes: int


def normalise_path(value: str) -> str:
    """Normalise paths without resolving them (many inputs are cross-host)."""
    return value.replace("\\", "/").replace("//", "/").lower()


def source_candidates(value: str, source_root: Path) -> set[str]:
    path = normalise_path(value)
    candidates = {path}
    root = normalise_path(str(source_root.resolve())).rstrip("/")
    if path.startswith(root + "/"):
        candidates.add(path[len(root) + 1 :])
    for marker in ("cellular/", "com/", "modem/"):
        index = path.rfind(marker)
        if index >= 0:
            candidates.add(path[index:])
    return candidates


def canonical_file(value: str, source_root: Path) -> str:
    """Use a repository-relative suffix where possible for stable matching."""
    candidates = source_candidates(value, source_root)
    return min(candidates, key=lambda candidate: (len(candidate), candidate))


def parse_node(value: object, source_root: Path) -> Node | None:
    if not isinstance(value, dict):
        return None
    name, file_name = value.get("name"), value.get("file")
    if not isinstance(name, str) or not isinstance(file_name, str) or not name:
        return None
    return canonical_function(name), canonical_file(file_name, source_root)


def load_edges(
    filename: Path, source_root: Path, direct_only: bool, include_manual: bool
) -> tuple[set[tuple[Node, Node]], list[str]]:
    try:
        content = json.loads(filename.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read callgraph JSON {filename}: {exc}") from exc
    if not isinstance(content, list):
        raise ValueError("Callgraph JSON root must be a list of edges")

    edges: set[tuple[Node, Node]] = set()
    warnings: list[str] = []
    for index, item in enumerate(content, start=1):
        if not isinstance(item, dict):
            warnings.append(f"edge {index}: not an object")
            continue
        edge_type = item.get("type", "direct")
        if direct_only and edge_type != "direct":
            continue
        if edge_type == "manual" and not include_manual:
            continue
        caller = parse_node(item.get("caller"), source_root)
        callee = parse_node(item.get("callee"), source_root)
        if caller is None or callee is None:
            warnings.append(f"edge {index}: missing caller/callee name or file")
            continue
        edges.add((caller, callee))
    return edges, warnings


def resolve_graph_nodes(
    graph_nodes: set[Node], stack: dict[Node, int]
) -> tuple[dict[Node, Node], list[Node]]:
    """Exact match first; safely fall back to a unique function-name match."""
    by_name: dict[str, list[Node]] = defaultdict(list)
    for node in stack:
        by_name[node[0]].append(node)
    resolved: dict[Node, Node] = {}
    ambiguous: list[Node] = []
    for node in graph_nodes:
        if node in stack:
            resolved[node] = node
        elif len(by_name[node[0]]) == 1:
            resolved[node] = by_name[node[0]][0]
        elif node[0] in by_name:
            ambiguous.append(node)
    return resolved, ambiguous


def graph_roots(edges: set[tuple[Node, Node]]) -> set[Node]:
    """Return functions without incoming edges; stack data does not affect roots."""
    nodes = {node for edge in edges for node in edge}
    incoming = {callee for _, callee in edges}
    return nodes - incoming


def estimate_path_potential(
    adjacency: dict[Node, set[Node]], frames: dict[Node, int], depth: int
) -> dict[Node, int]:
    """Estimate high-stack successors to order DFS, without changing results.

    The estimate intentionally permits cycles: it is only a work-ordering
    heuristic.  Actual paths below still reject a repeated node.
    """
    score = dict(frames)
    for _ in range(depth):
        next_score = {
            node: frames[node] + max((score[child] for child in adjacency.get(node, ())
                                      if child in score), default=0)
            for node in frames
        }
        if next_score == score:
            break
        score = next_score
    return score


def find_paths(
    adjacency: dict[Node, set[Node]], frames: dict[Node, int], limit: int,
    max_expansions: int, starts: Iterable[Node], keep_top: int = 20,
) -> tuple[list[PathResult], list[tuple[Node, ...]], bool]:
    """Enumerate the best simple paths, stopping a branch at recursive edges.

    A recursive cycle has no finite stack bound without an application-specific
    recursion-depth limit.  It is returned separately and never counted twice.
    """
    results: list[PathResult] = []
    cycles: set[tuple[Node, ...]] = set()
    expansions = 0
    next_progress = time.monotonic() + 15
    depth_truncated = False
    potential = estimate_path_potential(adjacency, frames, min(limit, 128))
    for start in sorted(starts, key=lambda item: (item[0], item[1])):
        stack: list[tuple[Node, tuple[Node, ...], int, frozenset[Node]]] = [
            (start, (start,), frames[start], frozenset((start,)))
        ]
        while stack:
            if expansions >= max_expansions:
                results.sort(key=lambda item: (-item.stack_bytes, tuple(node[0] for node in item.nodes)))
                return results[:keep_top], sorted(cycles, key=lambda cycle: tuple(node[0] for node in cycle)), True
            current, path, total, seen = stack.pop()
            expansions += 1
            if expansions % 100000 == 0 and time.monotonic() >= next_progress:
                best = max((result.stack_bytes for result in results), default=0)
                print(f"Search: {expansions:,} states; current root: {start[0]}; best: {best} B", flush=True)
                next_progress = time.monotonic() + 15
            next_nodes = adjacency.get(current, ())
            # ``stack`` is LIFO: append lower potential first so the most
            # promising successor is examined first.
            usable = sorted(
                (node for node in next_nodes if node in frames and node not in seen),
                key=lambda node: (potential.get(node, 0), frames[node], node[0], node[1]),
            )
            for node in next_nodes:
                if node in seen:
                    begin = path.index(node)
                    cycles.add(path[begin:] + (node,))
            if not usable or len(path) >= limit:
                if usable and len(path) >= limit:
                    depth_truncated = True
                results.append(PathResult(path, total))
                if len(results) >= max(1000, keep_top * 2):
                    results.sort(key=lambda item: (-item.stack_bytes, item.nodes))
                    del results[keep_top:]
                continue

            for node in usable:
                stack.append(
                    (
                        node,
                        path + (node,),
                        total + frames[node],
                        seen | {node},
                    )
                )
    results.sort(key=lambda item: (-item.stack_bytes, tuple(node[0] for node in item.nodes)))
    return results[:keep_top], sorted(cycles, key=lambda cycle: tuple(node[0] for node in cycle)), depth_truncated


def find_paths_cached(adjacency, frames, starts, keep_top=20):
    """Compute exact top simple paths, reusing suffixes within SCC visit states.

    A visited mask is retained only inside the current strongly connected
    component. Once a path leaves it, it cannot return, so earlier masks are
    irrelevant. The bounded cache limits memory without changing the answer.
    Cycles are reported as representative DFS back-edge cycles.
    """
    starts = tuple(starts)
    reachable = set(starts)
    pending = list(starts)
    while pending:
        node = pending.pop()
        for child in adjacency.get(node, ()):
            if child not in reachable:
                reachable.add(child)
                pending.append(child)
    nodes = sorted(reachable)
    children = {n: tuple(sorted(adjacency.get(n, ()))) for n in nodes}
    reverse = defaultdict(set)
    for node in nodes:
        for child in children[node]:
            reverse[child].add(node)
    seen, order, cycles = set(), [], set()
    for start in nodes:
        if start in seen:
            continue
        seen.add(start)
        active = [start]
        active_positions = {start: 0}
        pending = [(start, iter(children[start]))]
        while pending:
            node, iterator = pending[-1]
            child = next(iterator, None)
            if child is None:
                pending.pop()
                active.pop()
                active_positions.pop(node)
                order.append(node)
            elif child in active_positions:
                cycles.add(tuple(active[active_positions[child]:] + [child]))
            elif child not in seen:
                seen.add(child)
                active_positions[child] = len(active)
                active.append(child)
                pending.append((child, iter(children[child])))
    components, bits = {}, {}
    for start in reversed(order):
        if start in components:
            continue
        component = len(components)
        components[start] = component
        pending, members = [start], []
        while pending:
            node = pending.pop()
            members.append(node)
            for parent in reverse[node]:
                if parent not in components:
                    components[parent] = component
                    pending.append(parent)
        for index, node in enumerate(sorted(members)):
            bits[node] = 1 << index

    calls = 0
    next_progress = time.monotonic() + 15
    @lru_cache(maxsize=20000)
    def suffix(node, visited):
        nonlocal calls, next_progress
        calls += 1
        if calls % 10000 == 0 and time.monotonic() >= next_progress:
            print(f"Search: {calls:,} suffix states; cache: {suffix.cache_info()}", flush=True)
            next_progress = time.monotonic() + 15
        candidates = []
        for child in children[node]:
            same_component = components[node] == components[child]
            if same_component and visited & bits[child]:
                continue
            child_mask = visited | bits[child] if same_component else bits[child]
            for result in suffix(child, child_mask):
                candidates.append(PathResult((node,) + result.nodes,
                                             frames[node] + result.stack_bytes))
            if len(candidates) > keep_top * 2:
                candidates.sort(key=lambda result: (-result.stack_bytes, result.nodes))
                del candidates[keep_top:]
        if not candidates:
            candidates.append(PathResult((node,), frames[node]))
        candidates.sort(key=lambda result: (-result.stack_bytes, result.nodes))
        return tuple(candidates[:keep_top])

    old_recursion_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_recursion_limit, len(nodes) * 4 + 100))
    try:
        results = []
        for start in sorted(starts):
            results.extend(suffix(start, bits[start]))
            results.sort(key=lambda result: (-result.stack_bytes, result.nodes))
            del results[keep_top:]
        print(f"Suffix search complete: {calls:,} computed states; {suffix.cache_info()}", flush=True)
        return results, sorted(cycles), False
    finally:
        suffix.cache_clear()
        sys.setrecursionlimit(old_recursion_limit)


def node_text(node: Node, frames: dict[Node, int]) -> str:
    return f"{node[0]} ({frames.get(node, 0)} B) — {node[1]}"


def markdown_report(
    paths: list[PathResult], cycles: list[tuple[Node, ...]], frames: dict[Node, int],
    edges: set[tuple[Node, Node]], unresolved: set[Node], ambiguous: list[Node],
    unknown: set[Node], top: int, limit: int, warnings: list[str], truncated: bool,
) -> str:
    lines = [
        "# Call-path stack analysis", "",
        f"- Functions in callgraph: {len(frames)}",
        f"- Functions with known static stack: {len(frames) - len(unresolved)}",
        f"- Callgraph edges considered: {len(edges)}",
        f"- Callgraph nodes without a known stack value: {len(unresolved)}",
        f"- Unknown stack functions: {len(unknown)}",
        f"- Maximum path length considered: {limit} functions", "",
        "## Highest known call paths", "",
        "Values are sums of Keil function stack values. Nodes without a known "
        "static stack value remain on the call path and contribute 0 B, including "
        "missing, ambiguous, and unknown values. This default does not prove "
        "that their actual stack usage is zero. Paths stop at recursive cycles.",
    ]
    if truncated:
        lines.extend((
            "",
            "**Partial result:** the search reached `--max-expanded-paths` or `--max-depth`; increase the limit "
            "to explore more paths. The listed maximum is not guaranteed to be global.",
        ))
    for index, result in enumerate(paths[:top], start=1):
        lines.extend(("", f"### {index}. {result.stack_bytes} B ({len(result.nodes)} frames)", ""))
        lines.extend(f"{position}. `{node_text(node, frames)}`" for position, node in enumerate(result.nodes, 1))
    if not paths:
        lines.extend(("", "No known call path could be formed."))
    if cycles:
        lines.extend(("", "## Recursive cycles", "", "Representative cycles are listed below; recursion can be unbounded without a depth limit:"))
        for cycle in cycles[:50]:
            lines.append("- " + " → ".join(f"`{node[0]}`" for node in cycle))
    if unresolved:
        lines.extend(("", "## Callgraph nodes without stack usage", ""))
        lines.extend(f"- `{node[0]}` — `{node[1]}`" for node in sorted(unresolved)[:200])
    if ambiguous:
        lines.extend(("", "## Ambiguous function matches", ""))
        lines.extend(f"- `{node[0]}` — `{node[1]}`" for node in sorted(ambiguous)[:200])
    if warnings:
        lines.extend(("", "## Input warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings[:200])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)

    # Folder containing stack_callgraph.py:
    # cellular/tools/stack_analysis_auto
    script_dir = Path(__file__).resolve().parent

    # Folder root:
    # cellular
    cellular_root = script_dir.parents[1]

    # Output folder:
    output_dir = script_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default input/output paths
    default_keil_stack = output_dir / "keil_stack.json"
    default_callgraph = output_dir / "callgraph.json"
    default_report = output_dir / "stack_call_paths.md"
    default_json = output_dir / "stack_call_paths.json"

    parser.add_argument(
        "--keil-stack",
        type=Path,
        default=default_keil_stack,
        help=(
            "Keil stack JSON generated from the map file "
            f"(default: {default_keil_stack})"
        ),
    )

    parser.add_argument(
        "--callgraph",
        type=Path,
        default=default_callgraph,
        help=(
            "Callgraph JSON exported by the callgraph builder "
            f"(default: {default_callgraph})"
        ),
    )

    parser.add_argument(
        "--source-root",
        type=Path,
        default=cellular_root,
        help=(
            "Cellular source root used to normalize source paths "
            f"(default: {cellular_root})"
        ),
    )


    parser.add_argument(
        "--direct-only",
        action="store_true",
        help=(
            "Ignore resolved indirect edges "
            "(default includes direct and indirect edges)"
        ),
    )

    parser.add_argument(
        "--include-manual",
        action="store_true",
        default=True,
        help=(
            "Include manual JSON edges too "
            "(included by default to traverse the complete callgraph)"
        ),
    )

    parser.add_argument(
        "--include-non-direct",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--entry",
        action="append",
        metavar="FUNCTION",
        help=(
            "Analyse paths starting at this function; "
            "repeat for multiple entry functions"
        ),
    )

    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of paths in the report (default: 20)",
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum functions per path (default: all functions)",
    )

    parser.add_argument(
        "--max-expanded-paths",
        type=int,
        default=None,
        help=(
            "Stop after this many path states to avoid callback-path "
            "explosion (default: unlimited)"
        ),
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=default_report,
        help=(
            "Markdown report output "
            f"(default: {default_report})"
        ),
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=default_json,
        help=(
            "Machine-readable JSON output "
            f"(default: {default_json})"
        ),
    )

    args = parser.parse_args()

    if (
        args.top < 1
        or (args.max_depth is not None and args.max_depth < 1)
        or (args.max_expanded_paths is not None and args.max_expanded_paths < 1)
    ):
        parser.error(
            "--top, --max-depth, and --max-expanded-paths "
            "must be positive"
        )

    if not args.keil_stack.is_file():
        parser.error(
            f"Keil stack JSON file does not exist: {args.keil_stack}"
        )

    if not args.callgraph.is_file():
        parser.error(
            f"Callgraph JSON does not exist: {args.callgraph}"
        )

    print("========== INPUT ==========")
    print(f"Script folder : {script_dir}")
    print(f"Cellular root : {cellular_root}")
    print(f"Keil stack    : {args.keil_stack}")
    print(f"Callgraph     : {args.callgraph}")
    print(f"Report        : {args.report}")
    print(f"JSON result   : {args.json}")
    print("===========================")

    try:
        frames, unknown, warnings = load_keil_stack(args.keil_stack, args.source_root)
        edges, edge_warnings = load_edges(
            args.callgraph, args.source_root,
            args.direct_only and not args.include_non_direct, args.include_manual,
        )
        warnings.extend(edge_warnings)
    except ValueError as exc:
        parser.error(str(exc))

    graph_nodes = {
        node
        for edge in edges
        for node in edge
    }

    resolved, ambiguous = resolve_graph_nodes(
        graph_nodes,
        frames,
    )

    unresolved = graph_nodes - set(resolved)

    # Stack metadata must not determine graph connectivity: optimized builds
    # may omit records for functions that still appear in the input callgraph.
    graph_frames = {
        node: frames[resolved[node]] if node in resolved else 0
        for node in graph_nodes
    }

    adjacency: dict[Node, set[Node]] = defaultdict(set)
    graph_edges: set[tuple[Node, Node]] = set()

    for caller, callee in edges:
        adjacency[caller].add(callee)
        graph_edges.add((caller, callee))

    if args.entry:
        requested_entries = set(args.entry)

        starts = {
            node
            for node in graph_frames
            if node[0] in requested_entries
        }

        found_entry_names = {
            node[0]
            for node in starts
        }

        missing_entries = sorted(
            requested_entries - found_entry_names
        )

        if missing_entries:
            parser.error("Entry function(s) not found in callgraph: " + ", ".join(missing_entries))
    else:
        starts = graph_roots(graph_edges)
        if graph_nodes and not starts:
            warnings.append("No root functions: every function has an incoming call edge.")
    print(f"Starting functions: {len(starts)}", flush=True)

    use_cached_search = args.max_depth is None and args.max_expanded_paths is None
    args.max_depth = args.max_depth or max(1, len(graph_nodes))
    args.max_expanded_paths = args.max_expanded_paths or sys.maxsize
    if use_cached_search:
        paths, cycles, truncated = find_paths_cached(adjacency, graph_frames, starts, args.top)
    else:
        paths, cycles, truncated = find_paths(
            adjacency, graph_frames, args.max_depth,
            args.max_expanded_paths, starts, args.top,
        )

    report = markdown_report(
        paths,
        cycles,
        graph_frames,
        graph_edges,
        unresolved,
        ambiguous,
        unknown,
        args.top,
        args.max_depth,
        warnings,
        truncated,
    )

    args.report.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.report.write_text(
        report,
        encoding="utf-8",
    )

    best_stack = (
        paths[0].stack_bytes
        if paths
        else 0
    )

    print()
    print("========== RESULT ==========")
    print(f"Known stack functions : {len(frames)}")
    print(f"Graph edges used      : {len(graph_edges)}")
    print(f"Top paths retained    : {len(paths)}")
    print(f"Unresolved nodes      : {len(unresolved)}")
    print(f"Ambiguous nodes       : {len(ambiguous)}")
    print(f"Dynamic/unknown       : {len(unknown)}")
    print(f"Best known stack      : {best_stack} B")
    print("============================")

    print(
        f"Wrote {args.report} "
        f"({len(paths)} finite paths; best: {best_stack} B)"
    )

    if cycles:
        print(
            f"Warning: found {len(cycles)} recursive cycle(s); "
            "those totals are unbounded without a depth limit",
            file=sys.stderr,
        )

    if truncated:
        print(
            "Warning: path search stopped at "
            "--max-expanded-paths or --max-depth; result is partial",
            file=sys.stderr,
        )

    if args.json:
        data = {
            "format": "cmcell-callpath-stack-v1",
            "source_root": normalise_path(str(args.source_root)),
            "keil_stack": normalise_path(str(args.keil_stack)),
            "callgraph": normalise_path(str(args.callgraph)),
            "functions": [
                {
                    "name": node[0],
                    "file": node[1],
                    "stack_bytes": stack_bytes,
                }
                for node, stack_bytes in sorted((frames | graph_frames).items())
            ],
            "dynamic_or_unknown_functions": [
                {
                    "name": node[0],
                    "file": node[1],
                }
                for node in sorted(unknown)
            ],
            "paths": [
                {
                    "stack_bytes": item.stack_bytes,
                    "nodes": [
                        {
                            "name": node[0],
                            "file": node[1],
                            "stack_bytes": graph_frames[node],
                        }
                        for node in item.nodes
                    ],
                }
                for item in paths[:args.top]
            ],
            "recursive_cycles": [
                [
                    {
                        "name": node[0],
                        "file": node[1],
                    }
                    for node in cycle
                ]
                for cycle in cycles
            ],
            "search_algorithm": "cached SCC suffixes" if use_cached_search else "bounded DFS",
            "cycle_reporting": "representative cycles" if use_cached_search else "encountered cycles",
            "truncated": truncated,
            "entry_functions": [{"name": node[0], "file": node[1]} for node in sorted(starts)],
            "start_mode": "explicit entries" if args.entry else "roots (no incoming edges)",
            "max_depth": args.max_depth,
            "max_expanded_paths": args.max_expanded_paths,
            "missing_stack_bytes": 0,
            "path_kind": "simple (no repeated function)",
            "unresolved_nodes": [
                {
                    "name": node[0],
                    "file": node[1],
                }
                for node in sorted(unresolved)
            ],
            "ambiguous_nodes": [
                {
                    "name": node[0],
                    "file": node[1],
                }
                for node in sorted(ambiguous)
            ],
            "input_warnings": warnings,
        }

        args.json.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.json.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(f"Wrote {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())