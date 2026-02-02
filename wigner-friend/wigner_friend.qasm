OPENQASM 2.0;
include "qelib1.inc";

// Wigner's Friend: Explores observer-dependent reality
// q[0]: quantum system, q[1]: friend's memory, q[2]: Wigner's observation
// Demonstrates nested measurement and superposition of outcomes

qreg q[3];
creg c[3];

// Prepare quantum system in superposition
h q[0];
barrier q[0], q[1], q[2];

// Friend measures the system (entangles friend's memory with system)
cx q[0], q[1];
barrier q[0], q[1], q[2];

// From Wigner's perspective, friend+system is in superposition
// Wigner applies interference test on the combined system
h q[0];
barrier q[0], q[1], q[2];

// Wigner's measurement
cx q[0], q[2];
h q[2];
barrier q[0], q[1], q[2];

// Final measurements reveal the paradox
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
