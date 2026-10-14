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

`reproduce.py` runs seed0 followed by seed1 using the official CLI with
`-l 3 --engine python` and all other
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

## Comparison input

`benchmark/seed0.qasm` uses the same generation rule with `random.Random(0)`.
Both inputs contain 8 qubits and 16 CNOTs and are run with the same compiler
settings, without command-line arguments. Each equivalence result is printed;
the assertion is checked after both inputs have been processed.
Seed0 has not yet been verified with this checkout.
