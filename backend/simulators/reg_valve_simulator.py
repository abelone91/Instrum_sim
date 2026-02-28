"""
Regulating Valve Simulator
Simulates a modulating control valve with analog positioning.
"""
import logging
from typing import Dict, Any
from .base import BaseSimulator, IOPin

logger = logging.getLogger(__name__)

class RegValveSimulator(BaseSimulator):
    """
    Simulates a regulating (modulating) valve with analog control.

    Inputs (from PLC):
    - Open command: Digital input (for LVRA/LVRD)
    - Hold command: Digital input
    - Position setpoint: Analog input (0-10V or 4-20mA)

    Outputs (to PLC):
    - Closed limit: Digital output
    - Position feedback: Analog output (4-20mA)

    Links to:
    - Flowmeter: Affects flow based on position

    Configuration:
    - Type: LVRA (raise to open) / LVRD (raise to close)
    - Open speed (seconds)
    - Close speed (seconds)
    - 20% signal: Enable/disable minimum position
    - Feedback type: Closed limit switch / Analog position

    State:
    - Position: 0-100%
    - Setpoint: 0-100%
    - Status
    """

    def _load_config(self, config: Dict[str, Any]):
        """Load reg valve configuration"""
        self.valve_type = config.get('valve_type', 'LVRA')  # 'LVRA' or 'LVRD'
        self.open_speed_sec = config.get('open_speed_sec', 10.0)
        self.close_speed_sec = config.get('close_speed_sec', 10.0)
        self.min_position_20_pct = config.get('min_position_20_pct', False)
        self.feedback_type = config.get('feedback_type', 'analog')  # 'switch' or 'analog'

        # Initialize state
        self.state = {
            'position_percent': 0.0,  # Actual valve position
            'setpoint_percent': 0.0,  # Commanded position
            'open_cmd': False,
            'hold_cmd': False,
            'at_closed_limit': True,
            'pressure_bar': 0.0  # Pressure drop across valve
        }

    def update(self, delta_time: float):
        """Update valve position to track setpoint"""
        with self.update_lock:
            target = self.state['setpoint_percent']

            # Apply 20% minimum if enabled
            if self.min_position_20_pct and target > 0:
                target = max(20.0, target)

            # Handle hold command
            if self.state['hold_cmd']:
                return

            # Ramp position towards setpoint
            current_pos = self.state['position_percent']

            if current_pos < target:
                # Opening
                delta = (100.0 / self.open_speed_sec) * delta_time
                self.state['position_percent'] = min(target, current_pos + delta)
            elif current_pos > target:
                # Closing
                delta = (100.0 / self.close_speed_sec) * delta_time
                self.state['position_percent'] = max(target, current_pos - delta)

            # Update limit switch
            self.state['at_closed_limit'] = self.state['position_percent'] < 5.0

            # Calculate pressure drop (simple model)
            # More open = less pressure drop
            # Cv = flow coefficient increases with position
            position_factor = self.state['position_percent'] / 100.0
            if position_factor > 0:
                # Pressure drop inversely proportional to position
                self.state['pressure_bar'] = 2.0 * (1.0 - position_factor)
            else:
                self.state['pressure_bar'] = 10.0  # Fully closed = max pressure drop

    def read_inputs(self, gpio_driver, adc_drivers: Dict[int, Any]):
        """Read valve control inputs"""
        with self.update_lock:
            # Read digital open command
            if 'open_input' in self.io_pins:
                pin = self.io_pins['open_input']
                if pin.pin_number is not None:
                    self.state['open_cmd'] = gpio_driver.read(pin.pin_number)

            # Read digital hold command
            if 'hold_input' in self.io_pins:
                pin = self.io_pins['hold_input']
                if pin.pin_number is not None:
                    self.state['hold_cmd'] = gpio_driver.read(pin.pin_number)

            # Read analog position setpoint
            if 'position_input' in self.io_pins:
                pin = self.io_pins['position_input']
                if pin.i2c_address in adc_drivers:
                    adc = adc_drivers[pin.i2c_address]

                    # Read as 4-20mA or 0-10V
                    voltage = adc.read_voltage(pin.channel or 0)

                    # Assume 0-10V input maps to 0-100%
                    self.state['setpoint_percent'] = (voltage / 10.0) * 100.0
                    self.state['setpoint_percent'] = max(0.0, min(100.0, self.state['setpoint_percent']))

    def write_outputs(self, gpio_driver, dac_drivers: Dict[int, Any]):
        """Write valve feedback outputs"""
        with self.update_lock:
            # Closed limit digital output
            if 'closed_limit_output' in self.io_pins:
                pin = self.io_pins['closed_limit_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['at_closed_limit'])

            # Analog position feedback (4-20mA)
            if 'position_output' in self.io_pins:
                pin = self.io_pins['position_output']
                if pin.i2c_address in dac_drivers:
                    dac = dac_drivers[pin.i2c_address]
                    position_pct = self.state['position_percent']
                    current_ma = 4.0 + (position_pct / 100.0) * 16.0
                    dac.set_current_ma(current_ma)

    def get_display_data(self) -> Dict[str, Any]:
        """Get data for web UI display"""
        return {
            'id': self.id,
            'type': 'reg_valve',
            'position_percent': round(self.state['position_percent'], 1),
            'setpoint_percent': round(self.state['setpoint_percent'], 1),
            'pressure_bar': round(self.state['pressure_bar'], 2),
            'at_closed_limit': self.state['at_closed_limit'],
            'config': {
                'valve_type': self.valve_type,
                'open_speed_sec': self.open_speed_sec,
                'close_speed_sec': self.close_speed_sec,
                'min_position_20_pct': self.min_position_20_pct
            }
        }
