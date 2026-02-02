"""
Wigner's Friend Paradox Demonstration on IBM Quantum Hardware

The paradox: Two observers can have contradictory descriptions of reality.
- Friend (inside lab) measures a qubit and sees a definite result
- Wigner (outside lab) describes Friend + qubit as being in superposition

This creates a conflict: Friend has a definite experience, but Wigner
says Friend is in superposition of "saw 0" and "saw 1" simultaneously!

This experiment demonstrates:
1. Basic Wigner's Friend scenario
2. Extended Wigner's Friend (Frauchiger-Renner thought experiment)
3. How different "observers" can have incompatible descriptions
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_wigner_friend_circuit() -> QuantumCircuit:
    """
    Create Wigner's Friend scenario circuit.

    Qubits:
    - q0: The quantum system (spin/photon)
    - q1: Friend's memory (records measurement result)

    From Friend's perspective: q0 collapses, q1 records the result
    From Wigner's perspective: (q0, q1) are in entangled superposition
    """
    qc = QuantumCircuit(2, 2, name="wigner_friend")

    # System starts in superposition
    qc.h(0)  # |+> = (|0> + |1>) / sqrt(2)

    # Friend "measures" by entangling with memory
    # |0>|memory> -> |0>|saw_0>
    # |1>|memory> -> |1>|saw_1>
    qc.cx(0, 1)

    # At this point:
    # Friend's view: collapsed to either |0,saw_0> or |1,saw_1>
    # Wigner's view: (|0,saw_0> + |1,saw_1>) / sqrt(2)

    qc.barrier(label="Wigner's test")

    # Measure in computational basis (Friend's perspective)
    qc.measure([0, 1], [0, 1])

    return qc


def create_wigner_interference_circuit() -> QuantumCircuit:
    """
    Wigner tests for interference to prove superposition existed.

    If Friend+system were truly in superposition, Wigner can undo
    the entanglement and observe interference.
    """
    qc = QuantumCircuit(2, 2, name="wigner_interference")

    # Create superposition
    qc.h(0)

    # Friend's "measurement" (entanglement)
    qc.cx(0, 1)

    qc.barrier(label="Friend measured")

    # Wigner undoes Friend's measurement
    qc.cx(0, 1)  # Undo CNOT
    qc.h(0)  # Undo Hadamard

    # If superposition existed, q0 should be back to |0>
    qc.measure([0, 1], [0, 1])

    return qc


def create_extended_wigner_friend_circuit() -> QuantumCircuit:
    """
    Extended Wigner's Friend (Frauchiger-Renner 2018).

    Two labs with Friends measuring entangled qubits.
    """
    qc = QuantumCircuit(4, 4, name="extended_wigner")

    # q0: Alice's system, q1: Alice's memory
    # q2: Bob's system, q3: Bob's memory

    # Create entangled state between Alice and Bob's systems
    qc.h(0)
    qc.cx(0, 2)  # |00> + |11>

    qc.barrier(label="Entangled pair")

    # Alice measures (entangles with her memory)
    qc.cx(0, 1)

    # Bob measures (entangles with his memory)
    qc.cx(2, 3)

    qc.barrier(label="Friends measured")

    # Measure everything
    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])

    return qc


def create_ewf_interference_circuit() -> QuantumCircuit:
    """
    Extended Wigner's Friend with interference test.
    """
    qc = QuantumCircuit(4, 4, name="ewf_interference")

    # Create entangled state
    qc.h(0)
    qc.cx(0, 2)

    # Friends measure
    qc.cx(0, 1)
    qc.cx(2, 3)

    qc.barrier(label="Friends measured")

    # Wigner undoes measurements
    qc.cx(2, 3)
    qc.cx(0, 1)
    qc.cx(0, 2)
    qc.h(0)

    # Should return to |0000>
    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])

    return qc


def create_bell_wigner_circuit() -> QuantumCircuit:
    """
    Bell test version of Wigner's Friend.
    """
    qc = QuantumCircuit(4, 4, name="bell_wigner")

    # Create Bell state
    qc.h(0)
    qc.cx(0, 2)

    # Alice measures in Z basis
    qc.cx(0, 1)

    # Bob measures in X basis
    qc.h(2)
    qc.cx(2, 3)

    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])

    return qc


def extract_counts(pub_result, circuit: QuantumCircuit) -> dict:
    """Extract measurement counts from SamplerV2 result."""
    try:
        creg_name = circuit.cregs[0].name if circuit.cregs else "c"
        data = getattr(pub_result.data, creg_name, None)
        if data is not None:
            return data.get_counts()
    except (AttributeError, IndexError):
        pass

    try:
        for name in ["meas", "c", "c0"]:
            data = getattr(pub_result.data, name, None)
            if data is not None:
                return data.get_counts()
    except AttributeError:
        pass

    try:
        for attr in dir(pub_result.data):
            if not attr.startswith("_"):
                data = getattr(pub_result.data, attr)
                if hasattr(data, "get_counts"):
                    return data.get_counts()
    except Exception:
        pass

    return {}


def run_wigner_friend_experiment(shots: int = 4096) -> dict:
    """Run Wigner's Friend experiments on IBM Quantum hardware."""
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=4)
    print(f"Backend: {backend.name}")
    print(f"Qubits: {backend.num_qubits}")

    circuits = []
    labels = []

    circuits.append(create_wigner_friend_circuit())
    labels.append("wigner_friend_basic")

    circuits.append(create_wigner_interference_circuit())
    labels.append("wigner_interference")

    circuits.append(create_extended_wigner_friend_circuit())
    labels.append("extended_wigner")

    circuits.append(create_ewf_interference_circuit())
    labels.append("ewf_interference")

    circuits.append(create_bell_wigner_circuit())
    labels.append("bell_wigner")

    print(f"\nTranspiling {len(circuits)} circuits...")
    transpiled = transpile(circuits, backend, optimization_level=1)

    print(f"Submitting job ({shots} shots per circuit)...")
    sampler = Sampler(mode=backend)
    job = sampler.run(transpiled, shots=shots)
    job_id = job.job_id()
    print(f"Job ID: {job_id}")
    print("Waiting for results...\n")

    result = job.result()

    processed_results = {}
    for idx, label in enumerate(labels):
        pub_result = result[idx]
        counts = extract_counts(pub_result, circuits[idx])
        processed_results[label] = {
            "counts": counts,
            "total": sum(counts.values()) if counts else shots,
            "circuit": circuits[idx]
        }

    return {
        "results": processed_results,
        "job_id": job_id,
        "backend": backend.name,
        "shots": shots
    }


def analyze_results(experiment: dict) -> None:
    """Analyze and display Wigner's Friend experiment results."""
    print("=" * 72)
    print("WIGNER'S FRIEND PARADOX - EXPERIMENTAL RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    results = experiment["results"]

    # Basic Wigner's Friend
    print("\n" + "-" * 72)
    print("1. BASIC WIGNER'S FRIEND")
    print("-" * 72)

    wf = results["wigner_friend_basic"]
    counts = wf["counts"]
    total = wf["total"]

    p_00 = counts.get("00", 0) / total
    p_11 = counts.get("11", 0) / total

    print(f"   |00> (system=0, saw 0): {counts.get('00', 0):4d} ({p_00*100:5.1f}%)")
    print(f"   |11> (system=1, saw 1): {counts.get('11', 0):4d} ({p_11*100:5.1f}%)")
    print(f"\n   Friend: Definite result")
    print(f"   Wigner: Superposition (|00> + |11>)/sqrt(2)")

    # Interference test
    print("\n" + "-" * 72)
    print("2. WIGNER'S INTERFERENCE TEST")
    print("-" * 72)

    wi = results["wigner_interference"]
    counts = wi["counts"]
    total = wi["total"]

    p_00 = counts.get("00", 0) / total

    print(f"   |00> (interference): {counts.get('00', 0):4d} ({p_00*100:5.1f}%)")
    print(f"   Other states:        {total - counts.get('00', 0):4d}")

    if p_00 > 0.7:
        print(f"\n   [OK] Interference confirms superposition existed!")
    else:
        print(f"\n   [~] Partial interference (hardware noise)")

    # Extended Wigner's Friend
    print("\n" + "-" * 72)
    print("3. EXTENDED WIGNER'S FRIEND")
    print("-" * 72)

    ewf = results["extended_wigner"]
    counts = ewf["counts"]
    total = ewf["total"]

    p_0000 = counts.get("0000", 0) / total
    p_1111 = counts.get("1111", 0) / total

    print(f"   |0000>: {counts.get('0000', 0):4d} ({p_0000*100:5.1f}%)")
    print(f"   |1111>: {counts.get('1111', 0):4d} ({p_1111*100:5.1f}%)")
    print(f"   Correlation: {(p_0000 + p_1111)*100:.1f}%")

    # EWF Interference
    print("\n" + "-" * 72)
    print("4. EXTENDED WIGNER - INTERFERENCE")
    print("-" * 72)

    ewfi = results["ewf_interference"]
    counts = ewfi["counts"]
    total = ewfi["total"]

    p_0000 = counts.get("0000", 0) / total
    print(f"   |0000> (full reversal): {counts.get('0000', 0):4d} ({p_0000*100:5.1f}%)")

    # Bell-Wigner
    print("\n" + "-" * 72)
    print("5. BELL-WIGNER TEST")
    print("-" * 72)

    bw = results["bell_wigner"]
    counts = bw["counts"]
    total = bw["total"]

    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])[:4]
    for bitstring, count in sorted_counts:
        print(f"   |{bitstring}>: {count:4d} ({count/total*100:5.1f}%)")

    print("\n" + "-" * 72)
    print("THE PARADOX")
    print("-" * 72)
    print("""
Wigner's Friend Paradox (1961):
  - Friend measures and gets a definite result
  - Wigner treats Friend + system as quantum superposition
  - Both descriptions are valid from their perspectives!

Extended Wigner's Friend (Frauchiger-Renner 2018):
  Shows that combining:
  1. QM applies to all systems
  2. Measurements have single outcomes
  3. Logical consistency
  ...leads to contradictions!

Possible resolutions:
  - Many-worlds (all outcomes happen)
  - QBism (probabilities are subjective)
  - Relational QM (facts are observer-dependent)
  - Consciousness causes collapse
""")
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Basic Wigner's Friend ---")
    print(create_wigner_friend_circuit().draw(output="text"))

    print("\n--- Wigner Interference Test ---")
    print(create_wigner_interference_circuit().draw(output="text"))


def main():
    """Main entry point for Wigner's Friend demonstration."""
    print("=" * 72)
    print("WIGNER'S FRIEND PARADOX DEMONSTRATION")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
Wigner's Friend (1961):
  Friend is in a sealed lab measuring a quantum system.
  Wigner is outside, treating the entire lab as quantum.

  From Friend's view: Measurement happened, result is definite.
  From Wigner's view: Friend is in superposition!

Extended Wigner's Friend (2018):
  Two labs with two Friends lead to logical contradictions.

Experiment design:
  1. Basic scenario: entangle "system" with "memory"
  2. Interference test: verify superposition existed
  3. Extended: two entangled Friend-system pairs
  4. Bell-Wigner: incompatible measurement bases
""")

    print_circuit_diagrams()

    try:
        print("\n" + "=" * 72)
        print("RUNNING EXPERIMENT ON IBM QUANTUM HARDWARE")
        print("=" * 72 + "\n")

        experiment = run_wigner_friend_experiment(shots=4096)
        analyze_results(experiment)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Check .env file has valid credentials")
        print("  2. Ensure packages are installed: uv sync")
        print("  3. Verify IBM Quantum account at quantum.ibm.com")


if __name__ == "__main__":
    main()
