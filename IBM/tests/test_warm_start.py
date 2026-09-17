import numpy as np

from qlomps_ibm.warm_start import extrapolate


def test_damped_linear_extrapolation() -> None:
    points = [np.zeros(6), np.ones(6)]
    np.testing.assert_allclose(extrapolate(1, points, 0.8), np.full(6, 1.8))

