import numpy as np

from qlomps_quantinuum.optimizer import (
    accept_quadratic,
    choose_screen_direction,
    damped_extrapolation,
    missing_line_points,
    quadratic_fit,
)


def test_linear_damped_extrapolation():
    history = np.array([[0, 0, 0, 0, 0, 0], [1, 2, 3, 4, 5, 6]], dtype=float)
    assert np.allclose(damped_extrapolation(history, 1, 0.5), 1.5 * history[-1])


def test_screen_stops_after_keep_and_chooses_largest_difference():
    pairs = [
        {"direction": 3, "f_plus": 0.5, "f_minus": 0.4},
        {"direction": 1, "f_plus": 0.8, "f_minus": 0.1},
        {"direction": 4, "f_plus": 0.2, "f_minus": -0.2},
        {"direction": 0, "f_plus": 9.0, "f_minus": -9.0},
    ]
    result = choose_screen_direction(pairs, threshold=0.15, keep=2)
    assert len(result["consumed"]) == 3
    assert result["winner"]["direction"] == 1


def test_quadratic_fit_and_gate():
    t = np.linspace(-1, 1, 8)
    samples = np.column_stack([t, 0.4 * (t - 0.2) ** 2 - 0.3])
    accepted = accept_quadratic(
        quadratic_fit(samples), r2_min=0.7, sigma_max=0.1, t_max=0.5
    )
    assert accepted["accepted"]
    assert np.isclose(accepted["t0"], 0.2)


def test_screen_points_are_reused_when_close_to_grid():
    missing = missing_line_points([-0.6, 0.6], fit_range=1.0, fit_points=8)
    assert len(missing) == 6

