OPENQASM 2.0;
include "qelib1.inc";

// Extended Wigner's Friend (Frauchiger-Renner Paradox)
// Two labs with friends (F1, F2) and two external observers (W1, W2)
// Leads to contradictory conclusions about measurement outcomes
// q[0]: system for F1, q[1]: F1's memory, q[2]: system for F2, q[3]: F2's memory

qreg q[4];
creg c[4];

// F1 prepares state based on coin toss (superposition)
h q[0];
barrier q[0], q[1], q[2], q[3];

// F1 measures and records in memory
cx q[0], q[1];
barrier q[0], q[1], q[2], q[3];

// F1's result determines state sent to F2
// If F1 sees |1>, prepare |+> for F2; if |0>, prepare |0>
cx q[1], q[2];
ch q[1], q[2];
barrier q[0], q[1], q[2], q[3];

// F2 measures in computational basis
cx q[2], q[3];
barrier q[0], q[1], q[2], q[3];

// W1 and W2 perform interference measurements on their respective labs
h q[0];
h q[1];
h q[2];
h q[3];
barrier q[0], q[1], q[2], q[3];

// Final measurements - reveals the paradox
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];
