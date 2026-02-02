"""
Elitzur-Vaidman Bomb Tester on IBM Quantum Hardware

The Elitzur-Vaidman bomb test (1993) demonstrates interaction-free measurement:
detecting an object without any particle interacting with it.

The scenario:
- You have bombs that may be "live" (explodes if a photon hits the sensor)
  or "duds" (sensor doesn't work)
- Goal: Identify live bombs WITHOUT detonating them
- Classical physics: Impossible! Must interact to detect.
- Quantum mechanics: Can detect ~25-50% of live bombs without explosion

Uses a Mach-Zehnder interferometer where quantum interference reveals
information about path blockage without the photon taking that path.
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_no_bomb_circuit() -> QuantumCircuit:
    """
    Mach-Zehnder interferometer with NO bomb (dud).

    Without blockage, interference causes photon to always exit
    one specific port (constructive interference).

    q[0]: photon path
    """
    qc = QuantumCircuit(1, 1, name="no_bomb")

    # First beam splitter
    qc.h(0)
    qc.barrier(label="BS1")

    # No interaction (empty path)
    qc.barrier(label="No bomb")

    # Second beam splitter
    qc.h(0)
    qc.barrier(label="BS2")

    # Measurement - should always be |0> (constructive interference)
    qc.measure(0, 0)

    return qc


def create_live_bomb_circuit() -> QuantumCircuit:
    """
    Mach-Zehnder interferometer with LIVE bomb.

    The bomb acts as a measurement device on one path.
    This destroys interference, allowing detection at the "dark" port.

    q[0]: photon path
    q[1]: bomb sensor (measures if photon takes that path)
    """
    qc = QuantumCircuit(2, 2, name="live_bomb")

    # First beam splitter - photon in superposition of paths
    qc.h(0)
    qc.barrier(label="BS1")

    # Bomb interaction: if photon is in path 1, bomb detects it
    # This is a controlled operation - bomb "measures" the path
    qc.cx(0, 1)
    qc.barrier(label="Bomb")

    # Second beam splitter
    qc.h(0)
    qc.barrier(label="BS2")

    # Measurement
    qc.measure([0, 1], [0, 1])

    return qc


def create_bomb_test_circuit() -> QuantumCircuit:
    """
    Full bomb testing circuit showing all outcomes.

    Outcomes for live bomb:
    - |00>: Photon exits normal port, bomb NOT triggered, no info
    - |01>: BOOM! Photon triggered the bomb (50% of live bombs)
    - |10>: Photon exits "dark" port, bomb NOT triggered = DETECTED!
    - |11>: Not possible in ideal case

    The |10> outcome is the "miracle": bomb detected without interaction!
    """
    qc = QuantumCircuit(2, 2, name="bomb_test")

    # Photon enters interferometer
    qc.h(0)
    qc.barrier()

    # Bomb sensor in one arm
    qc.cx(0, 1)
    qc.barrier()

    # Second beam splitter
    qc.h(0)
    qc.barrier()

    qc.measure([0, 1], [0, 1])
    return qc


def create_enhanced_bomb_test() -> QuantumCircuit:
    """
    Enhanced bomb test using quantum Zeno effect for higher efficiency.

    By using multiple weak measurements, efficiency can approach 100%.
    This simplified version uses 3 stages.
    """
    qc = QuantumCircuit(2, 2, name="enhanced_bomb")

    # Small rotation instead of full H
    theta = np.pi / 6  # 30 degrees

    for i in range(3):
        qc.ry(theta, 0)
        qc.cx(0, 1)  # Bomb check
        qc.barrier()

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


def run_experiment(shots: int = 4096) -> dict:
    """Run Elitzur-Vaidman bomb test on IBM Quantum hardware."""
    print("Connecting to IBM Quantum...")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=IBM_QUANTUM_TOKEN,
        instance=IBM_QUANTUM_INSTANCE
    )

    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=2)
    print(f"Backend: {backend.name}")
    print(f"Qubits: {backend.num_qubits}")

    circuits = [
        create_no_bomb_circuit(),
        create_live_bomb_circuit(),
        create_bomb_test_circuit(),
        create_enhanced_bomb_test(),
    ]
    labels = ["no_bomb", "live_bomb", "bomb_test", "enhanced"]

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
    """Analyze and display bomb test results."""
    print("=" * 72)
    print("ELITZUR-VAIDMAN BOMB TESTER - RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    print("\n" + "-" * 72)
    print("THE BOMB TESTING PROBLEM")
    print("-" * 72)
    print("""
    Challenge: Detect live bombs without detonating them

    Classical physics: IMPOSSIBLE
      - Must send a particle to interact with sensor
      - If live, it explodes; if dud, no information

    Quantum mechanics: POSSIBLE via interaction-free measurement
      - Use Mach-Zehnder interferometer
      - Bomb's presence destroys interference
      - Some photons reveal bomb WITHOUT taking that path!
    """)

    results = experiment["results"]

    # No bomb case
    print("-" * 72)
    print("CASE 1: NO BOMB (Dud)")
    print("-" * 72)

    no_bomb = results["no_bomb"]
    counts = no_bomb["counts"]
    total = no_bomb["total"]

    print("\n   Expected: Always |0> (constructive interference)")
    p_0 = counts.get("0", 0) / total * 100
    p_1 = counts.get("1", 0) / total * 100
    print(f"   |0>: {counts.get('0', 0):4d} ({p_0:.1f}%)")
    print(f"   |1>: {counts.get('1', 0):4d} ({p_1:.1f}%)")

    # Live bomb case
    print("\n" + "-" * 72)
    print("CASE 2: LIVE BOMB")
    print("-" * 72)

    live = results["live_bomb"]
    counts = live["counts"]
    total = live["total"]

    print("\n   Outcomes (photon_port, bomb_triggered):")
    print("   |00>: Normal exit, bomb OK     - No information")
    print("   |01>: BOOM! Bomb exploded      - Bomb was live (bad)")
    print("   |10>: Dark port, bomb OK       - DETECTED without explosion!")
    print("   |11>: Not expected")

    for outcome in ["00", "01", "10", "11"]:
        c = counts.get(outcome, 0)
        p = c / total * 100
        print(f"\n   |{outcome}>: {c:4d} ({p:5.1f}%)")

    # Calculate success rate
    detected = counts.get("10", 0)
    exploded = counts.get("01", 0)
    live_bombs = detected + exploded

    print("\n" + "-" * 72)
    print("BOMB DETECTION ANALYSIS")
    print("-" * 72)

    if live_bombs > 0:
        success_rate = detected / live_bombs * 100
        print(f"\n   Live bombs tested: {live_bombs}")
        print(f"   Detected safely: {detected} ({success_rate:.1f}%)")
        print(f"   Exploded: {exploded}")
        print(f"\n   Theory predicts: ~25% safe detection, ~50% explosion")
        print(f"   (Remaining 25% give no information)")

    # Enhanced test
    print("\n" + "-" * 72)
    print("ENHANCED BOMB TEST (Quantum Zeno)")
    print("-" * 72)

    enhanced = results["enhanced"]
    counts = enhanced["counts"]
    total = enhanced["total"]

    print("\n   Using multiple weak measurements:")
    for outcome in ["00", "01", "10", "11"]:
        c = counts.get(outcome, 0)
        p = c / total * 100
        print(f"   |{outcome}>: {c:4d} ({p:5.1f}%)")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
    The Elitzur-Vaidman bomb test demonstrates:

    1. INTERACTION-FREE MEASUREMENT
       - Information gained without physical interaction
       - The photon that detects the bomb never touches it!

    2. COUNTERFACTUAL DEFINITENESS VIOLATION
       - "What would have happened" affects what does happen
       - The bomb's ability to explode matters, even when it doesn't

    3. WHICH-PATH INFORMATION
       - Bomb acts as a "which-path" detector
       - This destroys interference, revealing the bomb

    4. PRACTICAL APPLICATIONS
       - Ultra-sensitive imaging (quantum imaging)
       - Detecting light-sensitive samples
       - Quantum cryptography protocols

    With quantum Zeno enhancement, efficiency can approach 100%!
    """)
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- No Bomb (Dud) ---")
    print(create_no_bomb_circuit().draw(output="text"))

    print("\n--- Live Bomb ---")
    print(create_live_bomb_circuit().draw(output="text"))

    print("\n--- Enhanced Test ---")
    print(create_enhanced_bomb_test().draw(output="text"))


def main():
    """Main entry point for Elitzur-Vaidman bomb test demonstration."""
    print("=" * 72)
    print("ELITZUR-VAIDMAN BOMB TESTER")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
The Elitzur-Vaidman Bomb Test (1993):

  Can you detect a bomb without setting it off?

  Classical answer: NO - must interact to detect
  Quantum answer: YES - via interaction-free measurement!

  The setup (Mach-Zehnder interferometer):
  1. Photon enters beam splitter -> superposition of paths
  2. One path may contain a bomb sensor
  3. Paths recombine at second beam splitter
  4. Interference determines output port

  Without bomb: Always exits port A (constructive interference)
  With bomb: Sometimes exits port B (interference destroyed)

  If photon exits port B and bomb didn't explode:
  -> Bomb detected WITHOUT interaction!

Experiment:
  1. No bomb case (interference test)
  2. Live bomb case (detection test)
  3. Enhanced test (quantum Zeno for higher efficiency)
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
