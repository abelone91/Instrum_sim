"""
Level (Tank) Simulator
Simulates a tank with level measurement and high-high alarm.
"""
import logging
from typing import Dict, Any
from .base import BaseSimulator, IOPin

logger = logging.getLogger(__name__)

class LevelSimulator(BaseSimulator):
    """
    Simulates a tank level sensor.

    Inputs:
    - Tank height parameters (config)
    - Flow from linked instruments (flowmeter)

    Outputs:
    - Level: 4-20mA analog output
    - HH-Alarm: Digital output

    State:
    - Current level (mm)
    - Current volume (m3)
    - HH alarm active
    """

    def _load_config(self, config: Dict[str, Any]):
        """Load tank configuration"""
        # Tank dimensions
        self.tank_height_mm = config.get('tank_height_mm', 2000)
        self.height_100_percent = config.get('height_100_percent', 2000)
        self.height_hh_alarm = config.get('height_hh_alarm', 1800)
        self.tank_volume_m3 = config.get('tank_volume_m3', 10.0)

        # Calculate cross-sectional area
        self.cross_section_m2 = self.tank_volume_m3 / (self.tank_height_mm / 1000.0)

        # Initialize state
        self.state = {
            'level_mm': 0.0,
            'level_percent': 0.0,
            'volume_m3': 0.0,
            'hh_alarm': False
        }

    def update(self, delta_time: float):
        """Update tank level based on flow inputs"""
        with self.update_lock:
            # Get flow from linked flowmeter (liters/min)
            flow_lpm = self.get_linked_value('flowmeter', 'flow_lpm') or 0.0

            # Convert to m3/s
            flow_m3_s = (flow_lpm / 1000.0) / 60.0

            # Update volume
            delta_volume = flow_m3_s * delta_time
            new_volume = max(0.0, min(self.tank_volume_m3,
                                      self.state['volume_m3'] + delta_volume))

            # Calculate level from volume
            level_m = new_volume / self.cross_section_m2
            level_mm = level_m * 1000.0

            # Update state
            self.state['volume_m3'] = new_volume
            self.state['level_mm'] = level_mm
            self.state['level_percent'] = (level_mm / self.height_100_percent) * 100.0

            # Check HH alarm
            self.state['hh_alarm'] = level_mm >= self.height_hh_alarm

    def read_inputs(self, gpio_driver, adc_drivers: Dict[int, Any]):
        """Level simulator has no hardware inputs (receives data from links)"""
        pass

    def write_outputs(self, gpio_driver, dac_drivers: Dict[int, Any]):
        """Write level (4-20mA) and HH alarm (digital) outputs"""
        with self.update_lock:
            # Write analog level output (4-20mA)
            if 'level_output' in self.io_pins:
                pin = self.io_pins['level_output']
                if pin.i2c_address in dac_drivers:
                    dac = dac_drivers[pin.i2c_address]

                    # Convert level percentage to 4-20mA
                    level_pct = self.state['level_percent']
                    current_ma = 4.0 + (level_pct / 100.0) * 16.0
                    dac.set_current_ma(current_ma)

            # Write HH alarm digital output
            if 'hh_alarm_output' in self.io_pins:
                pin = self.io_pins['hh_alarm_output']
                if pin.pin_number is not None:
                    gpio_driver.write(pin.pin_number, self.state['hh_alarm'])

    def get_display_data(self) -> Dict[str, Any]:
        """Get data for web UI display"""
        return {
            'id': self.id,
            'type': 'level',
            'level_mm': round(self.state['level_mm'], 2),
            'level_percent': round(self.state['level_percent'], 1),
            'volume_m3': round(self.state['volume_m3'], 3),
            'hh_alarm': self.state['hh_alarm'],
            'config': {
                'tank_height_mm': self.tank_height_mm,
                'height_100_percent': self.height_100_percent,
                'height_hh_alarm': self.height_hh_alarm,
                'tank_volume_m3': self.tank_volume_m3
            }
        }

    def set_level_percent(self, percent: float):
        """Manually set tank level (for testing/initialization)"""
        with self.update_lock:
            percent = max(0.0, min(100.0, percent))
            level_mm = (percent / 100.0) * self.height_100_percent
            volume_m3 = (level_mm / 1000.0) * self.cross_section_m2

            self.state['level_mm'] = level_mm
            self.state['level_percent'] = percent
            self.state['volume_m3'] = volume_m3
            self.state['hh_alarm'] = level_mm >= self.height_hh_alarm
