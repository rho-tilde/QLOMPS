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
