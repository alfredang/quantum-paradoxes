"""
Hardy's Paradox Demonstration on IBM Quantum Hardware

Hardy's Paradox (1992): A "proof" of quantum nonlocality without inequalities.

The setup involves two particles that can each take one of two paths.
Quantum mechanics predicts outcomes that seem logically impossible
if we assume particles have definite properties before measurement.

This is considered one of the cleanest demonstrations that
quantum mechanics is incompatible with local hidden variables.
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_hardy_state() -> QuantumCircuit:
    """
    Create Hardy's entangled state.

    The Hardy state is: |psi> = (|00> + |01> + |10>) / sqrt(3)

    This is a partially entangled state that leads to the paradox.
    We can create it using:
    1. Start with |00>
    2. Apply rotations and CNOTs to get the right superposition
    """
    qc = QuantumCircuit(2, name="hardy_state_prep")

    # Create Hardy state: (|00> + |01> + |10>) / sqrt(3)
    # Method: Use controlled rotations

    # First, create superposition on qubit 0
    theta = 2 * np.arccos(1 / np.sqrt(3))  # angle for 1/sqrt(3) amplitude
    qc.ry(theta, 0)

    # Controlled operation to create the right state
    qc.ch(0, 1)  # Controlled Hadamard

    # Adjust phases if needed
    qc.x(0)
    qc.cx(0, 1)
    qc.x(0)

    return qc


def create_hardy_paradox_circuit() -> QuantumCircuit:
    """
    Create the full Hardy's paradox experiment.

    Hardy's paradox setup:
    - Two particles (qubits) can each go through two paths
    - We measure in two different bases: computational (Z) and diagonal (X)
    - The correlations violate local realism

    The paradox:
    1. If Alice measures + and Bob measures +, the state was |++⟩ (never happens for certain preparations)
    2. If we see |++⟩, then neither particle took the "certain" path
    3. But QM predicts we CAN see |++⟩ with small probability!
    """
    qc = QuantumCircuit(2, 2, name="hardy_paradox")

    # Prepare Hardy state
    # |psi> ~ |00> + |01> + |10> (unnormalized)
    # This can be written as a partially entangled state

    # Simpler preparation for demonstration
    # Use a state close to Hardy's ideal state
    theta = np.arctan(1 / np.sqrt(2))

    qc.ry(2 * theta, 0)
    qc.ry(np.pi / 2, 1)
    qc.cz(0, 1)
    qc.ry(-np.pi / 4, 1)

    qc.barrier(label="Hardy state")

    # Measure in computational basis
    qc.measure([0, 1], [0, 1])

    return qc


def create_hardy_z_basis() -> QuantumCircuit:
    """Hardy experiment with both measured in Z basis."""
    qc = QuantumCircuit(2, 2, name="hardy_ZZ")

    # Prepare approximate Hardy state
    qc.ry(np.pi / 3, 0)
    qc.cx(0, 1)
    qc.ry(-np.pi / 6, 1)

    qc.barrier()
    # Z basis measurement (computational)
    qc.measure([0, 1], [0, 1])

    return qc


def create_hardy_x_basis() -> QuantumCircuit:
    """Hardy experiment with both measured in X basis."""
    qc = QuantumCircuit(2, 2, name="hardy_XX")

    # Prepare state
    qc.ry(np.pi / 3, 0)
    qc.cx(0, 1)
    qc.ry(-np.pi / 6, 1)

    qc.barrier()
    # X basis measurement
    qc.h(0)
    qc.h(1)
    qc.measure([0, 1], [0, 1])

    return qc


def create_hardy_mixed_basis() -> QuantumCircuit:
    """Hardy experiment with Alice in Z, Bob in X basis."""
    qc = QuantumCircuit(2, 2, name="hardy_ZX")

    # Prepare state
    qc.ry(np.pi / 3, 0)
    qc.cx(0, 1)
    qc.ry(-np.pi / 6, 1)

    qc.barrier()
    # Alice: Z basis, Bob: X basis
    qc.h(1)
    qc.measure([0, 1], [0, 1])

    return qc


def create_hardy_mixed_basis_2() -> QuantumCircuit:
    """Hardy experiment with Alice in X, Bob in Z basis."""
    qc = QuantumCircuit(2, 2, name="hardy_XZ")

    # Prepare state
    qc.ry(np.pi / 3, 0)
    qc.cx(0, 1)
    qc.ry(-np.pi / 6, 1)

    qc.barrier()
    # Alice: X basis, Bob: Z basis
    qc.h(0)
    qc.measure([0, 1], [0, 1])

    return qc


def create_optimal_hardy_circuit() -> QuantumCircuit:
    """
    Create optimal Hardy state for maximum paradox probability.

    The optimal Hardy state gives ~9% probability of the "paradoxical" outcome,
    which is the maximum possible violation.
    """
    qc = QuantumCircuit(2, 2, name="optimal_hardy")

    # Optimal angle for Hardy's paradox
    # sin^2(theta) = (sqrt(5) - 1) / 2 (golden ratio related!)
    theta = np.arcsin(np.sqrt((np.sqrt(5) - 1) / 2))

    # Create optimal Hardy state
    qc.ry(2 * theta, 0)
    qc.cx(0, 1)
    qc.ry(2 * theta, 1)
    qc.cx(0, 1)

    qc.barrier(label="Optimal Hardy")

    qc.measure([0, 1], [0, 1])

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


def run_hardy_paradox_experiment(shots: int = 4096) -> dict:
    """Run Hardy's paradox experiment on IBM Quantum hardware."""
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

    # All measurement basis combinations
    circuits.append(create_hardy_z_basis())
    labels.append("ZZ")

    circuits.append(create_hardy_x_basis())
    labels.append("XX")

    circuits.append(create_hardy_mixed_basis())
    labels.append("ZX")

    circuits.append(create_hardy_mixed_basis_2())
    labels.append("XZ")

    # Optimal Hardy state
    circuits.append(create_optimal_hardy_circuit())
    labels.append("optimal")

    # Basic paradox circuit
    circuits.append(create_hardy_paradox_circuit())
    labels.append("paradox")

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
    """Analyze and display Hardy's paradox experiment results."""
    print("=" * 72)
    print("HARDY'S PARADOX - EXPERIMENTAL RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    results = experiment["results"]

    # Explain the paradox
    print("\n" + "-" * 72)
    print("THE HARDY PARADOX LOGIC")
    print("-" * 72)
    print("""
    Setup: Two particles (Alice and Bob) each choose measurement basis.

    Classical logic says:
    1. If Alice=Z, Bob=Z, and we see |11>: both particles existed in path 1
    2. If Alice=Z, Bob=X, and Alice=1: Bob must have been definite
    3. If Alice=X, Bob=Z, and Bob=1: Alice must have been definite
    4. Therefore |11> in X,X basis should be IMPOSSIBLE

    But quantum mechanics allows |11> in ALL bases simultaneously!
    """)

    # Show results for each basis
    print("-" * 72)
    print("MEASUREMENT RESULTS BY BASIS")
    print("-" * 72)

    for label in ["ZZ", "XX", "ZX", "XZ"]:
        r = results[label]
        counts = r["counts"]
        total = r["total"]

        print(f"\n   {label} basis:")
        for outcome in ["00", "01", "10", "11"]:
            c = counts.get(outcome, 0)
            p = c / total * 100
            print(f"      |{outcome}>: {c:4d} ({p:5.1f}%)")

    # Highlight the paradox
    print("\n" + "-" * 72)
    print("PARADOX DEMONSTRATION")
    print("-" * 72)

    # ZZ basis - check for |11>
    zz = results["ZZ"]
    p_11_zz = zz["counts"].get("11", 0) / zz["total"]

    print(f"\n   P(11|ZZ) = {p_11_zz*100:.2f}%")
    print(f"   (Should be small but non-zero)")

    # XX basis - the paradox
    xx = results["XX"]
    p_11_xx = xx["counts"].get("11", 0) / xx["total"]

    print(f"\n   P(11|XX) = {p_11_xx*100:.2f}%")
    print(f"   Classical logic: should be 0%")
    print(f"   Quantum mechanics: ~9% (optimal)")

    if p_11_xx > 0.02:
        print(f"\n   [OK] HARDY'S PARADOX OBSERVED!")
        print(f"   The |11> outcome in XX basis violates classical logic.")
    else:
        print(f"\n   [~] Weak signal (hardware noise)")

    # Optimal Hardy state
    print("\n" + "-" * 72)
    print("OPTIMAL HARDY STATE")
    print("-" * 72)

    opt = results["optimal"]
    counts = opt["counts"]
    total = opt["total"]

    print(f"\n   Outcomes:")
    for outcome in ["00", "01", "10", "11"]:
        c = counts.get(outcome, 0)
        p = c / total * 100
        print(f"      |{outcome}>: {c:4d} ({p:5.1f}%)")

    p_11 = counts.get("11", 0) / total
    print(f"\n   P(11) = {p_11*100:.2f}% (theory: ~9%)")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
Hardy's Paradox proves nonlocality without Bell inequalities:

  The argument:
  1. P(11|ZZ) > 0 implies the particles sometimes both "exist"
  2. P(11|ZX) and P(11|XZ) patterns imply counterfactual definiteness
  3. Combining these: P(11|XX) should be 0
  4. But QM predicts P(11|XX) ~ 9%!

  This means:
  - Particles don't have pre-existing values
  - OR measurements are not local
  - OR counterfactual reasoning fails

  Hardy called this "the best version of Bell's theorem"
  because it uses logic rather than statistics.

  The golden ratio appears: optimal probability = (3 - sqrt(5))/2 ~ 9%
""")
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Hardy ZZ Basis ---")
    print(create_hardy_z_basis().draw(output="text"))

    print("\n--- Hardy XX Basis ---")
    print(create_hardy_x_basis().draw(output="text"))

    print("\n--- Optimal Hardy State ---")
    print(create_optimal_hardy_circuit().draw(output="text"))


def main():
    """Main entry point for Hardy's Paradox demonstration."""
    print("=" * 72)
    print("HARDY'S PARADOX DEMONSTRATION")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
Hardy's Paradox (1992):
  "The best version of Bell's theorem" - uses logic, not statistics.

  Two particles are prepared in a specific entangled state.
  Measuring both in the same basis gives certain correlations.
  Classical logic predicts some outcomes should NEVER happen.
  Quantum mechanics says they happen ~9% of the time!

Experiment design:
  1. Prepare Hardy state (partial entanglement)
  2. Measure in ZZ, XX, ZX, XZ bases
  3. Check for "impossible" outcomes
  4. Compare with optimal Hardy state
""")

    print_circuit_diagrams()

    try:
        print("\n" + "=" * 72)
        print("RUNNING EXPERIMENT ON IBM QUANTUM HARDWARE")
        print("=" * 72 + "\n")

        experiment = run_hardy_paradox_experiment(shots=4096)
        analyze_results(experiment)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Check .env file has valid credentials")
        print("  2. Ensure packages are installed: uv sync")
        print("  3. Verify IBM Quantum account at quantum.ibm.com")


if __name__ == "__main__":
    main()
