import numpy as np

from qlomps_quantinuum.objective import objective_from_shots


def test_all_zero_bits_give_unit_overlaps_and_cost_minus_one():
    result = objective_from_shots(np.zeros((20, 14), dtype=np.uint8))
    assert result["purity"] == 1.0
    assert result["fidelity"] == 1.0
    assert result["cost"] == -1.0


def test_forward_and_reverse_register_orders_agree():
    rng = np.random.default_rng(4)
    forward = rng.integers(0, 2, size=(30, 14), dtype=np.uint8)
    reverse = np.hstack([forward[:, 10:14], forward[:, 6:10], forward[:, 3:6], forward[:, 0:3]])
    assert objective_from_shots(forward) == objective_from_shots(reverse, order="reverse")

