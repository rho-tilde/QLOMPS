"""Six-angle MPS tensor and right-fixed-point preparation gates.

The matrix ordering and Euler-angle conventions match the implementation used
to generate the IBM Boston circuits.
"""

from __future__ import annotations

import numpy as np


def _rx(theta: float) -> np.ndarray:
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=np.complex128)


def _ry(theta: float) -> np.ndarray:
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=np.complex128)


def _rz(theta: float) -> np.ndarray:
    return np.array(
        [[np.exp(-1j * theta / 2.0), 0], [0, np.exp(1j * theta / 2.0)]],
        dtype=np.complex128,
    )


def _cnot() -> np.ndarray:
    return np.array(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=np.complex128,
    )


def reduced_unitary(parameters: np.ndarray) -> np.ndarray:
    """Return the 4x4 two-qubit unitary for the six-angle ansatz."""
    p = np.asarray(np.real_if_close(parameters, tol=1000), dtype=float)
    if p.shape != (6,):
        raise ValueError("parameters must contain exactly six real angles")

    phi1, phi2, phi3, psi3, phi6, psi7 = p
    psi1 = -np.pi / 2.0
    psi2 = np.pi / 2.0
    psi4 = -np.pi / 2.0
    psi6 = -np.pi / 2.0

    layers = (
        np.kron(_rx(phi1), _rx(psi1)),
        np.kron(_rz(phi2), _rz(psi2)),
        np.kron(np.eye(2), _rx(psi3)),
        _cnot(),
        np.kron(_rx(phi3), _rz(psi4)),
        np.kron(np.eye(2), np.eye(2)),
        _cnot(),
        np.kron(np.eye(2), _rz(psi6)),
        np.kron(_rz(phi6), _rx(psi7)),
    )
    unitary = np.eye(4, dtype=np.complex128)
    for layer in layers:
        unitary = layer @ unitary
    return unitary


def mps_tensor(parameters: np.ndarray) -> np.ndarray:
    """Extract the left-canonical `(D_left, physical, D_right)` tensor."""
    return reduced_unitary(parameters)[:, :2].reshape(2, 2, 2, order="C")


def _right_fixed_point(tensor: np.ndarray) -> np.ndarray:
    transfer = np.einsum("asb,csd->acbd", tensor, tensor.conj()).reshape(4, 4)
    values, vectors = np.linalg.eig(transfer)
    index = int(np.argmin(np.abs(values - 1.0)))
    if not np.isclose(values[index], 1.0, atol=1e-8, rtol=1e-8):
        raise ValueError("MPS transfer matrix has no unit right fixed point")
    right = vectors[:, index].reshape(2, 2)
    trace = np.trace(right)
    right /= trace / abs(trace)
    right = 0.5 * (right + right.conj().T)
    right *= np.sign(np.trace(right).real)
    right /= np.trace(right).real
    return right


def _zyz_angles(unitary: np.ndarray, eps: float = 1e-8) -> tuple[float, float, float]:
    a = complex(unitary[0, 0])
    b = complex(unitary[0, 1])
    ra, rb = abs(a), abs(b)
    if rb < eps:
        return float(-2.0 * np.angle(a)), 0.0, 0.0
    if ra < eps:
        return float(-2.0 * np.angle(-b)), float(np.pi), 0.0
    beta = 2.0 * np.arctan2(rb, ra)
    phi_a = np.angle(a)
    phi_b = np.angle(-b)
    return (
        float(-phi_a - phi_b),
        float(beta),
        float(-phi_a + phi_b),
    )


def right_fixed_point_gate_parameters(parameters: np.ndarray) -> tuple[float, ...]:
    """Return `(sqrt(lambda_0), sqrt(lambda_1), alpha, beta, gamma)`.

    The eigenvalues are ordered from largest to smallest. The final three
    angles prepare the fixed-point eigenbasis as `Rz(alpha) Ry(beta)
    Rz(gamma)`.
    """
    tensor = mps_tensor(parameters)
    canonical = sum(tensor[:, s, :].conj().T @ tensor[:, s, :] for s in range(2))
    if not np.allclose(canonical, np.eye(2), atol=1e-8, rtol=0.0):
        raise ValueError("ansatz tensor is not left canonical")
    eigenvalues, eigenvectors = np.linalg.eigh(_right_fixed_point(tensor))
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    diagonalizer = eigenvectors[:, order].conj().T
    alpha, beta, gamma = _zyz_angles(diagonalizer)
    return (
        float(np.sqrt(eigenvalues[0])),
        float(np.sqrt(eigenvalues[1])),
        alpha,
        beta,
        gamma,
    )


def ansatz_gate_qasm(parameters: np.ndarray, qubits: tuple[int, int] | list[int]) -> str:
    p = np.asarray(np.real_if_close(parameters, tol=1000), dtype=float)
    if p.shape != (6,):
        raise ValueError("parameters must contain exactly six real angles")
    q0, q1 = (int(qubits[0]), int(qubits[1]))
    phi1, phi2, phi3, psi3, phi6, psi7 = p
    return f"""
    // Six-angle QLOMPS tensor on qubits {q0} and {q1}
    rx({-np.pi / 2.0}) q[{q0}];
    rz({np.pi / 2.0}) q[{q0}];
    rx({psi3}) q[{q0}];
    rx({phi1}) q[{q1}];
    rz({phi2}) q[{q1}];
    cx q[{q1}],q[{q0}];
    rz({-np.pi / 2.0}) q[{q0}];
    rx({phi3}) q[{q1}];
    cx q[{q1}],q[{q0}];
    rz({-np.pi / 2.0}) q[{q0}];
    rx({psi7}) q[{q0}];
    rz({phi6}) q[{q1}];
    """


def fixed_point_gate_qasm(parameters: np.ndarray, qubits: tuple[int, int] | list[int]) -> str:
    d0, d1, alpha, beta, gamma = right_fixed_point_gate_parameters(parameters)
    q0, q1 = (int(qubits[0]), int(qubits[1]))
    theta = 2.0 * np.arctan2(d1, d0)
    return f"""
    ry({theta}) q[{q0}];
    cx q[{q0}], q[{q1}];
    rz({gamma}) q[{q1}];
    ry({beta}) q[{q1}];
    rz({alpha}) q[{q1}];
    """

