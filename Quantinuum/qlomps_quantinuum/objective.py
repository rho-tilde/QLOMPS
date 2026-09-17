"""Convert H2 measurement bitstrings into purity, fidelity and objective."""

from __future__ import annotations

import numpy as np


def _swap_expectation(left: np.ndarray, right: np.ndarray, indices: tuple[int, ...]) -> float:
    parity = np.sum(np.bitwise_and(left[:, indices], right[:, indices]), axis=1) % 2
    return float(2.0 * np.mean(parity == 0) - 1.0)


def objective_from_shots(bitstrings: np.ndarray, *, order: str = "forward") -> dict[str, float]:
    """Parse one circuit's 14 classical bits.

    `forward` matches the executed QNexus parser: `[m0(3), m1(3), m2(4),
    m3(4)]`. `reverse` supports exports returning registers oppositely.
    """
    bits = np.asarray(bitstrings, dtype=np.uint8)
    if bits.ndim != 2 or bits.shape[0] == 0 or bits.shape[1] != 14:
        raise ValueError("bitstrings must have shape (shots, 14)")
    if order == "forward":
        m0, m1 = bits[:, 0:3], bits[:, 3:6]
        m2, m3 = bits[:, 6:10], bits[:, 10:14]
    elif order == "reverse":
        m3, m2 = bits[:, 0:4], bits[:, 4:8]
        m1, m0 = bits[:, 8:11], bits[:, 11:14]
    else:
        raise ValueError("order must be 'forward' or 'reverse'")

    purity = _swap_expectation(m0, m1, (0, 1, 2))
    fidelity_left = _swap_expectation(m2, m3, (0, 1, 2))
    fidelity_right = _swap_expectation(m2, m3, (1, 2, 3))
    fidelity = 0.5 * (fidelity_left + fidelity_right)
    return {
        "purity": purity,
        "fidelity_left": fidelity_left,
        "fidelity_right": fidelity_right,
        "fidelity": fidelity,
        "cost": purity - 2.0 * fidelity,
    }

