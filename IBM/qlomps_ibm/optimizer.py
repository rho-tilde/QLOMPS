"""Adaptive directional-parabola optimizer used by the IBM experiment."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np

from .constants import IBM_BOSTON, ProtocolConfig


def directional_plan(radius: float = 0.5, points: int = 20) -> list[dict[str, float | int]]:
    """Return the interleaved six-direction scan order used on hardware."""
    offsets = np.linspace(-radius, radius, points)
    magnitudes = sorted((float(abs(t)) for t in offsets if t > 0), reverse=True)
    plan: list[dict[str, float | int]] = []
    for magnitude_index, magnitude in enumerate(magnitudes):
        for direction in range(6):
            signs = (
                (1.0, -1.0)
                if (magnitude_index + direction) % 2 == 0
                else (-1.0, 1.0)
            )
            for sign in signs:
                plan.append({"direction": direction, "t": sign * magnitude})
    if len(plan) != 6 * points:
        raise RuntimeError("directional plan has the wrong number of samples")
    return plan


def coarse_and_refinement_offsets(
    config: ProtocolConfig = IBM_BOSTON,
) -> tuple[np.ndarray, np.ndarray]:
    offsets = np.linspace(-config.radius, config.radius, config.points_per_direction)
    coarse_indices = np.array([0, 2, 4, 6, 8, 11, 13, 15, 17, 19], dtype=int)
    refinement_indices = np.array(
        [i for i in range(config.points_per_direction) if i not in set(coarse_indices)],
        dtype=int,
    )
    return offsets[coarse_indices], offsets[refinement_indices]


def plan_subset(
    directions: Iterable[int],
    offsets: Sequence[float],
    config: ProtocolConfig = IBM_BOSTON,
) -> list[dict[str, float | int]]:
    selected = {int(direction) for direction in directions}
    values = np.asarray(offsets, dtype=float)
    return [
        row
        for row in directional_plan(config.radius, config.points_per_direction)
        if int(row["direction"]) in selected
        and np.any(np.isclose(float(row["t"]), values, atol=1e-14, rtol=0.0))
    ]


def parameter_rows(
    center: Sequence[float],
    plan: Sequence[dict[str, float | int]],
) -> list[dict[str, Any]]:
    center_array = np.asarray(center, dtype=float)
    if center_array.shape != (6,):
        raise ValueError("center must contain six parameters")
    rows = []
    for index, item in enumerate(plan):
        direction = int(item["direction"])
        offset = float(item["t"])
        parameters = center_array.copy()
        parameters[direction] += offset
        rows.append(
            {
                "sample_index": index,
                "direction": direction,
                "t": offset,
                "parameters": parameters,
            }
        )
    return rows


def fit_directions(
    samples: Sequence[dict[str, Any]],
    *,
    candidate_directions: Sequence[int] | None = None,
    apply_large_move_gate: bool = True,
    config: ProtocolConfig = IBM_BOSTON,
) -> dict[str, Any]:
    """Fit one quadratic per direction and apply the production gates."""
    directions = list(range(6)) if candidate_directions is None else list(candidate_directions)
    if not directions or len(set(directions)) != len(directions):
        raise ValueError("candidate directions must be unique and non-empty")

    fits: list[dict[str, Any]] = []
    for direction in directions:
        rows = sorted(
            (row for row in samples if int(row["direction"]) == int(direction)),
            key=lambda row: float(row["t"]),
        )
        if len(rows) < 3:
            raise ValueError(f"direction {direction} has fewer than three samples")
        t = np.asarray([row["t"] for row in rows], dtype=float)
        y = np.asarray([row["actual_cost"] for row in rows], dtype=float)
        a, b, c = np.polyfit(t, y, deg=2)
        fitted = a * t**2 + b * t + c
        sse = float(np.sum((y - fitted) ** 2))
        sst = float(np.sum((y - np.mean(y)) ** 2))
        r2 = float(1.0 - sse / sst) if sst > 0 else float("-inf")
        valid_parabola = np.isfinite(a) and a > 0 and np.isfinite(b)
        t_min = float(-b / (2.0 * a)) if valid_parabola else float("nan")
        improvement = float(b * b / (4.0 * a)) if valid_parabola else float("nan")

        reasons: list[str] = []
        if not (np.isfinite(a) and a > 0):
            reasons.append("a_nonpositive")
        if not np.isfinite(t_min):
            reasons.append("t_min_nonfinite")
        elif abs(t_min) > config.radius:
            reasons.append("t_min_outside_window")
        if not np.isfinite(r2) or r2 < config.r2_min:
            reasons.append("r2_low")
        if (
            apply_large_move_gate
            and np.isfinite(t_min)
            and abs(t_min) > config.large_move_threshold
            and (not np.isfinite(r2) or r2 < config.large_move_r2_min)
        ):
            reasons.append("large_move_r2_low")
        if not np.isfinite(improvement) or improvement <= config.predicted_improvement_min:
            reasons.append("predicted_improvement_not_above_threshold")

        fits.append(
            {
                "direction": int(direction),
                "a": float(a),
                "b": float(b),
                "c": float(c),
                "t_min": t_min,
                "predicted_improvement": improvement,
                "r2": r2,
                "actionable": not reasons,
                "rejection_reasons": reasons,
            }
        )

    actionable = [fit for fit in fits if fit["actionable"]]
    selected = (
        max(
            actionable,
            key=lambda fit: (
                float(fit["r2"]),
                float(fit["predicted_improvement"]),
                -int(fit["direction"]),
            ),
        )
        if actionable
        else None
    )
    return {
        "fits": fits,
        "selected_direction": None if selected is None else int(selected["direction"]),
        "selected_t_min": None if selected is None else float(selected["t_min"]),
        "selected_fit_r2": None if selected is None else float(selected["r2"]),
        "selected_predicted_improvement": (
            None if selected is None else float(selected["predicted_improvement"])
        ),
    }


def rank_coarse_directions(fits: Sequence[dict[str, Any]]) -> list[int]:
    """Rank coarse fits by geometry and offset-invariant improvement."""

    def key(fit: dict[str, Any]) -> tuple[float, ...]:
        a = float(fit["a"])
        t_min = float(fit["t_min"])
        improvement = float(fit["predicted_improvement"])
        valid = (
            np.isfinite(a)
            and a > 0.0
            and np.isfinite(t_min)
            and abs(t_min) <= IBM_BOSTON.radius
            and np.isfinite(improvement)
            and improvement >= 0.0
        )
        r2 = float(fit["r2"])
        return (
            1.0 if valid else 0.0,
            improvement if valid else float("-inf"),
            r2 if np.isfinite(r2) else float("-inf"),
            -float(fit["direction"]),
        )

    return [int(fit["direction"]) for fit in sorted(fits, key=key, reverse=True)]


def apply_selected_move(
    center: Sequence[float], analysis: dict[str, Any]
) -> tuple[np.ndarray, str]:
    updated = np.asarray(center, dtype=float).copy()
    direction = analysis["selected_direction"]
    if direction is None:
        return updated, "converged"
    updated[int(direction)] += float(analysis["selected_t_min"])
    return updated, "accept_greedy_move"


def sentinel_drift_z(start: dict[str, float], end: dict[str, float]) -> float:
    denominator = np.sqrt(float(start["cost_se"]) ** 2 + float(end["cost_se"]) ** 2)
    return float(abs(float(end["actual_cost"]) - float(start["actual_cost"])) / denominator)

