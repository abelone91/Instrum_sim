# Complete Wiring Diagrams for PLC Simulator

## Table of Contents
1. [Component Overview](#component-overview)
2. [Power Supply Wiring](#power-supply-wiring)
3. [I2C Bus Wiring](#i2c-bus-wiring)
4. [Digital Inputs (PLC → Pi)](#digital-inputs-plc--pi)
5. [Digital Outputs (Pi → PLC)](#digital-outputs-pi--plc)
6. [Analog Outputs (4-20mA)](#analog-outputs-4-20ma)
7. [Analog Inputs](#analog-inputs)
8. [Complete System Diagram](#complete-system-diagram)
9. [Example Configurations](#example-configurations)

---

## Component Overview

### Required Components

| Component | Quantity | Purpose | Example Part Number |
|-----------|----------|---------|---------------------|
| Raspberry Pi 4 | 1 | Main controller | RPi 4B 4GB |
| MCP4725 DAC | 1-4 | 4-20mA analog outputs | Adafruit 935 |
| ADS1115 ADC | 1-4 | Analog inputs | Adafruit 1085 |
| PC817 Optocoupler | 8-32 | Digital I/O isolation | PC817C |
| LM358 Op-Amp | 1-4 | 4-20mA converter | LM358N |
| 2N3904 Transistor | 1-4 | Current driver | 2N3904 |
| Resistors | Various | See circuits below | |
| Terminal blocks | 10-20 | Wiring connections | Phoenix Contact |
| 24VDC Power Supply | 1 | PLC interface power | Mean Well HDR-15-24 |

### Pin Reference - Raspberry Pi 4 (BCM Numbering)

```
        3.3V  (1) (2)  5V
       GPIO2  (3) (4)  5V
       GPIO3  (5) (6)  GND
       GPIO4  (7) (8)  GPIO14
         GND  (9) (10) GPIO15
      GPIO17 (11) (12) GPIO18
      GPIO27 (13) (14) GND
      GPIO22 (15) (16) GPIO23
        3.3V (17) (18) GPIO24
      GPIO10 (19) (20) GND
       GPIO9 (21) (22) GPIO25
      GPIO11 (23) (24) GPIO8
         GND (25) (26) GPIO7
       GPIO0 (27) (28) GPIO1
       GPIO5 (29) (30) GND
       GPIO6 (31) (32) GPIO12
      GPIO13 (33) (34) GND
      GPIO19 (35) (36) GPIO16
      GPIO26 (37) (38) GPIO20
         GND (39) (40) GPIO21

I2C Bus:
- SDA: GPIO2 (Pin 3)
- SCL: GPIO3 (Pin 5)
```

---

## Power Supply Wiring

### Raspberry Pi Power

```
┌─────────────────────────────────────────┐
│  5V 3A Power Supply                     │
│  (USB-C or GPIO header)                 │
└───────────────┬─────────────────────────┘
                │
                ├──────────► Pin 2 (5V)
                ├──────────► Pin 4 (5V)
                └──────────► Pin 6 (GND)
```

### 24VDC PLC Interface Power

```
┌─────────────────────────────────────────┐
│  24VDC Power Supply                     │
│  (For optoisolators & PLC interface)    │
└────┬──────────┬─────────────────────────┘
     │          │
   24V+       24V-
     │          │
     └──────────┴──► Used for:
                     - Optoisolator circuits
                     - 4-20mA loop power
                     - PLC digital I/O
```

**WARNING:** Keep 24V and 3.3V circuits completely separate!

---

## I2C Bus Wiring

All I2C devices (DACs and ADCs) share the same I2C bus.

```
Raspberry Pi
┌─────────────────────────────────────────────────┐
│                                                 │
│  Pin 3 (SDA/GPIO2) ────────────────┬───────────┤
│                                    │           │
│  Pin 5 (SCL/GPIO3) ──────────────┬─┼───────────┤
│                                  │ │           │
│  Pin 1 (3.3V) ────────────────┬──┼─┼───────────┤
│                               │  │ │           │
│  Pin 9 (GND) ─────────────┬───┼──┼─┼───────────┤
│                           │   │  │ │           │
└───────────────────────────┼───┼──┼─┼───────────┘
                            │   │  │ │
                            │   │  │ │
        ┌───────────────────┼───┼──┼─┼──────────┐
        │ MCP4725 DAC #1    │   │  │ │          │
        │ Address: 0x60     │   │  │ │          │
        ├───────────────────┼───┼──┼─┼──────────┤
        │ VCC ──────────────┘   │  │ │          │
        │ GND ──────────────────┘  │ │          │
        │ SDA ─────────────────────┘ │          │
        │ SCL ───────────────────────┘          │
        │ OUT ──────────► To 4-20mA converter   │
        └───────────────────────────────────────┘

        ┌───────────────────────────────────────┐
        │ MCP4725 DAC #2                        │
        │ Address: 0x61                         │
        │ (Connect VCC, GND, SDA, SCL same way) │
        └───────────────────────────────────────┘

        ┌───────────────────────────────────────┐
        │ ADS1115 ADC #1                        │
        │ Address: 0x48                         │
        │ (Connect VCC, GND, SDA, SCL same way) │
        │ A0 ◄── Analog Input Channel 0         │
        │ A1 ◄── Analog Input Channel 1         │
        │ A2 ◄── Analog Input Channel 2         │
        │ A3 ◄── Analog Input Channel 3         │
        └───────────────────────────────────────┘
```

### I2C Address Configuration

**MCP4725 (DAC):**
- Base address: 0x60
- A0 pin: Tie to GND for 0x60, VCC for 0x61
- Available: 0x60, 0x61, 0x62, 0x63

**ADS1115 (ADC):**
- ADDR pin determines address:
  - GND: 0x48
  - VDD: 0x49
  - SDA: 0x4A
  - SCL: 0x4B

---

## Digital Inputs (PLC → Pi)

### Optoisolator Circuit for PLC Digital Output → Pi Input

```
PLC Digital Output                    Raspberry Pi
┌─────────────┐                      ┌──────────────┐
│             │                      │              │
│  DO+ (24V)  ├──[R1: 1kΩ]──┬───────┤              │
│             │              │       │              │
│             │         ┌────▼────┐  │              │
│             │         │ PC817   │  │              │
│             │      1  │  ┌──┐   │4 │              │
│             │     ───►│  │  │   ├──┼──► GPIO17    │
│             │         │  └──┘   │  │   (Pin 11)   │
│             │      2  │         │3 │              │
│  DO- (GND)  ├─────────┤         ├──┼─[R2: 10kΩ]  │
│             │         └─────────┘  │      │       │
└─────────────┘                      │      └──GND  │
                                     │              │
                                     └──────────────┘

Components:
- R1: 1kΩ (LED current limiting, ~20mA @ 24V)
- R2: 10kΩ (Pull-down resistor)
- PC817: Optoisolator

How it works:
1. When PLC output is ON (24V):
   - Current flows through R1 and PC817 LED
   - Phototransistor turns ON
   - GPIO17 sees HIGH (3.3V)

2. When PLC output is OFF (0V):
   - No current through LED
   - Phototransistor is OFF
   - R2 pulls GPIO17 to LOW (0V)
```

### Multi-Channel Digital Input Module

```
       PLC Digital Outputs              Raspberry Pi
┌──────────────────────────┐           ┌─────────────────┐
│                          │           │                 │
│  DO1+ (24V) ─┐           │           │  GPIO5  (Pin 29)│
│  DO1- (GND) ─┼─► [OPT1]──┼───────────┤  GPIO6  (Pin 31)│
│              │           │           │  GPIO13 (Pin 33)│
│  DO2+ (24V) ─┤           │           │  GPIO19 (Pin 35)│
│  DO2- (GND) ─┼─► [OPT2]──┼───────────┤  GPIO26 (Pin 37)│
│              │           │           │  GPIO16 (Pin 36)│
│  DO3+ (24V) ─┤           │           │  GPIO20 (Pin 38)│
│  DO3- (GND) ─┼─► [OPT3]──┼───────────┤  GPIO21 (Pin 40)│
│              │           │           │                 │
│  DO4+ (24V) ─┤           │           │  GND    (Pin 39)│
│  DO4- (GND) ─┼─► [OPT4]──┼───────────┤                 │
│              │           │           └─────────────────┘
└──────────────┘           │
                           │
   Each [OPT] is the circuit shown above
```

---

## Digital Outputs (Pi → PLC)

### Optoisolator Circuit for Pi Output → PLC Digital Input

```
Raspberry Pi                          PLC Digital Input
┌──────────────┐                     ┌─────────────┐
│              │                     │             │
│  GPIO6       ├──[R1: 470Ω]──┬─────┤             │
│  (Pin 31)    │               │     │             │
│              │          ┌────▼────┐│             │
│              │          │ PC817   ││             │
│              │       1  │  ┌──┐   ││  4          │
│              │      ───►│  │  │   │├─[R2: 10kΩ]─┤ DI+
│              │          │  └──┘   ││      │      │
│              │       2  │         ││  3   │      │
│  3.3V        ├──────────┤         │├──────┘      │
│  (Pin 17)    │          └─────────┘│             │
│              │                     │             │
│              │                     │  DI- (24V+) │
└──────────────┘                     └─────────────┘

Components:
- R1: 470Ω (LED current limiting for 3.3V)
- R2: 10kΩ (Pull-up to 24V)

How it works:
1. When GPIO6 is HIGH (3.3V):
   - Current flows through PC817 LED
   - Phototransistor turns ON
   - PLC sees 0V (active low logic)

2. When GPIO6 is LOW (0V):
   - No current through LED
   - Phototransistor is OFF
   - R2 pulls PLC input to 24V (inactive)

Note: This provides active-low signaling.
For active-high, invert the circuit.
```

### Alternative: Solid State Relay Module

For higher current or voltage switching:

```
Raspberry Pi                     SSR Module              Load
┌──────────────┐                ┌────────────┐       ┌─────────┐
│              │                │            │       │         │
│  GPIO20      ├────────────────┤ IN+        │       │  PLC    │
│  (Pin 38)    │                │            │       │  DI+    │
│              │                │    SSR     ├───────┤         │
│  GND         ├────────────────┤ IN-        │       │         │
│  (Pin 39)    │                │            │       │  DI-    │
│              │                │  OUT+      │       │         │
│              │                │            ├───────┤ 24V+    │
│              │                │  OUT-      │       │         │
└──────────────┘                └────────────┘       └─────────┘

Advantages:
- No resistors needed
- Higher isolation voltage
- Can switch AC or DC
- Built-in LED indicators
```

---

## Analog Outputs (4-20mA)

### MCP4725 DAC to 4-20mA Converter Circuit

```
┌─────────────────────────────────────────────────────────────┐
│  Complete 4-20mA Output Circuit                             │
└─────────────────────────────────────────────────────────────┘

Raspberry Pi I2C          MCP4725 DAC         4-20mA Converter
┌──────────────┐         ┌──────────┐         ┌────────────────────┐
│              │         │          │         │                    │
│ 3.3V ────────┼─────────┤ VCC      │         │                    │
│ GND ─────────┼─────────┤ GND      │         │                    │
│ SDA ─────────┼─────────┤ SDA      │         │                    │
│ SCL ─────────┼─────────┤ SCL      │         │                    │
│              │         │          │         │    +24V (Loop)     │
│              │         │      OUT ├─────────┤         │          │
│              │         │          │ 0-3.3V  │    ┌────▼────┐     │
└──────────────┘         └──────────┘         │    │ R1: 1kΩ │     │
                                               │    └────┬────┘     │
                                               │         │          │
                              ┌────────────────┼─────────┤ Q1       │
                              │                │         │ 2N3904   │
   0V → 4mA                   │  R3: 220Ω      │    ┌────▼────┐     │
   3.3V → 20mA                │                │    │         │     │
                              └────────────────┼────┤ Base    │     │
                                               │    │         │     │
                                               │    │ Emitter ├─────┤
                                               │    │         │     │
                                               │    └─────────┘     │
                                               │         │          │
                                               │    ┌────▼────┐     │
                                               │    │R2: 250Ω │     │
                                               │    │  (1%)   │     │
                                               │    └────┬────┘     │
                                               │         │          │
                                               │         └──────────┤► To PLC AI-
                                               │                    │
                                               │         PLC AI+ ───┤
                                               │                    │
                                               └────────────────────┘

Component Values:
- Q1: 2N3904 NPN transistor
- R1: 1kΩ (current limiting)
- R2: 250Ω 1% (sense resistor, 20mA × 250Ω = 5V)
- R3: 220Ω (base resistor)

Current Calculation:
Vout(DAC) → Vbe → Ie = Vout / (R3 + Re)
With proper biasing: 0V → 4mA, 3.3V → 20mA
```

### Using LM358 Op-Amp (More Accurate)

```
                        +24V Loop Supply
                             │
                        ┌────▼────┐
                        │ R1: 1kΩ │
                        └────┬────┘
                             │
    MCP4725 OUT              │      ┌─────────────┐
    (0-3.3V)                 │      │   LM358     │
         │              ┌────┴──────┤ V+          │
         │              │           │             │
         └──────────────┤ IN+ (3)   │         OUT ├────► To PLC AI+
                        │           │      (1)    │
         ┌──────────────┤ IN- (2)   │             │
         │              │           │             │
    ┌────▼────┐         │           │ V- ─────────┤
    │R2: 10kΩ │         │           │             │
    └────┬────┘         │           │ GND ────────┤
         │              └───────────┴─────────────┘
         │                               │
    ┌────▼────┐                     ┌────▼────┐
    │R3: 250Ω │                     │R4: 250Ω │  Current sense
    │  (1%)   │                     │  (1%)   │
    └────┬────┘                     └────┬────┘
         │                               │
         └───────────┬───────────────────┘
                     │
                    GND                  To PLC AI-

This circuit provides:
- Better linearity
- More stable 4-20mA output
- Temperature compensation
- Higher accuracy (~0.1% vs ~2%)
```

### Commercial 4-20mA Module (Easiest Solution)

```
┌──────────────────────────────────────────────────┐
│  XY-WDV Voltage to Current Module                │
│                                                  │
│  Vi+ ◄─── MCP4725 OUT (0-3.3V or 0-5V)         │
│  Vi- ◄─── GND                                   │
│                                                  │
│  Io+ ───► To PLC AI+                            │
│  Io- ───► To PLC AI-                            │
│                                                  │
│  VCC ◄─── 12-24VDC (loop power)                 │
│  GND ◄─── GND                                   │
│                                                  │
│  Configuration: 0-5V → 4-20mA                   │
│  (Adjust potentiometer for calibration)          │
└──────────────────────────────────────────────────┘

Advantages:
- No soldering required
- Pre-calibrated
- Isolated
- Plug and play
- ~$5-10 per channel

Recommended for production use!
```

---

## Analog Inputs

### Reading 4-20mA Signals

```
From PLC AO                    ADS1115 ADC
(4-20mA)
    │
    │          ┌────────────────────────────┐
    ├──────────┤ A0                         │
    │          │                            │
┌───▼────┐     │  VCC ◄─── 3.3V             │
│ R1:    │     │  GND ◄─── GND              │
│ 250Ω   │     │  SDA ◄─── I2C SDA          │
│ (1%)   │     │  SCL ◄─── I2C SCL          │
└───┬────┘     │                            │
    │          │  ADDR ◄─── GND (0x48)      │
    └──────────┤ GND                        │
               │                            │
               └────────────────────────────┘

Voltage Calculation:
4mA × 250Ω = 1.0V
20mA × 250Ω = 5.0V

⚠️ WARNING: 5V exceeds ADS1115 max input!

Solution: Use voltage divider or different resistor
```

### Safe 4-20mA Input with Voltage Divider

```
From PLC AO        Voltage Divider         ADS1115
(4-20mA)
    │
    │
┌───▼────┐
│ R1:    │     ┌────────────┐         ┌──────────┐
│ 150Ω   │     │ R2: 150Ω   │         │          │
└───┬────┘     └─────┬──────┘         │  A0 ◄────┤
    │                │                │          │
    └────────────────┼────────────────┤          │
                     │                │          │
                ┌────▼────┐           │  GND ────┤
                │ R3: 150Ω│           │          │
                └────┬────┘           └──────────┘
                     │
                    GND

Total Resistance: 300Ω
Voltage at A0:
  4mA × 150Ω = 0.6V
 20mA × 150Ω = 3.0V

✓ Safe for ADS1115 (max 4.096V)
```

### Reading 0-10V Signals

```
From PLC AO           Voltage Divider        ADS1115
(0-10V)
    │
    │           ┌──────────┐
    ├───────────┤ R1: 20kΩ │
    │           └─────┬────┘          ┌──────────┐
    │                 │                │          │
    │                 ├────────────────┤ A0       │
    │                 │                │          │
    │           ┌─────▼────┐           │          │
    │           │ R2: 10kΩ │           │  GND ────┤
    │           └─────┬────┘           │          │
    │                 │                └──────────┘
    └─────────────────┴── GND

Voltage Divider Ratio: 10k / (20k + 10k) = 1/3

Input Range: 0-10V
ADS1115 sees: 0-3.33V (safe!)

Calculation:
V_out = V_in × (R2 / (R1 + R2))
V_out = 10V × (10k / 30k) = 3.33V
```

---

## Complete System Diagram

### Typical Setup: Pump Simulator

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          RASPBERRY PI 4                                             │
│                                                                                     │
│  GPIO5 (IN)  ◄──[Opto]◄── PLC DO "Enable Pump"                                    │
│  GPIO6 (OUT) ──►[Opto]──► PLC DI "Pump Running"                                   │
│  GPIO13(OUT) ──►[Opto]──► PLC DI "Pump Fault"                                     │
│                                                                                     │
│  I2C Bus:                                                                          │
│    SDA/SCL ──┬──► MCP4725 #1 (0x60) ──► [4-20mA] ──► PLC AI "Pump Speed"        │
│              │                                                                     │
│              └──► ADS1115 #1 (0x48) ◄── [4-20mA] ◄── PLC AO "Speed Setpoint"    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

Power Supplies:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 5V 3A       │    │ 24VDC 2A    │    │ PLC Power   │
│ (USB-C)     │    │ (Opto/Loop) │    │ 24VDC       │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Complete Tank Level System

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                     TANK LEVEL SIMULATOR                                              │
│                                                                                       │
│  Raspberry Pi:                                                                        │
│    I2C → MCP4725 (0x60) → [4-20mA Circuit] → PLC AI "Tank Level" (4-20mA)          │
│    GPIO17 (OUT) → [Optoisolator] → PLC DI "HH Alarm" (Digital)                      │
│                                                                                       │
│  Configuration (instruments.yaml):                                                    │
│    io:                                                                                │
│      level_output:                                                                    │
│        type: analog_out                                                               │
│        i2c_address: 0x60                                                              │
│      hh_alarm_output:                                                                 │
│        type: digital_out                                                              │
│        pin: 17                                                                        │
│                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Example Configurations

### Example 1: Single Pump with All Features

**Hardware Needed:**
- 1× Raspberry Pi 4
- 1× MCP4725 DAC (for speed feedback)
- 1× ADS1115 ADC (for speed setpoint input)
- 4× PC817 Optoisolators
- 1× 4-20mA output circuit
- 1× 4-20mA input circuit

**Connections:**

| Signal | Direction | Hardware | GPIO/I2C | PLC Connection |
|--------|-----------|----------|----------|----------------|
| Enable Input | PLC→Pi | Optoisolator | GPIO5 | DO1 |
| Running Output | Pi→PLC | Optoisolator | GPIO6 | DI1 |
| Fault Output | Pi→PLC | Optoisolator | GPIO13 | DI2 |
| Speed Feedback | Pi→PLC | MCP4725→4-20mA | 0x60 | AI1 |
| Speed Setpoint | PLC→Pi | 4-20mA→ADS1115 | 0x48 CH0 | AO1 |

**Wiring Steps:**

1. **I2C Devices:**
   ```
   Pi Pin 3 (SDA) → MCP4725 SDA, ADS1115 SDA
   Pi Pin 5 (SCL) → MCP4725 SCL, ADS1115 SCL
   Pi Pin 1 (3.3V) → MCP4725 VCC, ADS1115 VCC
   Pi Pin 9 (GND) → MCP4725 GND, ADS1115 GND
   ```

2. **Digital I/O:**
   ```
   PLC DO1+ → [1kΩ] → PC817 Pin1
   PLC DO1- → PC817 Pin2
   PC817 Pin4 → GPIO5
   PC817 Pin3 → [10kΩ] → GND

   GPIO6 → [470Ω] → PC817 Pin1
   3.3V → PC817 Pin2
   PC817 Pin4 → [10kΩ] → 24V
   PC817 Pin3 → PLC DI1

   (Repeat for GPIO13 → PLC DI2)
   ```

3. **Analog Output:**
   ```
   MCP4725 OUT → 4-20mA Circuit → PLC AI1+ and AI1-
   ```

4. **Analog Input:**
   ```
   PLC AO1+ → [150Ω] → ADS1115 A0
   ADS1115 A0 → [150Ω] → GND
   PLC AO1- → GND
   ```

**YAML Configuration:**

```yaml
- id: pump_01
  type: pump
  parameters:
    control_type: "analog"
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
    speed_input:
      type: analog_in
      i2c_address: 0x48
      channel: 0
```

### Example 2: Multi-Instrument Setup

**System:** Pump → Flow Meter → Tank Level

**Hardware Needed:**
- 1× Raspberry Pi 4
- 2× MCP4725 DAC
- 1× ADS1115 ADC
- 8× PC817 Optoisolators

**I2C Address Allocation:**

| Device | Address | Use |
|--------|---------|-----|
| MCP4725 #1 | 0x60 | Tank level output |
| MCP4725 #2 | 0x61 | Pump feedback |
| ADS1115 #1 | 0x48 | Pump setpoint input |

**GPIO Allocation:**

| Pin | Direction | Instrument | Signal |
|-----|-----------|------------|--------|
| GPIO5 | IN | Pump | Enable |
| GPIO6 | OUT | Pump | Running |
| GPIO13 | OUT | Pump | Fault |
| GPIO17 | OUT | Tank | HH Alarm |
| GPIO27 | OUT | Flow | Pulse A |
| GPIO22 | OUT | Flow | Pulse B |
| GPIO23 | IN | Flow | Start |
| GPIO24 | IN | Flow | Reset |

---

## Terminal Block Wiring

### Recommended Terminal Block Layout

```
┌──────────────────────────────────────────────────┐
│  PLC Interface Terminal Block                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  [24V+] [24V-] [GND]  ← Power Supply            │
│                                                  │
│  Digital Inputs (from PLC):                      │
│  [DO1+] [DO1-]  ← Pump Enable                   │
│  [DO2+] [DO2-]  ← Flow Start                    │
│  [DO3+] [DO3-]  ← Flow Reset                    │
│  [DO4+] [DO4-]  ← Spare                         │
│                                                  │
│  Digital Outputs (to PLC):                       │
│  [DI1+] [DI1-]  ← Pump Running                  │
│  [DI2+] [DI2-]  ← Pump Fault                    │
│  [DI3+] [DI3-]  ← Tank HH Alarm                 │
│  [DI4+] [DI4-]  ← Flow Pulse A                  │
│  [DI5+] [DI5-]  ← Flow Pulse B                  │
│                                                  │
│  Analog Outputs (to PLC):                        │
│  [AI1+] [AI1-]  ← Tank Level (4-20mA)           │
│  [AI2+] [AI2-]  ← Pump Speed (4-20mA)           │
│                                                  │
│  Analog Inputs (from PLC):                       │
│  [AO1+] [AO1-]  ← Pump Setpoint (4-20mA)        │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Labeling System

Use heat-shrink labels or label printer:

```
Example Labels:
┌──────────────────────┐
│ Pi-GPIO5             │  ← On wire at Pi end
│ Pump-Enable          │
│ PLC-DO1              │  ← On wire at PLC end
└──────────────────────┘

┌──────────────────────┐
│ Pi-I2C-0x60          │
│ Tank-Level-4-20mA    │
│ PLC-AI1              │
└──────────────────────┘
```

---

## Safety Checklist

Before powering on:

- [ ] All 24V and 3.3V circuits are isolated (optoisolators in place)
- [ ] No direct connections between Pi GPIO and 24V
- [ ] All power supplies have correct polarity
- [ ] I2C devices have unique addresses
- [ ] All ground connections are properly made
- [ ] 4-20mA loops are properly terminated
- [ ] Optoisolator orientations are correct (check LED polarity)
- [ ] Current limiting resistors are in place
- [ ] No short circuits (use multimeter to check)
- [ ] All connections are secure (no loose wires)
- [ ] Documentation is complete (wire labels, diagrams)

---

## Testing Procedure

### Step 1: Test I2C Devices

```bash
# Power on Pi only (no 24V yet)
sudo i2cdetect -y 1

# Should show:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
# 60: 60 61 -- -- -- -- -- -- -- -- -- -- -- -- -- --

# 0x48 = ADS1115
# 0x60, 0x61 = MCP4725s
```

### Step 2: Test Digital Outputs

```python
# Test GPIO outputs
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(6, GPIO.OUT)

GPIO.output(6, True)   # Should light up optoisolator LED
GPIO.output(6, False)  # LED should turn off
```

### Step 3: Test Analog Outputs

```python
# Test DAC output
from adafruit_mcp4725 import MCP4725
import board, busio

i2c = busio.I2C(board.SCL, board.SDA)
dac = MCP4725(i2c, address=0x60)

# Set to 12mA
dac.normalized_value = 0.5  # (12-4)/(20-4) = 0.5

# Measure with multimeter at PLC AI terminals
# Should read approximately 12mA
```

### Step 4: Apply 24V and Test Full System

```bash
# Run the simulator
python run.py

# Check web interface
# All instruments should show in dashboard

# Test PLC I/O
# Toggle PLC outputs and verify Pi inputs change
# Verify Pi outputs control PLC inputs correctly
```

---

## Troubleshooting

### I2C Device Not Detected

1. Check wiring: SDA, SCL, VCC, GND
2. Verify 3.3V power supply
3. Check I2C address configuration (ADDR pins)
4. Try different I2C addresses
5. Check for short circuits on I2C bus

### 4-20mA Output Incorrect

1. Measure DAC output voltage (should be 0-3.3V)
2. Check transistor connections (E, B, C)
3. Verify resistor values
4. Check loop power supply (24V)
5. Use multimeter in series to measure current

### Digital I/O Not Working

1. Check optoisolator orientation (LED polarity)
2. Verify resistor values
3. Test optoisolator with known good circuit
4. Check for correct voltage levels
5. Verify ground connections

### GPIO Damage Prevention

**Never:**
- Connect 24V directly to GPIO
- Exceed 3.3V on GPIO pins
- Draw more than 16mA from single GPIO
- Connect inductive loads without flyback diodes

**Always:**
- Use optoisolators for PLC interface
- Add current limiting resistors
- Test with multimeter before connecting
- Double-check polarity

---

## Bill of Materials

### Complete Starter Kit (1 Pump, 1 Tank, 1 Flow)

| Item | Qty | Unit Price | Total | Notes |
|------|-----|-----------|-------|-------|
| Raspberry Pi 4 (4GB) | 1 | $55 | $55 | Main controller |
| MCP4725 Breakout | 2 | $6 | $12 | Analog outputs |
| ADS1115 Breakout | 1 | $15 | $15 | Analog inputs |
| PC817 Optocoupler | 10 | $0.20 | $2 | Digital isolation |
| LM358 Op-Amp | 2 | $0.50 | $1 | 4-20mA converter |
| 2N3904 Transistor | 2 | $0.10 | $0.20 | Current driver |
| Resistor kit | 1 | $10 | $10 | Various values |
| Terminal blocks | 1 set | $15 | $15 | Wiring connections |
| 24V 2A Power Supply | 1 | $12 | $12 | PLC interface |
| Prototype board | 1 | $5 | $5 | Circuit assembly |
| Wire (22AWG) | 50ft | $10 | $10 | Connections |
| DIN rail kit | 1 | $20 | $20 | Mounting (optional) |
| **Total** | | | **$157.20** | |

### Alternative: Using Commercial Modules

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Raspberry Pi 4 | 1 | $55 | $55 |
| 8-CH Opto Input Module | 1 | $25 | $25 |
| 8-CH Relay Output Module | 1 | $15 | $15 |
| XY-WDV 4-20mA Module | 2 | $8 | $16 |
| ADS1115 Breakout | 1 | $15 | $15 |
| **Total** | | | **$126** |

Easier assembly, less soldering!

---

## Additional Resources

- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
- [MCP4725 Datasheet](https://www.microchip.com/en-us/product/MCP4725)
- [ADS1115 Datasheet](https://www.ti.com/product/ADS1115)
- [PC817 Datasheet](https://www.mouser.com/datasheet/2/348/pc817-e-260560.pdf)
- [4-20mA Loop Basics](https://www.analog.com/media/en/training-seminars/tutorials/MT-085.pdf)

---

**Document Version:** 1.0
**Last Updated:** 2026-02-28
**Repository:** https://github.com/abelone91/Instrum_sim.git
