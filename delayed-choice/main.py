"""
Wheeler's Delayed Choice Experiment on IBM Quantum Hardware

Wheeler's delayed choice experiment (1978) demonstrates that the choice of
measurement apparatus can apparently influence the past behavior of a photon.

The puzzle:
- In a double-slit experiment, we can measure "which path" OR "interference"
- Wheeler proposed: What if we choose AFTER the photon has "decided"?
- The photon seems to "know" in advance what we'll choose!

This challenges our classical notions of causality and suggests that
quantum properties are not determined until measurement.
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_wave_measurement() -> QuantumCircuit:
    """
    Delayed choice: Wave measurement (interference).

    Insert second beam splitter -> observe interference pattern.
    Photon behaves as a wave, taking both paths.
    """
    qc = QuantumCircuit(2, 2, name="wave_choice")

    # Photon enters interferometer (first beam splitter)
    qc.h(0)
    qc.barrier(label="Enter")

    # Mark which-path information
    qc.cx(0, 1)
    qc.barrier(label="Paths")

    # CHOICE: Insert second beam splitter (wave measurement)
    qc.h(0)
    qc.barrier(label="BS2 inserted")

    # Erase which-path info to see interference
    qc.cx(0, 1)
    qc.barrier()

    qc.measure([0, 1], [0, 1])
    return qc


def create_particle_measurement() -> QuantumCircuit:
    """
    Delayed choice: Particle measurement (which-path).

    No second beam splitter -> observe which path taken.
    Photon behaves as a particle, taking one definite path.
    """
    qc = QuantumCircuit(2, 2, name="particle_choice")

    # Photon enters interferometer
    qc.h(0)
    qc.barrier(label="Enter")

    # Mark which-path information
    qc.cx(0, 1)
    qc.barrier(label="Paths")

    # CHOICE: No second beam splitter (particle measurement)
    qc.barrier(label="No BS2")

    qc.measure([0, 1], [0, 1])
    return qc


def create_quantum_delayed_choice() -> QuantumCircuit:
    """
    Quantum delayed choice: Choice itself in superposition!

    q[0]: photon
    q[1]: path marker
    q[2]: choice qubit (0=particle, 1=wave)

    The measurement choice is entangled with the photon,
    creating a superposition of "wave" and "particle" histories.
    """
    qc = QuantumCircuit(3, 3, name="quantum_choice")

    # Photon enters interferometer
    qc.h(0)
    qc.barrier()

    # Mark which-path
    qc.cx(0, 1)
    qc.barrier()

    # Put CHOICE in superposition
    qc.h(2)
    qc.barrier(label="Quantum choice")

    # Controlled beam splitter: only if choice=|1>
    qc.ch(2, 0)
    qc.barrier()

    # Controlled erasure
    qc.ccx(2, 0, 1)
    qc.barrier()

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_delayed_erasure() -> QuantumCircuit:
    """
    Delayed choice quantum eraser variant.

    The "erasure" of which-path information happens after detection,
    yet still affects the observed pattern.
    """
    qc = QuantumCircuit(3, 3, name="delayed_eraser")

    # Create entangled pair (signal and idler)
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier(label="Entangled")

    # Signal goes through double slit (superposition)
    qc.h(0)
    qc.barrier(label="Double slit")

    # Which-path marking
    qc.cx(0, 2)
    qc.barrier()

    # Delayed choice: erase or keep which-path info on idler
    qc.h(1)  # Eraser on idler
    qc.barrier(label="Delayed erasure")

    qc.measure([0, 1, 2], [0, 1, 2])
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
    """Run delayed choice experiment on IBM Quantum hardware."""
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=3)
    print(f"Backend: {backend.name}")
    print(f"Qubits: {backend.num_qubits}")

    circuits = [
        create_wave_measurement(),
        create_particle_measurement(),
        create_quantum_delayed_choice(),
        create_delayed_erasure(),
    ]
    labels = ["wave", "particle", "quantum_choice", "delayed_eraser"]

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
    """Analyze and display delayed choice experiment results."""
    print("=" * 72)
    print("WHEELER'S DELAYED CHOICE EXPERIMENT - RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    print("\n" + "-" * 72)
    print("THE DELAYED CHOICE PUZZLE")
    print("-" * 72)
    print("""
    Wheeler's thought experiment:

    1. Photon enters interferometer through beam splitter
       -> Superposition of two paths

    2. Photon "travels" through the apparatus

    3. AFTER photon has "committed" to its path:
       - Insert second beam splitter -> See interference (wave)
       - Don't insert -> See which-path (particle)

    The paradox:
    - If photon is a particle, it took ONE path
    - If photon is a wave, it took BOTH paths
    - But we choose AFTER the photon "decided"!
    - How does the photon "know" our future choice?
    """)

    results = experiment["results"]

    # Wave measurement
    print("-" * 72)
    print("WAVE MEASUREMENT (Second beam splitter inserted)")
    print("-" * 72)

    wave = results["wave"]
    counts = wave["counts"]
    total = wave["total"]

    print("\n   With interference, expect concentrated output:")
    for outcome in sorted(counts.keys()):
        c = counts.get(outcome, 0)
        p = c / total * 100
        print(f"   |{outcome}>: {c:4d} ({p:5.1f}%)")

    # Particle measurement
    print("\n" + "-" * 72)
    print("PARTICLE MEASUREMENT (No second beam splitter)")
    print("-" * 72)

    particle = results["particle"]
    counts = particle["counts"]
    total = particle["total"]

    print("\n   Without interference, see which-path information:")
    for outcome in sorted(counts.keys()):
        c = counts.get(outcome, 0)
        p = c / total * 100
        print(f"   |{outcome}>: {c:4d} ({p:5.1f}%)")

    # Quantum delayed choice
    print("\n" + "-" * 72)
    print("QUANTUM DELAYED CHOICE (Choice in superposition)")
    print("-" * 72)

    quantum = results["quantum_choice"]
    counts = quantum["counts"]
    total = quantum["total"]

    print("\n   Choice qubit in superposition - both histories coexist:")
    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])
    for outcome, count in sorted_outcomes[:6]:
        p = count / total * 100
        choice_bit = outcome[-1] if len(outcome) >= 1 else "?"
        behavior = "wave" if choice_bit == "1" else "particle"
        print(f"   |{outcome}>: {count:4d} ({p:5.1f}%) - {behavior} behavior")

    # Delayed eraser
    print("\n" + "-" * 72)
    print("DELAYED CHOICE QUANTUM ERASER")
    print("-" * 72)

    eraser = results["delayed_eraser"]
    counts = eraser["counts"]
    total = eraser["total"]

    print("\n   Which-path erasure happens 'after' signal detection:")
    sorted_outcomes = sorted(counts.items(), key=lambda x: -x[1])
    for outcome, count in sorted_outcomes[:6]:
        p = count / total * 100
        print(f"   |{outcome}>: {count:4d} ({p:5.1f}%)")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
    Wheeler's Delayed Choice teaches us:

    1. NO RETROCAUSALITY
       - The photon doesn't "go back in time" to change its behavior
       - Rather, it never had definite particle/wave nature to begin with!

    2. COMPLEMENTARITY
       - Wave and particle are complementary descriptions
       - Neither is "real" until measurement forces a choice
       - "No phenomenon is a phenomenon until it is an observed phenomenon"

    3. QUANTUM DELAYED CHOICE
       - When choice itself is quantum, both histories coexist
       - Entanglement between photon and choice qubit
       - Measurement of choice collapses to wave OR particle history

    4. IMPLICATIONS
       - Properties don't exist before measurement
       - The past is not fixed until observed
       - Reality is participatory (Wheeler's "it from bit")

    As Wheeler said: "The past has no existence except as it is recorded
    in the present."
    """)
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- Wave Measurement ---")
    print(create_wave_measurement().draw(output="text"))

    print("\n--- Particle Measurement ---")
    print(create_particle_measurement().draw(output="text"))

    print("\n--- Quantum Delayed Choice ---")
    print(create_quantum_delayed_choice().draw(output="text"))


def main():
    """Main entry point for delayed choice experiment demonstration."""
    print("=" * 72)
    print("WHEELER'S DELAYED CHOICE EXPERIMENT")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
Wheeler's Delayed Choice (1978):

  "Does the photon decide to be a wave or particle
   BEFORE or AFTER we choose how to measure it?"

  The experiment:
  1. Photon enters Mach-Zehnder interferometer
  2. First beam splitter creates superposition of paths
  3. Photon "travels" through apparatus
  4. DELAYED CHOICE: Insert or remove second beam splitter
     - Insert -> Wave behavior (interference)
     - Remove -> Particle behavior (which-path)

  The twist:
  - Choice is made AFTER photon enters
  - Yet the pattern matches the choice!
  - Photon seems to "know" our future decision

Experiments:
  1. Wave measurement (interference)
  2. Particle measurement (which-path)
  3. Quantum delayed choice (choice in superposition)
  4. Delayed choice quantum eraser
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
