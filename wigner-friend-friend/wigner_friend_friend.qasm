OPENQASM 2.0;
include "qelib1.inc";

// Wigner's Friend's Friend: Three levels of nested observers
// q[0]: quantum system
// q[1]: Friend's memory (first observer)
// q[2]: Wigner's memory (second observer, observes Friend)
// q[3]: Super-Wigner's memory (third observer, observes Wigner)
// Explores what happens when observers observe observers observing

qreg q[4];
creg c[4];

// Prepare quantum system in superposition
h q[0];
barrier q[0], q[1], q[2], q[3];

// Friend measures the system
cx q[0], q[1];
barrier q[0], q[1], q[2], q[3];

// Wigner measures Friend+System
cx q[0], q[2];
cx q[1], q[2];
barrier q[0], q[1], q[2], q[3];

// Super-Wigner applies interference to entire lab
h q[0];
h q[1];
h q[2];
barrier q[0], q[1], q[2], q[3];

// Super-Wigner's observation
cx q[2], q[3];
h q[3];
barrier q[0], q[1], q[2], q[3];

// Final measurements
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];
