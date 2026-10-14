"""Compile seed1.qasm with the sibling TopoLS checkout and verify its export."""
from pathlib import Path
import subprocess
import sys


def main():
    here = Path(__file__).resolve().parent
    subprocess.run([
        sys.executable, str(here.parent / "TopoLS/docs/prog.py"),
        "-f", "seed1", "-l", "3", "--engine", "python",
    ], cwd=here, check=True)

    import pyzx as zx
    from topols.export.bgraph import build_pipe_diagram, save_bigraph
    from topols.tools.pipe_sim import load_block_graph
    from tqec.interop.pyzx.positioned import PositionedZX

    nodes, edges = build_pipe_diagram(here / "result/topols/seed1.pkl")
    exported = here / "result/seed1.bgraph"
    save_bigraph(exported, nodes, edges)
    block = load_block_graph(exported)
    block.validate()
    positioned = PositionedZX.from_block_graph(block)
    graph = positioned.g
    expected = zx.Circuit.load(str(here / "benchmark/seed1.qasm"))
    graph.set_inputs(tuple(positioned.p2v[block.ports[f"input_{q}"]] for q in range(expected.qubits)))
    graph.set_outputs(tuple(positioned.p2v[block.ports[f"output_{q}"]] for q in range(expected.qubits)))
    zx.full_reduce(graph)
    assert zx.compare_tensors(expected, graph, preserve_scalar=False), "Exported BlockGraph is not equivalent to input QASM"
    print("Equivalent")


if __name__ == "__main__":
    main()
