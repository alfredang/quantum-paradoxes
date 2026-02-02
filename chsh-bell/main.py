"""
CHSH-Bell Inequality Test on IBM Quantum Hardware

The CHSH inequality (Clauser-Horne-Shimony-Holt, 1969) is the most common
experimental test of Bell's theorem and quantum nonlocality.

Bell's theorem: No local hidden variable theory can reproduce all
predictions of quantum mechanics.

The CHSH inequality:
- Classical bound: |S| ≤ 2
- Quantum bound: |S| ≤ 2√2 ≈ 2.83 (Tsirelson's bound)
- Experimental violation proves quantum nonlocality

This is the basis for device-independent quantum cryptography and
certified randomness generation.
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_bell_state() -> QuantumCircuit:
    """
    Create the Bell state |Φ+⟩ = (|00⟩ + |11⟩) / √2

    This maximally entangled state gives the maximum CHSH violation.
    """
    qc = QuantumCircuit(2, name="bell_state")
    qc.h(0)
    qc.cx(0, 1)
    return qc


def create_chsh_circuit(a_setting: int, b_setting: int) -> QuantumCircuit:
    """
    Create CHSH measurement circuit for given settings.

    CHSH optimal settings:
    - Alice: A0 at 0°, A1 at 45° (π/4)
    - Bob: B0 at 22.5° (π/8), B1 at 67.5° (3π/8)

    Args:
        a_setting: Alice's setting (0 or 1)
        b_setting: Bob's setting (0 or 1)
    """
    qc = QuantumCircuit(2, 2, name=f"CHSH_A{a_setting}B{b_setting}")

    # Create Bell state
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier(label="Bell state")

    # Alice's measurement rotation
    if a_setting == 0:
        # A0: measure at 0° (Z basis)
        pass
    else:
        # A1: measure at 45° (π/4)
        qc.ry(-np.pi/4, 0)

    # Bob's measurement rotation
    if b_setting == 0:
        # B0: measure at 22.5° (π/8)
        qc.ry(-np.pi/8, 1)
    else:
        # B1: measure at 67.5° (3π/8) = -22.5° from X
        qc.ry(-3*np.pi/8, 1)

    qc.barrier(label="Measure")
    qc.measure([0, 1], [0, 1])

    return qc


def create_all_chsh_circuits() -> list:
    """Create circuits for all four CHSH measurement settings."""
    circuits = []
    for a in [0, 1]:
        for b in [0, 1]:
            circuits.append(create_chsh_circuit(a, b))
    return circuits


def create_classical_correlation_circuit() -> QuantumCircuit:
    """
    Classical correlation circuit for comparison.

    Uses a product state (not entangled) to show classical bound.
    """
    qc = QuantumCircuit(2, 2, name="classical")

    # Product state |00⟩ - no entanglement
    # Classical correlations only

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


def calculate_correlator(counts: dict, total: int) -> float:
    """
    Calculate the correlation E(a,b) from measurement counts.

    E = P(same) - P(different)
      = (P(00) + P(11)) - (P(01) + P(10))
    """
    same = counts.get("00", 0) + counts.get("11", 0)
    diff = counts.get("01", 0) + counts.get("10", 0)
    return (same - diff) / total


def run_experiment(shots: int = 4096) -> dict:
    """Run CHSH-Bell experiment on IBM Quantum hardware."""
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=2)
    print(f"Backend: {backend.name}")
    print(f"Qubits: {backend.num_qubits}")

    # Four CHSH circuits + classical reference
    chsh_circuits = create_all_chsh_circuits()
    circuits = chsh_circuits + [create_classical_correlation_circuit()]
    labels = ["A0B0", "A0B1", "A1B0", "A1B1", "classical"]

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
    """Analyze and display CHSH-Bell experiment results."""
    print("=" * 72)
    print("CHSH-BELL INEQUALITY TEST - RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    print("\n" + "-" * 72)
    print("THE CHSH INEQUALITY")
    print("-" * 72)
    print("""
    Bell's Theorem (1964):
      No local hidden variable theory can reproduce quantum predictions.

    CHSH Inequality (1969):
      S = E(A0,B0) + E(A0,B1) + E(A1,B0) - E(A1,B1)

      Classical bound:    |S| ≤ 2
      Quantum bound:      |S| ≤ 2√2 ≈ 2.83 (Tsirelson)
      Our target:         S ≈ 2.83 (maximum violation)

    Optimal measurement angles:
      Alice: A0 = 0°, A1 = 45°
      Bob:   B0 = 22.5°, B1 = 67.5°
    """)

    results = experiment["results"]

    # Calculate correlators
    print("-" * 72)
    print("MEASUREMENT RESULTS")
    print("-" * 72)

    correlators = {}
    for setting in ["A0B0", "A0B1", "A1B0", "A1B1"]:
        r = results[setting]
        counts = r["counts"]
        total = r["total"]

        E = calculate_correlator(counts, total)
        correlators[setting] = E

        print(f"\n   {setting}:")
        for outcome in ["00", "01", "10", "11"]:
            c = counts.get(outcome, 0)
            p = c / total * 100
            print(f"      |{outcome}>: {c:4d} ({p:5.1f}%)")
        print(f"      E({setting}) = {E:+.4f}")

    # Calculate S value
    S = correlators["A0B0"] + correlators["A0B1"] + correlators["A1B0"] - correlators["A1B1"]

    print("\n" + "-" * 72)
    print("CHSH VALUE CALCULATION")
    print("-" * 72)

    print(f"\n   S = E(A0,B0) + E(A0,B1) + E(A1,B0) - E(A1,B1)")
    print(f"   S = ({correlators['A0B0']:+.4f}) + ({correlators['A0B1']:+.4f}) + ({correlators['A1B0']:+.4f}) - ({correlators['A1B1']:+.4f})")
    print(f"\n   S = {S:+.4f}")

    print("\n" + "-" * 72)
    print("VIOLATION ANALYSIS")
    print("-" * 72)

    classical_bound = 2.0
    quantum_bound = 2 * np.sqrt(2)

    print(f"\n   Classical bound:  |S| ≤ {classical_bound:.4f}")
    print(f"   Quantum bound:    |S| ≤ {quantum_bound:.4f}")
    print(f"   Measured value:   |S| = {abs(S):.4f}")

    if abs(S) > classical_bound:
        violation = abs(S) - classical_bound
        sigma = violation / (0.1)  # rough error estimate
        print(f"\n   [OK] BELL INEQUALITY VIOLATED!")
        print(f"   Violation: {violation:.4f} above classical bound")
        print(f"   Achieved: {abs(S)/quantum_bound*100:.1f}% of quantum maximum")
    else:
        print(f"\n   [X] No violation observed (hardware noise)")

    # Error estimation
    print("\n" + "-" * 72)
    print("ERROR ANALYSIS")
    print("-" * 72)

    shots = experiment["shots"]
    # Statistical error for each correlator ~ 1/sqrt(N)
    stat_error = 1 / np.sqrt(shots)
    # S error (adding 4 correlators)
    S_error = 2 * stat_error  # rough estimate

    print(f"\n   Shots per setting: {shots}")
    print(f"   Statistical error per E: ~{stat_error:.4f}")
    print(f"   Estimated S error: ~{S_error:.4f}")
    print(f"\n   Note: Hardware noise typically dominates over statistical error")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
    What does CHSH violation prove?

    1. NO LOCAL HIDDEN VARIABLES
       - Particles don't carry pre-determined answers
       - OR information travels faster than light
       - OR measurement settings aren't free choices

    2. QUANTUM NONLOCALITY
       - Entangled particles are correlated in ways impossible classically
       - This correlation can't be used for signaling (no FTL communication)
       - But it IS a real physical phenomenon

    3. PRACTICAL APPLICATIONS
       - Device-independent quantum cryptography
       - Certified random number generation
       - Quantum advantage verification

    4. LOOPHOLES (all closed in modern experiments)
       - Locality: measurements must be spacelike separated
       - Detection: must detect enough particles
       - Freedom of choice: settings must be truly random

    The 2022 Nobel Prize in Physics was awarded for experimental
    work closing these loopholes and establishing nonlocality.
    """)
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Bell State Preparation ---")
    print(create_bell_state().draw(output="text"))

    print("\n--- CHSH A0B0 Setting ---")
    print(create_chsh_circuit(0, 0).draw(output="text"))

    print("\n--- CHSH A1B1 Setting ---")
    print(create_chsh_circuit(1, 1).draw(output="text"))


def main():
    """Main entry point for CHSH-Bell experiment demonstration."""
    print("=" * 72)
    print("CHSH-BELL INEQUALITY TEST")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
The CHSH-Bell Inequality Test:

  The most famous test of quantum mechanics vs local realism.

  Setup:
  - Two particles in Bell state: (|00⟩ + |11⟩)/√2
  - Alice measures her particle (settings A0 or A1)
  - Bob measures his particle (settings B0 or B1)
  - They compare results

  The CHSH parameter:
    S = E(A0,B0) + E(A0,B1) + E(A1,B0) - E(A1,B1)

  Where E(a,b) = P(same) - P(different)

  Bounds:
  - Classical (local hidden variables): |S| ≤ 2
  - Quantum mechanics: |S| ≤ 2√2 ≈ 2.83

  Violation of |S| ≤ 2 proves quantum nonlocality!

Experiment:
  1. Create Bell state
  2. Measure all four setting combinations
  3. Calculate S value
  4. Check for classical violation
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
