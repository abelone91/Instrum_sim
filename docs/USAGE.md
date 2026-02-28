# PLC Instrument Simulator - Usage Guide

## Quick Start

### Starting the Simulator

```bash
cd simulator
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m backend.main
```

The simulator will:
1. Load configuration from `config/instruments.yaml`
2. Initialize all instruments
3. Start the simulation loop
4. Launch the web server on http://localhost:8000

### Web Interface

Open your browser to `http://localhost:8000` (or `http://<pi-ip>:8000` from another device)

The interface shows:
- **Status bar**: Connection status, simulation status, update rate
- **Control buttons**: Start/Stop simulation, Refresh data
- **Instrument cards**: Real-time display for each configured instrument

## Configuring Instruments

### Configuration File Structure

`config/instruments.yaml` defines all instruments:

```yaml
instruments:
  - id: unique_name        # Unique identifier
    type: level            # Instrument type
    parameters:            # Type-specific configuration
      tank_height_mm: 2000
      # ...
    io:                    # I/O pin allocation
      level_output:
        type: analog_out
        i2c_address: 0x60
    links:                 # Links to other instruments
      flowmeter: flow_01
```

### Instrument Types

#### 1. Level Simulator (`type: level`)

Simulates a tank with level measurement.

**Parameters:**
```yaml
parameters:
  tank_height_mm: 2000        # Total tank height
  height_100_percent: 2000    # Height for 100% reading
  height_hh_alarm: 1800       # High-high alarm setpoint
  tank_volume_m3: 10.0        # Total volume
```

**I/O:**
- `level_output` (analog_out): 4-20mA level signal
- `hh_alarm_output` (digital_out): High-high alarm

**Links:**
- `flowmeter`: Links to flow meter for filling/emptying

---

#### 2. Valve Simulator (`type: valve`)

Simulates an on/off valve.

**Parameters:**
```yaml
parameters:
  open_speed_sec: 5.0         # Time to fully open
  close_speed_sec: 5.0        # Time to fully close
  has_hold_solenoid: true     # Enable hold function
  has_return_spring: false    # Auto-close when power off
  valve_type: "import"        # Visual only
```

**I/O:**
- `open_input` (digital_in): Open command from PLC
- `close_input` (digital_in): Close command
- `hold_input` (digital_in): Hold position (if enabled)

---

#### 3. Pump Simulator (`type: pump`)

Simulates a centrifugal pump.

**Parameters:**
```yaml
parameters:
  control_type: "digital"     # "digital" or "analog"
  max_pressure_bar: 10.0      # Maximum pressure
  set_pressure_bar: 8.0       # Target pressure
  max_flow_lpm: 100.0         # Maximum flow rate
  ramp_time_sec: 5.0          # Startup ramp time
```

**I/O:**
- `enable_input` (digital_in): Start/enable pump
- `speed_input` (analog_in): Speed control (if analog)
- `running_output` (digital_out): Running status
- `fault_output` (digital_out): Fault alarm
- `feedback_output` (analog_out): Speed/pressure feedback

**Links:**
- `reg_valve`: Reads back-pressure

---

#### 4. Flow Simulator (`type: flow`)

Simulates a flow meter with pulse output.

**Parameters:**
```yaml
parameters:
  unit: "L/min"               # "L/sec" or "L/min"
  pulse_type: "quadrature"    # "single" or "quadrature"
  velocity_ms: 1.5            # Flow velocity
  noise_enabled: false        # Enable pulse dropout
  noise_dropout_ms: 10        # Dropout duration
  pulses_per_liter: 100       # K-factor
```

**I/O:**
- `pulse_a_output` (digital_out): Pulse train A
- `pulse_b_output` (digital_out): Pulse train B (quadrature)
- `start_input` (digital_in): Enable pulses
- `reset_input` (digital_in): Reset totalizer

**Links:**
- `pump`: Gets flow from pump output

---

#### 5. REG Valve Simulator (`type: reg_valve`)

Simulates a modulating control valve.

**Parameters:**
```yaml
parameters:
  valve_type: "LVRA"          # "LVRA" or "LVRD"
  open_speed_sec: 10.0        # Stroke time
  close_speed_sec: 10.0
  min_position_20_pct: false  # Enforce 20% minimum
  feedback_type: "analog"     # "analog" or "switch"
```

**I/O:**
- `position_input` (analog_in): Position setpoint (0-10V)
- `open_input` (digital_in): Digital open command
- `hold_input` (digital_in): Hold position
- `closed_limit_output` (digital_out): Closed limit switch
- `position_output` (analog_out): Position feedback

---

#### 6. Tankbil Simulator (`type: tankbil`)

Simulates tank truck safety interlock system.

**Parameters:**
```yaml
parameters:
  deadman_enabled: true       # Enable dead-man timer
```

**I/O:**
- `ground_ok_input` (digital_in): Grounding verified
- `overfill_ok_input` (digital_in): Overfill protection OK
- `deadman_input` (digital_in): Operator present button
- `test_ground_output` (digital_out): Test ground circuit
- `test_overfill_output` (digital_out): Test overfill sensor
- `deadman_warning_output` (digital_out): Press button warning

---

## Inter-Instrument Linking

Instruments can share data through links:

```yaml
- id: pump_01
  type: pump
  links:
    reg_valve: reg_valve_01   # Pump reads back-pressure from valve

- id: reg_valve_01
  type: reg_valve
  # Valve provides pressure data to pump
```

**Available Links:**
- Pump → Reg Valve: Back-pressure feedback
- Pump → Flow Meter: Flow output
- Flow Meter → Tank: Fill/empty tank
- Any → Any: Custom data sharing via `get_linked_value()`

## API Reference

### REST Endpoints

```
GET  /api/status                          # Simulator status
GET  /api/simulators                      # List all instruments
GET  /api/simulators/{id}                 # Get instrument details
GET  /api/data                            # Get all display data
GET  /api/data/{id}                       # Get instrument data
POST /api/simulators/{id}/parameter       # Set parameter
POST /api/control/start                   # Start simulation
POST /api/control/stop                    # Stop simulation
```

### WebSocket

Connect to `/ws` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'update') {
        // message.data contains all instrument data
    }
};
```

## Testing Without Hardware

The simulator automatically detects if it's running on Raspberry Pi hardware.

**On development machines:**
- GPIO and I2C are mocked
- Simulation works normally
- Web interface fully functional
- Perfect for testing configurations

**On Raspberry Pi:**
- Real hardware is used
- I/O pins are initialized
- Actual voltage/current signals generated

## Example Workflows

### Testing a Single Pump

1. Create simple config:
```yaml
instruments:
  - id: test_pump
    type: pump
    parameters:
      control_type: "digital"
      max_flow_lpm: 50.0
    io:
      enable_input:
        type: digital_in
        pin: 5
      running_output:
        type: digital_out
        pin: 6
```

2. Start simulator
3. Connect GPIO5 to 3.3V (simulate PLC enable)
4. Check GPIO6 for running output
5. Monitor in web interface

### Simulating a Tank Filling Process

1. Configure: Pump → Flow Meter → Tank
2. Link them in config
3. Start simulation
4. Enable pump (digital input)
5. Watch:
   - Flow meter generates pulses
   - Tank level rises
   - HH alarm triggers when tank is full

### Creating a Complete System

See `config/instruments.yaml` for a full example with:
- Tank level control
- Pump with pressure feedback
- Regulating valve
- Flow measurement
- Safety interlocks

## Customization

### Adding New Instrument Types

1. Create simulator class in `backend/simulators/`
2. Inherit from `BaseSimulator`
3. Implement required methods
4. Register in `config_manager.py`

### Modifying the Web Interface

Edit files in `frontend/`:
- `index.html`: Page structure
- `style.css`: Styling
- `app.js`: Logic and visualization

The interface auto-updates via WebSocket.

## Performance

- **Update rate**: 10 Hz (configurable in `simulation_engine.py`)
- **Simulators**: Tested with 20+ instruments
- **Latency**: <100ms for WebSocket updates
- **CPU usage**: ~5-10% on Raspberry Pi 4

## Troubleshooting

### Simulation Not Starting
- Check config file syntax (YAML)
- Verify I/O pin conflicts
- Check logs: `journalctl -u plc-simulator -f`

### Instruments Not Responding
- Verify links are correct
- Check I/O allocation
- Test hardware connections

### Web Interface Issues
- Clear browser cache
- Check WebSocket connection
- Verify network connectivity
