"""IBM transpilation, layout assignment and destructive-SWAP decoding."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .circuits import circuit_triplet
from .constants import (
    FIDELITY_LEFT_QUBITS,
    FIDELITY_RIGHT_QUBITS,
    IBM_BOSTON,
    PURITY_QUBITS,
    ProtocolConfig,
)


def qasm_to_ibm_circuit(
    qasm: str,
    backend: Any,
    physical_qubits: Sequence[int],
    *,
    optimization_level: int = 2,
    production_parser: bool = True,
) -> Any:
    """Compile logical QASM with the frozen physical layout.

    The production run used pytket's OpenQASM parser followed by
    `tk_to_qiskit`. Set `production_parser=False` only for environments where
    pytket is unavailable; that fallback may lead to a different transpiled
    circuit even though the logical circuit is the same.
    """
    if production_parser:
        try:
            from pytket.extensions.qiskit import tk_to_qiskit
            from pytket.qasm import circuit_from_qasm_str
        except ImportError as exc:
            raise ImportError(
                "Exact IBM parsing requires the 'ibm-exact-parser' extra"
            ) from exc
        circuit = tk_to_qiskit(circuit_from_qasm_str(qasm))
    else:
        from qiskit import QuantumCircuit

        circuit = QuantumCircuit.from_qasm_str(qasm)

    if circuit.num_qubits != len(physical_qubits):
        raise ValueError("logical circuit width and physical layout differ")
    from qiskit.transpiler import generate_preset_pass_manager

    pass_manager = generate_preset_pass_manager(
        backend=backend,
        optimization_level=optimization_level,
        initial_layout=list(physical_qubits),
    )
    return pass_manager.run(circuit)


def compile_triplet(
    target_parameters: Sequence[float],
    candidate_parameters: Sequence[float],
    backend: Any,
    *,
    config: ProtocolConfig = IBM_BOSTON,
    production_parser: bool = True,
) -> list[Any]:
    """Compile the purity, left-fidelity and right-fidelity circuits."""
    logical = circuit_triplet(
        target_parameters,
        candidate_parameters,
        g=config.g,
        dt=config.dt,
    )
    layouts = {
        "purity": PURITY_QUBITS,
        "fidelity_left": FIDELITY_LEFT_QUBITS,
        "fidelity_right": FIDELITY_RIGHT_QUBITS,
    }
    compiled = []
    for name in ("purity", "fidelity_left", "fidelity_right"):
        circuit = qasm_to_ibm_circuit(
            logical[name],
            backend,
            layouts[name],
            optimization_level=config.optimization_level,
            production_parser=production_parser,
        )
        circuit.name = name
        compiled.append(circuit)
    return compiled


def _register_bitstrings(data: Any) -> tuple[list[str], list[str]]:
    left = list(data.m0.get_bitstrings())
    right = list(data.m1.get_bitstrings())
    if len(left) != len(right):
        raise RuntimeError("m0 and m1 contain different shot counts")
    return left, right


def destructive_swap_expectation(data: Any, *, register_width: int) -> tuple[float, int]:
    """Decode the product of `register_width` destructive SWAP tests."""
    left, right = _register_bitstrings(data)
    if any(len(value) != register_width for value in left + right):
        raise RuntimeError("classical register width does not match the circuit")
    even = 0
    for left_bits, right_bits in zip(left, right):
        parity = sum(
            int(a) & int(b) for a, b in zip(left_bits, right_bits)
        ) % 2
        even += int(parity == 0)
    shots = len(left)
    return 2.0 * even / shots - 1.0, even


def decode_triplet_result(
    sampler_result: Any,
    *,
    target_purity: float,
) -> dict[str, float | int]:
    """Decode one three-PUB objective sample from SamplerV2 output."""
    if len(sampler_result) != 3:
        raise RuntimeError("one QLOMPS sample must contain exactly three PUB results")
    purity, purity_even = destructive_swap_expectation(
        sampler_result[0].data, register_width=2
    )
    left, left_even = destructive_swap_expectation(
        sampler_result[1].data, register_width=3
    )
    right, right_even = destructive_swap_expectation(
        sampler_result[2].data, register_width=3
    )
    shots = len(list(sampler_result[0].data.m0.get_bitstrings()))

    def variance(even_count: int) -> float:
        probability = (even_count + 0.5) / (shots + 1.0)
        return 4.0 * probability * (1.0 - probability) / shots

    return {
        "shots": shots,
        "purity": purity,
        "fidelity_left": left,
        "fidelity_right": right,
        "purity_even_count": purity_even,
        "fidelity_left_even_count": left_even,
        "fidelity_right_even_count": right_even,
        "actual_cost": purity - left - right + float(target_purity),
        "cost_se": float(
            np.sqrt(variance(purity_even) + variance(left_even) + variance(right_even))
        ),
    }


def submit_circuits(
    circuits: Sequence[Any],
    *,
    mode: Any,
    shots: int = IBM_BOSTON.shots,
) -> Any:
    """Submit precompiled circuits using an IBM Runtime backend, Batch or Session."""
    from qiskit_ibm_runtime import SamplerV2

    return SamplerV2(mode=mode).run(list(circuits), shots=shots)

