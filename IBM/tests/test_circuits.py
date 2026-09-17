import numpy as np
from qiskit import QuantumCircuit

from qlomps_ibm.circuits import circuit_triplet


def test_triplet_has_production_widths() -> None:
    target = np.array([-0.2, -0.7, 0.8, 0.3, 2.0, -1.0])
    candidate = target + 0.1
    circuits = circuit_triplet(target, candidate)
    assert list(circuits) == ["purity", "fidelity_left", "fidelity_right"]
    parsed = {name: QuantumCircuit.from_qasm_str(qasm) for name, qasm in circuits.items()}
    assert all(circuit.num_qubits == 12 for circuit in parsed.values())
    assert parsed["purity"].num_clbits == 4
    assert parsed["fidelity_left"].num_clbits == 6
    assert parsed["fidelity_right"].num_clbits == 6

