# IBM source provenance

The public-facing IBM package is a clean port of the completed Boston
implementation. It removes result persistence, authorization files, machine
paths and experiment identifiers while retaining the logical circuits,
layouts, measurement decoder and optimizer decisions.

The port was audited against the following frozen local sources (SHA-256):

| Role | Frozen source | SHA-256 |
|---|---|---|
| hardware engine | `ibm_hardware_step0/run_step0_greedy_session.py` | `35524acd2fb9b886363bb2abfde54cba708112914c3e95c0f9db0c2ed5fc6533` |
| steps 1--3 controller | `ibm_hardware_full_protocol/run_full_protocol_session.py` | `a2c54cffa13cfe0b1f1e29f0a2f77243f98fb739d3c93cd373afebdd41508281` |
| Step-3 batch completion | `ibm_hardware_full_protocol/run_step3_batch_resume.py` | `244ec0ca88aedc674fb96c73f8719563d37512fce3cbe9f5d5e32446b89e02ad` |
| Step-4 batch controller | `ibm_hardware_full_protocol/run_step4_batch.py` | `9142cdaa1dacac633964e069e489e8914e999bc4d28fd90a211fff76a51b6202` |
| Step-5 capped controller | `ibm_hardware_full_protocol/run_step5_budgeted_batch.py` | `20a9ec3570ac89e6a8ddc67e5b0931d4c806d9a9b2fd638f9c0c82efb592166d` |
| staged direction ranking | `local_dry_run/greedy_protocol.py` | `118ac949ce4a114071c5f772ed5bc30e98cdbdcd873de526c34fd2412097bb7f` |
| quadratic acceptance | `local_dry_run/legacy_repeat_protocol.py` | `d0d4dc5b99385c41f4198d0a840c92324adcc899b98cad00460e57604a75772b` |
| scan order/warm start | `local_dry_run/local_protocol.py` | `58bd3c84b9a27b37d7965281e6b424f365f04c252902775ef39f2f7d26a2335b` |
| IBM logical circuits | `qDMT/snansatz_circ_ibm.py` | `e4769c4475171992fe48e0894ee92ebcd01c4446da19e8cb2e39ae08ef5f43b9` |
| six-angle gate | `qDMT/snansatz_gates.py` | `c314dfbde0daf4eae67e1a3a2df334a4f87d3fa6acf6ca5fe91c2411aa361667` |
| MPS fixed point | `qDMT/snansatz.py` | `88a3578115cf8a9ca8c107fe8c50b6a22570a164a4fc6465eb1fe3c3cfd75717` |
| IBM parsing/readout | `qdmt_ibm/src/ibm_runtime.py` | `ac501e3ff3405c3ed071e5de7644d9483303fc8a355d75bbdd457b6aabb30ea3` |

## Equivalence checks performed during the port

- the clean six-angle unitary agreed with the frozen implementation to a
  Frobenius norm of `3.81e-16` for an independent parameter vector;
- the right-fixed-point eigenvalues and Euler angles agreed to floating-point
  precision;
- generated purity and split-fidelity circuits had identical qubit/classical
  widths and operation counts to the frozen QASM generators; and
- the clean QASM triplet parses successfully with Qiskit 2.4.1.

These checks establish logical-circuit equivalence. Bit-for-bit transpiled
circuit reproduction additionally requires the recorded software versions,
the pytket parser path, the same IBM backend target/calibration and the same
transpiler behaviour. The repository therefore distinguishes reproducibility
of the algorithm from reproducibility of a historical cloud execution.

