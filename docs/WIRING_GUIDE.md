# Hardware Wiring Guide

## Overview

This guide provides detailed wiring diagrams for connecting the Raspberry Pi simulator to PLC systems.

## Safety Notice

**WARNING:**
- Industrial PLCs typically operate at 24VDC for I/O
- Raspberry Pi GPIO operates at 3.3V logic
- **NEVER** connect 24V directly to Raspberry Pi GPIO pins
- **ALWAYS** use optoisolators or level shifters
- Double-check all connections before powering on

## Component List

### Essential Components

1. **Raspberry Pi 4** (or 3B+)
2. **MCP4725 DAC Modules** (for 4-20mA outputs)
   - I2C address configurable: 0x60, 0x61, 0x62, 0x63
   - Adafruit MCP4725 breakout recommended
3. **ADS1115 ADC Modules** (for analog inputs)
   - 16-bit, 4-channel
   - Adafruit ADS1115 breakout recommended
4. **Optoisolators** (PC817 or similar)
   - For digital I/O isolation
5. **4-20mA Converter Circuits**
6. **Terminal blocks** for wiring
7. **DIN rail** (optional, for professional installation)

## I2C Device Connections

### MCP4725 DAC Wiring

```
Raspberry Pi          MCP4725 DAC
-----------          -----------
3.3V        ------>  VCC
GND         ------>  GND
SDA (GPIO2) ------>  SDA
SCL (GPIO3) ------>  SCL
                     OUT -----> [To 4-20mA converter]
```

**Multiple DACs:**
- Each MCP4725 can have address: 0x60, 0x61, 0x62, or 0x63
- Set address using A0 pin on some modules, or buy pre-addressed modules
- All DACs share same I2C bus (SDA/SCL)

### ADS1115 ADC Wiring

```
Raspberry Pi          ADS1115 ADC
-----------          -----------
3.3V        ------>  VCC
GND         ------>  GND
SDA (GPIO2) ------>  SDA
SCL (GPIO3) ------>  SCL
                     A0 -----> [Analog Input 0]
                     A1 -----> [Analog Input 1]
                     A2 -----> [Analog Input 2]
                     A3 -----> [Analog Input 3]
```

**Address Selection:**
- ADDR pin → GND: 0x48 (default)
- ADDR pin → VDD: 0x49
- ADDR pin → SDA: 0x4A
- ADDR pin → SCL: 0x4B

## 4-20mA Signal Generation

### Simple V-to-I Converter Circuit

```
MCP4725 OUT (0-3.3V) → V-to-I Converter → 4-20mA → PLC Analog Input

Circuit:
         +24V (from PLC or external supply)
          |
          R1 (1kΩ)
          |
          +---[Transistor Q1 (2N3904)]---+
          |                              |
MCP4725 --+                              |
  OUT     R2 (220Ω)                      |
          |                              |
         GND                          To PLC AI+
                                         |
                                      R_sense (250Ω)
                                         |
                                      To PLC AI-
```

**Formula:**
- 0V input → 4mA output
- 3.3V input → 20mA output
- Linear mapping

**Commercial Alternative:**
- XY-WDV voltage to current converter module
- 0-5V → 4-20mA
- Isolated, easier to use

## Digital Input from PLC

### PLC Digital Output → Raspberry Pi Digital Input

```
PLC DO                          Raspberry Pi
------                          ------------
DO+ (24V) ----[R1 1kΩ]----+
                           |
                     [LED ←] PC817 Optoisolator
                           |    [→ Photo-transistor]
DO- (GND)  ---------------+         |
                                    +----> GPIO (Input)
                                    |
                                  [R2 10kΩ]
                                    |
Raspberry Pi GND -------------------+
```

**Components:**
- R1: 1kΩ (current limiting for LED in optoisolator)
- PC817 optoisolator
- R2: 10kΩ pull-down resistor
- 24V PLC output drives optoisolator LED
- Transistor provides 0V or 3.3V to GPIO

**Alternative:**
- Pre-built optoisolator modules (8-channel boards available)

## Digital Output to PLC

### Raspberry Pi Digital Output → PLC Digital Input

```
Raspberry Pi                    PLC DI
------------                    ------
GPIO (Output) ----[R1 470Ω]----+
                                |
                          [LED ←] PC817
                                |    [→ Photo-transistor]
3.3V          ------------------+         |
                                          +----> PLC DI+
                                          |
                                    [R2 10kΩ]
                                          |
PLC 24V Common ----------------------------+----> PLC DI-
```

**Components:**
- R1: 470Ω (LED current limiting)
- PC817 optoisolator
- R2: 10kΩ pull-up to PLC common
- GPIO drives optoisolator LED
- PLC sees 0V or 24V

**Alternative:**
- Relay modules (for higher current/voltage)
- Solid-state relay modules

## Complete Wiring Example

### Example: Tank Level Simulator with Pump

**Instruments:**
1. Tank Level Simulator
2. Pump Simulator
3. Flow Meter Simulator

#### Tank Level - 4-20mA Output

```yaml
io:
  level_output:
    type: analog_out
    i2c_address: 0x60
```

**Wiring:**
```
Raspberry Pi I2C → MCP4725 (0x60) → V-to-I Converter → PLC AI CH1 (4-20mA)
```

#### Pump - Digital Input/Output

```yaml
io:
  enable_input:
    type: digital_in
    pin: 5
  running_output:
    type: digital_out
    pin: 6
```

**Wiring:**
```
PLC DO1 (Start Pump) → Optoisolator → GPIO 5 (Input)
GPIO 6 (Output) → Optoisolator → PLC DI1 (Pump Running)
```

#### Flow Meter - Pulse Outputs

```yaml
io:
  pulse_a_output:
    type: digital_out
    pin: 27
  pulse_b_output:
    type: digital_out
    pin: 22
```

**Wiring:**
```
GPIO 27 (Pulse A) → Optoisolator → PLC DI2 (Flow Pulse A)
GPIO 22 (Pulse B) → Optoisolator → PLC DI3 (Flow Pulse B)
```

## Pin Allocation Table

### Recommended GPIO Pin Assignment

| BCM Pin | Function | Typical Use |
|---------|----------|-------------|
| 2 | I2C SDA | DAC/ADC Communication |
| 3 | I2C SCL | DAC/ADC Communication |
| 4 | Digital I/O | General purpose |
| 5-13 | Digital I/O | Inputs from PLC |
| 16-27 | Digital I/O | Outputs to PLC |

**Avoid these pins:**
- GPIO 14, 15 (UART - used for serial console)
- GPIO 0, 1 (I2C ID EEPROM)

### I2C Device Address Map

| Address | Device Type | Purpose |
|---------|-------------|---------|
| 0x60 | MCP4725 #1 | Analog Output 1 |
| 0x61 | MCP4725 #2 | Analog Output 2 |
| 0x62 | MCP4725 #3 | Analog Output 3 |
| 0x63 | MCP4725 #4 | Analog Output 4 |
| 0x48 | ADS1115 #1 | Analog Inputs 0-3 |
| 0x49 | ADS1115 #2 | Analog Inputs 4-7 |

## Testing Connections

### Test Digital Output

```bash
# Set GPIO 17 high
echo "17" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio17/direction
echo "1" > /sys/class/gpio/gpio17/value

# Measure voltage at pin - should be 3.3V
```

### Test Digital Input

```bash
# Configure GPIO 27 as input
echo "27" > /sys/class/gpio/export
echo "in" > /sys/class/gpio/gpio27/direction

# Read value
cat /sys/class/gpio/gpio27/value
# 0 = low, 1 = high
```

### Test I2C Devices

```bash
# Scan I2C bus
sudo i2cdetect -y 1

# Should show addresses of connected DAC/ADC modules
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 60: 60 61 -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 70: -- -- -- -- -- -- -- --
```

### Test 4-20mA Output

```python
# Quick test script
from adafruit_mcp4725 import MCP4725
import board
import busio

i2c = busio.I2C(board.SCL, board.SDA)
dac = MCP4725(i2c, address=0x60)

# Set to 12mA (mid-range)
# 4mA = 0V, 20mA = 3.3V
# 12mA = 1.65V
dac.normalized_value = 0.5

# Measure with multimeter at PLC input
# Should read ~12mA
```

## Troubleshooting

### I2C Devices Not Detected
- Check VCC (3.3V) and GND connections
- Verify SDA/SCL not swapped
- Check for loose connections
- Try different I2C addresses

### GPIO Not Working
- Verify pin numbering (BCM vs BOARD mode)
- Check for GPIO conflicts (other programs using pins)
- Test with simple scripts first

### 4-20mA Output Incorrect
- Measure DAC output voltage (0-3.3V range)
- Check V-to-I converter circuit
- Verify 24V supply to converter
- Measure current with multimeter in series

### Optoisolator Issues
- Check LED polarity
- Verify current-limiting resistors
- Test with multimeter
- Replace if damaged

## Professional Installation Tips

1. **Use DIN rail mounting** for industrial environment
2. **Label all wires** with instrument ID and signal name
3. **Use terminal blocks** for easy maintenance
4. **Keep I2C wires short** (<30cm recommended)
5. **Separate signal and power wiring**
6. **Use shielded cable** for analog signals in noisy environments
7. **Add fuses** on 24V supplies
8. **Document everything** in config file and physical labels
