"""Regression tests for call paths with incomplete stack metadata."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class StackCallgraphTests(unittest.TestCase):
    def analyse(self, records, calls, entry=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.su").write_text(records, encoding="utf-8")
            edges = [
                {"caller": {"name": caller, "file": "sample.c"},
                 "callee": {"name": callee, "file": "sample.c"},
                 "type": "direct"}
                for caller, callee in calls
            ]
            (root / "graph.json").write_text(json.dumps(edges), encoding="utf-8")
            command = [
                sys.executable, str(Path(__file__).with_name("stack_callgraph.py")),
                "--su-dir", str(root), "--source-root", str(root), "--all-sources",
                "--callgraph", str(root / "graph.json"),
                "--report", str(root / "report.md"), "--json", str(root / "result.json"),
            ]
            if entry:
                command.extend(["--entry", entry])
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return (json.loads((root / "result.json").read_text(encoding="utf-8")),
                    (root / "report.md").read_text(encoding="utf-8"))

    def test_missing_and_zero_intermediates_preserve_full_path(self):
        data, report = self.analyse(
            "sample.c:1:1:root\t16\tstatic\n"
            "sample.c:2:1:zero\t0\tstatic\n"
            "sample.c:3:1:leaf\t32\tstatic\n",
            [("root", "missing"), ("missing", "zero"), ("zero", "leaf")],
        )
        self.assertEqual(len(data["paths"]), 1)
        path = data["paths"][0]
        self.assertEqual(path["stack_bytes"], 48)
        self.assertEqual([(n["name"], n["stack_bytes"]) for n in path["nodes"]],
                         [("root", 16), ("missing", 0), ("zero", 0), ("leaf", 32)])
        self.assertEqual([n["name"] for n in data["unresolved_nodes"]], ["missing"])
        self.assertIn({"name": "missing", "file": "sample.c", "stack_bytes": 0},
                      data["functions"])
        self.assertIn("Callgraph edges considered: 3", report)
        self.assertIn("Functions with known static stack: 3", report)

    def test_missing_entry_and_all_missing_stack(self):
        data, _ = self.analyse("", [("entry", "leaf")], entry="entry")
        self.assertEqual(data["paths"][0]["stack_bytes"], 0)
        self.assertEqual([n["name"] for n in data["paths"][0]["nodes"]],
                         ["entry", "leaf"])

    def test_cycle_through_missing_node_is_detected(self):
        data, _ = self.analyse("sample.c:1:1:root\t16\tstatic\n",
                               [("root", "missing"), ("missing", "root")], entry="root")
        self.assertEqual([n["name"] for n in data["recursive_cycles"][0]],
                         ["root", "missing", "root"])
        self.assertEqual(data["paths"][0]["stack_bytes"], 16)


if __name__ == "__main__":
    unittest.main()
