"""Shot-frugal coordinate screening and polynomial fits used for H2-2."""

from __future__ import annotations

from math import comb
from typing import Any, Sequence

import numpy as np


def damped_extrapolation(history: Sequence[Sequence[float]], order: int, damping: float) -> np.ndarray:
    points = np.asarray(history, dtype=float)
    if order < 1 or points.shape != (order + 1, 6):
        raise ValueError("history must have shape (order + 1, 6)")
    coefficients = np.array(
        [(-1) ** (order - k) * comb(order + 1, k) for k in range(order + 1)],
        dtype=float,
    )
    prediction = np.tensordot(coefficients, points, axes=(0, 0))
    return points[-1] + float(damping) * (prediction - points[-1])


def paired_probe_points(center: Sequence[float], direction: int, radius: float) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(center, dtype=float)
    if x.shape != (6,) or direction not in range(6):
        raise ValueError("center must have six values and direction must be 0..5")
    unit = np.zeros(6)
    unit[direction] = 1.0
    return x + radius * unit, x - radius * unit


def choose_screen_direction(
    ordered_pairs: Sequence[dict[str, float | int]],
    *,
    threshold: float,
    keep: int,
) -> dict[str, Any]:
    """Replay the greedy screen from pairs in their randomized acquisition order."""
    significant: list[dict[str, float | int]] = []
    consumed: list[dict[str, float | int]] = []
    seen: set[int] = set()
    for row in ordered_pairs:
        direction = int(row["direction"])
        if direction in seen or direction not in range(6):
            raise ValueError("directions must be unique and in 0..5")
        seen.add(direction)
        delta = float(row["f_plus"]) - float(row["f_minus"])
        evaluated = {**row, "paired_difference": delta, "significant": abs(delta) > threshold}
        consumed.append(evaluated)
        if evaluated["significant"]:
            significant.append(evaluated)
            if len(significant) >= keep:
                break
    winner = max(significant, key=lambda row: abs(float(row["paired_difference"]))) if significant else None
    return {"consumed": consumed, "significant": significant, "winner": winner}


def quadratic_fit(samples: Sequence[Sequence[float]]) -> dict[str, Any]:
    values = np.asarray(samples, dtype=float)
    if values.ndim != 2 or values.shape[1] != 2 or len(values) < 3:
        raise ValueError("samples must contain at least three (offset, cost) pairs")
    t, y = values[:, 0], values[:, 1]
    design = np.column_stack([t**2, t, np.ones_like(t)])
    (a, b, c0), *_ = np.linalg.lstsq(design, y, rcond=None)
    residuals = y - design @ np.array([a, b, c0])
    rss = float(np.sum(residuals**2))
    tss = float(np.sum((y - np.mean(y)) ** 2))
    sigma = float(np.sqrt(rss / max(len(y) - 3, 1)))
    r2 = float(1.0 - rss / tss) if tss > 0 else 0.0
    t0 = float(-b / (2.0 * a)) if not np.isclose(a, 0.0) else float("nan")
    minimum = float(c0 - b * b / (4.0 * a)) if np.isfinite(t0) else float(np.mean(y))
    return {"a": float(a), "t0": t0, "c": minimum, "rss": rss, "sigma_hat": sigma, "r2": r2}


def accept_quadratic(
    fit: dict[str, Any], *, r2_min: float, sigma_max: float | None, t_max: float
) -> dict[str, Any]:
    reason = None
    if not np.isfinite(float(fit["t0"])):
        reason = "t0_nonfinite"
    elif float(fit["a"]) <= 0:
        reason = "a_nonpos"
    elif abs(float(fit["t0"])) > t_max:
        reason = "t0_too_far"
    elif float(fit["r2"]) < r2_min:
        reason = "r2_low"
    elif sigma_max is not None and float(fit["sigma_hat"]) > sigma_max:
        reason = "sigma_high"
    return {**fit, "accepted": reason is None, "reason": reason}


def quartic_fit(samples: Sequence[Sequence[float]]) -> dict[str, Any]:
    values = np.asarray(samples, dtype=float)
    if values.ndim != 2 or values.shape[1] != 2 or len(values) < 5:
        raise ValueError("quartic fit needs at least five (offset, cost) pairs")
    t, y = values[:, 0], values[:, 1]
    coefficients = np.polyfit(t, y, 4)
    polynomial = np.poly1d(coefficients)
    fitted = polynomial(t)
    rss = float(np.sum((y - fitted) ** 2))
    tss = float(np.sum((y - np.mean(y)) ** 2))
    sigma = float(np.sqrt(rss / max(len(y) - 5, 1)))
    r2 = float(1.0 - rss / tss) if tss > 0 else 0.0
    first, second = np.polyder(polynomial), np.polyder(polynomial, 2)
    minima = [
        (float(root.real), float(polynomial(root.real)))
        for root in np.roots(first)
        if abs(root.imag) < 1e-10 and second(root.real) > 0
    ]
    t0, minimum = min(minima, key=lambda pair: pair[1]) if minima else (float("nan"), float("nan"))
    return {
        "coefficients": coefficients,
        "t0": t0,
        "c": minimum,
        "rss": rss,
        "sigma_hat": sigma,
        "r2": r2,
        "order": 4,
    }


def accept_quartic(
    fit: dict[str, Any], *, r2_min: float, sigma_max: float | None, t_max: float
) -> dict[str, Any]:
    reason = None
    if not np.isfinite(float(fit["t0"])):
        reason = "t0_nonfinite"
    elif abs(float(fit["t0"])) > t_max:
        reason = "t0_too_far"
    elif float(fit["r2"]) < r2_min:
        reason = "r2_low"
    elif sigma_max is not None and float(fit["sigma_hat"]) > sigma_max:
        reason = "sigma_high"
    return {**fit, "accepted": reason is None, "reason": reason}


def missing_line_points(
    existing_offsets: Sequence[float], *, fit_range: float, fit_points: int
) -> np.ndarray:
    """Return line-grid points not already supplied by the paired screen."""
    grid = np.linspace(-fit_range, fit_range, fit_points)
    existing = np.asarray(existing_offsets, dtype=float)
    tolerance = 0.0 if fit_points <= 1 else abs(grid[1] - grid[0]) / 2.1
    return np.array(
        [t for t in grid if len(existing) == 0 or np.min(np.abs(existing - t)) > tolerance],
        dtype=float,
    )


def qualifies_for_quartic(repeats: Sequence[dict[str, Any]]) -> bool:
    for left, first in enumerate(repeats):
        for second in repeats[left + 1 :]:
            if (
                int(first["direction"]) == int(second["direction"])
                and int(first["direction"]) < 6
                and (first.get("reason") == "t0_too_far" or second.get("reason") == "t0_too_far")
            ):
                return True
    return False

