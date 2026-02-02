OPENQASM 2.0;
include "qelib1.inc";

// Wheeler's Delayed Choice Experiment
// The choice of measurement (wave vs particle) is made AFTER
// the photon has entered the interferometer
// q[0]: photon, q[1]: path marker, q[2]: delayed choice control

qreg q[3];
creg c[3];

// Photon enters interferometer (first beam splitter)
h q[0];
barrier q[0], q[1], q[2];

// Mark which-path information
cx q[0], q[1];
barrier q[0], q[1], q[2];

// DELAYED CHOICE: q[2] controls whether we "insert" second beam splitter
// |0> = particle measurement (no interference)
// |1> = wave measurement (interference)
// Put choice qubit in superposition to test both simultaneously
h q[2];
barrier q[0], q[1], q[2];

// Controlled second beam splitter (applied only if choice = wave)
ch q[2], q[0];
barrier q[0], q[1], q[2];

// Erase which-path if doing wave measurement
ccx q[2], q[0], q[1];
barrier q[0], q[1], q[2];

// Measure everything
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
