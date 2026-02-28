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
python run.py
```

4. Open web interface: `http://localhost:8000`

## Wiring & Hardware Setup

**Complete wiring documentation available:**

- **[QUICK_WIRING_GUIDE.md](QUICK_WIRING_GUIDE.md)** - Quick visual reference with shopping lists
- **[EXAMPLE_PUMP_WIRING.md](EXAMPLE_PUMP_WIRING.md)** - Complete step-by-step pump simulator example
- **[docs/WIRING_DIAGRAMS.md](docs/WIRING_DIAGRAMS.md)** - Comprehensive circuits and diagrams
- **[docs/SETUP.md](docs/SETUP.md)** - Detailed installation and hardware setup
- **[docs/USAGE.md](docs/USAGE.md)** - Configuration and operation guide

**Recommended starting point:**
1. Read [QUICK_WIRING_GUIDE.md](QUICK_WIRING_GUIDE.md) for overview
2. Follow [EXAMPLE_PUMP_WIRING.md](EXAMPLE_PUMP_WIRING.md) for your first build
3. Reference [docs/WIRING_DIAGRAMS.md](docs/WIRING_DIAGRAMS.md) for other instrument types

## Configuration

### Via Web Interface (NEW!)

1. Open `http://localhost:8000`
2. Click "Add Instrument" button
3. Select instrument type and configure parameters
4. Save - configuration automatically updated!

### Via YAML File

Edit `config/instruments.yaml` to define your instruments and I/O allocation.
See `config/example_simple.yaml` for reference.
