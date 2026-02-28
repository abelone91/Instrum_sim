"""
Pump Simulator
Simulates a centrifugal pump with pressure and flow control.
"""
import logging
from typing import Dict, Any
from .base import BaseSimulator, IOPin

logger = logging.getLogger(__name__)

class PumpSimulator(BaseSimulator):
    """
    Simulates a pump with pressure and flow output.

    Inputs (from PLC):
    - Enable/Start: Digital input
    - Speed control: Analog input (if analog control)

    Outputs (to PLC):
    - Running: Digital output
    - Fault: Digital output
    - Feedback: Analog output (speed/pressure)

    Links to:
    - Reg Valve: Reads back-pressure
    - Flowmeter: Reads actual flow

    Configuration:
    - Control type: Digital/Analog
    - Max pressure (bar)
    - Set pressure (bar)
    - Max flow (L/min)
    - Ramp time (seconds)

    State:
    - Running
    - Current pressure
    - Current flow
    - Fault status
    """

    def _load_config(self, config: Dict[str, Any]):
        """Load pump configuration"""
        self.control_type = config.get('control_type', 'digital')  # 'digital' or 'analog'
        self.max_pressure_bar = config.get('max_pressure_bar', 10.0)
        self.set_pressure_bar = config.get('set_pressure_bar', 8.0)
        self.max_flow_lpm = config.get('max_flow_lpm', 100.0)
        self.ramp_time_sec = config.get('ramp_time_sec', 5.0)

        # Initialize state
        self.state = {
            'running': False,
            'enable_cmd': False,
            'speed_cmd_percent': 0.0,  # For analog control
            'current_speed_percent': 0.0,
            'pressure_bar': 0.0,
            'flow_lpm': 0.0,
            'fault': False
        }

    def update(self, delta_time: float):
        """Update pump state"""
        with self.update_lock:
            enable = self.state['enable_cmd']
            target_speed = 100.0 if self.control_type == 'digital' else self.state['speed_cmd_percent']

            if not enable:
                target_speed = 0.0

            # Ramp speed
            current_speed = self.state['current_speed_percent']
            ramp_rate = (100.0 / self.ramp_time_sec) * delta_time

            if current_speed < target_speed:
                self.state['current_speed_percent'] = min(target_speed, current_speed + ramp_rate)
            elif current_speed > target_speed:
                self.state['current_speed_percent'] = max(target_speed, current_speed - ramp_rate)

            # Update running status
            self.state['running'] = self.state['current_speed_percent'] > 1.0

            # Calculate pressure and flow
            speed_factor = self.state['current_speed_percent'] / 100.0

            # Get back-pressure from linked reg valve
            back_pressure = self.get_linked_value('reg_valve', 'pressure_bar') or 0.0

            # Pressure increases with speed, decreases with back-pressure
            self.state['pressure_bar'] = (self.set_pressure_bar * speed_factor) - (back_pressure * 0.5)
            self.state['pressure_bar'] = max(0.0, min(self.max_pressure_bar, self.state['pressure_bar']))

            # Flow depends on pressure differential
            pressure_diff = self.state['pressure_bar'] - back_pressure
            if pressure_diff > 0:
                self.state['flow_lpm'] = min(self.max_flow_lpm,
                                             (pressure_diff / self.max_pressure_bar) * self.max_flow_lpm * speed_factor)
            else:
                self.state['flow_lpm'] = 0.0

            # Simple fault detection (overpressure)
            self.state['fault'] = self.state['pressure_bar'] >= self.max_pressure_bar

    def read_inputs(self, gpio_driver, adc_drivers: Dict[int, Any]):
        """Read pump control inputs"""
        with self.update_lock:
            # Read enable/start digital input
            if 'enable_input' in self.io_pins:
                pin = self.io_pins['enable_input']
                if pin.pin_number is not None:
                    self.state['enable_cmd'] = gpio_driver.read(pin.pin_number)

            # Read analog speed control
            if self.control_type == 'analog' and 'speed_input' in self.io_pins:
                pin = self.io_pins['speed_input']
                if pin.i2c_address in adc_drivers:
                    adc = adc_drivers[pin.i2c_address]
                    voltage = adc.read_voltage(pin.channel or 0)
                    # 0-10V -> 0-100%
                    self.state['speed_cmd_percent'] = (voltage / 10.0) * 100.0

    def write_outputs(self, gpio_driver, dac_drivers: Dict[int, Any]):
        """Write pump status outputs"""
        with self.update_lock:
            # Running digital output
            if 'running_output' in self.io_pins:
                pin = self.io_pins['running_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['running'])

            # Fault digital output
            if 'fault_output' in self.io_pins:
                pin = self.io_pins['fault_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['fault'])

            # Feedback analog output (4-20mA representing speed or pressure)
            if 'feedback_output' in self.io_pins:
                pin = self.io_pins['feedback_output']
                if pin.i2c_address in dac_drivers:
                    dac = dac_drivers[pin.i2c_address]
                    # Send current speed as 4-20mA
                    feedback_percent = self.state['current_speed_percent']
                    current_ma = 4.0 + (feedback_percent / 100.0) * 16.0
                    dac.set_current_ma(current_ma)

    def get_display_data(self) -> Dict[str, Any]:
        """Get data for web UI display"""
        return {
            'id': self.id,
            'type': 'pump',
            'running': self.state['running'],
            'speed_percent': round(self.state['current_speed_percent'], 1),
            'pressure_bar': round(self.state['pressure_bar'], 2),
            'flow_lpm': round(self.state['flow_lpm'], 2),
            'fault': self.state['fault'],
            'enable_cmd': self.state['enable_cmd'],
            'config': {
                'control_type': self.control_type,
                'max_pressure_bar': self.max_pressure_bar,
                'set_pressure_bar': self.set_pressure_bar,
                'max_flow_lpm': self.max_flow_lpm,
                'ramp_time_sec': self.ramp_time_sec
            }
        }
