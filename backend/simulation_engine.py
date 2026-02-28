"""
Simulation Engine
Manages simulation loop, updates all simulators, and handles hardware I/O.
"""
import logging
import time
import threading
from typing import Dict, Any
from datetime import datetime

from .hardware.gpio_driver import GPIODriver
from .hardware.analog_io import DACDriver, ADCDriver
from .config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class SimulationEngine:
    """
    Main simulation engine that orchestrates all simulators and hardware I/O.
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.simulators = config_manager.get_all_simulators()

        # Hardware drivers
        self.gpio_driver = GPIODriver(use_bcm_numbering=True)
        self.dac_drivers: Dict[int, DACDriver] = {}
        self.adc_drivers: Dict[int, ADCDriver] = {}

        # Simulation state
        self.is_running = False
        self.sim_thread = None
        self.update_rate_hz = 10  # 10Hz update rate
        self.last_update_time = None

        # Statistics
        self.stats = {
            'total_updates': 0,
            'update_rate': 0.0,
            'last_update': None
        }

    def initialize_hardware(self):
        """
        Initialize hardware drivers based on I/O configuration.
        Scans all simulators to find required GPIO pins and I2C devices.
        """
        logger.info("Initializing hardware...")

        # Collect all GPIO pins that need to be configured
        gpio_outputs = set()
        gpio_inputs = set()
        dac_addresses = set()
        adc_addresses = set()

        for sim_id, simulator in self.simulators.items():
            for io_name, io_pin in simulator.io_pins.items():
                if io_pin.pin_type == 'digital_out':
                    if io_pin.pin_number is not None:
                        gpio_outputs.add(io_pin.pin_number)

                elif io_pin.pin_type == 'digital_in':
                    if io_pin.pin_number is not None:
                        gpio_inputs.add(io_pin.pin_number)

                elif io_pin.pin_type == 'analog_out':
                    if io_pin.i2c_address is not None:
                        dac_addresses.add(io_pin.i2c_address)

                elif io_pin.pin_type == 'analog_in':
                    if io_pin.i2c_address is not None:
                        adc_addresses.add(io_pin.i2c_address)

        # Configure GPIO pins
        for pin in gpio_outputs:
            self.gpio_driver.setup_output(pin, initial_value=0)

        for pin in gpio_inputs:
            self.gpio_driver.setup_input(pin)

        # Initialize DAC drivers
        for address in dac_addresses:
            self.dac_drivers[address] = DACDriver(i2c_address=address)
            logger.info(f"Initialized DAC at 0x{address:02X}")

        # Initialize ADC drivers
        for address in adc_addresses:
            self.adc_drivers[address] = ADCDriver(i2c_address=address)
            logger.info(f"Initialized ADC at 0x{address:02X}")

        logger.info(f"Hardware initialized: {len(gpio_outputs)} outputs, {len(gpio_inputs)} inputs, "
                   f"{len(dac_addresses)} DACs, {len(adc_addresses)} ADCs")

    def start(self):
        """Start the simulation loop"""
        if self.is_running:
            logger.warning("Simulation already running")
            return

        self.is_running = True
        self.last_update_time = time.time()
        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()
        logger.info("Simulation started")

    def stop(self):
        """Stop the simulation loop"""
        if not self.is_running:
            return

        self.is_running = False
        if self.sim_thread:
            self.sim_thread.join(timeout=2.0)

        logger.info("Simulation stopped")

    def _simulation_loop(self):
        """
        Main simulation loop.
        Runs at specified update rate, reads inputs, updates simulators, writes outputs.
        """
        update_interval = 1.0 / self.update_rate_hz

        while self.is_running:
            loop_start = time.time()

            try:
                # Calculate delta time
                current_time = time.time()
                if self.last_update_time is None:
                    delta_time = update_interval
                else:
                    delta_time = current_time - self.last_update_time
                self.last_update_time = current_time

                # Read all inputs from hardware
                for simulator in self.simulators.values():
                    simulator.read_inputs(self.gpio_driver, self.adc_drivers)

                # Update all simulators
                for simulator in self.simulators.values():
                    simulator.update(delta_time)

                # Write all outputs to hardware
                for simulator in self.simulators.values():
                    simulator.write_outputs(self.gpio_driver, self.dac_drivers)

                # Update statistics
                self.stats['total_updates'] += 1
                self.stats['last_update'] = datetime.now().isoformat()
                self.stats['update_rate'] = 1.0 / delta_time if delta_time > 0 else 0

            except Exception as e:
                logger.error(f"Error in simulation loop: {e}", exc_info=True)

            # Sleep to maintain update rate
            loop_duration = time.time() - loop_start
            sleep_time = max(0, update_interval - loop_duration)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_all_display_data(self) -> Dict[str, Any]:
        """
        Get display data from all simulators.

        Returns:
            Dictionary with data for all simulators
        """
        data = {}
        for sim_id, simulator in self.simulators.items():
            try:
                data[sim_id] = simulator.get_display_data()
            except Exception as e:
                logger.error(f"Error getting display data from {sim_id}: {e}")
                data[sim_id] = {'error': str(e)}

        return data

    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'simulator_count': len(self.simulators),
            'update_rate_hz': self.update_rate_hz
        }

    def cleanup(self):
        """Clean up resources"""
        self.stop()
        self.gpio_driver.cleanup()
        logger.info("Simulation engine cleanup complete")
