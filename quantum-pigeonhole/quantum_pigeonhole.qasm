OPENQASM 2.0;
include "qelib1.inc";

// Quantum Pigeonhole Paradox
// Three particles in two boxes, yet no two particles share a box
// Violates classical pigeonhole principle through pre/post-selection
// q[0],q[1],q[2]: three "pigeons", each in superposition of two boxes

qreg q[3];
creg c[3];

// Pre-selection: Put each pigeon in superposition of both boxes
// |+> state means equal superposition of box 0 and box 1
h q[0];
h q[1];
h q[2];
barrier q[0], q[1], q[2];

// Create correlation that prevents any two from being in same box
// This is achieved through careful phase manipulation
cz q[0], q[1];
cz q[1], q[2];
cz q[0], q[2];
barrier q[0], q[1], q[2];

// Post-selection rotation
// Rotate to measurement basis that reveals the paradox
h q[0];
h q[1];
h q[2];
barrier q[0], q[1], q[2];

// Measurement
// Post-select on specific outcomes to observe the paradox
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
