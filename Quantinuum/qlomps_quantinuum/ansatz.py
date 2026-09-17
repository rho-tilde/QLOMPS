"""Six-angle MPS tensor and right-fixed-point preparation used on H2-2."""

from __future__ import annotations

import numpy as np


def _rx(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2.0), np.sin(theta / 2.0)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=np.complex128)


def _rz(theta: float) -> np.ndarray:
    return np.diag([np.exp(-1j * theta / 2.0), np.exp(1j * theta / 2.0)])


def _cnot() -> np.ndarray:
    return np.array(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=np.complex128,
    )


def reduced_unitary(parameters: np.ndarray) -> np.ndarray:
    """Return the 4x4 two-qubit unitary for the executed six-angle ansatz."""
    p = np.asarray(np.real_if_close(parameters, tol=1000), dtype=float)
    if p.shape != (6,):
        raise ValueError("parameters must contain six real angles")
    phi1, phi2, phi3, psi3, phi6, psi7 = p
    layers = (
        np.kron(_rx(phi1), _rx(-np.pi / 2.0)),
        np.kron(_rz(phi2), _rz(np.pi / 2.0)),
        np.kron(np.eye(2), _rx(psi3)),
        _cnot(),
        np.kron(_rx(phi3), _rz(-np.pi / 2.0)),
        np.eye(4),
        _cnot(),
        np.kron(np.eye(2), _rz(-np.pi / 2.0)),
        np.kron(_rz(phi6), _rx(psi7)),
    )
    result = np.eye(4, dtype=np.complex128)
    for layer in layers:
        result = layer @ result
    return result


def mps_tensor(parameters: np.ndarray) -> np.ndarray:
    """Return the `(left bond, physical, right bond)` MPS tensor."""
    return reduced_unitary(parameters)[:, :2].reshape(2, 2, 2, order="C")


def _right_fixed_point(tensor: np.ndarray) -> np.ndarray:
    transfer = np.einsum("asb,csd->acbd", tensor, tensor.conj()).reshape(4, 4)
    values, vectors = np.linalg.eig(transfer)
    index = int(np.argmin(np.abs(values - 1.0)))
    if not np.isclose(values[index], 1.0, atol=1e-8, rtol=1e-8):
        raise ValueError("transfer matrix has no unit right fixed point")
    right = vectors[:, index].reshape(2, 2)
    phase = np.trace(right)
    right /= phase / abs(phase)
    right = 0.5 * (right + right.conj().T)
    right *= np.sign(np.trace(right).real)
    return right / np.trace(right).real


def _zyz_angles(unitary: np.ndarray, eps: float = 1e-8) -> tuple[float, float, float]:
    a, b = complex(unitary[0, 0]), complex(unitary[0, 1])
    if abs(b) < eps:
        return float(-2.0 * np.angle(a)), 0.0, 0.0
    if abs(a) < eps:
        return float(-2.0 * np.angle(-b)), float(np.pi), 0.0
    beta = 2.0 * np.arctan2(abs(b), abs(a))
    phi_a, phi_b = np.angle(a), np.angle(-b)
    return float(-phi_a - phi_b), float(beta), float(-phi_a + phi_b)


def right_fixed_point_gate_parameters(parameters: np.ndarray) -> tuple[float, ...]:
    """Return amplitudes and ZYZ angles for the right fixed-point gate."""
    tensor = mps_tensor(parameters)
    canonical = sum(tensor[:, s, :].conj().T @ tensor[:, s, :] for s in range(2))
    if not np.allclose(canonical, np.eye(2), atol=1e-8, rtol=0.0):
        raise ValueError("ansatz tensor is not left canonical")
    eigenvalues, eigenvectors = np.linalg.eigh(_right_fixed_point(tensor))
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    alpha, beta, gamma = _zyz_angles(eigenvectors[:, order].conj().T)
    return (
        float(np.sqrt(eigenvalues[0])),
        float(np.sqrt(eigenvalues[1])),
        alpha,
        beta,
        gamma,
    )


def ansatz_gate_qasm(parameters: np.ndarray, qubits: tuple[int, int]) -> str:
    p = np.asarray(np.real_if_close(parameters, tol=1000), dtype=float)
    if p.shape != (6,):
        raise ValueError("parameters must contain six real angles")
    q0, q1 = map(int, qubits)
    phi1, phi2, phi3, psi3, phi6, psi7 = p
    return f"""
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


def fixed_point_gate_qasm(parameters: np.ndarray, qubits: tuple[int, int]) -> str:
    d0, d1, alpha, beta, gamma = right_fixed_point_gate_parameters(parameters)
    q0, q1 = map(int, qubits)
    theta = 2.0 * np.arctan2(d1, d0)
    return f"""
    ry({theta}) q[{q0}];
    cx q[{q0}], q[{q1}];
    rz({gamma}) q[{q1}];
    ry({beta}) q[{q1}];
    rz({alpha}) q[{q1}];
    """

