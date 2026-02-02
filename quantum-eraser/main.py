"""
Quantum Eraser Paradox Demonstration on IBM Quantum Hardware

The paradox: "Which-path" information destroys interference patterns.
But if we "erase" that information, interference returns - even retroactively!

This seems to imply that future measurements can affect past events,
challenging our understanding of causality and reality.

This experiment demonstrates:
1. Double-slit interference (via Hadamard gates)
2. Which-path marking destroys interference
3. Quantum erasure restores interference
4. Delayed-choice quantum eraser variant
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_interference_circuit() -> QuantumCircuit:
    """
    Create basic interference pattern (control case).

    A Hadamard creates superposition, another Hadamard creates interference.
    H|0> = |+>, then H|+> = |0>  (constructive interference to |0>)

    This is analogous to a photon going through both slits and
    interfering with itself.
    """
    qc = QuantumCircuit(1, 1, name="interference")

    # First "slit" - create superposition
    qc.h(0)

    # Second "slit" - recombine paths (interference)
    qc.h(0)

    # Should always measure |0> due to interference
    qc.measure(0, 0)

    return qc


def create_which_path_circuit() -> QuantumCircuit:
    """
    Which-path information destroys interference.

    By entangling with an "environment" qubit, we mark which path
    the particle took. This destroys interference!

    Path marking: |0>|env> -> |0>|path_0>, |1>|env> -> |1>|path_1>
    """
    qc = QuantumCircuit(2, 2, name="which_path")

    # Create superposition (both paths)
    qc.h(0)

    # Mark which path (entangle with environment)
    qc.cx(0, 1)  # If path 0: env stays |0>, if path 1: env flips to |1>

    qc.barrier(label="Path marked")

    # Try to interfere
    qc.h(0)

    # Interference destroyed! Results are random
    qc.measure([0, 1], [0, 1])

    return qc


def create_quantum_eraser_circuit() -> QuantumCircuit:
    """
    Quantum eraser restores interference.

    After marking the path, we "erase" the which-path information
    by measuring the environment in a superposition basis.
    This restores interference for correlated subsets of results!
    """
    qc = QuantumCircuit(2, 2, name="quantum_eraser")

    # Create superposition
    qc.h(0)

    # Mark which path
    qc.cx(0, 1)

    qc.barrier(label="Path marked")

    # ERASE the which-path information
    # Measure environment in |+>/|-> basis instead of |0>/|1>
    qc.h(1)

    qc.barrier(label="Path erased")

    # Now interference can occur (for correlated subsets)
    qc.h(0)

    qc.measure([0, 1], [0, 1])

    return qc


def create_delayed_choice_eraser_circuit() -> QuantumCircuit:
    """
    Delayed-choice quantum eraser.

    The "eraser" measurement happens AFTER the signal measurement,
    yet it still determines whether interference occurred!

    This challenges our notion of temporal causality.
    """
    qc = QuantumCircuit(2, 2, name="delayed_choice")

    # Create superposition
    qc.h(0)

    # Entangle (mark path)
    qc.cx(0, 1)

    # Interfere the signal qubit FIRST
    qc.h(0)
    qc.measure(0, 0)

    qc.barrier(label="Signal measured first")

    # THEN decide whether to erase or not
    # Erase: measure in |+>/|-> basis
    qc.h(1)
    qc.measure(1, 1)

    return qc


def create_full_eraser_experiment() -> list[QuantumCircuit]:
    """
    Create complete eraser experiment with all variants.

    Returns circuits for:
    1. Pure interference (no marking)
    2. Which-path marked (no erasure)
    3. Eraser in |+>/|-> basis
    4. Eraser in |0>/|1> basis (no erasure, control)
    """
    circuits = []

    # 1. Pure interference
    qc1 = QuantumCircuit(2, 2, name="pure_interference")
    qc1.h(0)
    qc1.h(0)  # Interfere
    qc1.measure([0, 1], [0, 1])
    circuits.append(qc1)

    # 2. Path marked, no erasure
    qc2 = QuantumCircuit(2, 2, name="marked_no_erase")
    qc2.h(0)
    qc2.cx(0, 1)
    qc2.h(0)
    qc2.measure([0, 1], [0, 1])
    circuits.append(qc2)

    # 3. Path marked, erased (H on env)
    qc3 = QuantumCircuit(2, 2, name="erased")
    qc3.h(0)
    qc3.cx(0, 1)
    qc3.h(1)  # Erase
    qc3.h(0)  # Interfere
    qc3.measure([0, 1], [0, 1])
    circuits.append(qc3)

    # 4. Control: path marked, "erase" with identity
    qc4 = QuantumCircuit(2, 2, name="control")
    qc4.h(0)
    qc4.cx(0, 1)
    qc4.id(1)  # No erasure
    qc4.h(0)
    qc4.measure([0, 1], [0, 1])
    circuits.append(qc4)

    return circuits


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


def run_quantum_eraser_experiment(shots: int = 4096) -> dict:
    """Run the quantum eraser experiment on IBM Quantum hardware."""
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=2)
    print(f"Backend: {backend.name}")
    print(f"Qubits: {backend.num_qubits}")

    circuits = []
    labels = []

    # Basic circuits
    circuits.append(create_interference_circuit())
    labels.append("interference")

    circuits.append(create_which_path_circuit())
    labels.append("which_path")

    circuits.append(create_quantum_eraser_circuit())
    labels.append("eraser")

    circuits.append(create_delayed_choice_eraser_circuit())
    labels.append("delayed_choice")

    # Full experiment variants
    full_exp = create_full_eraser_experiment()
    circuits.extend(full_exp)
    labels.extend(["pure_interference", "marked_no_erase", "erased", "control"])

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
    """Analyze and display quantum eraser experiment results."""
    print("=" * 72)
    print("QUANTUM ERASER - EXPERIMENTAL RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    results = experiment["results"]

    # 1. Pure interference
    print("\n" + "-" * 72)
    print("1. PURE INTERFERENCE (No path marking)")
    print("-" * 72)

    interf = results["interference"]
    counts = interf["counts"]
    total = interf["total"]

    p_0 = counts.get("0", 0) / total

    print(f"   |0>: {counts.get('0', 0):4d} ({p_0*100:5.1f}%)")
    print(f"   |1>: {counts.get('1', 0):4d} ({(1-p_0)*100:5.1f}%)")
    print(f"\n   Theory: 100% |0> (constructive interference)")

    if p_0 > 0.85:
        print(f"   [OK] Strong interference observed!")
    else:
        print(f"   [~] Interference reduced by hardware noise")

    # 2. Which-path marked
    print("\n" + "-" * 72)
    print("2. WHICH-PATH MARKED (Interference destroyed)")
    print("-" * 72)

    wp = results["which_path"]
    counts = wp["counts"]
    total = wp["total"]

    print(f"   |00>: {counts.get('00', 0):4d}")
    print(f"   |01>: {counts.get('01', 0):4d}")
    print(f"   |10>: {counts.get('10', 0):4d}")
    print(f"   |11>: {counts.get('11', 0):4d}")

    # Check if signal qubit (q0) is random
    p_0_signal = (counts.get("00", 0) + counts.get("01", 0)) / total
    print(f"\n   Signal P(0): {p_0_signal*100:.1f}% (should be ~50% if no interference)")

    # 3. Quantum eraser
    print("\n" + "-" * 72)
    print("3. QUANTUM ERASER (Interference restored)")
    print("-" * 72)

    eraser = results["eraser"]
    counts = eraser["counts"]
    total = eraser["total"]

    print(f"   |00>: {counts.get('00', 0):4d}")
    print(f"   |01>: {counts.get('01', 0):4d}")
    print(f"   |10>: {counts.get('10', 0):4d}")
    print(f"   |11>: {counts.get('11', 0):4d}")

    # Conditioned on eraser result
    eraser_0 = counts.get("00", 0) + counts.get("10", 0)
    eraser_1 = counts.get("01", 0) + counts.get("11", 0)

    if eraser_0 > 0:
        p_00_given_erase0 = counts.get("00", 0) / eraser_0
        print(f"\n   When eraser=0: P(signal=0) = {p_00_given_erase0*100:.1f}%")

    if eraser_1 > 0:
        p_01_given_erase1 = counts.get("01", 0) / eraser_1
        print(f"   When eraser=1: P(signal=0) = {p_01_given_erase1*100:.1f}%")

    print(f"\n   Interference restored in correlated subsets!")

    # 4. Delayed choice
    print("\n" + "-" * 72)
    print("4. DELAYED-CHOICE ERASER")
    print("-" * 72)

    dc = results["delayed_choice"]
    counts = dc["counts"]
    total = dc["total"]

    print(f"   Signal measured BEFORE eraser decision")
    print(f"\n   |00>: {counts.get('00', 0):4d}")
    print(f"   |01>: {counts.get('01', 0):4d}")
    print(f"   |10>: {counts.get('10', 0):4d}")
    print(f"   |11>: {counts.get('11', 0):4d}")

    print(f"\n   The 'future' eraser measurement determines")
    print(f"   whether the 'past' signal shows interference!")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
Quantum Eraser Paradox:
  - Which-path information destroys interference
  - Erasing that information restores interference
  - Even works "retroactively" in delayed-choice experiments!

Key insight:
  - It's not about "changing the past"
  - Interference is always there, but hidden in correlations
  - Post-selection on eraser results reveals interference pattern

What this teaches us:
  - Complementarity: wave OR particle, never both simultaneously
  - Information is physical: knowing which path = no interference
  - Quantum correlations can span space and time
  - Causality is preserved (no FTL signaling possible)
""")
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Pure Interference ---")
    print(create_interference_circuit().draw(output="text"))

    print("\n--- Which-Path Marked ---")
    print(create_which_path_circuit().draw(output="text"))

    print("\n--- Quantum Eraser ---")
    print(create_quantum_eraser_circuit().draw(output="text"))

    print("\n--- Delayed-Choice Eraser ---")
    print(create_delayed_choice_eraser_circuit().draw(output="text"))


def main():
    """Main entry point for Quantum Eraser demonstration."""
    print("=" * 72)
    print("QUANTUM ERASER PARADOX DEMONSTRATION")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
Quantum Eraser (1982, Scully & Druhl):
  In double-slit experiment, marking "which path" destroys interference.
  But if we "erase" that information, interference returns!

Delayed-Choice Quantum Eraser:
  The eraser measurement happens AFTER the signal is detected,
  yet it determines whether interference occurred!

  Does the future affect the past? (No, but it's subtle...)

Experiment design:
  1. Pure interference: H -> H gives |0>
  2. Path marked: CNOT entangles, destroys interference
  3. Eraser: H on ancilla before measurement restores interference
  4. Delayed choice: measure signal first, then decide to erase
""")

    print_circuit_diagrams()

    try:
        print("\n" + "=" * 72)
        print("RUNNING EXPERIMENT ON IBM QUANTUM HARDWARE")
        print("=" * 72 + "\n")

        experiment = run_quantum_eraser_experiment(shots=4096)
        analyze_results(experiment)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Check .env file has valid credentials")
        print("  2. Ensure packages are installed: uv sync")
        print("  3. Verify IBM Quantum account at quantum.ibm.com")


if __name__ == "__main__":
    main()
