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
