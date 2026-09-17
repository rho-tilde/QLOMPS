"""Optional pytket/QNexus adapter matching the H2 execution path.

Nothing is submitted on import. Hardware mutation occurs only when the
explicit `submit_objective_batch` function is called by a configured user.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from .circuits import objective_qasm


def compile_objective_qasm(qasm: str, *, compile_device: str = "H2-2") -> Any:
    """Parse and compile logical QASM for the historical H2-2 target."""
    from pytket.extensions.quantinuum import QuantinuumBackend
    from pytket.qasm import circuit_from_qasm_str

    logical = circuit_from_qasm_str(qasm)
    return QuantinuumBackend(compile_device).get_compiled_circuit(logical)


def submit_objective_batch(
    *,
    target_parameters: Sequence[float],
    candidate_parameters: Sequence[Sequence[float]],
    project: Any,
    backend_config: Any,
    shots: int = 500,
    g: float = 0.2,
    dt: float = 0.2,
    compile_device: str = "H2-2",
    name: str | None = None,
) -> Any:
    """Compile, upload and submit one QNexus multi-program execute job."""
    import qnexus as qnx

    if shots <= 0:
        raise ValueError("shots must be positive")
    programs = []
    for index, candidate in enumerate(candidate_parameters):
        qasm = objective_qasm(target_parameters, candidate, g=g, dt=dt)
        compiled = compile_objective_qasm(qasm, compile_device=compile_device)
        programs.append(
            qnx.circuits.upload(
                name=f"qlomps_h2_objective_{index}_{datetime.now().isoformat()}",
                circuit=compiled,
                project=project,
            )
        )
    return qnx.start_execute_job(
        programs=programs,
        n_shots=[int(shots)] * len(programs),
        backend_config=backend_config,
        name=name or f"qlomps_h2_batch_{datetime.now().isoformat()}",
        project=project,
    )

