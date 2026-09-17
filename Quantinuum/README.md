# Quantinuum H2-2 implementation

This directory is a clean, data-free reconstruction of the code used for the
QLOMPS experiment on Quantinuum H2-2. It contains the six-angle MPS tensor,
the combined 14-qubit purity/fidelity circuit, objective parsing, the
shot-frugal optimizer, and an optional QNexus/pytket adapter.

No hardware result, credential, job identifier, checkpoint or plotted
trajectory is included. Importing this package never submits a job. The
runtime adapter submits only when its explicit submission function is called.

## Executed setting

- backend and compile target: H2-2;
- transverse field `g = 0.2`, time step `dt = 0.2`;
- 500 shots per parameter-point circuit;
- one combined circuit supplied both purity and averaged-fidelity bits;
- objective: `P - 2 F`;
- driver method: `single_fold`.

At each physical step, damped extrapolation supplied the centre. Coordinate
directions were probed at `centre +/- radius * e_j`, in random order without
replacement. Screening stopped once the configured number of significant
directions was found. The largest resolved paired difference was sampled on a
six-, eight- or ten-point line grid. Quadratic fits were gated by curvature,
displacement, R-squared and residual scale; a fourth-order refit was used once
in the displayed run.

The actual trajectory also involved interrupted retrieval, offline refits of
already acquired samples and one post-hoc acceptance adjustment. These are
documented in [PROVENANCE.md](PROVENANCE.md), not silently idealized away.

```python
import numpy as np
from qlomps_quantinuum.circuits import objective_qasm

qasm = objective_qasm(np.zeros(6), np.ones(6) * 0.1)
```

The optional hardware adapter needs QNexus and pytket-quantinuum installed and
an independently configured account. Review every program before submission.
