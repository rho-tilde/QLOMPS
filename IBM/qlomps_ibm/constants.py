"""Frozen constants for the completed IBM Boston protocol."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ProtocolConfig:
    backend_name: str = "ibm_boston"
    shots: int = 5_000
    g: float = 0.2
    dt: float = 0.2
    radius: float = 0.5
    points_per_direction: int = 20
    optimization_level: int = 2
    r2_min: float = 0.5
    large_move_threshold: float = 0.25
    large_move_r2_min: float = 0.7
    predicted_improvement_min: float = 1e-3
    sentinel_z_max: float = 3.0
    max_attempts_steps_0_to_4: int = 8
    max_attempts_step_5: int = 4


IBM_BOSTON = ProtocolConfig()

PURITY_QUBITS = (42, 41, 36, 21, 22, 23, 24, 25, 37, 45, 44, 43)
FIDELITY_LEFT_QUBITS = (24, 25, 37, 45, 44, 43, 42, 41, 36, 21, 22, 23)
FIDELITY_RIGHT_QUBITS = PURITY_QUBITS

# Initial candidate used by physical Step 0. This is a protocol parameter,
# not measured data.
STEP0_INITIAL_PARAMETERS = np.array(
    [-0.544352, -1.002635, 0.883436, 0.423478, 2.298352, -0.826764],
    dtype=float,
)

# Three classical seed tensors used only to define the first target and the
# initial finite-difference history. Keeping them in code avoids distributing
# the historical NPZ result archive.
CLASSICAL_SEED_PARAMETERS = np.array(
    [
        [
            0.17711545668323495,
            -0.2518481121372291,
            0.5284448483553372,
            -0.18182901196647608,
            1.3657034815272886,
            -1.633544688048852,
        ],
        [
            0.1553966906632699,
            -0.528423866774761,
            0.699586625113805,
            0.16461372241435185,
            1.657105180349798,
            -1.2326249790359143,
        ],
        [
            -0.2128922730851428,
            -0.7780085366436588,
            0.7963496174266883,
            0.30085812399779893,
            1.9946036601957091,
            -1.0190138729336014,
        ],
    ],
    dtype=float,
)

TRANSITION_INDICES = (None, 1, 2, 3, 4, 4)
EXTRAPOLATION_ORDERS = (1, 1, 2, 1, 1, 1, 1, 1)
EXTRAPOLATION_DAMPING = (0.9, 0.9, 0.6, 0.7, 0.8, 0.8, 0.8, 0.8)

