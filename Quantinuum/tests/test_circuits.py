import numpy as np
from qiskit import QuantumCircuit

from qlomps_quantinuum.circuits import objective_qasm


def test_objective_circuit_layout():
    target = np.array([0.2, -0.5, 0.7, 0.3, 1.1, -0.8])
    candidate = target + 0.05
    circuit = QuantumCircuit.from_qasm_str(objective_qasm(target, candidate))
    assert circuit.num_qubits == 14
    assert circuit.num_clbits == 14
    assert circuit.count_ops()["measure"] == 14
    assert circuit.count_ops()["reset"] == 8

