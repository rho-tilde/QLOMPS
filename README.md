# QLOMPS

Code for the quantum local optimization of matrix-product-state (MPS) time
evolution used in the QLOMPS experiments.

The repository is intentionally code-only. It does **not** contain hardware
results, raw bitstrings, IBM job identifiers, Quantinuum result handles,
credentials, or manuscript data.

## Backends

- [`IBM/`](IBM/) contains the IBM implementation reconstructed from the
  completed `ibm_boston` experiment. It includes the exact circuit families,
  physical layouts, measurement decoding and classical directional-parabola
  optimizer.
- [`Quantinuum/`](Quantinuum/) contains the independently audited H2-2
  implementation: the combined full-swap circuit, measurement decoding,
  shot-frugal coordinate optimizer and an optional QNexus adapter. Its
  provenance file explicitly separates the clean circuit path from the
  manually recovered and post-hoc optimizer decisions in the displayed run.

See each backend's README and provenance file for its protocol-to-code map and
evidence limits.

## Paper, code snapshot and data

The manuscript uses commit
[`05329f8`](https://github.com/rho-tilde/QLOMPS/tree/05329f8) as its fixed
quantum-code snapshot. Supporting numerical and hardware data are deposited
in the UCL Research Data Repository at
[doi:10.5522/04/33898246](https://doi.org/10.5522/04/33898246).

## System requirements and installation

QLOMPS requires Python 3.10 or newer. The base installation requires NumPy
1.24 or newer, Qiskit 2.4 or newer but earlier than 3, and
`qiskit-ibm-runtime` 0.46 or newer but earlier than 1. The IBM parser was
validated with Qiskit 2.4.1. The optional IBM exact-parser path requires
`pytket` 2 or newer and `pytket-qiskit` 0.70 or newer. The optional
Quantinuum hardware adapter requires QNexus, `pytket` 2 or newer and
`pytket-quantinuum`.

The offline circuit-export demonstrations below were verified on macOS 27.2
with Python 3.12.14 and NumPy 2.3.5. They require only a standard desktop
computer and do not submit hardware jobs. Full hardware execution requires a
separately configured provider account and access to an IBM Heron r3 processor
or Quantinuum H2-2; credentials and hardware access are not included.

Create an environment and install the package with

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Allow approximately two to five minutes on an internet-connected modern
desktop, excluding installation and configuration of optional
hardware-provider SDKs.

## Offline demonstrations

The demonstrations use synthetic six-angle parameter vectors as their input,
so no external dataset or hardware access is required.

Export the three IBM logical circuits with

```bash
python IBM/examples/export_circuits.py \
  --target 0 0 0 0 0 0 \
  --candidate 0 0 0 0 0 0 \
  --output demo_ibm
```

The expected output is

```text
demo_ibm/purity.qasm
demo_ibm/fidelity_left.qasm
demo_ibm/fidelity_right.qasm
```

Export the Quantinuum objective circuit with

```bash
python Quantinuum/examples/export_qasm.py
```

The expected output is `h2_objective.qasm`, an OpenQASM 2 description of the
14-qubit objective circuit. Each export demonstration completed in less than
one second on the tested desktop. Neither command submits a hardware job.

## Instructions for use

The [IBM README](IBM/README.md) documents the logical circuits, fixed layouts,
measurement decoding, directional optimizer and optional runtime interface.
The [Quantinuum README](Quantinuum/README.md) documents the combined circuit,
objective parsing, optimizer protocol and optional QNexus adapter. Provider
credentials must be configured independently before any hardware submission.

Run the code-only tests from the repository root with

```bash
python -m pytest
```

## License

No explicit software license has currently been assigned to this repository.
The source is publicly accessible for research transparency and peer review;
all rights remain with the copyright holders.
