"""Step-dependent settings and documented executed-run qualifications."""

from __future__ import annotations

from dataclasses import dataclass


H2_SHOTS_PER_POINT = 500
NOMINAL_SCREEN_SIGMA = 0.07


@dataclass(frozen=True)
class H2Step:
    step: int
    extrapolation_order: int
    damping: float
    screen_radius: float
    k_sigma: float
    fit_range: float
    fit_points: int
    r2_min: float
    sigma_max_nominal: float
    t_max: float
    keep_directions: int
    repeats_nominal: int
    higher_fit_enabled: bool
    fallback_enabled: bool
    sigma_max_executed_recovery: float | None = None
    executed_note: str = ""

    @property
    def screen_threshold(self) -> float:
        return self.k_sigma * NOMINAL_SCREEN_SIGMA


EXECUTED_H2_STEPS = (
    H2Step(1, 1, 0.9, 0.6, 2.7, 1.0, 6, 0.85, 0.07, 0.3, 2, 1, False, False,
           executed_note="Quadratic rejected; extrapolated point retained."),
    H2Step(2, 1, 0.9, 0.8, 2.2, 1.0, 8, 0.70, 0.12, 0.4, 4, 1, True, True,
           executed_note="Fallback made two effective repeats; reconstructed quartic vertex retained."),
    H2Step(3, 2, 0.6, 0.6, 2.0, 1.0, 8, 0.80, 0.08, 0.5, 1, 2, True, True, 0.09,
           "Recovered samples were refitted with sigma_max=0.09."),
    H2Step(4, 1, 0.7, 0.6, 0.5, 1.0, 8, 0.70, 0.10, 0.6, 2, 2, True, True,
           executed_note="Accepted repeat-0 vertex retained after repeat 1 rejected."),
    H2Step(5, 1, 0.8, 0.6, 1.0, 1.0, 10, 0.70, 0.07, 0.7, 1, 2, True, True,
           executed_note="Repeat-1 vertex retained post hoc after nominal sigma rejection."),
    H2Step(6, 1, 0.8, 0.6, 1.0, 1.0, 10, 0.70, 0.08, 0.8, 1, 3, True, True,
           executed_note="Selected repeat-1 fit reconstructed from acquired samples."),
)

