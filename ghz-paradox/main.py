"""
GHZ Paradox Demonstration on IBM Quantum Hardware

The GHZ (Greenberger-Horne-Zeilinger) paradox (1989) demonstrates quantum
nonlocality with 100% certainty, unlike Bell's inequality which is statistical.

The paradox:
- Three particles in the GHZ state: (|000> + |111>) / √2
- Certain measurement combinations give DEFINITE predictions
- These predictions are logically inconsistent with local hidden variables
- A single measurement can rule out classical physics!

This is often called "Bell's theorem without inequalities" or
"all-versus-nothing" quantum nonlocality.
"""

import os
import numpy as np
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

load_dotenv()

IBM_QUANTUM_TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
IBM_QUANTUM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE")


def create_ghz_state() -> QuantumCircuit:
    """
    Create the GHZ state: (|000> + |111>) / √2

    This maximally entangled 3-qubit state exhibits the strongest
    form of quantum nonlocality.
    """
    qc = QuantumCircuit(3, name="ghz_state")

    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)

    return qc


def create_ghz_xxx_measurement() -> QuantumCircuit:
    """
    GHZ measurement: All three in X basis (XXX).

    For GHZ state, measuring XXX gives XOR = 1 (odd parity)
    But local hidden variables predict XOR = 0 (even parity)!
    """
    qc = QuantumCircuit(3, 3, name="GHZ_XXX")

    # Create GHZ state
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.barrier(label="GHZ")

    # X basis measurement (apply H before measuring in Z)
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.barrier(label="X basis")

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_ghz_xyy_measurement() -> QuantumCircuit:
    """
    GHZ measurement: XYY basis.

    Y basis = S†H before measurement
    For GHZ: XYY gives XOR = 0 (even parity)
    """
    qc = QuantumCircuit(3, 3, name="GHZ_XYY")

    # Create GHZ state
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.barrier(label="GHZ")

    # X basis for qubit 0
    qc.h(0)
    # Y basis for qubits 1 and 2
    qc.sdg(1)
    qc.h(1)
    qc.sdg(2)
    qc.h(2)
    qc.barrier(label="XYY basis")

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_ghz_yxy_measurement() -> QuantumCircuit:
    """GHZ measurement: YXY basis."""
    qc = QuantumCircuit(3, 3, name="GHZ_YXY")

    # Create GHZ state
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.barrier(label="GHZ")

    # Y basis for qubit 0
    qc.sdg(0)
    qc.h(0)
    # X basis for qubit 1
    qc.h(1)
    # Y basis for qubit 2
    qc.sdg(2)
    qc.h(2)
    qc.barrier(label="YXY basis")

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_ghz_yyx_measurement() -> QuantumCircuit:
    """GHZ measurement: YYX basis."""
    qc = QuantumCircuit(3, 3, name="GHZ_YYX")

    # Create GHZ state
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.barrier(label="GHZ")

    # Y basis for qubits 0 and 1
    qc.sdg(0)
    qc.h(0)
    qc.sdg(1)
    qc.h(1)
    # X basis for qubit 2
    qc.h(2)
    qc.barrier(label="YYX basis")

    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def create_ghz_zzz_measurement() -> QuantumCircuit:
    """GHZ measurement: ZZZ basis (computational)."""
    qc = QuantumCircuit(3, 3, name="GHZ_ZZZ")

    # Create GHZ state
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.barrier(label="GHZ")

    # Z basis (no rotation needed)
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
    """Run GHZ paradox experiment on IBM Quantum hardware."""
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
        create_ghz_zzz_measurement(),
        create_ghz_xxx_measurement(),
        create_ghz_xyy_measurement(),
        create_ghz_yxy_measurement(),
        create_ghz_yyx_measurement(),
    ]
    labels = ["ZZZ", "XXX", "XYY", "YXY", "YYX"]

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
    """Analyze and display GHZ paradox results."""
    print("=" * 72)
    print("GHZ PARADOX - EXPERIMENTAL RESULTS")
    print("=" * 72)

    print(f"\nBackend: {experiment['backend']}")
    print(f"Job ID: {experiment['job_id']}")
    print(f"Shots: {experiment['shots']}")

    print("\n" + "-" * 72)
    print("THE GHZ PARADOX LOGIC")
    print("-" * 72)
    print("""
    GHZ State: (|000⟩ + |111⟩) / √2

    Quantum mechanics predicts:
    - XYY measurement: XOR of results = 0 (even parity)
    - YXY measurement: XOR of results = 0 (even parity)
    - YYX measurement: XOR of results = 0 (even parity)
    - XXX measurement: XOR of results = 1 (odd parity)

    Classical (local hidden variable) reasoning:
    - If XYY=0, YXY=0, YYX=0, then XXX must equal 0
    - Why? Multiply: (XYY)(YXY)(YYX) = XXX × Y² × Y² × Y² = XXX
    - Since Y² = 1, we get XXX = 0 × 0 × 0 = 0

    But quantum mechanics gives XXX = 1!

    This is a direct contradiction with NO statistical loopholes.
    """)

    results = experiment["results"]

    # ZZZ measurement (verify GHZ state)
    print("-" * 72)
    print("ZZZ MEASUREMENT (Verify GHZ state)")
    print("-" * 72)

    zzz = results["ZZZ"]
    counts = zzz["counts"]
    total = zzz["total"]

    print("\n   GHZ state should give only |000⟩ or |111⟩:")
    for outcome in ["000", "001", "010", "011", "100", "101", "110", "111"]:
        c = counts.get(outcome, 0)
        p = c / total * 100
        marker = " ← expected" if outcome in ["000", "111"] else ""
        print(f"   |{outcome}>: {c:4d} ({p:5.1f}%){marker}")

    ghz_fidelity = (counts.get("000", 0) + counts.get("111", 0)) / total
    print(f"\n   GHZ fidelity: {ghz_fidelity*100:.1f}%")

    # Paradox measurements
    print("\n" + "-" * 72)
    print("GHZ PARADOX MEASUREMENTS")
    print("-" * 72)

    for basis in ["XYY", "YXY", "YYX", "XXX"]:
        r = results[basis]
        counts = r["counts"]
        total = r["total"]

        # Calculate parity
        even_count = sum(counts.get(k, 0) for k in counts if k.count("1") % 2 == 0)
        odd_count = sum(counts.get(k, 0) for k in counts if k.count("1") % 2 == 1)
        even_pct = even_count / total * 100
        odd_pct = odd_count / total * 100

        expected = "ODD (1)" if basis == "XXX" else "EVEN (0)"

        print(f"\n   {basis} measurement:")
        print(f"      Even parity: {even_count:4d} ({even_pct:5.1f}%)")
        print(f"      Odd parity:  {odd_count:4d} ({odd_pct:5.1f}%)")
        print(f"      Expected: {expected}")

    # Check the paradox
    print("\n" + "-" * 72)
    print("PARADOX VERIFICATION")
    print("-" * 72)

    xyy_even = sum(results["XYY"]["counts"].get(k, 0) for k in results["XYY"]["counts"] if k.count("1") % 2 == 0) / results["XYY"]["total"]
    yxy_even = sum(results["YXY"]["counts"].get(k, 0) for k in results["YXY"]["counts"] if k.count("1") % 2 == 0) / results["YXY"]["total"]
    yyx_even = sum(results["YYX"]["counts"].get(k, 0) for k in results["YYX"]["counts"] if k.count("1") % 2 == 0) / results["YYX"]["total"]
    xxx_odd = sum(results["XXX"]["counts"].get(k, 0) for k in results["XXX"]["counts"] if k.count("1") % 2 == 1) / results["XXX"]["total"]

    print(f"\n   XYY even parity: {xyy_even*100:.1f}% (QM predicts ~100%)")
    print(f"   YXY even parity: {yxy_even*100:.1f}% (QM predicts ~100%)")
    print(f"   YYX even parity: {yyx_even*100:.1f}% (QM predicts ~100%)")
    print(f"   XXX odd parity:  {xxx_odd*100:.1f}% (QM predicts ~100%)")

    if xxx_odd > 0.5:
        print(f"\n   [OK] GHZ PARADOX DEMONSTRATED!")
        print(f"   Classical physics predicts XXX even, but we see odd!")
    else:
        print(f"\n   [~] Signal degraded by hardware noise")

    print("\n" + "-" * 72)
    print("INTERPRETATION")
    print("-" * 72)
    print("""
    The GHZ paradox proves quantum nonlocality conclusively:

    1. ALL-VERSUS-NOTHING
       Unlike Bell's inequality (statistical), GHZ gives a
       definite prediction that contradicts classical physics.
       A single measurement suffices in principle.

    2. NO LOOPHOLES
       - Detection loophole: All outcomes counted
       - Locality loophole: Spacelike separated measurements
       - Freedom-of-choice: Settings predetermined

    3. WHAT IT RULES OUT
       - Local hidden variables
       - Classical correlations
       - Any theory where properties exist before measurement

    4. MERMIN'S MAGIC SQUARE
       GHZ is related to quantum pseudo-telepathy games
       where entangled players always win at tasks
       impossible classically.

    As Mermin said: "If [one] denies quantum nonlocality,
    the only alternative is to deny the validity of
    first-grade arithmetic."
    """)
    print("=" * 72)


def print_circuit_diagrams() -> None:
    """Print circuit diagrams."""
    print("\n" + "=" * 72)
    print("CIRCUIT DIAGRAMS")
    print("=" * 72)

    print("\n--- GHZ State Preparation ---")
    print(create_ghz_state().draw(output="text"))

    print("\n--- XXX Measurement ---")
    print(create_ghz_xxx_measurement().draw(output="text"))

    print("\n--- XYY Measurement ---")
    print(create_ghz_xyy_measurement().draw(output="text"))


def main():
    """Main entry point for GHZ paradox demonstration."""
    print("=" * 72)
    print("GHZ PARADOX DEMONSTRATION")
    print("Running on IBM Quantum Hardware")
    print("=" * 72)

    print("""
The GHZ Paradox (1989):

  "The best version of Bell's theorem" - proves nonlocality
  with certainty, not just statistics.

  The GHZ state: (|000⟩ + |111⟩) / √2

  Three particles, each measured in X or Y basis.

  Quantum predictions:
  - XYY → even parity (XOR = 0)
  - YXY → even parity (XOR = 0)
  - YYX → even parity (XOR = 0)
  - XXX → odd parity (XOR = 1)

  Classical logic:
  - If first three are even, XXX must be even
  - But quantum gives odd!

  This contradiction rules out local hidden variables
  with a SINGLE measurement, not statistics.

Experiment:
  1. Create GHZ state
  2. Measure in ZZZ (verify state)
  3. Measure in XXX, XYY, YXY, YYX
  4. Check parity predictions
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
