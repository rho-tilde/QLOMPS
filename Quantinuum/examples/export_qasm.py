"""Export one logical H2 objective circuit without submitting it."""

from pathlib import Path

import numpy as np

from qlomps_quantinuum.circuits import objective_qasm


target = np.zeros(6)
candidate = np.full(6, 0.1)
Path("h2_objective.qasm").write_text(objective_qasm(target, candidate), encoding="utf-8")

