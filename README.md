# CNOT-only circuit fails equivalence after export

Hello, I am Hiroki Hamaguchi, a PhD student at the University of Tokyo.

Thank you for developing TopoLS. TopoLS has been very helpful for our research, and we would like to cite it in our paper.

However, I encountered the equivalence mismatch reproduced below and would appreciate your help investigating and fixing it.

See also my repository made for this issue ([TopoLS_Issue](https://github.com/HirokiHamaguchi/TopoLS_Issue)).

## Issue

An 8-qubit, 16-CNOT randomly generated circuit (see also `benchmark/generate.py` in [my repository](https://github.com/HirokiHamaguchi/TopoLS_Issue/blob/master/benchmark/generate.py)) fails equivalence after the official TopoLS export/loader workflow, although `BlockGraph.validate()` passes.

### Reproduction

I provide a minimal reproduction of the issue.
I reproduced the issue on WSL2 with Python 3.13 and uv.

Keep this folder beside the TopoLS checkout:

```text
TopoLS/
TopoLS_Issue/
```

Then run the following commands:

```sh
cd TopoLS_Issue
uv sync
uv run reproduce.py
```

`reproduce.py` ([link to the file](https://github.com/HirokiHamaguchi/TopoLS_Issue/blob/master/reproduce.py)) is as follows:

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

    # Official PyZX equality-verification example:
    # https://pyzx.readthedocs.io/en/stable/notebooks/simplify.html#circuit-equality-verification
    equivalent = zx.compare_tensors(expected, graph, preserve_scalar=False)
    print(f"{name}: equivalent = {equivalent}", flush=True)
    return equivalent


if __name__ == "__main__":
    results = [main(name) for name in ("seed0", "seed1")]
    assert all(results), "Exported BlockGraph is not equivalent to input QASM"
```

The observed output is the following:

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

This indicates that the exported BlockGraph for `seed1` is not equivalent to the input QASM circuit, even though `BlockGraph.validate()` passes.

## Possible Fix

With assistance from an AI coding assistant, I traced a possible cause to the ceiling lift in `EmbeddingState.reward()`.
The lifted end of a branching X spider can become Z.
In the saved seed1 example, changing only that lifted ZX vertex back to X restored equivalence to the input circuit.

I tried the following small guard in `src/topols/embedding/state.py`:

```diff
--- a/src/topols/embedding/state.py
+++ b/src/topols/embedding/state.py
@@ -720,3 +720,6 @@
                     if ori_map[(last_dir, curr_type, self.node_type[node])] == 'k':
+                        # A branching endpoint must preserve the spider type.
+                        if self.output_connect[node] > 1:
+                            return None
                         ceiling_track[node]["ori"] = ori_map[(last_dir, curr_type, 1 if self.node_type[node]!=1 else 0)]
                         ceiling_track[node]["type"]= 1 if self.node_type[node]!=1 else 0
```

With this guard, input seeds 0-4 passed both BlockGraph validation and tensor equivalence, including the previously failing seed1. Still, seed5 failed with a duplicate `output_3` port-label error.

Although I have some understanding of ZX spiders and checked the code, I am not confident that this is the correct fix. I have found the implementation difficult to follow and do not yet fully understand its behavior.
I apologize if I have overlooked something, and would be grateful if you help investigate and fix the issue.

---

Thank you for your time and consideration.
