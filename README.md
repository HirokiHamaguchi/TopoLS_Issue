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
uv venv --python 3.13
uv pip install -r requirements.txt
uv pip install --no-deps -e ../TopoLS
.venv/bin/python reproduce.py
```

Only dependencies used by this reproducer are installed. Rendering and Rust
dependencies are omitted. No lattice_surgery code or precomputed pickle is needed.

`reproduce.py` runs the official CLI with `-l 3 --engine python` and all other
defaults, exports and loads the result using official functions, then compares
the ZX tensors in logical-qubit port order, ignoring a global nonzero scalar.

Expected failure:

```text
AssertionError: Exported BlockGraph is not equivalent to input QASM
```

TopoLS checkout: `e564d350a596cfea3227e09698733210e2e14dcf`.
PyZX: `0.10.6`. TQEC: `0.2.0` (PyPI).
Generated files are under `result/`. The verification assertion is in this
reproducer; the TopoLS compilation itself completes.
Reproduced from a fresh environment with Python 3.13.6; see `run.log`.
