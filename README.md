# Quantum Paradoxes

A collection of quantum paradox demonstrations designed to run on IBM Quantum hardware. Each paradox folder contains:
- `main.py` - Run the experiment on real IBM Quantum hardware
- `.qasm` file - Upload directly to IBM Quantum Composer

## Paradoxes

| Paradox | Description | Qubits |
|---------|-------------|--------|
| [Schrödinger's Cat](schrodinger-cat/) | GHZ "cat state" - macroscopic superposition | 4 |
| [Wigner's Friend](wigner-friend/) | Observer-dependent reality | 3 |
| [Extended Wigner's Friend](extended-wigner-friend/) | Frauchiger-Renner paradox with nested observers | 4 |
| [Wigner's Friend's Friend](wigner-friend-friend/) | Three levels of nested observers | 4 |
| [Hardy's Paradox](hardys-paradox/) | Nonlocality without inequalities | 2 |
| [GHZ Paradox](ghz-paradox/) | "All vs nothing" quantum nonlocality | 3 |
| [CHSH-Bell](chsh-bell/) | Bell inequality violation test | 2 |
| [Quantum Eraser](quantum-eraser/) | Which-path erasure restores interference | 3 |
| [Delayed Choice](delayed-choice/) | Wheeler's delayed choice experiment | 3 |
| [Quantum Zeno Effect](quantum-zeno-effect/) | Frequent measurements freeze evolution | 1 |
| [Elitzur-Vaidman Bomb](elitzur-vaidman-bomb/) | Interaction-free measurement | 2 |
| [Quantum Pigeonhole](quantum-pigeonhole/) | 3 pigeons in 2 boxes, none sharing | 3 |

## Usage

### Run on IBM Quantum Hardware

```bash
# Install dependencies
uv sync

# Set up IBM Quantum credentials
cp .env.example .env
# Edit .env with your IBM Quantum API token

# Run any paradox
python schrodinger-cat/main.py
python chsh-bell/main.py
# etc.
```

### IBM Quantum Composer

1. Go to [IBM Quantum Composer](https://quantum.ibm.com/composer)
2. Create a new circuit
3. Import the `.qasm` file from any paradox folder
4. Run on simulator or real quantum hardware

## Requirements

- Python >= 3.13
- Qiskit >= 1.0.0
- IBM Quantum account (free tier available)

## Environment Variables

Create a `.env` file with:

```
IBM_QUANTUM_TOKEN=your_token_here
IBM_QUANTUM_INSTANCE=ibm-q/open/main
```

## License

MIT
