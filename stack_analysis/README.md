# Stack-usage inventory

Build the emulator with GCC callgraph output enabled:

```powershell
cmake --preset cmcell-local-stack
cmake --build emulator/build/cmcell-stack -j 8
```

`CMCELL_ENABLE_STACK_ANALYSIS` adds both `-fcallgraph-info=su` and
`-fstack-usage`. GCC writes one stack-usage file (`.su`) for each compiled C
source. The current script uses `.su` only and does not analyse the callgraph.

Create an inventory containing every compiled function and its own stack
frame:

```powershell
python tools/stack_analysis/analyze_callgraph.py `
  --su-dir emulator/build/cmcell-stack `
  --report emulator/build/cmcell-stack/stack_functions.md `
  --json emulator/build/cmcell-stack/stack_functions.json `
  --csv emulator/build/cmcell-stack/stack_functions.csv
```

The Markdown report is sorted by individual stack frame, largest first.  Each
row has:

- stack usage in bytes;
- GCC frame classification (`static`, `dynamic`, or `dynamic,bounded`);
- function name;
- source file and position.

By default, only source files under `cellular/`, `com/`, and `modem/` are
included.  This excludes the host emulator, CLI, and third-party libraries.
Use `--all-sources` only when an inventory of the complete emulator build is
needed.

`--ci-dir` remains accepted as a legacy alias for `--su-dir`; it does not read
the `.ci` files.  Call-path calculation, indirect-function resolution, and
graph output will be added as a separate later step.

The host emulator's numbers are useful for validating the pipeline. Generate
the final inventory with the target GCC configuration, because compiler, ABI,
target, and optimisation level affect frame sizes.
