# Quick Reference Card

## Starting the Simulator

### Windows
```cmd
run.bat
```

### Linux/Raspberry Pi
```bash
./run.sh
```

### Manual
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
python run.py
```

## Testing Installation

```bash
python test_setup.py
```

## Access Points

- **Web Interface:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **WebSocket:** ws://localhost:8000/ws

## Common Configuration Patterns

### Add a Pump

```yaml
- id: pump_01
  type: pump
  parameters:
    control_type: "digital"     # or "analog"
    max_flow_lpm: 100.0
  io:
    enable_input:
      type: digital_in
      pin: 5
    running_output:
      type: digital_out
      pin: 6
```

### Add a Tank

```yaml
- id: tank_01
  type: level
  parameters:
    tank_height_mm: 2000
    tank_volume_m3: 10.0
  io:
    level_output:
      type: analog_out
      i2c_address: 0x60
```

### Add a Flow Meter

```yaml
- id: flow_01
  type: flow
  parameters:
    pulses_per_liter: 100
  io:
    pulse_a_output:
      type: digital_out
      pin: 27
```

### Link Instruments

```yaml
- id: tank_01
  type: level
  links:
    flowmeter: flow_01    # Tank gets flow from flow_01

- id: flow_01
  type: flow
  links:
    pump: pump_01         # Flow meter reads pump output
```

## I/O Pin Types

| Type | Use | Hardware |
|------|-----|----------|
| `digital_in` | Input from PLC | GPIO pin |
| `digital_out` | Output to PLC | GPIO pin |
| `analog_in` | 0-10V / 4-20mA input | ADS1115 + channel |
| `analog_out` | 4-20mA output | MCP4725 |

## I2C Addresses

### DAC (MCP4725)
- 0x60, 0x61, 0x62, 0x63

### ADC (ADS1115)
- 0x48, 0x49, 0x4A, 0x4B

## GPIO Pin Reference (BCM Numbering)

**Avoid:** 0, 1, 2, 3, 14, 15

**Safe to use:** 4-13, 16-27

## API Quick Reference

### Get Status
```bash
curl http://localhost:8000/api/status
```

### List Simulators
```bash
curl http://localhost:8000/api/simulators
```

### Get Data
```bash
curl http://localhost:8000/api/data
```

### Start/Stop Simulation
```bash
curl -X POST http://localhost:8000/api/control/start
curl -X POST http://localhost:8000/api/control/stop
```

## Testing Hardware

### Check I2C Devices
```bash
sudo i2cdetect -y 1
```

### Test GPIO Pin
```bash
echo "17" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio17/direction
echo "1" > /sys/class/gpio/gpio17/value
```

### Test DAC Output
```python
from adafruit_mcp4725 import MCP4725
import board, busio

i2c = busio.I2C(board.SCL, board.SDA)
dac = MCP4725(i2c, address=0x60)
dac.normalized_value = 0.5  # 50% output
```

## Troubleshooting

### Simulator Won't Start
```bash
# Check Python version
python --version  # Need 3.8+

# Reinstall dependencies
pip install -r requirements.txt

# Check config syntax
python test_setup.py
```

### I2C Not Working
```bash
# Enable I2C
sudo raspi-config  # Interface Options → I2C

# Check devices
sudo i2cdetect -y 1
```

### GPIO Permission Error
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
sudo reboot
```

## File Locations

| File | Purpose |
|------|---------|
| `config/instruments.yaml` | Main configuration |
| `backend/main.py` | FastAPI server |
| `frontend/index.html` | Web interface |
| `docs/SETUP.md` | Detailed setup guide |
| `docs/USAGE.md` | Usage documentation |
| `docs/WIRING_GUIDE.md` | Hardware wiring |

## Default Update Rate

10 Hz (100ms cycle time) - Configurable in `backend/simulation_engine.py`:

```python
self.update_rate_hz = 10  # Change this value
```

## Systemd Service (Auto-start)

```bash
sudo systemctl enable plc-simulator
sudo systemctl start plc-simulator
sudo systemctl status plc-simulator
sudo systemctl stop plc-simulator
```

## View Logs

```bash
# If running as systemd service
journalctl -u plc-simulator -f

# If running manually
# Logs appear in terminal
```

## Backup Configuration

```bash
cp config/instruments.yaml config/instruments.yaml.bak
```

## Reset to Defaults

```bash
cp config/example_simple.yaml config/instruments.yaml
```
