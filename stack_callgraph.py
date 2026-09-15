#!/usr/bin/env python3
"""Find high stack-usage call chains from GCC .su files and callgraph JSON.

The JSON format is the one exported by callgraph_gui.py::

    {"caller": {"name": "...", "file": "..."},
     "callee": {"name": "...", "file": "..."}, "type": "direct"}

Only direct calls are used by default: indirect and manual edges can be
included explicitly, but they are not compiler-proven call paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from analyze_callgraph import StackUsage, collect_stack_usage


Node = tuple[str, str]  # (function name, normalized source file)


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
        index = path.find(marker)
        if index >= 0:
            candidates.add(path[index:])
    return candidates


def canonical_file(value: str, source_root: Path) -> str:
    """Use a repository-relative suffix where possible for stable matching."""
    candidates = source_candidates(value, source_root)
    for candidate in candidates:
        if candidate.startswith(("cellular/", "com/", "modem/")):
            return candidate
    return min(candidates, key=len)


def parse_node(value: object, source_root: Path) -> Node | None:
    if not isinstance(value, dict):
        return None
    name, file_name = value.get("name"), value.get("file")
    if not isinstance(name, str) or not isinstance(file_name, str) or not name:
        return None
    return name, canonical_file(file_name, source_root)


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


def aggregate_stack(records: Iterable[StackUsage], source_root: Path) -> tuple[dict[Node, int], set[Node]]:
    """Return frame sizes keyed by function + source, keeping the largest duplicate.

    A source can appear in multiple build directories/configurations.  The
    largest value is safest for a worst-case report; dynamic or unknown GCC
    values are recorded separately. Graph nodes without a static value later
    receive a zero contribution while remaining visible in the report.
    """
    known: dict[Node, int] = {}
    unknown: set[Node] = set()
    for record in records:
        node = (record.function, canonical_file(record.source, source_root))
        if record.stack_bytes is None or "dynamic" in record.stack_kind:
            unknown.add(node)
            continue
        known[node] = max(known.get(node, 0), record.stack_bytes)
    return known, unknown


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
    max_expansions: int, starts: Iterable[Node],
) -> tuple[list[PathResult], list[tuple[Node, ...]], bool]:
    """Enumerate the best simple paths, stopping a branch at recursive edges.

    A recursive cycle has no finite stack bound without an application-specific
    recursion-depth limit.  It is returned separately and never counted twice.
    """
    results: list[PathResult] = []
    cycles: set[tuple[Node, ...]] = set()
    expansions = 0
    potential = estimate_path_potential(adjacency, frames, limit)
    for start in sorted(starts, key=lambda item: (item[0], item[1])):
        stack: list[tuple[Node, tuple[Node, ...], int, frozenset[Node]]] = [
            (start, (start,), frames[start], frozenset((start,)))
        ]
        while stack:
            if expansions >= max_expansions:
                results.sort(key=lambda item: (-item.stack_bytes, tuple(node[0] for node in item.nodes)))
                return results, sorted(cycles, key=lambda cycle: tuple(node[0] for node in cycle)), True
            current, path, total, seen = stack.pop()
            expansions += 1
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
            if not usable:
                results.append(PathResult(path, total))
                continue
            for node in usable:
                if len(path) >= limit:
                    results.append(PathResult(path, total))
                    continue
                stack.append((node, path + (node,), total + frames[node], seen | {node}))
    results.sort(key=lambda item: (-item.stack_bytes, tuple(node[0] for node in item.nodes)))
    return results, sorted(cycles, key=lambda cycle: tuple(node[0] for node in cycle)), False


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
        f"- Dynamic/unknown `.su` functions: {len(unknown)}",
        f"- Maximum path length considered: {limit} functions", "",
        "## Highest known call paths", "",
        "Values are sums of GCC static function frames only. Nodes without a known "
        "static stack value remain on the call path and contribute 0 B, including "
        "missing, ambiguous, and dynamic/unknown values. This default does not prove "
        "that their actual stack usage is zero. Paths stop at recursive cycles.",
    ]
    if truncated:
        lines.extend((
            "",
            "**Partial result:** the search reached `--max-expanded-paths`; increase that value "
            "to explore more paths. The listed maximum is not guaranteed to be global.",
        ))
    for index, result in enumerate(paths[:top], start=1):
        lines.extend(("", f"### {index}. {result.stack_bytes} B ({len(result.nodes)} frames)", ""))
        lines.extend(f"{position}. `{node_text(node, frames)}`" for position, node in enumerate(result.nodes, 1))
    if not paths:
        lines.extend(("", "No known call path could be formed."))
    if cycles:
        lines.extend(("", "## Recursive cycles", "", "These paths can be unbounded without a recursion-depth limit:"))
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
    parser.add_argument("--su-dir", required=True, type=Path, help="Build directory containing .su files")
    parser.add_argument("--callgraph", required=True, type=Path, help="JSON exported by callgraph_gui.py")
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--all-sources", action="store_true", help="Include emulator and third-party .su records")
    parser.add_argument(
        "--direct-only", action="store_true",
        help="Ignore resolved indirect edges (default includes direct and indirect edges)",
    )
    parser.add_argument(
        "--include-manual", action="store_true",
        help="Include manual JSON edges too (default excludes them because they are user assertions)",
    )
    parser.add_argument(
        "--include-non-direct", action="store_true", help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--entry", action="append", metavar="FUNCTION",
        help="Analyse paths starting at this function; repeat for multiple entry functions",
    )
    parser.add_argument("--top", type=int, default=20, help="Number of paths in the report (default: 20)")
    parser.add_argument("--max-depth", type=int, default=128, help="Maximum functions per path (default: 128)")
    parser.add_argument(
        "--max-expanded-paths", type=int, default=250000,
        help="Stop after this many path states to avoid callback-path explosion (default: 250000)",
    )
    parser.add_argument("--report", type=Path, default=Path("stack_call_paths.md"))
    parser.add_argument("--json", type=Path, help="Optional machine-readable result")
    args = parser.parse_args()
    if args.top < 1 or args.max_depth < 1 or args.max_expanded_paths < 1:
        parser.error("--top, --max-depth, and --max-expanded-paths must be positive")
    if not args.su_dir.is_dir():
        parser.error(f"Directory does not exist: {args.su_dir}")
    if not any(args.su_dir.rglob("*.su")):
        parser.error(f"No .su files found below {args.su_dir}")

    records, _raw, _outside, malformed = collect_stack_usage(args.su_dir, args.source_root, args.all_sources)
    frames, unknown = aggregate_stack(records, args.source_root)
    try:
        edges, warnings = load_edges(
            args.callgraph, args.source_root, args.direct_only, args.include_manual
        )
    except ValueError as exc:
        parser.error(str(exc))
    warnings.extend(f"malformed .su record: {item}" for item in malformed)
    graph_nodes = {node for edge in edges for node in edge}
    resolved, ambiguous = resolve_graph_nodes(graph_nodes, frames)
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
        starts = {node for node in graph_frames if node[0] in set(args.entry)}
        missing_entries = sorted(set(args.entry) - {node[0] for node in starts})
        if missing_entries:
            parser.error("Entry function(s) not found in callgraph: " + ", ".join(missing_entries))
    else:
        incoming = {callee for _caller, callee in graph_edges}
        starts = set(graph_frames) - incoming
        # A graph consisting entirely of cycles has no root. Analyse all nodes
        # in that exceptional case so the recursive-cycle warning is preserved.
        if not starts:
            starts = set(graph_frames)
    paths, cycles, truncated = find_paths(
        adjacency, graph_frames, args.max_depth, args.max_expanded_paths, starts
    )
    report = markdown_report(paths, cycles, graph_frames, graph_edges, unresolved, ambiguous, unknown,
                             args.top, args.max_depth, warnings, truncated)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    print(f"Wrote {args.report} ({len(paths)} finite paths; best: {paths[0].stack_bytes if paths else 0} B)")
    if cycles:
        print(f"Warning: found {len(cycles)} recursive cycle(s); those totals are unbounded without a depth limit", file=sys.stderr)
    if truncated:
        print("Warning: path search stopped at --max-expanded-paths; result is partial", file=sys.stderr)
    if args.json:
        data = {
            "format": "cmcell-callpath-stack-v1",
            "functions": [
                {"name": node[0], "file": node[1], "stack_bytes": stack_bytes}
                for node, stack_bytes in sorted((frames | graph_frames).items())
            ],
            "dynamic_or_unknown_functions": [
                {"name": node[0], "file": node[1]} for node in sorted(unknown)
            ],
            "paths": [
                {"stack_bytes": item.stack_bytes, "nodes": [
                    {"name": node[0], "file": node[1], "stack_bytes": graph_frames[node]}
                    for node in item.nodes]}
                for item in paths[:args.top]],
            "recursive_cycles": [[{"name": node[0], "file": node[1]} for node in cycle] for cycle in cycles],
            "truncated": truncated,
            "unresolved_nodes": [{"name": node[0], "file": node[1]} for node in sorted(unresolved)],
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
