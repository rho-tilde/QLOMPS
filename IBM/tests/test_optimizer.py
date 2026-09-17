import numpy as np

from qlomps_ibm.acquisition import coarse_rows, refinement_rows
from qlomps_ibm.optimizer import apply_selected_move, fit_directions


def test_stage_sizes_match_hardware_jobs() -> None:
    center = np.zeros(6)
    assert len(coarse_rows(center)) == 60
    assert len(refinement_rows(center, [0, 1, 2])) == 30


def test_quadratic_vertex_is_selected() -> None:
    samples = []
    offsets = np.linspace(-0.5, 0.5, 20)
    for direction in range(6):
        vertex = 0.1 if direction == 2 else 0.0
        scale = 2.0 if direction == 2 else 0.0001
        for t in offsets:
            samples.append(
                {
                    "direction": direction,
                    "t": float(t),
                    "actual_cost": float(scale * (t - vertex) ** 2),
                }
            )
    result = fit_directions(samples)
    assert result["selected_direction"] == 2
    np.testing.assert_allclose(result["selected_t_min"], 0.1, atol=1e-12)
    moved, decision = apply_selected_move(np.zeros(6), result)
    assert decision == "accept_greedy_move"
    np.testing.assert_allclose(moved[2], 0.1, atol=1e-12)

