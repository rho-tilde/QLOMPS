"""Logical OpenQASM circuits submitted by the IBM QLOMPS protocol."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .ansatz import ansatz_gate_qasm, fixed_point_gate_qasm


def _layer(label: str, body: str) -> str:
    return f"\n// {label}\n{body}"


def _swap(q0: int, q1: int) -> str:
    return f"""
    cx q[{q0}],q[{q1}];
    cx q[{q1}],q[{q0}];
    cx q[{q0}],q[{q1}];
    """


def _pre_swaptest(q0: int, q1: int) -> str:
    return f"""
    cx q[{q0}],q[{q1}];
    h q[{q0}];
    """


def _complete_swaptest(
    q0: int,
    q1: int,
    index: int,
    *,
    flipped: bool = False,
) -> str:
    flip = f"x q[{q1}];\nx q[{q0}];" if flipped else ""
    return f"""
    {flip}
    measure q[{q1}] -> m0[{index}];
    measure q[{q0}] -> m1[{index}];
    """


def _swaptest(
    q0: int,
    q1: int,
    index: int,
    *,
    flipped: bool = False,
) -> str:
    return _pre_swaptest(q0, q1) + _complete_swaptest(
        q0, q1, index, flipped=flipped
    )


def _evolution(q0: int, q1: int, *, g: float, dt: float) -> str:
    """TFIM gate with the convention used by the hardware implementation."""
    rz_angle = -2.0 * dt
    rx_angle = -dt * g
    return f"""
    // TFIM evolution: g={g}, dt={dt}
    rx({rx_angle:.12e}) q[{q0}];
    rx({rx_angle:.12e}) q[{q1}];
    cx q[{q0}], q[{q1}];
    rz({rz_angle:.12e}) q[{q1}];
    cx q[{q0}], q[{q1}];
    """


def _header(register_width: int) -> str:
    return "\n".join(
        [
            "OPENQASM 2.0;",
            'include "qelib1.inc";',
            "qreg q[12];",
            f"creg m0[{register_width}];",
            f"creg m1[{register_width}];",
            "",
        ]
    )


def purity_qasm(parameters: Sequence[float]) -> str:
    """Return the 12-qubit ansatz-purity circuit."""
    theta = np.asarray(parameters, dtype=float)
    body = "".join(
        [
            _layer(
                "right fixed-point preparation",
                fixed_point_gate_qasm(theta, (1, 2))
                + fixed_point_gate_qasm(theta, (10, 9)),
            ),
            _layer(
                "sequential tensor layer 1",
                ansatz_gate_qasm(theta, (2, 3))
                + ansatz_gate_qasm(theta, (9, 8)),
            ),
            _layer(
                "sequential tensor layer 2",
                ansatz_gate_qasm(theta, (3, 4))
                + ansatz_gate_qasm(theta, (8, 7)),
            ),
            _layer(
                "sequential tensor layer 3",
                ansatz_gate_qasm(theta, (4, 5))
                + ansatz_gate_qasm(theta, (7, 6)),
            ),
            _layer("boundary routing", _swap(0, 1) + _swap(11, 10)),
            _layer(
                "destructive SWAP measurements",
                _swaptest(0, 11, 0) + _swaptest(5, 6, 1),
            ),
        ]
    )
    return _header(2) + body


def split_fidelity_qasm(
    target_parameters: Sequence[float],
    candidate_parameters: Sequence[float],
    *,
    side: str,
    g: float = 0.2,
    dt: float = 0.2,
    flipped: bool = False,
) -> str:
    """Return one of the two 12-qubit split-fidelity circuits."""
    if side not in {"left", "right"}:
        raise ValueError("side must be 'left' or 'right'")
    target = np.asarray(target_parameters, dtype=float)
    candidate = np.asarray(candidate_parameters, dtype=float)
    effective_dt = 2.0 * float(dt)

    common = "".join(
        [
            _layer(
                "target/candidate fixed points",
                fixed_point_gate_qasm(target, (0, 1))
                + fixed_point_gate_qasm(candidate, (11, 10)),
            ),
            _layer(
                "sequential tensor layer 1",
                ansatz_gate_qasm(target, (1, 2))
                + ansatz_gate_qasm(candidate, (10, 9)),
            ),
            _layer(
                "sequential tensor layer 2",
                ansatz_gate_qasm(target, (2, 3))
                + ansatz_gate_qasm(candidate, (9, 8)),
            ),
            _layer(
                "first evolution gate and tensor layer 3",
                _evolution(1, 2, g=g, dt=effective_dt)
                + ansatz_gate_qasm(target, (3, 4))
                + ansatz_gate_qasm(candidate, (8, 7)),
            ),
            _layer(
                "sequential tensor layer 4",
                ansatz_gate_qasm(target, (4, 5))
                + ansatz_gate_qasm(candidate, (7, 6)),
            ),
            _layer(
                "second evolution gate",
                _evolution(3, 4, g=g, dt=effective_dt),
            ),
        ]
    )

    if side == "left":
        routing = "".join(
            [
                _layer(
                    "left routing 1",
                    _swap(0, 1)
                    + _swap(3, 4)
                    + _swap(11, 10)
                    + _swap(8, 7),
                ),
                _layer(
                    "left premeasurement and routing",
                    _pre_swaptest(0, 11)
                    + _swap(1, 2)
                    + _swap(4, 5)
                    + _swap(10, 9)
                    + _swap(7, 6),
                ),
                _layer("left routing 2", _swap(0, 1) + _swap(11, 10)),
                _layer(
                    "left destructive SWAP measurements",
                    _complete_swaptest(1, 10, 0, flipped=flipped)
                    + _swaptest(0, 11, 1, flipped=flipped)
                    + _swaptest(5, 6, 2, flipped=flipped),
                ),
            ]
        )
    else:
        routing = "".join(
            [
                _layer(
                    "right routing 1",
                    _swap(1, 2)
                    + _swap(4, 5)
                    + _swap(10, 9)
                    + _swap(7, 6),
                ),
                _layer(
                    "right premeasurement and routing",
                    _pre_swaptest(5, 6)
                    + _swap(0, 1)
                    + _swap(3, 4)
                    + _swap(11, 10)
                    + _swap(8, 7),
                ),
                _layer("right routing 2", _swap(4, 5) + _swap(7, 6)),
                _layer(
                    "right destructive SWAP measurements",
                    _complete_swaptest(4, 7, 0, flipped=flipped)
                    + _swaptest(0, 11, 1, flipped=flipped)
                    + _swaptest(5, 6, 2, flipped=flipped),
                ),
            ]
        )

    return _header(3) + common + routing


def fidelity_left_qasm(
    target_parameters: Sequence[float],
    candidate_parameters: Sequence[float],
    *,
    g: float = 0.2,
    dt: float = 0.2,
) -> str:
    return split_fidelity_qasm(
        target_parameters,
        candidate_parameters,
        side="left",
        g=g,
        dt=dt,
    )


def fidelity_right_qasm(
    target_parameters: Sequence[float],
    candidate_parameters: Sequence[float],
    *,
    g: float = 0.2,
    dt: float = 0.2,
) -> str:
    return split_fidelity_qasm(
        target_parameters,
        candidate_parameters,
        side="right",
        g=g,
        dt=dt,
    )


def circuit_triplet(
    target_parameters: Sequence[float],
    candidate_parameters: Sequence[float],
    *,
    g: float = 0.2,
    dt: float = 0.2,
) -> dict[str, str]:
    """Return the three logical QASM circuits for one objective sample."""
    return {
        "purity": purity_qasm(candidate_parameters),
        "fidelity_left": fidelity_left_qasm(
            target_parameters, candidate_parameters, g=g, dt=dt
        ),
        "fidelity_right": fidelity_right_qasm(
            target_parameters, candidate_parameters, g=g, dt=dt
        ),
    }

