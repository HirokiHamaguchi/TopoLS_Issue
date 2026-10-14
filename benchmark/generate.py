"""Generate the 8-qubit, 16-CNOT inputs used in this report."""
from pathlib import Path
import random


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    for seed in range(10):
        rng = random.Random(seed)
        pairs = [rng.sample(range(8), 2) for _ in range(16)]
        lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[8];"]
        lines += [f"cx q[{control}],q[{target}];" for control, target in pairs]
        (here / f"seed{seed}.qasm").write_text("\n".join(lines) + "\n", newline="\n")
