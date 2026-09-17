# IBM QLOMPS protocol

This directory contains a code-only reconstruction of the protocol actually
used for the completed Boston experiment (physical steps 0--5). It is not the
earlier aspirational protocol and it does not include experimental results.

## What was sent to the QPU

Every sampled six-angle parameter vector produced three 12-qubit circuits:

1. an ansatz-purity circuit;
2. a left split-fidelity circuit; and
3. a right split-fidelity circuit.

All three were sampled with 5,000 shots. The two fidelity circuits contain the
TFIM time-evolution gates for `g = 0.2` and `dt = 0.2`. Each observable is
decoded from destructive-SWAP parity. The measured objective is

`purity - fidelity_left - fidelity_right + target_purity`.

The target-purity term is constant during an optimizer acquisition and
therefore shifts the objective without changing a fitted direction or vertex.

The Boston physical layouts are frozen in `qlomps_ibm.constants`:

- purity and right fidelity: `[42, 41, 36, 21, 22, 23, 24, 25, 37, 45, 44, 43]`;
- left fidelity: `[24, 25, 37, 45, 44, 43, 42, 41, 36, 21, 22, 23]`.

`qlomps_ibm.circuits` is the authoritative description of the logical
circuits. `qlomps_ibm.runtime` performs the OpenQASM-to-Qiskit conversion,
applies the frozen layout, and decodes SamplerV2 results.

## Classical optimizer actually used

For each optimizer attempt, all six coordinate directions were first sampled
at ten offsets within `[-0.5, 0.5]`. A quadratic was fitted independently in
each direction, and directions were ranked by predicted improvement after
basic vertex/curvature checks. The other ten offsets were then acquired for
the top three directions.

If no top-three fit passed the final gates, the remaining three directions
were refined before a full decision. Otherwise the accepted top-three result
was used directly. A start and end sentinel at the current centre tested for
hardware drift; an acquisition was usable only for sentinel drift `z <= 3`.

A fit was actionable only when:

- the quadratic curvature was positive;
- its vertex lay inside the scan window;
- `R^2 >= 0.5`;
- moves larger than `0.25` additionally had `R^2 >= 0.7`; and
- predicted improvement was strictly greater than `1e-3`.

Among actionable fits, the direction with the highest `(R^2, predicted
improvement, -direction_index)` tuple was selected. If none was actionable,
the physical step converged. The complete rule is implemented in
`qlomps_ibm.optimizer`.

This staging corresponds to the actual IBM submissions:

- coarse scan plus start sentinel: 61 parameter samples / 183 circuits;
- top-three refinement: 30 samples / 90 circuits;
- end sentinel only: 1 sample / 3 circuits; or
- remaining-three refinement plus end sentinel: 31 samples / 93 circuits.

## Physical-step policy

Steps 1--5 used the accepted endpoint of the preceding step as their target.
Their starting point was a damped finite-difference extrapolation, implemented
in `qlomps_ibm.warm_start`. Steps 0--4 permitted up to eight optimizer
attempts. Step 5 used the later approved cap of four attempts, retained a move
found on the fourth attempt, and required review instead of automatically
starting a fifth confirmation attempt. Step 6 was not run.

The original run used Session mode for the early steps and Batch mode for the
later completion work. Session versus Batch changes scheduling, not the
logical circuits or fit rule represented here.

## Minimal use

Export the three logical OpenQASM circuits for one target/candidate pair:

```bash
python IBM/examples/export_circuits.py \
  --target 0 0 0 0 0 0 \
  --candidate 0 0 0 0 0 0 \
  --output /tmp/qlomps-circuits
```

The zero vectors above demonstrate the interface only; they are not
experimental parameters.

Run the code-only tests from the repository root:

```bash
python -m pytest
```

IBM authentication is intentionally left to Qiskit's standard account
configuration. No token, cloud resource name, instance identifier, job ID or
result file is stored here.

