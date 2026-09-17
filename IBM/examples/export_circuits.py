#!/usr/bin/env python3
"""Export the three logical QLOMPS circuits for inspection."""

from __future__ import annotations

import argparse
from pathlib import Path

from qlomps_ibm.circuits import circuit_triplet


def six_floats(values: list[str]) -> list[float]:
    parsed = [float(value) for value in values]
    if len(parsed) != 6:
        raise argparse.ArgumentTypeError("exactly six angles are required")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", nargs=6, required=True, type=float)
    parser.add_argument("--candidate", nargs=6, required=True, type=float)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, qasm in circuit_triplet(args.target, args.candidate).items():
        (args.output / f"{name}.qasm").write_text(qasm, encoding="utf-8")


if __name__ == "__main__":
    main()

