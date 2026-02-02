OPENQASM 2.0;
include "qelib1.inc";

// Elitzur-Vaidman Bomb Tester: Interaction-Free Measurement
// Detect a bomb without detonating it using quantum interference
// q[0]: photon path, q[1]: bomb detector (simulated)
// Uses Mach-Zehnder interferometer concept

qreg q[2];
creg c[2];

// First beam splitter - photon enters superposition of paths
h q[0];
barrier q[0], q[1];

// Bomb interaction: if bomb is live (q[1]=|1>), it would absorb photon on one path
// This is simulated by controlled operation - bomb "measures" the path
// For live bomb test, initialize q[1] to |1> before running
cx q[0], q[1];
barrier q[0], q[1];

// Second beam splitter
h q[0];
barrier q[0], q[1];

// Measurement
// Without bomb: always detect at one port (constructive interference)
// With live bomb: 25% chance detect at "dark" port = bomb detected without explosion
measure q[0] -> c[0];
measure q[1] -> c[1];
