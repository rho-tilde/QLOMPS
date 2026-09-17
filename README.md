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
- [`Quantinuum/`](Quantinuum/) is reserved for the independently audited H2
  implementation. It is kept separate because the H2 retrieval history and
  optimizer variants require their own provenance audit.

The IBM package is the first reproducibility target. See
[`IBM/README.md`](IBM/README.md) for the protocol-to-code map.

