OPENQASM 2.0;
include "qelib1.inc";

// GHZ Paradox (Greenberger-Horne-Zeilinger)
// Three-particle entanglement that shows quantum vs classical
// contradiction with a SINGLE measurement (no statistics needed)
// Demonstrates "all vs nothing" quantum nonlocality

qreg q[3];
creg c[3];

// Create GHZ state: (|000> + |111>) / sqrt(2)
h q[0];
cx q[0], q[1];
cx q[1], q[2];
barrier q[0], q[1], q[2];

// GHZ paradox measurement settings:
// Measure in X-basis (apply H before measurement)
// or Y-basis (apply S-dagger then H)

// For XXX measurement (product should be +1 classically, -1 quantum):
h q[0];
h q[1];
h q[2];
barrier q[0], q[1], q[2];

// For XYY, YXY, YYX measurements, replace some H with: sdg then h
// Example YXY: sdg q[0]; h q[0]; h q[1]; sdg q[2]; h q[2];

measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];

// XOR of results reveals the paradox
// Classical prediction contradicts quantum result
