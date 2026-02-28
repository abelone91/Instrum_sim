# Example: Complete Pump Simulator Wiring

## Overview

This document shows the **complete, step-by-step wiring** for a single pump simulator connected to a PLC. This is a working example you can follow exactly.

## What You'll Build

A pump simulator with:
- ✓ Digital input: Enable pump from PLC
- ✓ Digital output: Pump running status to PLC
- ✓ Digital output: Fault alarm to PLC
- ✓ Analog output: Pump speed feedback (4-20mA) to PLC
- ✓ Real-time visualization in web interface

---

## Parts List

### Essential Components

| Item | Qty | Where to Buy | Price |
|------|-----|--------------|-------|
| Raspberry Pi 4 (4GB) | 1 | Amazon/Adafruit | $55 |
| MCP4725 DAC Breakout | 1 | Adafruit #935 | $6 |
| XY-WDV 4-20mA Module | 1 | eBay/Amazon | $8 |
| PC817 Optocouplers | 3 | eBay (pack of 10) | $2 |
| Resistors: 470Ω, 1kΩ, 10kΩ | 9 | Amazon (kit) | $10 |
| Breadboard | 1 | Amazon | $5 |
| Jumper wires (M-M, M-F) | 40pcs | Amazon | $8 |
| 24V 2A Power Supply | 1 | Amazon | $12 |
| **Total** | | | **$106** |

### Optional but Recommended

| Item | Price | Purpose |
|------|-------|---------|
| Multimeter | $20 | Testing voltages/currents |
| Label maker | $25 | Wire labeling |
| Terminal blocks | $10 | Professional connections |
| DIN rail | $15 | Mounting |

---

## Complete Wiring Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                RASPBERRY PI 4                                        │
│                                                                                      │
│  [Pin Layout]                                                                        │
│   1  3.3V    ●──────────────┬────────────────────┬──────────────────┐               │
│   3  SDA     ●──────────────┼──────────────┐     │                  │               │
│   5  SCL     ●──────────────┼──────┐       │     │                  │               │
│   9  GND     ●──────────────┼──────┼───────┼─────┼──────────────────┼───────┐       │
│  11  GPIO17  ●  (not used)  │      │       │     │                  │       │       │
│  29  GPIO5   ●──────────────┼──────┼───────┼─────┼──────────────┐   │       │       │
│  31  GPIO6   ●──────────────┼──────┼───────┼─────┼──────┐       │   │       │       │
│  33  GPIO13  ●──────────────┼──────┼───────┼─────┼───┐  │       │   │       │       │
│                              │      │       │     │   │  │       │   │       │       │
└──────────────────────────────┼──────┼───────┼─────┼───┼──┼───────┼───┼───────┼───────┘
                               │      │       │     │   │  │       │   │       │
                               │      │       │     │   │  │       │   │       │
┌──────────────────────────────┼──────┼───────┼─────┘   │  │       │   │       │
│ MCP4725 DAC (0x60)           │      │       │         │  │       │   │       │
├──────────────────────────────┤      │       │         │  │       │   │       │
│  VCC ────────────────────────┘      │       │         │  │       │   │       │
│  GND ───────────────────────────────┼───────┼─────────┼──┼───────┼───┘       │
│  SDA ───────────────────────────────┘       │         │  │       │           │
│  SCL ───────────────────────────────────────┘         │  │       │           │
│  OUT ─────► [XY-WDV Module] ──────────────────────────┼──┼───────┼─────────┐ │
└───────────────────────────────────────────────────────┼──┼───────┼─────────┼─┘
                                                        │  │       │         │
┌───────────────────────────────────────────────────────┼──┼───────┼─────────┼─┐
│ XY-WDV 4-20mA Converter Module                       │  │       │         │ │
├───────────────────────────────────────────────────────┤  │       │         │ │
│  Vi+ ◄── MCP4725 OUT (from above)                    │  │       │         │ │
│  Vi- ◄──────────────────────────────────────────────────┼───────┼─────────┼─┘
│  VCC ◄── +24V (see 24V supply below)                 │  │       │         │
│  GND ◄──────────────────────────────────────────────────┼───────┼─────────┘
│  Io+ ─────────────────────────────────────────────────► PLC AI+ │
│  Io- ─────────────────────────────────────────────────► PLC AI- │
└───────────────────────────────────────────────────────┼──┼───────┘
                                                        │  │
┌───────────────────────────────────────────────────────┼──┼──────────────────┐
│ OPTOISOLATOR #1 - Enable Input (PLC → Pi)            │  │                  │
│                                                       │  │                  │
│  PLC DO1+ (24V) ──[1kΩ]── Pin1 ──┐                  │  │                  │
│                                   │                   │  │                  │
│                            ┌──────▼──────┐            │  │                  │
│                            │   PC817 #1  │            │  │                  │
│                         1  │   ┌─────┐   │ 4          │  │                  │
│                        ──► │   │     │   ├─────────────┘  │                  │
│                            │   └─────┘   │                │                  │
│                         2  │             │ 3              │                  │
│  PLC DO1- (GND) ───────────┤             ├──[10kΩ]────────┼──────────────────┤
│                            └─────────────┘                │                  │
└───────────────────────────────────────────────────────────┼──────────────────┘
                                                            │
┌───────────────────────────────────────────────────────────┼──────────────────┐
│ OPTOISOLATOR #2 - Running Output (Pi → PLC)              │                  │
│                                                           │                  │
│  GPIO6 (Pi Pin 31) ──[470Ω]── Pin1 ──┐                  │                  │
│                                       │                   │                  │
│                              ┌────────▼──────┐            │                  │
│                              │   PC817 #2    │            │                  │
│                           1  │   ┌─────┐     │ 4          │                  │
│                          ──► │   │     │     ├──[10kΩ]──► PLC DI1+          │
│                              │   └─────┘     │                               │
│  3.3V (Pi Pin 1) ─────────2  │               │ 3                             │
│                              │               ├────────────────────────────┐  │
│                              └───────────────┘                            │  │
│                                                        24V Common ◄───────┘  │
└───────────────────────────────────────────────────────────┼──────────────────┘
                                                            │
┌───────────────────────────────────────────────────────────┼──────────────────┐
│ OPTOISOLATOR #3 - Fault Output (Pi → PLC)                │                  │
│                                                           │                  │
│  GPIO13 (Pi Pin 33) ─[470Ω]── Pin1 ──┐                  │                  │
│                                       │                   │                  │
│                              ┌────────▼──────┐            │                  │
│                              │   PC817 #3    │            │                  │
│                           1  │   ┌─────┐     │ 4          │                  │
│                          ──► │   │     │     ├──[10kΩ]──► PLC DI2+          │
│                              │   └─────┘     │                               │
│  3.3V (Pi Pin 1) ─────────2  │               │ 3                             │
│                              │               ├────────────────────────────┐  │
│                              └───────────────┘                            │  │
│                                                        24V Common ◄───────┘  │
└───────────────────────────────────────────────────────────┘                  │
                                                                               │
┌──────────────────────────────────────────────────────────────────────────────┘
│ 24V POWER SUPPLY (for PLC interface)
├──────────────────────────────────────────────────────────────────────────────┐
│  AC Input: 110-240V                                                          │
│  DC Output: 24V 2A                                                           │
│                                                                              │
│  +24V ──┬────► XY-WDV VCC                                                   │
│         ├────► PLC 24V Common (for DI pull-ups)                             │
│         └────► Any other 24V devices                                        │
│                                                                              │
│  GND ───┬────► All ground connections                                       │
│         └────► Common with Pi GND (IMPORTANT!)                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Assembly

### Step 1: Set Up Raspberry Pi (15 minutes)

```bash
# 1. Flash Raspberry Pi OS to SD card
# 2. Boot Pi and run updates
sudo apt update && sudo apt upgrade -y

# 3. Enable I2C
sudo raspi-config
# → Interface Options → I2C → Enable

# 4. Install required packages
sudo apt install -y python3-pip i2c-tools

# 5. Clone simulator repository
cd ~
git clone https://github.com/abelone91/Instrum_sim.git
cd Instrum_sim

# 6. Install dependencies
pip3 install -r requirements.txt

# 7. Test I2C (nothing connected yet, will show empty)
sudo i2cdetect -y 1
```

### Step 2: Connect MCP4725 DAC (5 minutes)

Using **female-to-female jumper wires**:

```
Raspberry Pi        Wire Color      MCP4725
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pin 1  (3.3V)  ───  Red      ───►  VCC
Pin 3  (SDA)   ───  Green    ───►  SDA
Pin 5  (SCL)   ───  White    ───►  SCL
Pin 9  (GND)   ───  Black    ───►  GND
```

**Verify:**
```bash
sudo i2cdetect -y 1
# Should show "60" at address 0x60
```

### Step 3: Connect XY-WDV Module (5 minutes)

Using **male-to-male jumper wires** on breadboard:

```
MCP4725         XY-WDV Module       24V Supply
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUT      ───►   Vi+
GND      ───►   Vi-
                VCC    ◄───   +24V
                GND    ◄───   GND
```

**Terminal connections:**
```
XY-WDV Module   →   PLC Terminal Block
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Io+             →   AI1+ (Analog Input 1 Positive)
Io-             →   AI1- (Analog Input 1 Negative)
```

### Step 4: Build Optoisolator #1 (PLC Input) (10 minutes)

On breadboard:

```
Row Numbers (example):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Row 10:  PLC DO1+ wire
Row 11:  1kΩ resistor (one end)
Row 12:  1kΩ resistor (other end) + PC817 Pin 1
Row 13:  PC817 Pin 2 + PLC DO1- wire
Row 14:  (empty)
Row 15:  PC817 Pin 4 + jumper to GPIO5
Row 16:  PC817 Pin 3 + 10kΩ resistor
Row 17:  10kΩ resistor (other end) + GND wire
```

**PC817 Pin Numbering (looking at chip from top):**
```
    ┌────────┐
  1 │●       │ 4
    │        │
  2 │        │ 3
    └────────┘
```

**Connections:**
- Pin 1 (Anode): To PLC DO1+ via 1kΩ resistor
- Pin 2 (Cathode): To PLC DO1- (GND)
- Pin 3 (Emitter): To Pi GND via 10kΩ resistor
- Pin 4 (Collector): To Pi GPIO5

### Step 5: Build Optoisolator #2 (Running Output) (10 minutes)

Same process as #1, but:

**Connections:**
- Pin 1: To GPIO6 via 470Ω resistor
- Pin 2: To Pi 3.3V (Pin 1)
- Pin 3: To 24V common
- Pin 4: To PLC DI1+ via 10kΩ resistor to 24V

### Step 6: Build Optoisolator #3 (Fault Output) (10 minutes)

Same as #2, but:
- Pin 1: To GPIO13 via 470Ω resistor
- Pin 4: To PLC DI2+ via 10kΩ resistor to 24V

### Step 7: Configure Software (5 minutes)

Edit `config/instruments.yaml`:

```yaml
instruments:
  - id: pump_01
    type: pump
    parameters:
      control_type: "digital"
      max_pressure_bar: 10.0
      set_pressure_bar: 8.0
      max_flow_lpm: 100.0
      ramp_time_sec: 5.0

    io:
      enable_input:
        type: digital_in
        pin: 5

      running_output:
        type: digital_out
        pin: 6

      fault_output:
        type: digital_out
        pin: 13

      feedback_output:
        type: analog_out
        i2c_address: 0x60
```

### Step 8: Test! (10 minutes)

```bash
# Start the simulator
python run.py

# Open browser to:
http://localhost:8000

# You should see:
# - "pump_01" card on dashboard
# - Real-time pump visualization
# - Animated gear icon
# - Speed, pressure, flow metrics
```

**Testing sequence:**

1. **With PLC OFF:**
   - Pump should show: Running = NO
   - Web interface shows pump stopped

2. **Turn PLC DO1 ON (24V):**
   - LED in optoisolator #1 should light up
   - Pump should show: Running = YES
   - Gear icon should animate
   - PLC DI1 should see signal (pump running)
   - PLC AI1 should read 4-20mA (pump speed)

3. **Measure with multimeter:**
   - At PLC AI1 terminals: Should read 4-20mA
   - At GPIO5: Should read 3.3V when PLC DO1 is ON
   - At GPIO6: Check LED lights when pump running

---

## PLC Ladder Logic Example

Simple PLC program to test the simulator:

```
Rung 1: Start Pump
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  I0.0          Q0.0
──┤ ├──────────( )─────────
 Start         DO1
Button       (Enable)


Rung 2: Monitor Running Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  I0.1          M0.0
──┤ ├──────────( )─────────
 DI1            Running
(Running)       Lamp


Rung 3: Monitor Speed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AI1           MW10
──┤ ├──────────[MOV]──────
(Speed)       (Speed
4-20mA)        Value)
```

---

## Troubleshooting

### Problem: I2C device not detected

```bash
sudo i2cdetect -y 1
# If nothing shows up:

# Check connections:
1. VCC to Pin 1 (3.3V) - measure with multimeter
2. GND to Pin 9 - continuity test
3. SDA to Pin 3 - visual check
4. SCL to Pin 5 - visual check

# Try different I2C bus:
sudo i2cdetect -y 0
```

### Problem: 4-20mA output incorrect

```bash
# Test DAC output directly:
python3
>>> from adafruit_mcp4725 import MCP4725
>>> import board, busio
>>> i2c = busio.I2C(board.SCL, board.SDA)
>>> dac = MCP4725(i2c, address=0x60)
>>> dac.normalized_value = 0.5  # Should give ~12mA
>>> # Measure at XY-WDV Io+ terminal with multimeter

# If voltage is wrong:
- Check 24V supply to XY-WDV
- Verify Vi+ gets 0-3.3V from MCP4725
- Adjust XY-WDV potentiometer for calibration
```

### Problem: Digital input not working

```bash
# Test GPIO manually:
python3
>>> import RPi.GPIO as GPIO
>>> GPIO.setmode(GPIO.BCM)
>>> GPIO.setup(5, GPIO.IN)
>>> GPIO.input(5)

# Should return:
# 1 (True) when PLC output is ON
# 0 (False) when PLC output is OFF

# If always 0:
- Check optoisolator orientation (Pin 1 has dot)
- Verify 1kΩ resistor value
- Check LED lights up when PLC ON
- Measure voltage at Pin 4 (should be 3.3V when ON)
```

### Problem: Digital output not working

```bash
# Test GPIO output:
python3
>>> import RPi.GPIO as GPIO
>>> GPIO.setmode(GPIO.BCM)
>>> GPIO.setup(6, GPIO.OUT)
>>> GPIO.output(6, True)  # LED should light

# Check PLC input:
- Measure voltage at PLC DI1+
- Should be 0V when GPIO = HIGH (active low)
- Should be 24V when GPIO = LOW
```

---

## Photos of Completed Build

### Expected Layout

```
┌─────────────────────────────────────┐
│  Raspberry Pi 4                     │
│  ┌──────────────────────────┐       │
│  │                          │       │
│  │  GPIO Header             │       │
│  │  ↓↓↓↓↓                   │       │
│  └──┬┬┬┬┬───────────────────┘       │
│     │││││                            │
└─────┼┼┼┼┼────────────────────────────┘
      │││││
      ↓↓↓↓↓
┌─────┴┴┴┴┴─────────────────┐
│  Breadboard               │
│  ┌─────────┐  ┌─────────┐│
│  │ MCP4725 │  │  PC817  ││
│  │  (DAC)  │  │ (Opto)  ││
│  └─────────┘  └─────────┘│
│                           │
│  ┌─────────┐  ┌─────────┐│
│  │ XY-WDV  │  │ More    ││
│  │ Module  │  │ Optos   ││
│  └─────────┘  └─────────┘│
└───────────────────────────┘
      ↓
┌─────┴─────────────────┐
│  Terminal Blocks      │
│  ┌────┬────┬────┐     │
│  │ AI │ DI │ DO │     │
│  └────┴────┴────┘     │
└───────────────────────┘
      ↓
    To PLC
```

---

## Next Steps

Once this works:

1. **Add more instruments:**
   - Follow same pattern
   - Use different GPIO pins
   - Add more I2C devices (different addresses)

2. **Migrate to PCB:**
   - Design custom PCB with all optoisolators
   - Add terminal blocks
   - Professional mounting

3. **Add DIN rail enclosure:**
   - Mount Pi on DIN rail
   - Use industrial terminal blocks
   - Add circuit breakers

---

## Files in This Project

```
Instrum_sim/
├── config/
│   └── instruments.yaml          ← Your pump configuration
├── backend/
│   ├── main.py                   ← FastAPI server
│   ├── simulators/
│   │   └── pump_simulator.py     ← Pump logic
│   └── hardware/
│       ├── gpio_driver.py        ← GPIO control
│       └── analog_io.py          ← MCP4725 driver
└── frontend/
    ├── index.html                ← Web interface
    ├── style.css                 ← Styling
    └── app.js                    ← JavaScript
```

---

## Support

- **Issues:** https://github.com/abelone91/Instrum_sim/issues
- **Documentation:** See `docs/` folder
- **Full Wiring:** See `docs/WIRING_DIAGRAMS.md`

---

**Total Build Time:** ~70 minutes
**Difficulty:** Intermediate (requires basic electronics knowledge)
**Cost:** ~$106 (or $148 with pre-made modules)

**Success Criteria:**
✓ I2C device detected at 0x60
✓ Pump shows in web interface
✓ PLC can enable/disable pump
✓ PLC receives running status
✓ PLC receives 4-20mA speed signal

**Congratulations!** You've built a working PLC pump simulator!
