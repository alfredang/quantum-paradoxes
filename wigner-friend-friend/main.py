"""
Wigner's Friend's Friend Paradox on IBM Quantum Hardware

An extension of Wigner's Friend with THREE levels of nested observers:
- Friend: Measures the quantum system
- Wigner: Observes Friend + System as a quantum system
- Super-Wigner: Observes Wigner + Friend + System as a quantum system

This creates a deeper paradox about the objectivity of measurement
outcomes and the consistency of quantum mechanics across observer levels.

Each level of observer treats the previous level as a quantum system,
leading to potentially contradictory conclusions about what was "really" measured.
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_three_level_observer_circuit() -> QuantumCircuit:
    """
    Create the full three-level observer chain.

    Qubits:
    - q[0]: Quantum system (spin particle)
    - q[1]: Friend's memory
    - q[2]: Wigner's memory
    - q[3]: Super-Wigner's memory

    The chain:
    1. System in superposition
    2. Friend measures → entangled with system
    3. Wigner "measures" Friend → entangled with Friend+System
    4. Super-Wigner performs interference on entire lab
    """
    qc = QuantumCircuit(4, 4, name="three_level_observers")

    # System starts in superposition
    qc.h(0)
    qc.barrier(label="System: |+⟩")

    # Friend measures system (records in memory)
    qc.cx(0, 1)
    qc.barrier(label="Friend measures")

    # Wigner observes Friend+System (but from outside, sees superposition)
    # Wigner's memory entangles with the Friend-System state
    qc.cx(0, 2)
    qc.cx(1, 2)
    qc.barrier(label="Wigner observes")

    # Super-Wigner can now perform operations on entire Wigner's lab
    # Applies Hadamard to "undo" measurements from Super-Wigner's perspective
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier(label="Super-Wigner interference")

    # Super-Wigner's measurement
    qc.cx(2, 3)
    qc.h(3)
    qc.barrier(label="Super-Wigner measures")

    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])
    return qc


def create_two_level_comparison() -> QuantumCircuit:
    """Standard two-level (Wigner's Friend) for comparison."""
    qc = QuantumCircuit(3, 3, name="two_level")

    qc.h(0)
    qc.barrier()

    qc.cx(0, 1)
    qc.barrier()

    qc.h(0)
    qc.cx(0, 2)
    qc.h(2)
    qc.barrier()

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_friend_only_circuit() -> QuantumCircuit:
    """Only Friend measures - baseline case."""
    qc = QuantumCircuit(4, 4, name="friend_only")

    qc.h(0)
    qc.cx(0, 1)

    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])
    return qc


def create_wigner_only_circuit() -> QuantumCircuit:
    """Friend + Wigner measure, no Super-Wigner interference."""
    qc = QuantumCircuit(4, 4, name="wigner_only")

    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()

    qc.cx(0, 2)
    qc.cx(1, 2)
    qc.barrier()

    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])
    return qc


def create_super_wigner_reversal() -> QuantumCircuit:
    """
    Super-Wigner completely reverses all measurements.

    If quantum mechanics is universal, Super-Wigner can "unmeasure"
    both Wigner's and Friend's observations, returning to original state.
    """
    qc = QuantumCircuit(4, 4, name="full_reversal")

    # Forward evolution
    qc.h(0)
    qc.cx(0, 1)  # Friend measures
    qc.cx(0, 2)  # Wigner measures
    qc.cx(1, 2)
    qc.barrier(label="All measured")

    # Super-Wigner's reversal (time-reverse the operations)
    qc.cx(1, 2)
    qc.cx(0, 2)  # Undo Wigner
    qc.cx(0, 1)  # Undo Friend
    qc.h(0)      # Undo initial superposition
    qc.barrier(label="Reversed")

    # Should return to |0000⟩ if reversal worked
    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])
    return qc


def create_inconsistency_test() -> QuantumCircuit:
    """
    Circuit designed to highlight potential inconsistencies.

    Creates a situation where different observer levels would
    make contradictory predictions about outcomes.
    """
    qc = QuantumCircuit(4, 4, name="inconsistency_test")

    # Entangle system with Friend
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()

    # Wigner entangles but with phase
    qc.cz(0, 2)
    qc.cz(1, 2)
    qc.h(2)
    qc.barrier()

    # Super-Wigner's test measurement
    qc.h(0)
    qc.h(1)
    qc.cz(2, 3)
    qc.h(3)
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
    """Run Wigner's Friend's Friend experiment on IBM Quantum hardware."""
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
        create_friend_only_circuit(),
        create_wigner_only_circuit(),
        create_three_level_observer_circuit(),
        create_super_wigner_reversal(),
        create_inconsistency_test(),
    ]
    labels = ["friend_only", "wigner_only", "three_level", "reversal", "inconsistency"]

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
    """Analyze and display Wigner's Friend's Friend results."""
    print("=" * 72)
    print("WIGNER'S FRIEND'S FRIEND PARADOX - RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    print("\n" + "-" * 72)
    print("THE NESTED OBSERVER PARADOX")
    print("-" * 72)
    print("""
    Three levels of observers:

    Level 1 - FRIEND:
      "I measured the spin and got a definite result"

    Level 2 - WIGNER:
      "Friend is in superposition of having seen up AND down"
      "The measurement hasn't really happened yet"

    Level 3 - SUPER-WIGNER:
      "Wigner is in superposition of thinking Friend saw definite result
       AND thinking Friend is still in superposition"

    Each level has a different view of what is "real"!

    The paradox deepens: Can Super-Wigner reverse everything?
    If so, did Friend ever really experience a definite outcome?
    """)

    results = experiment["results"]

    # Friend only
    print("-" * 72)
    print("LEVEL 1: FRIEND ONLY")
    print("-" * 72)

    friend = results["friend_only"]
    counts = friend["counts"]
    total = friend["total"]

    print("\n   Friend sees definite outcomes:")
    for outcome in ["0000", "0011", "1100", "1111"]:
        c = counts.get(outcome, 0)
        if c > 0:
            p = c / total * 100
            print(f"   |{outcome}>: {c:4d} ({p:5.1f}%)")

    # Wigner only
    print("\n" + "-" * 72)
    print("LEVEL 2: FRIEND + WIGNER")
    print("-" * 72)

    wigner = results["wigner_only"]
    counts = wigner["counts"]
    total = wigner["total"]

    print("\n   Wigner's view (correlations between levels):")
    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])[:6]
    for outcome, count in sorted_outcomes:
        p = count / total * 100
        print(f"   |{outcome}>: {count:4d} ({p:5.1f}%)")

    # Three-level
    print("\n" + "-" * 72)
    print("LEVEL 3: FULL THREE-LEVEL OBSERVATION")
    print("-" * 72)

    three = results["three_level"]
    counts = three["counts"]
    total = three["total"]

    print("\n   Super-Wigner sees interference across all levels:")
    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])[:8]
    for outcome, count in sorted_outcomes:
        p = count / total * 100
        # Interpret bits: [Super-Wigner, Wigner, Friend, System]
        print(f"   |{outcome}>: {count:4d} ({p:5.1f}%)")

    # Reversal test
    print("\n" + "-" * 72)
    print("REVERSAL TEST: CAN SUPER-WIGNER UNMEASURE EVERYTHING?")
    print("-" * 72)

    reversal = results["reversal"]
    counts = reversal["counts"]
    total = reversal["total"]

    p_0000 = counts.get("0000", 0) / total * 100
    print(f"\n   If reversal works, should return to |0000⟩")
    print(f"   P(|0000⟩) = {p_0000:.1f}%")

    if p_0000 > 50:
        print(f"\n   [OK] Reversal partially successful!")
        print(f"   Measurements can be 'undone' from higher level")
    else:
        print(f"\n   [~] Decoherence prevents clean reversal")
        print(f"   (Expected on noisy hardware)")

    # Inconsistency test
    print("\n" + "-" * 72)
    print("INCONSISTENCY TEST")
    print("-" * 72)

    inconsist = results["inconsistency"]
    counts = inconsist["counts"]
    total = inconsist["total"]

    print("\n   Designed to show prediction disagreements:")
    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])[:6]
    for outcome, count in sorted_outcomes:
        p = count / total * 100
        print(f"   |{outcome}>: {count:4d} ({p:5.1f}%)")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
    Wigner's Friend's Friend pushes the measurement problem further:

    1. INFINITE REGRESS?
       - If Super-Wigner needs a Super-Super-Wigner to collapse them...
       - Where does it end?
       - This is the "von Neumann chain" problem

    2. OBJECTIVITY OF FACTS
       - Friend has a definite experience
       - But Wigner says Friend is in superposition
       - And Super-Wigner says Wigner is in superposition of views
       - Are any facts objective?

    3. RELATIONAL QUANTUM MECHANICS
       - Perhaps facts ARE relative to observers
       - No "view from nowhere"
       - Each level has its own valid description

    4. MANY-WORLDS INTERPRETATION
       - All outcomes happen in different branches
       - No paradox, just branching
       - But what is "experience" in this view?

    5. QBism (Quantum Bayesianism)
       - Quantum states are beliefs, not reality
       - Each agent updates their own beliefs
       - No conflict because no claim to objectivity

    The experiment shows quantum coherence can span multiple
    "measurement" levels - the paradox is conceptual, not experimental.
    """)
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Three-Level Observer Circuit ---")
    print(create_three_level_observer_circuit().draw(output="text"))

    print("\n--- Super-Wigner Reversal ---")
    print(create_super_wigner_reversal().draw(output="text"))


def main():
    """Main entry point for Wigner's Friend's Friend demonstration."""
    print("=" * 72)
    print("WIGNER'S FRIEND'S FRIEND PARADOX")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
Wigner's Friend's Friend:

  An extension of Wigner's Friend with THREE observer levels.

  The hierarchy:
    System → Friend measures → Wigner observes → Super-Wigner observes

  Level 1 (Friend): "I saw spin UP" - definite result
  Level 2 (Wigner): "Friend is in superposition" - no definite result yet
  Level 3 (Super-Wigner): "Wigner is in superposition of views"

  Key questions:
  - Can Super-Wigner reverse all measurements?
  - Did Friend really experience a definite outcome?
  - Is there an objective fact about what happened?
  - How deep does the rabbit hole go?

Experiments:
  1. Friend-only measurement (baseline)
  2. Friend + Wigner (standard Wigner's Friend)
  3. Full three-level observation
  4. Super-Wigner reversal test
  5. Inconsistency demonstration
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
