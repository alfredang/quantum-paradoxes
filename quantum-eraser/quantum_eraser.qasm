OPENQASM 2.0;
include "qelib1.inc";

// Quantum Eraser: Shows how "which-path" information affects interference
// Erasing path information restores interference pattern
// q[0]: signal photon, q[1]: idler (which-path marker), q[2]: eraser control

qreg q[3];
creg c[3];

// Create superposition (double-slit)
h q[0];
barrier q[0], q[1], q[2];

// Entangle with idler to mark which-path info
cx q[0], q[1];
barrier q[0], q[1], q[2];

// Eraser: Apply Hadamard to idler to erase which-path info
h q[1];
barrier q[0], q[1], q[2];

// Interference operation on signal
h q[0];
barrier q[0], q[1], q[2];

// Measure all qubits
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
