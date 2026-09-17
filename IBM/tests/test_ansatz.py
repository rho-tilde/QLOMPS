import numpy as np

from qlomps_ibm.ansatz import (
    mps_tensor,
    reduced_unitary,
    right_fixed_point_gate_parameters,
)


PARAMETERS = np.array([-0.2, -0.7, 0.8, 0.3, 2.0, -1.0])


def test_reduced_unitary_is_unitary() -> None:
    unitary = reduced_unitary(PARAMETERS)
    np.testing.assert_allclose(unitary.conj().T @ unitary, np.eye(4), atol=1e-12)


def test_tensor_is_left_canonical() -> None:
    tensor = mps_tensor(PARAMETERS)
    canonical = sum(tensor[:, s, :].conj().T @ tensor[:, s, :] for s in range(2))
    np.testing.assert_allclose(canonical, np.eye(2), atol=1e-12)


def test_fixed_point_gate_parameters_are_finite() -> None:
    values = np.asarray(right_fixed_point_gate_parameters(PARAMETERS))
    assert values.shape == (5,)
    assert np.all(np.isfinite(values))
    np.testing.assert_allclose(values[0] ** 2 + values[1] ** 2, 1.0, atol=1e-12)

