# PLC Instrument Simulator - Setup Guide

## Hardware Requirements

### Raspberry Pi
- Raspberry Pi 4 (recommended) or Pi 3B+
- MicroSD card (16GB+)
- Power supply (5V 3A)

### I/O Hardware

#### For Analog Outputs (4-20mA)
- **MCP4725 DAC modules** (I2C, 12-bit)
  - Default addresses: 0x60, 0x61, 0x62, 0x63
  - Connect via I2C bus (SDA/SCL)
- **4-20mA converter circuit** (per channel)
  - Simple op-amp circuit: 0-3.3V → 4-20mA
  - Example: Use LM358 + transistor
  - OR use commercial modules (e.g., XY-WDV)

#### For Analog Inputs (4-20mA, 0-10V)
- **ADS1115 ADC modules** (I2C, 16-bit, 4 channels each)
  - Default addresses: 0x48, 0x49, 0x4A, 0x4B
  - Connect via I2C bus
- **Current-to-voltage converter** for 4-20mA inputs
  - 250Ω precision resistor (20mA × 250Ω = 5V)
  - Voltage divider to scale to 3.3V if needed

#### For Digital I/O
- **GPIO pins** (direct connection for 3.3V logic)
- **Optoisolators** (recommended for PLC interfacing)
  - Protects Raspberry Pi from industrial voltage levels
  - Use modules like PC817 optocouplers
  - Typical PLC outputs: 24VDC

#### PLC Interface
- **Wiring** depends on your PLC:
  - Digital outputs from PLC → Pi digital inputs (via optoisolator)
  - Pi digital outputs → PLC digital inputs (via optoisolator/relay)
  - 4-20mA from Pi → PLC analog inputs
  - 0-10V from PLC → Pi analog inputs (use voltage divider)

## Software Installation

### 1. Raspberry Pi OS Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and tools
sudo apt install -y python3 python3-pip python3-venv git

# Install I2C tools
sudo apt install -y i2c-tools

# Enable I2C interface
sudo raspi-config
# Navigate to: Interfacing Options → I2C → Enable
```

### 2. Verify I2C Hardware

```bash
# Check I2C devices
sudo i2cdetect -y 1

# You should see your DAC/ADC addresses (0x48, 0x60, etc.)
```

### 3. Install Simulator Software

```bash
# Clone or copy the simulator directory to Pi
cd ~
# (Copy simulator folder here)

cd simulator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For Raspberry Pi, also install hardware libraries:
pip install RPi.GPIO adafruit-circuitpython-mcp4725 adafruit-circuitpython-ads1x15 adafruit-blinka
```

### 4. Configure Your Instruments

Edit `config/instruments.yaml` to define your instruments and I/O allocation:

```yaml
instruments:
  - id: my_pump
    type: pump
    parameters:
      control_type: "digital"
      max_pressure_bar: 10.0
      # ... more parameters
    io:
      enable_input:
        type: digital_in
        pin: 5  # BCM pin number
      running_output:
        type: digital_out
        pin: 6
```

**I/O Pin Reference:**
- `type`: `digital_in`, `digital_out`, `analog_in`, `analog_out`
- `pin`: BCM GPIO pin number (for digital I/O)
- `i2c_address`: I2C device address (for analog I/O)
- `channel`: Channel number 0-3 (for multi-channel devices like ADS1115)

### 5. Test Configuration

```bash
# Activate virtual environment
source venv/bin/activate

# Run the simulator
python -m backend.main
```

### 6. Access the Web Interface

Open a browser and navigate to:
```
http://<raspberry-pi-ip>:8000
```

Or on the Pi itself:
```
http://localhost:8000
```

## I/O Allocation Strategy

### Planning Your I/O

1. **Count your instruments** and their I/O requirements
2. **Allocate GPIO pins** for digital signals
3. **Allocate I2C addresses** for analog I/O

### Example GPIO Allocation

| Pin (BCM) | Function | Instrument |
|-----------|----------|------------|
| 5 | Digital IN | Pump enable |
| 6 | Digital OUT | Pump running |
| 13 | Digital OUT | Pump fault |
| 16 | Digital IN | Valve open |
| 17 | Digital OUT | Tank HH alarm |
| 27 | Digital OUT | Flow pulse A |

### Example I2C Allocation

| Address | Device | Channel | Function |
|---------|--------|---------|----------|
| 0x60 | MCP4725 | - | Tank level 4-20mA out |
| 0x61 | MCP4725 | - | Pump feedback 4-20mA out |
| 0x48 | ADS1115 | 0 | Reg valve position in |
| 0x48 | ADS1115 | 1 | Pressure sensor in |

## Wiring Examples

### 4-20mA Output to PLC

```
[Raspberry Pi] → [MCP4725 DAC] → [V-to-I Converter] → [PLC AI]
   I2C (SDA/SCL)      0-3.3V             4-20mA         Input
```

### Digital Input from PLC

```
[PLC DO] → [Optoisolator] → [Raspberry Pi GPIO]
  24VDC      (PC817)            3.3V Logic
```

### Digital Output to PLC

```
[Raspberry Pi GPIO] → [Optoisolator/Relay] → [PLC DI]
      3.3V Logic          (PC817)             24VDC
```

## Running on Startup

Create a systemd service:

```bash
sudo nano /etc/systemd/system/plc-simulator.service
```

```ini
[Unit]
Description=PLC Instrument Simulator
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/simulator
Environment="PATH=/home/pi/simulator/venv/bin"
ExecStart=/home/pi/simulator/venv/bin/python -m backend.main
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable plc-simulator
sudo systemctl start plc-simulator
sudo systemctl status plc-simulator
```

## Scaling Up/Down

To add or remove instruments:

1. Edit `config/instruments.yaml`
2. Add/remove instrument definitions
3. Update I/O allocations
4. Rewire hardware as needed
5. Restart the simulator

The system automatically detects and initializes all configured instruments.

## Troubleshooting

### I2C Devices Not Detected

```bash
# Check I2C bus
sudo i2cdetect -y 1

# Verify connections (SDA, SCL, VCC, GND)
# Try different I2C addresses
```

### GPIO Permissions

```bash
# Add user to gpio group
sudo usermod -a -G gpio pi

# Reboot
sudo reboot
```

### Simulator Won't Start

```bash
# Check logs
journalctl -u plc-simulator -f

# Run manually to see errors
cd ~/simulator
source venv/bin/activate
python -m backend.main
```

## Development Mode

To test on a non-Pi machine (Windows/Mac/Linux):

1. The simulator will use **mock GPIO/I2C** automatically
2. No hardware required for development
3. Web interface works normally
4. Useful for UI development and testing

```bash
python -m backend.main
# Mock hardware will be used
```

## Next Steps

- Configure your specific instruments in `config/instruments.yaml`
- Wire up your PLC connections
- Test individual instruments before connecting to PLC
- Customize the web interface in `frontend/` directory
