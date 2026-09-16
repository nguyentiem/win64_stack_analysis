import contextlib
import io
import random
import unittest
from stack_callgraph import find_paths, find_paths_cached, graph_roots

class CachedSearchTests(unittest.TestCase):
    def test_matches_exhaustive_search(self):
        rng = random.Random(20260916)
        for sample in range(100):
            nodes = [(str(i), 'test.c') for i in range(7)]
            frames = {n: rng.choice([0, 0, 8, 32, 100]) for n in nodes}
            adjacency = {n: {c for c in nodes if rng.random() < .23} for n in nodes}
            roots = graph_roots({(a,b) for a in nodes for b in adjacency[a]})
            starts = roots or {nodes[0]}
            expected, _, partial = find_paths(adjacency, frames, 7, 1000000, starts, 20)
            with contextlib.redirect_stdout(io.StringIO()):
                actual, _, cached_partial = find_paths_cached(adjacency, frames, starts, 20)
            self.assertFalse(partial)
            self.assertFalse(cached_partial)
            self.assertEqual([p.stack_bytes for p in expected], [p.stack_bytes for p in actual], sample)
            for path in actual:
                self.assertEqual(len(path.nodes), len(set(path.nodes)))
                self.assertEqual(path.stack_bytes, sum(frames[n] for n in path.nodes))
                self.assertIn(path.nodes[0], starts)
                self.assertTrue(all(b in adjacency[a] for a,b in zip(path.nodes,path.nodes[1:])))

    def test_zero_frames_keep_path(self):
        a,b,c = [(n, 'test.c') for n in 'abc']
        with contextlib.redirect_stdout(io.StringIO()):
            paths, _, partial = find_paths_cached({a:{b},b:{c}}, {a:0,b:0,c:32}, {a})
        self.assertEqual(paths[0].nodes, (a,b,c))
        self.assertEqual(paths[0].stack_bytes, 32)
        self.assertFalse(partial)

if __name__ == '__main__':
    unittest.main()
