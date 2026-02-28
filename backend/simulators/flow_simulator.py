"""
Flow Meter Simulator
Simulates a turbine/pulse flowmeter with quadrature output.
"""
import logging
from typing import Dict, Any
import random
import math
from .base import BaseSimulator, IOPin

logger = logging.getLogger(__name__)

class FlowSimulator(BaseSimulator):
    """
    Simulates a flow meter with pulse outputs.

    Inputs:
    - Reset counter: Digital input (pulse)
    - Noise enable: Digital input
    - Start pulses: Digital input
    - Flow rate: Slider/setting (can be linked to pump/valve)

    Outputs:
    - Pulse A: Digital output
    - Pulse B: Digital output (90° phase shifted for quadrature)

    Links to:
    - Reg Valve: Read pressure/position to affect flow
    - Pump: Read pump flow output

    Configuration:
    - Unit: L/sec or L/min
    - Pulse type: Single or quadrature (90°)
    - Velocity: m/s (affects pulse frequency)
    - Noise: Random pulse dropout (ms)
    - Pulses per liter

    State:
    - Current flow rate
    - Total volume
    - Pulse state
    """

    def _load_config(self, config: Dict[str, Any]):
        """Load flow meter configuration"""
        self.unit = config.get('unit', 'L/min')  # 'L/sec' or 'L/min'
        self.pulse_type = config.get('pulse_type', 'quadrature')  # 'single' or 'quadrature'
        self.velocity_ms = config.get('velocity_ms', 1.0)
        self.noise_enabled = config.get('noise_enabled', False)
        self.noise_dropout_ms = config.get('noise_dropout_ms', 10)
        self.pulses_per_liter = config.get('pulses_per_liter', 100)  # K-factor

        # Initialize state
        self.state = {
            'flow_lpm': 0.0,
            'total_volume_liters': 0.0,
            'total_mass_kg': 0.0,  # Assuming density ~1.0
            'pulse_a': False,
            'pulse_b': False,
            'start_enabled': False,
            'reset_cmd': False,
            'noise_cmd': False,
            'pulse_accumulator': 0.0,  # Sub-pulse accumulator
            'pulse_count': 0
        }

    def update(self, delta_time: float):
        """Update flow meter pulses"""
        with self.update_lock:
            if not self.state['start_enabled']:
                return

            # Get flow from linked instruments
            linked_flow = self.get_linked_value('pump', 'flow_lpm') or 0.0
            self.state['flow_lpm'] = linked_flow

            # Convert flow to liters/second
            if self.unit == 'L/sec':
                flow_lps = linked_flow / 60.0
            else:
                flow_lps = linked_flow / 60.0

            # Calculate volume increment
            delta_volume_liters = flow_lps * delta_time

            # Update total volume
            self.state['total_volume_liters'] += delta_volume_liters
            self.state['total_mass_kg'] = self.state['total_volume_liters']  # Assume density = 1.0

            # Calculate pulses
            delta_pulses = delta_volume_liters * self.pulses_per_liter
            self.state['pulse_accumulator'] += delta_pulses

            # Generate pulse outputs
            if self.state['pulse_accumulator'] >= 1.0:
                # Time to generate a pulse
                self.state['pulse_count'] += 1
                self.state['pulse_accumulator'] -= 1.0

                # Apply noise (random dropout)
                if self.state['noise_cmd'] and random.random() < 0.1:
                    # Drop this pulse
                    pass
                else:
                    # Toggle pulse outputs
                    if self.pulse_type == 'quadrature':
                        # Generate quadrature output (A and B 90° apart)
                        phase = (self.state['pulse_count'] % 4)
                        if phase == 0:
                            self.state['pulse_a'] = True
                            self.state['pulse_b'] = False
                        elif phase == 1:
                            self.state['pulse_a'] = True
                            self.state['pulse_b'] = True
                        elif phase == 2:
                            self.state['pulse_a'] = False
                            self.state['pulse_b'] = True
                        elif phase == 3:
                            self.state['pulse_a'] = False
                            self.state['pulse_b'] = False
                    else:
                        # Simple pulse train
                        self.state['pulse_a'] = not self.state['pulse_a']
                        self.state['pulse_b'] = self.state['pulse_a']

            # Handle reset
            if self.state['reset_cmd']:
                self.state['total_volume_liters'] = 0.0
                self.state['total_mass_kg'] = 0.0
                self.state['pulse_count'] = 0
                self.state['pulse_accumulator'] = 0.0
                self.state['reset_cmd'] = False

    def read_inputs(self, gpio_driver, adc_drivers: Dict[int, Any]):
        """Read flow meter control inputs"""
        with self.update_lock:
            if 'start_input' in self.io_pins:
                pin = self.io_pins['start_input']
                if pin.pin_number is not None:
                    self.state['start_enabled'] = gpio_driver.read(pin.pin_number)

            if 'reset_input' in self.io_pins:
                pin = self.io_pins['reset_input']
                if pin.pin_number is not None:
                    self.state['reset_cmd'] = gpio_driver.read(pin.pin_number)

            if 'noise_input' in self.io_pins:
                pin = self.io_pins['noise_input']
                if pin.pin_number is not None:
                    self.state['noise_cmd'] = gpio_driver.read(pin.pin_number)

    def write_outputs(self, gpio_driver, dac_drivers: Dict[int, Any]):
        """Write pulse outputs"""
        with self.update_lock:
            if 'pulse_a_output' in self.io_pins:
                pin = self.io_pins['pulse_a_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['pulse_a'])

            if 'pulse_b_output' in self.io_pins:
                pin = self.io_pins['pulse_b_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['pulse_b'])

    def get_display_data(self) -> Dict[str, Any]:
        """Get data for web UI display"""
        return {
            'id': self.id,
            'type': 'flow',
            'flow_lpm': round(self.state['flow_lpm'], 2),
            'total_volume_liters': round(self.state['total_volume_liters'], 2),
            'total_mass_kg': round(self.state['total_mass_kg'], 2),
            'pulse_count': self.state['pulse_count'],
            'start_enabled': self.state['start_enabled'],
            'config': {
                'unit': self.unit,
                'pulse_type': self.pulse_type,
                'velocity_ms': self.velocity_ms,
                'pulses_per_liter': self.pulses_per_liter
            }
        }
