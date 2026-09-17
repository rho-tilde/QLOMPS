"""Build the adaptive groups of circuits used in one optimizer attempt."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .constants import IBM_BOSTON, ProtocolConfig
from .optimizer import (
    coarse_and_refinement_offsets,
    fit_directions,
    parameter_rows,
    plan_subset,
    rank_coarse_directions,
)


def coarse_rows(
    center: Sequence[float], config: ProtocolConfig = IBM_BOSTON
) -> list[dict[str, Any]]:
    offsets, _ = coarse_and_refinement_offsets(config)
    return parameter_rows(center, plan_subset(range(6), offsets, config))


def refinement_rows(
    center: Sequence[float],
    directions: Sequence[int],
    config: ProtocolConfig = IBM_BOSTON,
) -> list[dict[str, Any]]:
    _, offsets = coarse_and_refinement_offsets(config)
    return parameter_rows(center, plan_subset(directions, offsets, config))


def choose_refinement(
    coarse_samples: Sequence[dict[str, Any]],
    config: ProtocolConfig = IBM_BOSTON,
) -> tuple[list[int], list[int], dict[str, Any]]:
    analysis = fit_directions(
        coarse_samples, apply_large_move_gate=False, config=config
    )
    ranking = rank_coarse_directions(analysis["fits"])
    top = ranking[:3]
    remaining = [direction for direction in range(6) if direction not in set(top)]
    return top, remaining, analysis


def decide_after_top_three(
    coarse_samples: Sequence[dict[str, Any]],
    refined_samples: Sequence[dict[str, Any]],
    top_three: Sequence[int],
    config: ProtocolConfig = IBM_BOSTON,
) -> tuple[dict[str, Any], bool]:
    combined = list(coarse_samples) + list(refined_samples)
    analysis = fit_directions(
        combined,
        candidate_directions=top_three,
        apply_large_move_gate=True,
        config=config,
    )
    requires_remaining_three = analysis["selected_direction"] is None
    return analysis, requires_remaining_three


def attach_parameters_and_costs(
    rows: Sequence[dict[str, Any]], costs: Sequence[float]
) -> list[dict[str, Any]]:
    """Small helper for passing decoded hardware values into the fit code."""
    if len(rows) != len(costs):
        raise ValueError("rows and costs must have equal length")
    return [
        {**row, "parameters": np.asarray(row["parameters"]), "actual_cost": float(cost)}
        for row, cost in zip(rows, costs)
    ]

