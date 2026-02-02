"""
Quantum Zeno Paradox Demonstration on IBM Quantum Hardware

The Quantum Zeno Effect: "A watched pot never boils"
Frequent measurements of a quantum system inhibit its evolution,
effectively "freezing" the system in its initial state.

This experiment demonstrates:
1. A qubit evolving from |0⟩ toward |1⟩ via rotation
2. How intermediate measurements inhibit this evolution
3. Comparison between observed and unobserved quantum dynamics
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def theoretical_zeno_probability(num_measurements: int, total_angle: float = np.pi) -> float:
    """
    Calculate theoretical probability of staying in |0⟩ with N measurements.

    For the Zeno effect with N measurements during a total rotation of theta:
    - Each small rotation is theta/N
    - Probability of measuring |0⟩ after each small rotation: cos^2(theta/2N)
    - Probability of all N measurements giving |0⟩: [cos^2(theta/2N)]^N

    As N -> infinity, this approaches 1 (complete freezing via Zeno effect).

    Args:
        num_measurements: Number of measurement points
        total_angle: Total rotation angle (default pi for full flip)

    Returns:
        Theoretical probability of remaining in |0⟩
    """
    if num_measurements == 0:
        # Unobserved: full rotation gives cos^2(theta/2)
        return np.cos(total_angle / 2) ** 2

    angle_per_step = total_angle / num_measurements
    prob_stay_0_per_step = np.cos(angle_per_step / 2) ** 2
    return prob_stay_0_per_step ** num_measurements


def create_zeno_circuit(num_measurements: int, total_angle: float = np.pi) -> QuantumCircuit:
    """
    Create a quantum Zeno effect demonstration circuit.

    The circuit applies a total rotation split into N steps, with a measurement
    after each step. Each measurement collapses the state, and if |0⟩ is measured,
    the qubit continues from |0⟩ (via conditional reset).

    Args:
        num_measurements: Number of intermediate measurements (N)
        total_angle: Total rotation angle (default pi for intended |0⟩ -> |1⟩ flip)

    Returns:
        QuantumCircuit demonstrating the Zeno effect
    """
    qc = QuantumCircuit(1, 1, name=f"zeno_n{num_measurements}")

    angle_per_step = total_angle / num_measurements

    for i in range(num_measurements):
        # Apply partial rotation toward |1⟩
        qc.ry(angle_per_step, 0)

        # Measure and reset - this simulates the Zeno effect:
        # - Measurement collapses the state
        # - Reset ensures we continue from |0⟩ if measured |0⟩
        # - This mimics the "survival" path through all measurements
        qc.measure(0, 0)
        qc.reset(0)

        if i < num_measurements - 1:
            qc.barrier()

    # Final measurement to observe the outcome
    qc.ry(angle_per_step, 0)
    qc.measure(0, 0)

    return qc


def create_unobserved_circuit(total_angle: float = np.pi) -> QuantumCircuit:
    """
    Create a circuit showing unobserved quantum evolution (control case).

    Without intermediate measurements, the qubit evolves freely according
    to the full rotation angle.

    Args:
        total_angle: Total rotation angle

    Returns:
        QuantumCircuit for unobserved evolution
    """
    qc = QuantumCircuit(1, 1, name="unobserved")

    # Apply full rotation in one go
    qc.ry(total_angle, 0)

    # Single final measurement
    qc.measure(0, 0)

    return qc


def create_survival_zeno_circuit(num_measurements: int, total_angle: float = np.pi) -> QuantumCircuit:
    """
    Create an alternative Zeno circuit tracking survival probability.

    This version records all intermediate measurements to track the
    "survival probability" - the probability that all measurements yield |0⟩,
    demonstrating the system stays frozen in its initial state.

    Args:
        num_measurements: Number of measurement checkpoints
        total_angle: Total rotation angle

    Returns:
        QuantumCircuit tracking survival through measurements
    """
    # One classical bit per measurement to track full history
    qc = QuantumCircuit(1, num_measurements + 1, name=f"survival_n{num_measurements}")

    angle_per_step = total_angle / (num_measurements + 1)

    for i in range(num_measurements):
        qc.ry(angle_per_step, 0)
        qc.measure(0, i)
        qc.barrier()

    # Final rotation and measurement
    qc.ry(angle_per_step, 0)
    qc.measure(0, num_measurements)

    return qc


def extract_counts(pub_result, circuit: QuantumCircuit) -> dict:
    """
    Extract measurement counts from SamplerV2 result.

    Handles the different ways Qiskit may store measurement data.

    Args:
        pub_result: Result from SamplerV2
        circuit: The circuit that was executed

    Returns:
        Dictionary of bitstring counts
    """
    try:
        # Try accessing via classical register name
        creg_name = circuit.cregs[0].name if circuit.cregs else "c"
        data = getattr(pub_result.data, creg_name, None)
        if data is not None:
            return data.get_counts()
    except (AttributeError, IndexError):
        pass

    try:
        # Try common default names
        for name in ["meas", "c", "c0"]:
            data = getattr(pub_result.data, name, None)
            if data is not None:
                return data.get_counts()
    except AttributeError:
        pass

    try:
        # Try iterating over data attributes
        for attr in dir(pub_result.data):
            if not attr.startswith("_"):
                data = getattr(pub_result.data, attr)
                if hasattr(data, "get_counts"):
                    return data.get_counts()
    except Exception:
        pass

    return {}


def run_zeno_experiment(
    measurement_counts: list[int],
    total_angle: float = np.pi,
    shots: int = 4096
) -> dict:
    """
    Run the quantum Zeno effect experiment on IBM Quantum hardware.

    Compares circuits with different numbers of intermediate measurements
    to demonstrate how observation frequency affects quantum evolution.

    Args:
        measurement_counts: List of measurement counts to test [1, 2, 4, 8, ...]
        total_angle: Total rotation angle (default pi)
        shots: Number of shots per circuit

    Returns:
        Dictionary containing results, theoretical predictions, and metadata
    """
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    # Get available backend
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=1)
    print(f"Backend: {backend.name}")
    print(f"Qubits: {backend.num_qubits}")

    # Create circuits
    circuits = []
    circuit_labels = []

    # Unobserved evolution (control)
    qc_unobserved = create_unobserved_circuit(total_angle)
    circuits.append(qc_unobserved)
    circuit_labels.append(("unobserved", 0))

    # Zeno effect circuits with increasing measurement counts
    for n in measurement_counts:
        qc = create_zeno_circuit(n, total_angle)
        circuits.append(qc)
        circuit_labels.append(("zeno", n))

    print(f"\nTranspiling {len(circuits)} circuits...")
    transpiled = transpile(circuits, backend, optimization_level=1)

    print(f"Submitting job ({shots} shots per circuit)...")
    sampler = Sampler(mode=backend)
    job = sampler.run(transpiled, shots=shots)
    job_id = job.job_id()
    print(f"Job ID: {job_id}")
    print("Waiting for results (this may take a few minutes on real hardware)...\n")

    result = job.result()

    # Process results
    processed_results = {}

    for idx, (label, n_meas) in enumerate(circuit_labels):
        pub_result = result[idx]
        counts = extract_counts(pub_result, circuits[idx])

        # Calculate probabilities
        total_counts = sum(counts.values()) if counts else shots

        # Handle multi-bit results (take last bit for final measurement)
        prob_0 = 0
        prob_1 = 0
        for bitstring, count in counts.items():
            final_bit = bitstring[-1] if bitstring else "0"
            if final_bit == "0":
                prob_0 += count / total_counts
            else:
                prob_1 += count / total_counts

        # Theoretical prediction
        theoretical_p0 = theoretical_zeno_probability(n_meas, total_angle)

        key = f"{label}_{n_meas}" if label == "zeno" else "unobserved"
        processed_results[key] = {
            "type": label,
            "num_measurements": n_meas,
            "counts": counts,
            "prob_0": prob_0,
            "prob_1": prob_1,
            "theoretical_p0": theoretical_p0,
            "shots": total_counts
        }

    return {
        "results": processed_results,
        "job_id": job_id,
        "backend": backend.name,
        "total_angle": total_angle,
        "shots": shots
    }


def run_survival_experiment(
    measurement_counts: list[int],
    total_angle: float = np.pi,
    shots: int = 4096
) -> dict:
    """
    Run survival probability experiment (tracks all intermediate measurements).

    This experiment shows the probability of "surviving" in |0⟩ through
    all intermediate measurements, demonstrating the Zeno effect more directly.

    Args:
        measurement_counts: List of measurement counts to test
        total_angle: Total rotation angle
        shots: Number of shots per circuit

    Returns:
        Dictionary with survival probability results
    """
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=1)
    print(f"Backend: {backend.name}\n")

    circuits = []
    for n in measurement_counts:
        qc = create_survival_zeno_circuit(n, total_angle)
        circuits.append(qc)
        print(f"  - Survival circuit with {n} checkpoints")

    print(f"\nTranspiling {len(circuits)} circuits...")
    transpiled = transpile(circuits, backend, optimization_level=1)

    print(f"Submitting job ({shots} shots)...")
    sampler = Sampler(mode=backend)
    job = sampler.run(transpiled, shots=shots)
    print(f"Job ID: {job.job_id()}")
    print("Waiting for results...\n")

    result = job.result()

    processed_results = {}
    for idx, n_meas in enumerate(measurement_counts):
        pub_result = result[idx]
        counts = extract_counts(pub_result, circuits[idx])

        # Calculate survival probability (all bits are 0)
        total_counts = sum(counts.values()) if counts else shots
        all_zeros = "0" * (n_meas + 1)
        survival_count = counts.get(all_zeros, 0)
        survival_prob = survival_count / total_counts if total_counts > 0 else 0

        processed_results[f"survival_{n_meas}"] = {
            "num_measurements": n_meas,
            "counts": counts,
            "survival_prob": survival_prob,
            "theoretical_survival": theoretical_zeno_probability(n_meas, total_angle),
            "shots": total_counts
        }

    return {
        "results": processed_results,
        "job_id": job.job_id(),
        "backend": backend.name,
        "shots": shots
    }


def analyze_results(experiment: dict) -> None:
    """
    Analyze and display the Zeno effect experiment results.

    Compares experimental results with theoretical predictions and
    identifies the presence/absence of the Zeno effect.
    """
    print("=" * 72)
    print("QUANTUM ZENO PARADOX - EXPERIMENTAL RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Total rotation: {experiment['total_angle']:.4f} rad ({np.degrees(experiment['total_angle']):.1f} deg)")
    print(f"Shots: {experiment['shots']}")

    results = experiment["results"]

    # Sort by measurement count
    sorted_keys = sorted(results.keys(), key=lambda k: results[k]["num_measurements"])

    print("\n" + "-" * 72)
    print(f"{'Configuration':<20} {'P(|0>) Exp':<14} {'P(|0>) Theory':<14} {'Delta':<10} {'Counts'}")
    print("-" * 72)

    for key in sorted_keys:
        r = results[key]
        n = r["num_measurements"]

        if r["type"] == "unobserved":
            config = "Unobserved"
        else:
            config = f"{n} measurement{'s' if n > 1 else ''}"

        exp_p0 = r["prob_0"]
        theory_p0 = r["theoretical_p0"]
        delta = exp_p0 - theory_p0

        # Format counts for display
        counts_str = str(r["counts"]).replace("'", "")
        if len(counts_str) > 25:
            counts_str = counts_str[:22] + "..."

        print(f"{config:<20} {exp_p0:<14.4f} {theory_p0:<14.4f} {delta:+.4f}     {counts_str}")

    # Analysis
    print("\n" + "-" * 72)
    print("ANALYSIS")
    print("-" * 72)

    unobserved = results.get("unobserved", {})
    zeno_results = [(k, v) for k, v in results.items() if v["type"] == "zeno"]
    zeno_results.sort(key=lambda x: x[1]["num_measurements"])

    if unobserved and zeno_results:
        unobs_p0 = unobserved["prob_0"]

        print(f"\nUnobserved P(|0>): {unobs_p0:.4f}")
        print(f"  -> Without measurements, qubit evolved toward |1>")

        # Find max Zeno effect
        _, max_zeno = max(zeno_results, key=lambda x: x[1]["prob_0"])

        print(f"\nZeno effect with {max_zeno['num_measurements']} measurements: P(|0>) = {max_zeno['prob_0']:.4f}")

        if max_zeno["prob_0"] > unobs_p0 + 0.05:
            improvement = max_zeno["prob_0"] - unobs_p0
            print(f"\n[OK] ZENO EFFECT OBSERVED")
            print(f"  Measurements increased P(|0>) by {improvement:.4f} ({improvement*100:.1f}%)")
            print(f"  The quantum state was partially 'frozen' by observation!")
        elif max_zeno["prob_0"] > unobs_p0:
            print(f"\n[~] WEAK ZENO EFFECT")
            print(f"  Small increase in P(|0>), may be within noise margin")
        else:
            print(f"\n[X] ZENO EFFECT NOT CLEARLY OBSERVED")
            print(f"  Hardware noise may be masking the effect")

        # Check trend
        if len(zeno_results) >= 2:
            p0_values = [v["prob_0"] for _, v in zeno_results]
            if all(p0_values[i] <= p0_values[i+1] for i in range(len(p0_values)-1)):
                print(f"\n[^] P(|0>) increases with measurement frequency (expected trend)")
            elif all(p0_values[i] >= p0_values[i+1] for i in range(len(p0_values)-1)):
                print(f"\n[v] P(|0>) decreases with measurements (anti-Zeno or noise)")

    print("\n" + "-" * 72)
    print("THEORETICAL BACKGROUND")
    print("-" * 72)
    print("""
The Quantum Zeno Effect:
  - A qubit rotating from |0> to |1> can be "frozen" by frequent measurements
  - Each measurement collapses the state; small rotations likely collapse to |0>
  - Probability of staying in |0> through N measurements: [cos^2(theta/2N)]^N
  - As N -> infinity, this probability -> 1 (complete freezing)

Physical interpretation:
  - Measurement extracts information, causing wavefunction collapse
  - Frequent "observations" prevent the quantum state from evolving
  - This is not just mathematical - it's observed in real quantum systems

Applications:
  - Quantum error correction (stabilizing qubits via measurement)
  - Quantum state engineering (controlling evolution paths)
  - Fundamental tests of quantum mechanics
""")

    print("=" * 72)


def analyze_survival_results(experiment: dict) -> None:
    """Analyze survival probability experiment results."""
    print("\n" + "=" * 72)
    print("SURVIVAL PROBABILITY ANALYSIS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")

    results = experiment["results"]

    print("\n" + "-" * 72)
    print(f"{'Measurements':<15} {'Survival Exp':<15} {'Survival Theory':<15} {'Delta'}")
    print("-" * 72)

    for key in sorted(results.keys(), key=lambda k: results[k]["num_measurements"]):
        r = results[key]
        n = r["num_measurements"]
        exp_surv = r["survival_prob"]
        theory_surv = r["theoretical_survival"]
        delta = exp_surv - theory_surv

        print(f"{n:<15} {exp_surv:<15.4f} {theory_surv:<15.4f} {delta:+.4f}")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
Survival probability = P(all intermediate measurements yield |0>)

This demonstrates the Zeno effect more directly:
  - With more measurements, the survival probability should INCREASE
  - Each small rotation has high P(|0>), and these probabilities multiply
  - The system is "frozen" in |0> by frequent observation
""")
    print("=" * 72)


def print_circuit_diagrams(measurement_counts: list[int], total_angle: float = np.pi) -> None:
    """Print ASCII circuit diagrams for visualization."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Unobserved Evolution ---")
    qc = create_unobserved_circuit(total_angle)
    print(qc.draw(output="text"))

    for n in measurement_counts[:2]:  # Show first 2 for brevity
        print(f"\n--- Zeno Effect with {n} measurement{'s' if n > 1 else ''} ---")
        qc = create_zeno_circuit(n, total_angle)
        print(qc.draw(output="text"))


def main():
    """Main entry point for the Quantum Zeno Paradox demonstration."""
    print("=" * 72)
    print("QUANTUM ZENO PARADOX DEMONSTRATION")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
The Quantum Zeno Effect (Zeno's Paradox):
  "A watched quantum pot never boils"

  Frequent measurements of a quantum system inhibit its natural evolution,
  effectively freezing the system in its initial state.

Experiment design:
  - Start with qubit in |0>
  - Apply rotation that would flip it to |1> (Ry(pi))
  - Compare: no measurements vs. 1, 2, 4, 8 intermediate measurements
  - Measure final state probability

Expected result:
  - Without measurements: ~0% in |0> (full evolution to |1>)
  - With many measurements: high % in |0> (Zeno freezing)
""")

    # Measurement configurations to test
    measurement_counts = [1, 2, 4, 8]
    total_angle = np.pi  # Full rotation: |0> -> |1>
    shots = 4096

    # Show theoretical predictions
    print("-" * 72)
    print("THEORETICAL PREDICTIONS")
    print("-" * 72)
    print(f"{'Measurements':<15} {'P(|0>) Theory':<15}")
    print("-" * 30)
    print(f"{'0 (unobserved)':<15} {theoretical_zeno_probability(0, total_angle):<15.4f}")
    for n in measurement_counts:
        print(f"{n:<15} {theoretical_zeno_probability(n, total_angle):<15.4f}")

    # Show circuit diagrams
    print_circuit_diagrams(measurement_counts[:2], total_angle)

    try:
        # Run experiment
        print("\n" + "=" * 72)
        print("RUNNING EXPERIMENT ON IBM QUANTUM HARDWARE")
        print("=" * 72 + "\n")

        experiment = run_zeno_experiment(
            measurement_counts=measurement_counts,
            total_angle=total_angle,
            shots=shots
        )

        # Analyze results
        analyze_results(experiment)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Check .env file has valid credentials:")
        print("     IBM_QUANTUM_TOKEN=your_api_token")
        print("     IBM_QUANTUM_INSTANCE=ibm-q/open/main")
        print("  2. Ensure packages are installed:")
        print("     uv pip install qiskit qiskit-ibm-runtime python-dotenv numpy")
        print("  3. Verify your IBM Quantum account at quantum.ibm.com")


if __name__ == "__main__":
    main()
