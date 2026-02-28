# Quick Wiring Guide - Visual Summary

## At-a-Glance Connection Overview

### 1. I2C Devices (All share same bus)

```
Raspberry Pi GPIO Header
┌─────────────────────────┐
│ Pin 1  (3.3V)  ●────────┼──┐
│ Pin 3  (SDA)   ●────────┼──┼──┐
│ Pin 5  (SCL)   ●────────┼──┼──┼──┐
│ Pin 9  (GND)   ●────────┼──┼──┼──┼──┐
└─────────────────────────┘  │  │  │  │
                             │  │  │  │
    ┌────────────────────────┘  │  │  │
    │  ┌────────────────────────┘  │  │
    │  │  ┌────────────────────────┘  │
    │  │  │  ┌────────────────────────┘
    │  │  │  │
    V  S  S  G
    C  D  C  N
    C  A  L  D
    ↓  ↓  ↓  ↓
┌───┴──┴──┴──┴────┐  ┌───────────┐  ┌───────────┐
│ MCP4725 DAC #1  │  │  MCP4725  │  │ ADS1115   │
│ Addr: 0x60      │  │  DAC #2   │  │ ADC #1    │
│                 │  │  0x61     │  │  0x48     │
│ OUT→ 4-20mA→PLC │  │  OUT→PLC  │  │  A0←PLC   │
└─────────────────┘  └───────────┘  └───────────┘
```

**Shopping List:**
- MCP4725 Breakout: [Adafruit #935](https://www.adafruit.com/product/935) - $5.95 each
- ADS1115 Breakout: [Adafruit #1085](https://www.adafruit.com/product/1085) - $14.95 each

---

### 2. Digital Input (PLC → Pi)

```
        PLC Digital Output              Raspberry Pi
            (24VDC)
┌───────────────────┐                ┌──────────────┐
│                   │                │              │
│  Terminal DO1+    ├──[1kΩ]──┬─────┤              │
│  (24V when ON)    │          │     │              │
│                   │        ┌─▼─┐   │              │
│                   │     1→─┤●●●├─4 │              │
│                   │        │PC │   ├──────► GPIO5 │
│                   │        │817│   │              │
│  Terminal DO1-    │     2──┤●●●├─3 │              │
│  (GND)            ├────────┤   ├───┼──[10kΩ]     │
│                   │        └───┘   │    ↓         │
└───────────────────┘                │   GND        │
                                     └──────────────┘

Repeat for each digital input needed.
```

**Parts per channel:**
- PC817 Optocoupler: $0.20
- 1kΩ resistor (1/4W): $0.01
- 10kΩ resistor (1/4W): $0.01

**Pre-made solution:**
- 8-Channel Optoisolator Module: $25 (includes all resistors)

---

### 3. Digital Output (Pi → PLC)

```
  Raspberry Pi                         PLC Digital Input
                                           (24VDC)
┌──────────────┐                   ┌──────────────────┐
│              │                   │                  │
│  GPIO6       ├──[470Ω]──┬────────┤                  │
│              │           │        │                  │
│              │         ┌─▼─┐      │                  │
│              │      1→─┤●●●├─4    │                  │
│              │         │PC │      ├──[10kΩ]─► DI1+  │
│              │         │817│      │    ↑             │
│  3.3V        │      2──┤●●●├─3    │   24V            │
│              ├─────────┤   ├──────┤                  │
│              │         └───┘      │   DI1- (Common)  │
└──────────────┘                    └──────────────────┘

When GPIO6 = HIGH: PLC sees LOW (0V)
When GPIO6 = LOW:  PLC sees HIGH (24V)
```

**Alternative:** Relay Module
- 8-Channel 5V Relay Module: $15
- No resistors needed
- Can switch AC or DC
- Built-in LEDs

---

### 4. 4-20mA Output (Easiest Method)

```
Raspberry Pi I2C → MCP4725 → Commercial Module → PLC Analog Input
                     DAC       (XY-WDV)
┌──────┐         ┌────────┐  ┌─────────┐      ┌──────┐
│ SDA  ├─────────┤ SDA    │  │ Vi+ ◄───┤OUT   │ AI+  │
│ SCL  ├─────────┤ SCL    │  │ Vi- ◄───┤GND   │      │
│ 3.3V ├─────────┤ VCC    │  │         │      │      │
│ GND  ├─────────┤ GND    │  │ VCC ◄───┤24V   │      │
│      │         │        │  │ GND     │      │      │
│      │         │    OUT ├──► (0-3.3V)│      │      │
│      │         │        │  │         │      │      │
│      │         │        │  │ Io+ ────┼──────► AI+  │
│      │         │        │  │ Io- ────┼──────► AI-  │
└──────┘         └────────┘  └─────────┘      └──────┘

Module adjusts 0-3.3V input to 4-20mA output
```

**Recommended:**
- XY-WDV Module: $8 on eBay/Amazon
- No soldering required
- Pre-calibrated
- Just plug and play!

---

### 5. 4-20mA Input (Safe for ADS1115)

```
    PLC Analog Output              ADS1115 ADC
        (4-20mA)
┌──────────────────┐            ┌──────────────┐
│                  │            │              │
│  AO1+ ───────────┼───┬────────┤ A0           │
│  (4-20mA)        │   │        │              │
│                  │  [150Ω]    │  VCC ◄── 3.3V│
│                  │   │        │  GND ◄── GND │
│                  │   ├────┬───┤  SDA ◄── SDA │
│                  │   │    │   │  SCL ◄── SCL │
│                  │  [150Ω]│   │              │
│  AO1- (Common)   │   │    │   └──────────────┘
│                  ├───┴────┘
└──────────────────┘   GND

4mA × 150Ω = 0.6V  ✓ Safe
20mA × 150Ω = 3.0V ✓ Safe (< 4.096V max)
```

**Parts:**
- 2× 150Ω resistors (1%, 1/4W): $0.20 total

---

## Shopping Cart - Complete Starter Kit

### Option A: DIY (Cheapest, requires soldering)

| Item | Qty | Price | Link |
|------|-----|-------|------|
| Raspberry Pi 4 (4GB) | 1 | $55 | Adafruit/Amazon |
| MCP4725 Breakout | 2 | $12 | Adafruit #935 |
| ADS1115 Breakout | 1 | $15 | Adafruit #1085 |
| PC817 (pack of 10) | 1 | $2 | eBay |
| Resistor kit | 1 | $10 | Amazon |
| Breadboard | 1 | $5 | Amazon |
| Jumper wires | 1 | $8 | Amazon |
| 24V Power Supply | 1 | $12 | Amazon |
| **Total** | | **$119** | |

### Option B: Modules (Easiest, plug-and-play)

| Item | Qty | Price | Link |
|------|-----|-------|------|
| Raspberry Pi 4 (4GB) | 1 | $55 | Adafruit/Amazon |
| 8-CH Opto Input Module | 1 | $25 | Amazon |
| 8-CH Relay Module | 1 | $15 | Amazon |
| XY-WDV 4-20mA Module | 2 | $16 | eBay/Amazon |
| ADS1115 Breakout | 1 | $15 | Adafruit #1085 |
| Dupont cables | 1 | $10 | Amazon |
| 24V Power Supply | 1 | $12 | Amazon |
| **Total** | | **$148** | |

**Recommendation:** Option B for production use!

---

## Pin Allocation Example

### Recommended GPIO Assignment

| BCM Pin | Function | Instrument | Signal |
|---------|----------|------------|--------|
| **I2C Bus** | | | |
| GPIO2 (Pin 3) | SDA | All I2C | Data |
| GPIO3 (Pin 5) | SCL | All I2C | Clock |
| **Digital Inputs** | | | |
| GPIO5 (Pin 29) | Input | Pump | Enable |
| GPIO7 (Pin 26) | Input | Valve | Open Cmd |
| GPIO8 (Pin 24) | Input | Valve | Close Cmd |
| GPIO23 (Pin 16) | Input | Flow | Start |
| GPIO24 (Pin 18) | Input | Flow | Reset |
| **Digital Outputs** | | | |
| GPIO6 (Pin 31) | Output | Pump | Running |
| GPIO13 (Pin 33) | Output | Pump | Fault |
| GPIO16 (Pin 36) | Output | Valve | Position |
| GPIO17 (Pin 11) | Output | Tank | HH Alarm |
| GPIO27 (Pin 13) | Output | Flow | Pulse A |
| GPIO22 (Pin 15) | Output | Flow | Pulse B |
| **I2C Addresses** | | | |
| 0x60 | MCP4725 | Tank | Level (4-20mA) |
| 0x61 | MCP4725 | Pump | Speed (4-20mA) |
| 0x48 | ADS1115 | Pump | Setpoint Input |

---

## 5-Minute Quick Start

### Step 1: Connect I2C Devices (3 min)

```bash
# All devices connect to same 4 pins:
Pin 1 (3.3V) → All VCC pins
Pin 3 (SDA)  → All SDA pins
Pin 5 (SCL)  → All SCL pins
Pin 9 (GND)  → All GND pins
```

### Step 2: Test I2C (1 min)

```bash
sudo i2cdetect -y 1
# Should show: 48, 60, 61 (or your addresses)
```

### Step 3: Connect ONE optoisolator (1 min)

```bash
# Test digital input:
PLC DO+ → [1kΩ] → PC817 pin 1
PLC DO- → PC817 pin 2
PC817 pin 4 → GPIO5
PC817 pin 3 → [10kΩ] → GND
```

### Step 4: Run Simulator

```bash
python run.py
# Open browser: http://localhost:8000
```

---

## Common Mistakes to Avoid

❌ **DON'T:**
- Connect 24V directly to GPIO (will destroy Pi!)
- Exceed 3.3V on any GPIO pin
- Forget current limiting resistors
- Mix up optoisolator pin numbers
- Use I2C address twice

✓ **DO:**
- Always use optoisolators for PLC interface
- Double-check voltage levels with multimeter
- Test one connection at a time
- Label all wires
- Keep wiring diagram handy

---

## Wiring Color Code (Recommended)

```
Red    → +24V (PLC power)
Black  → GND (common ground)
Blue   → Digital signals
Yellow → Analog signals (4-20mA)
Green  → I2C SDA
White  → I2C SCL
Orange → 3.3V
```

---

## Support & Resources

- **Full Wiring Diagrams:** See `docs/WIRING_DIAGRAMS.md`
- **Hardware Setup:** See `docs/SETUP.md`
- **Repository:** https://github.com/abelone91/Instrum_sim.git

---

## Emergency Contact Info

**If something smokes or smells:**
1. Immediately disconnect power
2. Check for short circuits with multimeter
3. Verify all connections match diagrams
4. Replace damaged components
5. Test with multimeter before reconnecting

**Raspberry Pi Replacement:**
- If GPIO damaged, Pi may still boot but GPIO won't work
- Cost: ~$55 for new Pi 4
- Prevention: Always use optoisolators!

---

**Document Version:** 1.0
**For:** Raspberry Pi PLC Simulator
**Last Updated:** 2026-02-28
