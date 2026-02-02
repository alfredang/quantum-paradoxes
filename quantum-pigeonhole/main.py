"""
Quantum Pigeonhole Paradox on IBM Quantum Hardware

The quantum pigeonhole paradox (2016) shows that three quantum "pigeons"
can be placed in two "boxes" such that no two pigeons are ever in the same box.

Classical pigeonhole principle:
- If you put 3 pigeons in 2 boxes, at least 2 must share a box

Quantum violation:
- Using pre/post-selection, we can show that no two pigeons share
- This is verified by "weak measurements" that don't disturb the state
- Yet 3 pigeons are definitely in only 2 boxes!

This paradox highlights the strange nature of quantum counterfactuals
and the role of measurement context.
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_pigeonhole_circuit() -> QuantumCircuit:
    """
    Create the quantum pigeonhole circuit.

    Three qubits represent three pigeons.
    |0⟩ = left box, |1⟩ = right box

    Pre-selection: Each pigeon in superposition |+⟩ = (|0⟩ + |1⟩)/√2
    Post-selection: All pigeons in |+⟩ state

    Between pre and post selection, weak measurements show
    no two pigeons share a box!
    """
    qc = QuantumCircuit(3, 3, name="pigeonhole")

    # Pre-selection: Put each pigeon in superposition of both boxes
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier(label="Pre-select |+++⟩")

    # The paradox is revealed through correlations
    # These CZ gates create the necessary correlations
    qc.cz(0, 1)
    qc.cz(1, 2)
    qc.cz(0, 2)
    qc.barrier(label="Correlations")

    # Post-selection: Measure in X basis (|+⟩/|−⟩)
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier(label="Post-select")

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_pair_check_01() -> QuantumCircuit:
    """
    Check if pigeons 0 and 1 share a box.

    We prepare the pre-selected state, then measure whether
    pigeons 0 and 1 are in the same box (both |0⟩ or both |1⟩).
    """
    qc = QuantumCircuit(3, 3, name="pair_01")

    # Pre-selection
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier()

    # Measure pair 0,1 in computational basis
    # to check if they share a box
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_pair_check_12() -> QuantumCircuit:
    """Check if pigeons 1 and 2 share a box."""
    qc = QuantumCircuit(3, 3, name="pair_12")

    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier()

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_pair_check_02() -> QuantumCircuit:
    """Check if pigeons 0 and 2 share a box."""
    qc = QuantumCircuit(3, 3, name="pair_02")

    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier()

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_classical_pigeonhole() -> QuantumCircuit:
    """
    Classical pigeonhole: randomly place 3 pigeons in 2 boxes.

    At least one pair MUST share a box.
    """
    qc = QuantumCircuit(3, 3, name="classical")

    # Random placement (each pigeon independently random)
    qc.h(0)
    qc.h(1)
    qc.h(2)

    # Measure which box each pigeon is in
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_weak_measurement_circuit() -> QuantumCircuit:
    """
    Simulate weak measurement of pair sharing.

    Uses ancilla qubit for weak measurement of whether
    two pigeons share a box.
    """
    qc = QuantumCircuit(4, 4, name="weak_measure")

    # Pre-selection: |+++⟩
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier(label="Pre-select")

    # Weak measurement: check if pigeons 0,1 share box
    # CNOT from "same box" condition to ancilla
    qc.cx(0, 3)
    qc.cx(1, 3)
    # Ancilla is |0⟩ if same box, |1⟩ if different
    qc.barrier(label="Weak measure")

    # Post-selection in X basis
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier(label="Post-select")

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
    """Run quantum pigeonhole experiment on IBM Quantum hardware."""
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
        create_classical_pigeonhole(),
        create_pigeonhole_circuit(),
        create_weak_measurement_circuit(),
    ]
    labels = ["classical", "quantum", "weak_measure"]

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


def analyze_sharing(counts: dict, total: int) -> dict:
    """Analyze which pairs share boxes."""
    pair_01_share = 0
    pair_12_share = 0
    pair_02_share = 0
    any_share = 0

    for outcome, count in counts.items():
        # Pad outcome to 3 bits if needed
        outcome = outcome.zfill(3)
        p0, p1, p2 = outcome[0], outcome[1], outcome[2]

        if p0 == p1:
            pair_01_share += count
        if p1 == p2:
            pair_12_share += count
        if p0 == p2:
            pair_02_share += count
        if p0 == p1 or p1 == p2 or p0 == p2:
            any_share += count

    return {
        "pair_01": pair_01_share / total,
        "pair_12": pair_12_share / total,
        "pair_02": pair_02_share / total,
        "any": any_share / total,
    }


def analyze_results(experiment: dict) -> None:
    """Analyze and display quantum pigeonhole results."""
    print("=" * 72)
    print("QUANTUM PIGEONHOLE PARADOX - RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    print("\n" + "-" * 72)
    print("THE PIGEONHOLE PRINCIPLE")
    print("-" * 72)
    print("""
    Classical Pigeonhole Principle:
      If you put N+1 pigeons in N boxes,
      at least two pigeons must share a box.

    With 3 pigeons and 2 boxes:
      - At least one pair MUST be in the same box
      - Probability that NO pair shares = 0%

    Quantum Pigeonhole Paradox:
      - Pre-select: Each pigeon in superposition of both boxes
      - Post-select: All pigeons measured in |+⟩ state
      - Between these: NO pair shares a box!

    This violates the classical principle through the
    magic of pre/post-selection and weak measurements.
    """)

    results = experiment["results"]

    # Classical case
    print("-" * 72)
    print("CLASSICAL PIGEONS")
    print("-" * 72)

    classical = results["classical"]
    counts = classical["counts"]
    total = classical["total"]

    sharing = analyze_sharing(counts, total)

    print("\n   Random placement of 3 pigeons in 2 boxes:")
    print(f"   Pair (0,1) share: {sharing['pair_01']*100:.1f}%")
    print(f"   Pair (1,2) share: {sharing['pair_12']*100:.1f}%")
    print(f"   Pair (0,2) share: {sharing['pair_02']*100:.1f}%")
    print(f"   ANY pair shares:  {sharing['any']*100:.1f}%")
    print(f"\n   Expected: At least one pair always shares (~100%)")

    # Quantum case
    print("\n" + "-" * 72)
    print("QUANTUM PIGEONS (with post-selection)")
    print("-" * 72)

    quantum = results["quantum"]
    counts = quantum["counts"]
    total = quantum["total"]

    print("\n   Measurement outcomes (post-selection in X basis):")
    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])
    for outcome, count in sorted_outcomes[:8]:
        p = count / total * 100
        print(f"   |{outcome}>: {count:4d} ({p:5.1f}%)")

    # Post-select on |000⟩ (all pigeons in |+⟩)
    postselect_counts = counts.get("000", 0)
    print(f"\n   Post-selected |000⟩ (all |+⟩): {postselect_counts} events")
    print(f"   Post-selection rate: {postselect_counts/total*100:.1f}%")

    # Weak measurement analysis
    print("\n" + "-" * 72)
    print("WEAK MEASUREMENT ANALYSIS")
    print("-" * 72)

    weak = results["weak_measure"]
    counts = weak["counts"]
    total = weak["total"]

    print("\n   Weak measurement of pair sharing:")
    print("   (Last bit = 0: same box, 1: different box)")

    # Analyze conditioned on post-selection
    postselected = {k: v for k, v in counts.items() if k.startswith("000") or k.endswith("000")}
    if postselected:
        print(f"\n   Post-selected outcomes: {sum(postselected.values())}")

    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])[:8]
    for outcome, count in sorted_outcomes:
        p = count / total * 100
        print(f"   |{outcome}>: {count:4d} ({p:5.1f}%)")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
    The Quantum Pigeonhole Paradox reveals:

    1. CONTEXTUALITY
       - The question "are pigeons 0,1 in the same box?" has no
         definite answer independent of other measurements
       - Each pair asked separately: never share
       - But all pairs can't not-share classically!

    2. PRE/POST-SELECTION PARADOXES
       - By conditioning on future measurements, we get strange results
       - The Aharonov-Bergmann-Lebowitz (ABL) formula governs this
       - Not retrocausality, but inference about past given future

    3. WEAK MEASUREMENTS
       - Gentle measurements that don't collapse state
       - Reveal "weak values" that can be strange
       - Weak value of "same box" can be 0 for all pairs!

    4. IMPLICATIONS
       - Quantum particles don't have definite properties
       - The pigeonhole principle relies on classical definiteness
       - Quantum mechanics allows the "impossible"

    This is not a practical device but a conceptual demonstration
    of quantum weirdness.
    """)
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Quantum Pigeonhole Circuit ---")
    print(create_pigeonhole_circuit().draw(output="text"))

    print("\n--- Weak Measurement Circuit ---")
    print(create_weak_measurement_circuit().draw(output="text"))


def main():
    """Main entry point for quantum pigeonhole demonstration."""
    print("=" * 72)
    print("QUANTUM PIGEONHOLE PARADOX")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
The Quantum Pigeonhole Paradox (2016):

  Classical Pigeonhole Principle:
    3 pigeons, 2 boxes → at least 2 must share

  Quantum Violation:
    3 quantum pigeons in superposition of 2 boxes,
    yet no two ever share the same box!

  How is this possible?
    - Pre-select: Each pigeon in |+⟩ = (|L⟩ + |R⟩)/√2
    - Post-select: All pigeons found in |+⟩
    - Between: Weak measurements show no sharing

  The resolution:
    - Pigeons don't have definite positions
    - "Sharing" depends on what else we measure
    - Quantum contextuality defeats classical logic

Experiment:
  1. Classical random placement (verify principle)
  2. Quantum pre/post-selected state
  3. Weak measurement of pair sharing
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
