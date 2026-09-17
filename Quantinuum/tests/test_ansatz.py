import numpy as np

from qlomps_quantinuum.ansatz import mps_tensor, reduced_unitary


def test_reduced_unitary_is_unitary_and_tensor_is_left_canonical():
    parameters = np.array([0.2, -0.5, 0.7, 0.3, 1.1, -0.8])
    unitary = reduced_unitary(parameters)
    assert np.allclose(unitary.conj().T @ unitary, np.eye(4), atol=1e-12)
    tensor = mps_tensor(parameters)
    canonical = sum(tensor[:, s, :].conj().T @ tensor[:, s, :] for s in range(2))
    assert np.allclose(canonical, np.eye(2), atol=1e-12)

