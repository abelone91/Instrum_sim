"""
Valve Simulator
Simulates an on/off valve with open/close/hold control.
"""
import logging
from typing import Dict, Any
from .base import BaseSimulator, IOPin

logger = logging.getLogger(__name__)

class ValveSimulator(BaseSimulator):
    """
    Simulates a digital on/off valve.

    Inputs (from PLC):
    - Open valve: Digital input
    - Close valve: Digital input
    - Hold valve: Digital input (if hold solenoid enabled)

    Configuration:
    - Open speed (seconds to fully open)
    - Close speed (seconds to fully close)
    - Hold solenoid: Yes/No
    - Return spring: Yes/No
    - Type: Import/Export (visual only)

    State:
    - Position: 0-100%
    - Status: 'closed', 'opening', 'open', 'closing', 'hold'
    """

    def _load_config(self, config: Dict[str, Any]):
        """Load valve configuration"""
        self.open_speed_sec = config.get('open_speed_sec', 5.0)
        self.close_speed_sec = config.get('close_speed_sec', 5.0)
        self.has_hold_solenoid = config.get('has_hold_solenoid', False)
        self.has_return_spring = config.get('has_return_spring', False)
        self.valve_type = config.get('valve_type', 'import')  # 'import' or 'export'

        # Initialize state
        self.state = {
            'position_percent': 0.0,  # 0 = closed, 100 = open
            'status': 'closed',  # 'closed', 'opening', 'open', 'closing', 'hold'
            'open_cmd': False,
            'close_cmd': False,
            'hold_cmd': False
        }

    def update(self, delta_time: float):
        """Update valve position based on commands"""
        with self.update_lock:
            open_cmd = self.state['open_cmd']
            close_cmd = self.state['close_cmd']
            hold_cmd = self.state['hold_cmd']
            position = self.state['position_percent']

            # Determine action
            if hold_cmd and self.has_hold_solenoid:
                # Hold current position
                self.state['status'] = 'hold'

            elif open_cmd and not close_cmd:
                # Opening
                if position < 100.0:
                    delta_pos = (100.0 / self.open_speed_sec) * delta_time
                    self.state['position_percent'] = min(100.0, position + delta_pos)
                    self.state['status'] = 'opening'
                else:
                    self.state['status'] = 'open'

            elif close_cmd and not open_cmd:
                # Closing
                if position > 0.0:
                    delta_pos = (100.0 / self.close_speed_sec) * delta_time
                    self.state['position_percent'] = max(0.0, position - delta_pos)
                    self.state['status'] = 'closing'
                else:
                    self.state['status'] = 'closed'

            elif self.has_return_spring and not open_cmd:
                # Return spring closes valve when no open command
                if position > 0.0:
                    delta_pos = (100.0 / self.close_speed_sec) * delta_time
                    self.state['position_percent'] = max(0.0, position - delta_pos)
                    self.state['status'] = 'closing'
                else:
                    self.state['status'] = 'closed'

            else:
                # No active command, maintain position
                if position >= 99.0:
                    self.state['status'] = 'open'
                elif position <= 1.0:
                    self.state['status'] = 'closed'
                else:
                    self.state['status'] = 'hold'

    def read_inputs(self, gpio_driver, adc_drivers: Dict[int, Any]):
        """Read valve command inputs from PLC"""
        with self.update_lock:
            if 'open_input' in self.io_pins:
                pin = self.io_pins['open_input']
                if pin.pin_number is not None:
                    self.state['open_cmd'] = gpio_driver.read(pin.pin_number)

            if 'close_input' in self.io_pins:
                pin = self.io_pins['close_input']
                if pin.pin_number is not None:
                    self.state['close_cmd'] = gpio_driver.read(pin.pin_number)

            if 'hold_input' in self.io_pins and self.has_hold_solenoid:
                pin = self.io_pins['hold_input']
                if pin.pin_number is not None:
                    self.state['hold_cmd'] = gpio_driver.read(pin.pin_number)

    def write_outputs(self, gpio_driver, dac_drivers: Dict[int, Any]):
        """Valve simulator has no outputs (actuator only)"""
        pass

    def get_display_data(self) -> Dict[str, Any]:
        """Get data for web UI display"""
        return {
            'id': self.id,
            'type': 'valve',
            'position_percent': round(self.state['position_percent'], 1),
            'status': self.state['status'],
            'open_cmd': self.state['open_cmd'],
            'close_cmd': self.state['close_cmd'],
            'hold_cmd': self.state['hold_cmd'],
            'config': {
                'open_speed_sec': self.open_speed_sec,
                'close_speed_sec': self.close_speed_sec,
                'has_hold_solenoid': self.has_hold_solenoid,
                'has_return_spring': self.has_return_spring,
                'valve_type': self.valve_type
            }
        }
