OPENQASM 2.0;
include "qelib1.inc";

// Quantum Zeno Effect: Frequent measurements freeze quantum evolution
// Small rotations with intermediate measurements demonstrate the effect
// Compare: without measurements, full rotation would flip the qubit

qreg q[1];
creg c[5];

// Series of small rotations with measurements
// Each rotation is pi/10, total would be pi/2 without Zeno effect

ry(pi/10) q[0];
barrier q[0];
measure q[0] -> c[0];

ry(pi/10) q[0];
barrier q[0];
measure q[0] -> c[1];

ry(pi/10) q[0];
barrier q[0];
measure q[0] -> c[2];

ry(pi/10) q[0];
barrier q[0];
measure q[0] -> c[3];

ry(pi/10) q[0];
barrier q[0];
measure q[0] -> c[4];

// With Zeno effect, qubit likely stays in |0> despite total rotation of pi/2
