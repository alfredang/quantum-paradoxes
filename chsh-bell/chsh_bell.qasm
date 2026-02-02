OPENQASM 2.0;
include "qelib1.inc";

// CHSH-Bell Inequality Test
// Demonstrates quantum nonlocality by violating classical bound
// Classical: |S| <= 2, Quantum: |S| <= 2*sqrt(2) ≈ 2.83
// q[0]: Alice's qubit, q[1]: Bob's qubit

qreg q[2];
creg c[2];

// Create maximally entangled Bell state |Φ+> = (|00> + |11>)/sqrt(2)
h q[0];
cx q[0], q[1];
barrier q[0], q[1];

// CHSH optimal measurement settings:
// Alice: A0 = Z, A1 = X (angles 0, π/2)
// Bob: B0 = (Z+X)/√2, B1 = (Z-X)/√2 (angles π/4, -π/4)

// This circuit tests A0,B0 setting:
// Alice measures in Z basis (no rotation needed)
// Bob measures at π/8 angle
ry(-pi/4) q[1];
barrier q[0], q[1];

// For other settings, use:
// A0,B1: ry(pi/4) q[1];
// A1,B0: h q[0]; ry(-pi/4) q[1];
// A1,B1: h q[0]; ry(pi/4) q[1];

measure q[0] -> c[0];
measure q[1] -> c[1];

// Run all 4 settings, compute S = <A0B0> + <A0B1> + <A1B0> - <A1B1>
// Quantum mechanics predicts S ≈ 2.83, violating classical bound of 2
