"""Logical OpenQASM 2 circuit used for each Quantinuum objective sample."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .ansatz import ansatz_gate_qasm, fixed_point_gate_qasm


def _layer(label: str, body: str) -> str:
    return f"\n// {label}\n{body}"


def _swaptest(q0: int, q1: int, c0: int, c1: int, index: int, *, reset: bool) -> str:
    tail = f"reset q[{q1}];\nreset q[{q0}];" if reset else ""
    return f"""
    cx q[{q0}],q[{q1}];
    h q[{q0}];
    measure q[{q1}] -> m{c0}[{index}];
    measure q[{q0}] -> m{c1}[{index}];
    {tail}
    """


def _evolution(q0: int, q1: int, *, g: float, dt: float) -> str:
    return f"""
    rx({(-dt * g):.12e}) q[{q0}];
    rx({(-dt * g):.12e}) q[{q1}];
    cx q[{q0}], q[{q1}];
    rz({(-2.0 * dt):.12e}) q[{q1}];
    cx q[{q0}], q[{q1}];
    """


def _header(copies: int) -> str:
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{14 * copies}];",
    ]
    for copy in range(copies):
        shift = 4 * copy
        lines.extend(
            [
                f"creg m{shift}[3];",
                f"creg m{shift + 1}[3];",
                f"creg m{shift + 2}[4];",
                f"creg m{shift + 3}[4];",
            ]
        )
    return "\n".join(lines) + "\n"


def _purity_block(candidate: np.ndarray, copy: int) -> str:
    q, c = 14 * copy, 4 * copy
    return "".join(
        [
            _layer(
                "purity fixed points",
                fixed_point_gate_qasm(candidate, (q, q + 1))
                + fixed_point_gate_qasm(candidate, (q + 5, q + 4)),
            ),
            _layer(
                "purity tensor layer 1",
                ansatz_gate_qasm(candidate, (q + 1, q + 2))
                + ansatz_gate_qasm(candidate, (q + 4, q + 3)),
            ),
            _layer("purity swap 1", _swaptest(q + 1, q + 4, c, c + 1, 0, reset=True)),
            _layer(
                "purity tensor layer 2",
                ansatz_gate_qasm(candidate, (q + 2, q + 1))
                + ansatz_gate_qasm(candidate, (q + 3, q + 4)),
            ),
            _layer("purity swap 2", _swaptest(q + 2, q + 3, c, c + 1, 1, reset=True)),
            _layer(
                "purity tensor layer 3",
                ansatz_gate_qasm(candidate, (q + 1, q + 2))
                + ansatz_gate_qasm(candidate, (q + 4, q + 3)),
            ),
            _layer("purity swap 3", _swaptest(q + 1, q + 4, c, c + 1, 2, reset=False)),
        ]
    )


def _fidelity_block(target: np.ndarray, candidate: np.ndarray, copy: int, g: float, dt: float) -> str:
    q, c = 14 * copy + 6, 4 * copy
    effective_dt = 2.0 * dt
    return "".join(
        [
            _layer(
                "fidelity fixed points",
                fixed_point_gate_qasm(target, (q, q + 1))
                + fixed_point_gate_qasm(candidate, (q + 7, q + 6)),
            ),
            _layer(
                "fidelity tensor layer 1",
                ansatz_gate_qasm(target, (q + 1, q + 2))
                + ansatz_gate_qasm(candidate, (q + 6, q + 5)),
            ),
            _layer(
                "fidelity tensor layer 2",
                ansatz_gate_qasm(target, (q + 2, q + 3))
                + ansatz_gate_qasm(candidate, (q + 5, q + 4)),
            ),
            _layer("first evolution", _evolution(q + 1, q + 2, g=g, dt=effective_dt)),
            _layer(
                "fidelity swaps 1 and 2",
                _swaptest(q + 1, q + 6, c + 2, c + 3, 0, reset=True)
                + _swaptest(q + 2, q + 5, c + 2, c + 3, 1, reset=True),
            ),
            _layer(
                "fidelity tensor layer 3",
                ansatz_gate_qasm(target, (q + 3, q + 2))
                + ansatz_gate_qasm(candidate, (q + 4, q + 5)),
            ),
            _layer(
                "fidelity tensor layer 4",
                ansatz_gate_qasm(target, (q + 2, q + 1))
                + ansatz_gate_qasm(candidate, (q + 5, q + 6)),
            ),
            _layer("second evolution", _evolution(q + 3, q + 2, g=g, dt=effective_dt)),
            _layer(
                "fidelity swaps 3 and 4",
                _swaptest(q + 3, q + 4, c + 2, c + 3, 2, reset=False)
                + _swaptest(q + 2, q + 5, c + 2, c + 3, 3, reset=False),
            ),
        ]
    )


def combined_objective_qasm(
    target_parameters: Sequence[float],
    candidate_parameters: Sequence[Sequence[float]],
    *,
    g: float = 0.2,
    dt: float = 0.2,
) -> str:
    """Return one or more packed objective circuits in the historical layout."""
    target = np.asarray(target_parameters, dtype=float)
    candidates = [np.asarray(candidate, dtype=float) for candidate in candidate_parameters]
    if target.shape != (6,) or not candidates or any(x.shape != (6,) for x in candidates):
        raise ValueError("target and every candidate must contain six parameters")
    body = "".join(
        _purity_block(candidate, copy)
        + _fidelity_block(target, candidate, copy, float(g), float(dt))
        for copy, candidate in enumerate(candidates)
    )
    return _header(len(candidates)) + body


def objective_qasm(
    target_parameters: Sequence[float],
    candidate_parameters: Sequence[float],
    *,
    g: float = 0.2,
    dt: float = 0.2,
) -> str:
    """Return the executed single-copy 14-qubit objective circuit."""
    return combined_objective_qasm(
        target_parameters, [candidate_parameters], g=g, dt=dt
    )

