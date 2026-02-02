OPENQASM 2.0;
include "qelib1.inc";

// Hardy's Paradox: Demonstrates quantum nonlocality without inequalities
// Two entangled qubits measured in specific bases reveal contradictions
// with local hidden variable theories

qreg q[2];
creg c[2];

// Prepare partially entangled state
ry(pi/4) q[0];
cx q[0], q[1];
barrier q[0], q[1];

// Apply measurement basis rotations (Hardy's specific angles)
ry(pi/8) q[0];
ry(pi/8) q[1];
barrier q[0], q[1];

// Measure both qubits
measure q[0] -> c[0];
measure q[1] -> c[1];
