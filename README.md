# CNOT-only circuit fails equivalence after export

An 8-qubit, 16-CNOT circuit fails equivalence after the official TopoLS
export/loader workflow, although `BlockGraph.validate()` passes.
The input uses Python `random.Random(1)`, drawing each ordered CNOT pair with
`sample(range(8), 2)`. This input seed is separate from TopoLS's default search seed 0.

## Reproduce (Linux / WSL, Python 3.13, uv)

Keep this folder beside the TopoLS checkout:

```text
TopoLS/
TopoLS_Issue/
```

```sh
cd TopoLS_Issue
uv sync
uv run reproduce.py
```

`reproduce.py` is the following:

```python
"""Compile seed0.qasm and seed1.qasm and verify the official exports."""
from pathlib import Path
import subprocess
import sys

import pyzx as zx
from topols.export.bgraph import build_pipe_diagram, save_bigraph
from topols.tools.pipe_sim import load_block_graph
from tqec.interop.pyzx.positioned import PositionedZX


def main(name):
    here = Path(__file__).resolve().parent
    print(f"=== {name} ===", flush=True)
    subprocess.run([
        sys.executable, str(here.parent / "TopoLS/docs/prog.py"),
        "-f", name, "-l", "3", "--engine", "python",
    ], cwd=here, check=True)

    nodes, edges = build_pipe_diagram(here / f"result/topols/{name}.pkl")
    exported = here / f"result/{name}.bgraph"
    save_bigraph(exported, nodes, edges)
    block = load_block_graph(exported)
    block.validate()
    positioned = PositionedZX.from_block_graph(block)
    graph = positioned.g
    expected = zx.Circuit.load(str(here / f"benchmark/{name}.qasm"))
    graph.set_inputs(tuple(positioned.p2v[block.ports[f"input_{q}"]] for q in range(expected.qubits)))
    graph.set_outputs(tuple(positioned.p2v[block.ports[f"output_{q}"]] for q in range(expected.qubits)))
    zx.full_reduce(graph)
    equivalent = zx.compare_tensors(expected, graph, preserve_scalar=False)
    print(f"{name}: equivalent = {equivalent}", flush=True)
    return equivalent


if __name__ == "__main__":
    # Check both inputs before reporting an equivalence failure.
    results = [main(name) for name in ("seed0", "seed1")]
    assert all(results), "Exported BlockGraph is not equivalent to input QASM"
```

Expected failure:

```text
=== seed0 ===
Executing seed0 benchmark.
HTable: 0 same-qubit H, 0 cross-qubit H, 49 registered nodes
Embedding progress:
 80%|███████████████████████████████████████████████████████████████████████▏                 | 4/5 [00:30<00:07,  7.61s/it]
Engine: python
x_length: 7.0 y_length: 7.0 z_length: 8
Space-time volume: 392.0
Time: 8
Space: 49.0
Compilation time: 30.44304585456848
seed0: equivalent = True
=== seed1 ===
Executing seed1 benchmark.
HTable: 0 same-qubit H, 0 cross-qubit H, 58 registered nodes
Embedding progress:
 83%|██████████████████████████████████████████████████████████████████████████▏              | 5/6 [00:42<00:08,  8.60s/it]
Engine: python
x_length: 7.0 y_length: 7.0 z_length: 9
Space-time volume: 441.0
Time: 9
Space: 49.0
Compilation time: 42.97967457771301
seed1: equivalent = False
Traceback (most recent call last):
  File "/home/hirok/University/TopoLS_Issue/reproduce.py", line 39, in <module>
    assert all(results), "Exported BlockGraph is not equivalent to input QASM"
           ~~~^^^^^^^^^
AssertionError: Exported BlockGraph is not equivalent to input QASM
```

