OPENQASM 2.0;
include "qelib1.inc";

// Schrodinger's Cat: Macroscopic superposition state
// Creates a GHZ-like "cat state" where multiple qubits are
// in superposition of all-0 and all-1 (alive and dead)

qreg q[4];
creg c[4];

// Create cat state: (|0000> + |1111>) / sqrt(2)
// q[0] is the "radioactive atom", others represent the "cat"

// Put atom in superposition
h q[0];
barrier q[0], q[1], q[2], q[3];

// Entangle atom with cat (cascade of CNOTs)
cx q[0], q[1];
cx q[1], q[2];
cx q[2], q[3];
barrier q[0], q[1], q[2], q[3];

// Opening the box: measure all qubits
// Should see only |0000> or |1111>, never mixed states
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];
