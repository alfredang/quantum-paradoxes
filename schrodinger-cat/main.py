"""
Schrodinger's Cat Paradox Demonstration on IBM Quantum Hardware

The paradox: A cat in a box is simultaneously alive AND dead until observed.
In quantum terms, a system exists in superposition of all possible states
until measurement collapses it to a definite outcome.

This experiment demonstrates:
1. Creating a qubit in perfect superposition (the "cat" state)
2. Entangling it with another qubit (the "environment/detector")
3. Showing that measurement collapses the superposition
4. Demonstrating decoherence effects on real hardware
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_cat_state_circuit() -> QuantumCircuit:
    """
    Create a simple "cat state" - a qubit in superposition.

    |psi> = (|0> + |1>) / sqrt(2)

    This represents the cat being "alive" (|0>) AND "dead" (|1>) simultaneously.
    """
    qc = QuantumCircuit(1, 1, name="cat_superposition")

    # Create superposition: the cat is both alive and dead
    qc.h(0)

    # Measure to "open the box"
    qc.measure(0, 0)

    return qc


def create_entangled_cat_circuit() -> QuantumCircuit:
    """
    Create an entangled cat state (GHZ-like state).

    |psi> = (|00> + |11>) / sqrt(2)

    The "cat" qubit is entangled with a "detector" qubit.
    This models the cat's state being correlated with the radioactive atom.
    When one is measured, both collapse together.
    """
    qc = QuantumCircuit(2, 2, name="entangled_cat")

    # Qubit 0: radioactive atom / detector
    # Qubit 1: cat (alive=|0>, dead=|1>)

    # Create entanglement: atom decayed -> cat dead, atom intact -> cat alive
    qc.h(0)  # Atom in superposition of decayed/not decayed
    qc.cx(0, 1)  # Entangle cat's fate with atom

    # Measure both
    qc.measure([0, 1], [0, 1])

    return qc


def create_multi_cat_ghz_circuit(num_qubits: int = 3) -> QuantumCircuit:
    """
    Create a GHZ state - multiple "cats" in entangled superposition.

    |GHZ> = (|000...0> + |111...1>) / sqrt(2)

    All qubits are either ALL in state |0> or ALL in state |1>.
    This is the maximally entangled state for N qubits.
    """
    qc = QuantumCircuit(num_qubits, num_qubits, name=f"ghz_{num_qubits}")

    # Create GHZ state
    qc.h(0)
    for i in range(1, num_qubits):
        qc.cx(0, i)

    # Measure all qubits
    qc.measure(range(num_qubits), range(num_qubits))

    return qc


def create_decoherence_demo_circuit(delay_identity_gates: int = 0) -> QuantumCircuit:
    """
    Demonstrate decoherence - how the environment "measures" the cat.

    In the real world, superpositions decohere quickly because the
    environment constantly interacts with (measures) the system.

    We simulate this by adding identity gates (which add noise on real hardware).
    """
    qc = QuantumCircuit(1, 1, name=f"decoherence_{delay_identity_gates}")

    # Create superposition
    qc.h(0)

    # Add "delay" via identity gates (accumulates noise on real hardware)
    for _ in range(delay_identity_gates):
        qc.id(0)

    # Measure
    qc.measure(0, 0)

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


def run_schrodinger_cat_experiment(shots: int = 4096) -> dict:
    """
    Run the Schrodinger's Cat experiment on IBM Quantum hardware.

    Demonstrates:
    1. Single qubit superposition (basic cat state)
    2. Entangled cat state (cat + detector)
    3. GHZ state (multiple entangled cats)
    4. Decoherence effects
    """
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    print(f"Backend: {backend.name}")
    print(f"Qubits: {backend.num_qubits}")

    circuits = []
    labels = []

    # 1. Basic cat state
    qc_cat = create_cat_state_circuit()
    circuits.append(qc_cat)
    labels.append("basic_cat")

    # 2. Entangled cat state
    qc_entangled = create_entangled_cat_circuit()
    circuits.append(qc_entangled)
    labels.append("entangled_cat")

    # 3. GHZ states (3 and 5 qubits)
    for n in [3, 5]:
        qc_ghz = create_multi_cat_ghz_circuit(n)
        circuits.append(qc_ghz)
        labels.append(f"ghz_{n}")

    # 4. Decoherence demonstration
    for delay in [0, 10, 50, 100]:
        qc_decay = create_decoherence_demo_circuit(delay)
        circuits.append(qc_decay)
        labels.append(f"decoherence_{delay}")

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
        total = sum(counts.values()) if counts else shots

        processed_results[label] = {
            "counts": counts,
            "total": total,
            "circuit": circuits[idx]
        }

    return {
        "results": processed_results,
        "job_id": job_id,
        "backend": backend.name,
        "shots": shots
    }


def analyze_results(experiment: dict) -> None:
    """Analyze and display Schrodinger's Cat experiment results."""
    print("=" * 72)
    print("SCHRODINGER'S CAT - EXPERIMENTAL RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    results = experiment["results"]

    # Basic cat state
    print("\n" + "-" * 72)
    print("1. BASIC CAT STATE: |psi> = (|alive> + |dead>) / sqrt(2)")
    print("-" * 72)

    cat = results["basic_cat"]
    counts = cat["counts"]
    total = cat["total"]

    p_alive = counts.get("0", 0) / total
    p_dead = counts.get("1", 0) / total

    print(f"   |0> (alive): {counts.get('0', 0):4d} ({p_alive*100:5.1f}%)")
    print(f"   |1> (dead):  {counts.get('1', 0):4d} ({p_dead*100:5.1f}%)")
    print(f"\n   Theory: 50% / 50%")
    print(f"   The cat was in superposition until measured!")

    # Entangled cat
    print("\n" + "-" * 72)
    print("2. ENTANGLED CAT: |psi> = (|atom_intact, alive> + |atom_decayed, dead>) / sqrt(2)")
    print("-" * 72)

    ent = results["entangled_cat"]
    counts = ent["counts"]
    total = ent["total"]

    p_00 = counts.get("00", 0) / total
    p_11 = counts.get("11", 0) / total
    p_01 = counts.get("01", 0) / total
    p_10 = counts.get("10", 0) / total

    print(f"   |00> (intact, alive):  {counts.get('00', 0):4d} ({p_00*100:5.1f}%)")
    print(f"   |11> (decayed, dead):  {counts.get('11', 0):4d} ({p_11*100:5.1f}%)")
    print(f"   |01> (error):          {counts.get('01', 0):4d} ({p_01*100:5.1f}%)")
    print(f"   |10> (error):          {counts.get('10', 0):4d} ({p_10*100:5.1f}%)")

    correlation = p_00 + p_11
    print(f"\n   Correlation: {correlation*100:.1f}% (theory: 100%)")
    print(f"   The atom and cat are perfectly correlated!")

    # GHZ states
    print("\n" + "-" * 72)
    print("3. GHZ STATES: Multiple entangled 'cats'")
    print("-" * 72)

    for n in [3, 5]:
        ghz = results[f"ghz_{n}"]
        counts = ghz["counts"]
        total = ghz["total"]

        all_zeros = "0" * n
        all_ones = "1" * n
        p_zeros = counts.get(all_zeros, 0) / total
        p_ones = counts.get(all_ones, 0) / total

        print(f"\n   {n}-qubit GHZ state:")
        print(f"   |{'0'*n}>: {counts.get(all_zeros, 0):4d} ({p_zeros*100:5.1f}%)")
        print(f"   |{'1'*n}>: {counts.get(all_ones, 0):4d} ({p_ones*100:5.1f}%)")
        print(f"   Other:  {total - counts.get(all_zeros, 0) - counts.get(all_ones, 0):4d}")
        print(f"   Fidelity: {(p_zeros + p_ones)*100:.1f}%")

    # Decoherence
    print("\n" + "-" * 72)
    print("4. DECOHERENCE: Environment 'measures' the cat")
    print("-" * 72)
    print("\n   Adding delay accumulates hardware noise,")
    print("   simulating how environment destroys superposition.\n")

    print(f"   {'Delay':<10} {'P(|0>)':<12} {'P(|1>)':<12} {'Deviation'}")
    print("   " + "-" * 45)

    for delay in [0, 10, 50, 100]:
        dec = results[f"decoherence_{delay}"]
        counts = dec["counts"]
        total = dec["total"]

        p0 = counts.get("0", 0) / total
        p1 = counts.get("1", 0) / total
        deviation = abs(p0 - 0.5) * 100

        print(f"   {delay:<10} {p0:<12.4f} {p1:<12.4f} {deviation:.2f}%")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
Schrodinger's Cat Paradox:
  - The cat is in superposition (alive AND dead) until observed
  - Measurement "collapses" the wavefunction to a definite state
  - Entanglement correlates the cat's fate with the detector

Why we don't see macroscopic superpositions:
  - Decoherence: the environment constantly "measures" large objects
  - Information leaks into the environment, destroying superposition
  - This happens in femtoseconds for macroscopic objects

The paradox highlights:
  - The measurement problem: what constitutes a "measurement"?
  - The quantum-classical boundary
  - The role of the observer in quantum mechanics
""")
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams for visualization."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Basic Cat State ---")
    print(create_cat_state_circuit().draw(output="text"))

    print("\n--- Entangled Cat State ---")
    print(create_entangled_cat_circuit().draw(output="text"))

    print("\n--- 3-Qubit GHZ State ---")
    print(create_multi_cat_ghz_circuit(3).draw(output="text"))


def main():
    """Main entry point for Schrodinger's Cat demonstration."""
    print("=" * 72)
    print("SCHRODINGER'S CAT PARADOX DEMONSTRATION")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
Schrodinger's Cat (1935):
  A cat in a sealed box with a radioactive atom and poison.
  If the atom decays, the poison is released and the cat dies.

  Quantum mechanics says the atom is in superposition of
  decayed AND not-decayed. Therefore, the cat must be
  simultaneously ALIVE and DEAD until we open the box!

Experiment design:
  1. Basic cat state: single qubit in superposition
  2. Entangled cat: qubit entangled with "detector"
  3. GHZ states: multiple entangled qubits
  4. Decoherence: how environment destroys superposition
""")

    print_circuit_diagrams()

    try:
        print("\n" + "=" * 72)
        print("RUNNING EXPERIMENT ON IBM QUANTUM HARDWARE")
        print("=" * 72 + "\n")

        experiment = run_schrodinger_cat_experiment(shots=4096)
        analyze_results(experiment)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Check .env file has valid credentials")
        print("  2. Ensure packages are installed: uv sync")
        print("  3. Verify IBM Quantum account at quantum.ibm.com")


if __name__ == "__main__":
    main()
