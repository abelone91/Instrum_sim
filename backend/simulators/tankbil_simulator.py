"""
Tank Truck (Tankbil) Simulator
Simulates safety interlock system for tank truck loading/unloading.
"""
import logging
from typing import Dict, Any
from .base import BaseSimulator, IOPin

logger = logging.getLogger(__name__)

class TankbilSimulator(BaseSimulator):
    """
    Simulates tank truck safety interlock system.

    Inputs (from PLC):
    - Grounding OK: Digital input (earth connection verified)
    - Overfill OK: Digital input (overfill sensor OK)
    - Dead man button: Digital input (operator present)

    Outputs (to PLC):
    - Test ground: Digital output (initiate ground test)
    - Test overfill: Digital output (initiate overfill test)
    - Dead man warning: Digital output (operator must press button)

    Configuration:
    - Dead man enabled: Yes/No

    State:
    - Grounding OK
    - Overfill OK
    - Dead man active
    - System safe (all interlocks OK)
    """

    def _load_config(self, config: Dict[str, Any]):
        """Load tankbil configuration"""
        self.deadman_enabled = config.get('deadman_enabled', True)

        # Initialize state
        self.state = {
            'ground_ok': False,
            'overfill_ok': False,
            'deadman_pressed': False,
            'test_ground_cmd': False,
            'test_overfill_cmd': False,
            'deadman_warning': False,
            'system_safe': False,
            'deadman_timer': 0.0  # Time since last deadman press
        }

    def update(self, delta_time: float):
        """Update tankbil interlock state"""
        with self.update_lock:
            # Update deadman timer
            if self.deadman_enabled:
                if self.state['deadman_pressed']:
                    self.state['deadman_timer'] = 0.0
                else:
                    self.state['deadman_timer'] += delta_time

                # Issue warning if deadman not pressed for >2 seconds
                self.state['deadman_warning'] = self.state['deadman_timer'] > 2.0
            else:
                self.state['deadman_warning'] = False
                self.state['deadman_timer'] = 0.0

            # Determine if system is safe for operation
            ground_safe = self.state['ground_ok']
            overfill_safe = self.state['overfill_ok']
            deadman_safe = not self.deadman_enabled or (self.state['deadman_timer'] < 5.0)

            self.state['system_safe'] = ground_safe and overfill_safe and deadman_safe

    def read_inputs(self, gpio_driver, adc_drivers: Dict[int, Any]):
        """Read tankbil safety inputs"""
        with self.update_lock:
            if 'ground_ok_input' in self.io_pins:
                pin = self.io_pins['ground_ok_input']
                if pin.pin_number is not None:
                    self.state['ground_ok'] = gpio_driver.read(pin.pin_number)

            if 'overfill_ok_input' in self.io_pins:
                pin = self.io_pins['overfill_ok_input']
                if pin.pin_number is not None:
                    self.state['overfill_ok'] = gpio_driver.read(pin.pin_number)

            if 'deadman_input' in self.io_pins and self.deadman_enabled:
                pin = self.io_pins['deadman_input']
                if pin.pin_number is not None:
                    self.state['deadman_pressed'] = gpio_driver.read(pin.pin_number)

    def write_outputs(self, gpio_driver, dac_drivers: Dict[int, Any]):
        """Write tankbil test and warning outputs"""
        with self.update_lock:
            # Test ground output
            if 'test_ground_output' in self.io_pins:
                pin = self.io_pins['test_ground_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['test_ground_cmd'])

            # Test overfill output
            if 'test_overfill_output' in self.io_pins:
                pin = self.io_pins['test_overfill_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['test_overfill_cmd'])

            # Deadman warning output
            if 'deadman_warning_output' in self.io_pins:
                pin = self.io_pins['deadman_warning_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['deadman_warning'])

    def get_display_data(self) -> Dict[str, Any]:
        """Get data for web UI display"""
        return {
            'id': self.id,
            'type': 'tankbil',
            'ground_ok': self.state['ground_ok'],
            'overfill_ok': self.state['overfill_ok'],
            'deadman_pressed': self.state['deadman_pressed'],
            'deadman_warning': self.state['deadman_warning'],
            'system_safe': self.state['system_safe'],
            'deadman_timer': round(self.state['deadman_timer'], 1),
            'config': {
                'deadman_enabled': self.deadman_enabled
            }
        }

    def trigger_test_ground(self):
        """Trigger ground test sequence"""
        self.state['test_ground_cmd'] = True

    def trigger_test_overfill(self):
        """Trigger overfill test sequence"""
        self.state['test_overfill_cmd'] = True
