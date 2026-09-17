"""Damped finite-difference warm starts between physical time steps."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from .constants import EXTRAPOLATION_DAMPING, EXTRAPOLATION_ORDERS, TRANSITION_INDICES


def extrapolate(order: int, points: Sequence[np.ndarray], damping: float) -> np.ndarray:
    values = np.asarray(points, dtype=float)
    if values.shape[0] != order + 1:
        raise ValueError("extrapolation requires exactly order+1 points")
    coefficients = np.array(
        [(-1) ** (order - k) * math.comb(order + 1, k) for k in range(order + 1)],
        dtype=float,
    )
    prediction = np.tensordot(coefficients, values, axes=(0, 0))
    return values[-1] + damping * (prediction - values[-1])


def starting_parameters(physical_step: int, known_points: Sequence[np.ndarray]) -> np.ndarray:
    """Return the warm start used for physical steps 1--5."""
    if physical_step < 1 or physical_step >= len(TRANSITION_INDICES):
        raise ValueError("the completed hardware protocol contains steps 0--5")
    transition = int(TRANSITION_INDICES[physical_step])
    order = int(EXTRAPOLATION_ORDERS[transition])
    damping = float(EXTRAPOLATION_DAMPING[transition])
    return extrapolate(order, known_points[-(order + 1) :], damping)

