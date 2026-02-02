"""
Extended Wigner's Friend (Frauchiger-Renner) Paradox on IBM Quantum Hardware

The Frauchiger-Renner paradox (2018) extends Wigner's Friend to show that
quantum mechanics may be inconsistent when applied to observers who are
themselves in superposition.

Setup:
- Two labs, each with a "friend" (F1, F2) who can make measurements
- Two external observers (W1, W2) who can measure the entire labs
- F1 prepares a qubit and measures it
- Based on F1's result, a state is sent to F2
- F2 measures their qubit
- W1 and W2 perform "undoing" measurements on the labs

The paradox: Following quantum mechanics consistently leads to contradictory
conclusions about what the friends must have observed.
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_extended_wigner_friend_circuit() -> QuantumCircuit:
    """
    Create the Extended Wigner's Friend (Frauchiger-Renner) circuit.

    Qubits:
    - q[0]: System measured by Friend 1
    - q[1]: Friend 1's memory
    - q[2]: System sent to Friend 2
    - q[3]: Friend 2's memory

    The protocol:
    1. F1 prepares a coin in superposition and measures
    2. If F1 sees "tails" (|1>), sends |+> to F2; if "heads" (|0>), sends |0>
    3. F2 measures in computational basis
    4. Wigners perform interference measurements
    """
    qc = QuantumCircuit(4, 4, name="extended_wigner_friend")

    # Step 1: F1 prepares coin in superposition (|0> + |1>)/√2
    qc.h(0)
    qc.barrier(label="F1 coin")

    # Step 2: F1 measures coin (entangles with memory)
    qc.cx(0, 1)
    qc.barrier(label="F1 measures")

    # Step 3: Conditional state preparation for F2
    # If F1=|1>, prepare |+> for F2; if F1=|0>, prepare |0>
    qc.cx(1, 2)
    qc.ch(1, 2)  # Controlled-H: creates |+> only if F1=|1>
    qc.barrier(label="Send to F2")

    # Step 4: F2 measures in computational basis
    qc.cx(2, 3)
    qc.barrier(label="F2 measures")

    # Step 5: Wigners perform interference measurements on their labs
    # This "undoes" the friends' measurements from Wigner's perspective
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.h(3)
    qc.barrier(label="Wigner measurements")

    # Final measurement
    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])

    return qc


def create_simplified_fr_circuit() -> QuantumCircuit:
    """
    Simplified Frauchiger-Renner circuit focusing on the core paradox.

    Uses 3 qubits to demonstrate the essential features.
    """
    qc = QuantumCircuit(3, 3, name="simplified_FR")

    # Initial superposition (coin toss)
    qc.h(0)
    qc.barrier()

    # F1 measurement (entanglement)
    qc.cx(0, 1)
    qc.barrier()

    # Conditional preparation for F2
    qc.cx(0, 2)
    qc.ch(0, 2)
    qc.barrier()

    # Wigner's interference test
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier()

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_fr_no_wigner_circuit() -> QuantumCircuit:
    """
    FR circuit without Wigner's interference - shows friends' results.
    """
    qc = QuantumCircuit(4, 4, name="FR_friends_only")

    qc.h(0)
    qc.cx(0, 1)  # F1 measures
    qc.barrier()

    qc.cx(1, 2)
    qc.ch(1, 2)
    qc.cx(2, 3)  # F2 measures
    qc.barrier()

    # Direct measurement (no Wigner interference)
    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])
    return qc


def create_fr_wigner1_only() -> QuantumCircuit:
    """FR circuit with only Wigner 1 performing interference."""
    qc = QuantumCircuit(4, 4, name="FR_W1_only")

    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()

    qc.cx(1, 2)
    qc.ch(1, 2)
    qc.cx(2, 3)
    qc.barrier()

    # Only W1 does interference
    qc.h(0)
    qc.h(1)
    qc.barrier()

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


def run_experiment(shots: int = 4096) -> dict:
    """Run Extended Wigner's Friend experiment on IBM Quantum hardware."""
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=4)
    print(f"Backend: {backend.name}")
    print(f"Qubits: {backend.num_qubits}")

    circuits = [
        create_extended_wigner_friend_circuit(),
        create_simplified_fr_circuit(),
        create_fr_no_wigner_circuit(),
        create_fr_wigner1_only(),
    ]
    labels = ["full_FR", "simplified", "friends_only", "W1_only"]

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
    """Analyze and display Extended Wigner's Friend experiment results."""
    print("=" * 72)
    print("EXTENDED WIGNER'S FRIEND (FRAUCHIGER-RENNER) - RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    print("\n" + "-" * 72)
    print("THE FRAUCHIGER-RENNER PARADOX")
    print("-" * 72)
    print("""
    The scenario:
    1. Friend F1 measures a quantum coin, records result
    2. Based on F1's result, a quantum message is sent to F2
    3. F2 measures the message, records result
    4. External observers W1, W2 measure the entire labs

    The paradox:
    - Using QM, W1 can deduce what F2 "must have seen"
    - Using QM, W2 can deduce what F1 "must have seen"
    - Using QM, F1 can deduce what W2 "will conclude"
    - These deductions contradict each other!

    This suggests quantum mechanics may be inconsistent when applied
    to observers who are themselves quantum systems.
    """)

    results = experiment["results"]

    # Full FR results
    print("-" * 72)
    print("FULL FRAUCHIGER-RENNER CIRCUIT")
    print("-" * 72)

    full = results["full_FR"]
    counts = full["counts"]
    total = full["total"]

    print("\n   Measurement outcomes (W1.mem, W1.sys, W2.mem, W2.sys):")
    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])[:8]
    for outcome, count in sorted_outcomes:
        p = count / total * 100
        print(f"      |{outcome}>: {count:4d} ({p:5.1f}%)")

    # Friends only
    print("\n" + "-" * 72)
    print("FRIENDS' MEASUREMENTS (No Wigner interference)")
    print("-" * 72)

    friends = results["friends_only"]
    counts = friends["counts"]
    total = friends["total"]

    print("\n   What the friends observe (F1.mem, F1.sys, F2.mem, F2.sys):")
    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])[:8]
    for outcome, count in sorted_outcomes:
        p = count / total * 100
        print(f"      |{outcome}>: {count:4d} ({p:5.1f}%)")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
    The Frauchiger-Renner thought experiment shows:

    1. If quantum mechanics applies universally (including to observers)
    2. And we use single-world reasoning (no many-worlds)
    3. Then agents using QM will make contradictory predictions

    Possible resolutions:
    - Many-worlds: All branches exist, no contradiction
    - Copenhagen: QM doesn't apply to macroscopic observers
    - QBism: Probabilities are personal, not universal
    - Relational QM: Facts are relative to observers
    - Superdeterminism: Measurement choices aren't free

    This experiment tests whether quantum coherence can be maintained
    across nested measurement scenarios on real hardware.
    """)
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Full Frauchiger-Renner Circuit ---")
    print(create_extended_wigner_friend_circuit().draw(output="text"))

    print("\n--- Simplified FR Circuit ---")
    print(create_simplified_fr_circuit().draw(output="text"))


def main():
    """Main entry point for Extended Wigner's Friend demonstration."""
    print("=" * 72)
    print("EXTENDED WIGNER'S FRIEND (FRAUCHIGER-RENNER) PARADOX")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
The Frauchiger-Renner Paradox (2018):

  Extends Wigner's Friend to show potential inconsistency in QM.

  Setup:
  - Two isolated labs with "friends" F1 and F2
  - Two external "Wigners" W1 and W2
  - Friends make measurements inside labs
  - Wigners can measure entire labs as quantum systems

  The paradox emerges when agents reason about each other's
  observations using quantum mechanics consistently.

Experiment:
  1. Full FR protocol with all measurements
  2. Simplified version showing core features
  3. Friends-only version (classical correlations)
  4. Partial Wigner measurement
""")

    print_circuit_diagrams()

    try:
        print("\n" + "=" * 72)
        print("RUNNING EXPERIMENT ON IBM QUANTUM HARDWARE")
        print("=" * 72 + "\n")

        experiment = run_experiment(shots=4096)
        analyze_results(experiment)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Check .env file has valid credentials")
        print("  2. Ensure packages are installed: uv sync")
        print("  3. Verify IBM Quantum account at quantum.ibm.com")


if __name__ == "__main__":
    main()
