# PLC Instrument Simulator

Raspberry Pi-based industrial instrument simulator for PLC testing and training.

## Features

- **6 Instrument Types**: Level, Valve, Pump, Flow, REG Valve, Tank Truck
- **Flexible I/O**: Configurable GPIO/I2C pin allocation
- **Scalable**: Add/remove instruments as needed
- **Web Interface**: Browser-based configuration and monitoring
- **Inter-instrument Linking**: Simulators can share data (e.g., pump affects tank level)
- **Hardware Support**:
  - Digital I/O via GPIO
  - Analog output via MCP4725 DAC (4-20mA)
  - Analog input via ADS1115 ADC
  - Pulse generation for flow meters

## Architecture

```
simulator/
├── backend/           # Python FastAPI server
│   ├── main.py       # API server entry point
│   ├── simulators/   # Instrument simulation engines
│   ├── hardware/     # Raspberry Pi I/O drivers
│   └── config/       # Configuration management
├── frontend/         # React web interface
├── config/           # YAML configuration files
└── docs/             # Documentation
```

## Hardware Requirements

- Raspberry Pi 4 (or Pi 3B+)
- MCP4725 DAC modules (for 4-20mA outputs)
- ADS1115 ADC modules (for analog inputs)
- 4-20mA converter circuits
- Optoisolated digital I/O (recommended for PLC interfacing)

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure instruments in `config/instruments.yaml`

3. Run the simulator:
```bash
python backend/main.py
```

4. Open web interface: `http://localhost:8000`

## Configuration

Edit `config/instruments.yaml` to define your instruments and I/O allocation.
See `config/example.yaml` for reference.
