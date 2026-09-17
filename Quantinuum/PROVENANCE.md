# H2 provenance and evidence limits

The historical working tree was inspected read-only at
`/Users/phys2259/Documents/qDMT_ibm_quantinuum`. This port is based on these
local files as found on 17 September 2026:

| Historical file | SHA-256 |
|---|---|
| `qDMT/snansatz.py` | `88a3578115cf8a9ca8c107fe8c50b6a22570a164a4fc6465eb1fe3c3cfd75717` |
| `qDMT/snansatz_gates.py` | `c314dfbde0daf4eae67e1a3a2df334a4f87d3fa6acf6ca5fe91c2411aa361667` |
| `qDMT/snansatz_circ.py` | `dc4b56a9ca39c4527e715b1ff7ff5aa8bc164dad822852473e2dd1b379d32187` |
| `qDMT/snansatz_cost.py` | `a2a3a81dcab9dc67a05af4cf1471a44287b00c3139375ee985ef7edec9248dcd` |
| `qDMT/snansatz_evolution.py` | `1621dc94c854a4a4d2ce3df1c74ebf2f43368640ebff90f1d869323d6df8cf24` |
| `qDMT/configs/h2_run_config.py` | `7588db4f1e4c17203b53f07140482ac81bec525702db3b7aea92e9c2cbcb16bc` |
| `qDMT/batch_h2.py` | `a68b3ddd7dd443a02c25ed74f79f03afe621a3d39aef545826e67843bee06ce6` |
| `qDMT/retriever.py` | `897b21eccea788f5ab3b7e7c1267c8031933f7a44da35ace0a9bf90a1c60d04d` |

The historical repository identifies commit `6b67e4a` (`saving data etc`) as
the snapshot containing the step-3 recovery call. The working tree also has
later uncommitted edits; current driver arrays are therefore not sole evidence
for earlier decisions.

## Cleanly recoverable

The circuit generator is well determined. Each objective point used one
14-qubit OpenQASM 2 circuit with registers of widths 3, 3, 4 and 4. The first
two registers estimate three-site ansatz purity. The latter two estimate the
average of two three-site windows in a four-site overlap. The circuit was
parsed by pytket, compiled for H2-2 and submitted through QNexus with 500
shots.

The historical fixed-point routine used an iterative eigensolver whose
eigenvector phases were not canonicalized. Consequently, numerically
equivalent runs can differ by full-turn single-qubit phase rotations in the
fixed-point purification. The clean port fixes a deterministic eigenvector
gauge. Validation found identical instruction ordering, qubit/classical-bit
mapping and angles modulo these phase-gauge rotations.

The generic optimizer is also recoverable: damped polynomial extrapolation,
random coordinate screening without replacement, line-grid reuse, quadratic
gates and an optional quartic refit are implemented in `optimizer.py`.

## Executed-run qualifications

- Step 1 retained the extrapolated point after a rejected quadratic.
- Step 2 used a reconstructed fourth-order update; complete fit diagnostics
  and its exact invocation path were not preserved.
- Step 3 was refitted from recovered hardware samples with an executed
  residual ceiling of 0.09, while the interrupted online checkpoint stores
  the nominal value 0.08.
- Step 5 retained a fitted vertex post hoc after the original 0.07 residual
  gate rejected it. No exact predeclared replacement ceiling survives.
- Step 6 was refitted offline after a QNexus HTTP-500 retrieval failure using
  already acquired samples. A later accepted alternative endpoint was not
  selected by the plotting scripts.
- Step 7 was incomplete and excluded.

`protocol.py` therefore distinguishes nominal thresholds, executed recovery
thresholds and explicit selection exceptions. The package reproduces circuit
and decision machinery; it does not claim byte-for-byte replay of missing
service responses or an unrecoverable random direction order.

No environment lockfile was found. Present-day package versions are therefore
not asserted to be the versions installed during the hardware run.
