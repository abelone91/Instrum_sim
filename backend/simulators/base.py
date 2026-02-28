"""
Base class for all instrument simulators.
Provides common functionality for I/O, configuration, and state management.
"""
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class IOPin:
    """Represents a single I/O pin configuration"""
    def __init__(self, pin_type: str, pin_number: Optional[int] = None,
                 i2c_address: Optional[int] = None, channel: Optional[int] = None):
        self.pin_type = pin_type  # 'digital_in', 'digital_out', 'analog_in', 'analog_out'
        self.pin_number = pin_number  # GPIO pin number
        self.i2c_address = i2c_address  # I2C device address (for DAC/ADC)
        self.channel = channel  # Channel number (for multi-channel devices)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.pin_type,
            'pin': self.pin_number,
            'i2c_address': self.i2c_address,
            'channel': self.channel
        }

class BaseSimulator(ABC):
    """
    Base class for all instrument simulators.
    Handles I/O allocation, state management, and simulation updates.
    """

    def __init__(self, simulator_id: str, config: Dict[str, Any]):
        self.id = simulator_id
        self.config = config
        self.io_pins: Dict[str, IOPin] = {}
        self.state: Dict[str, Any] = {}
        self.linked_instruments: Dict[str, 'BaseSimulator'] = {}
        self.last_update = datetime.now()
        self.update_lock = threading.Lock()
        self.is_running = False

        # Initialize from config
        self._load_config(config)
        logger.info(f"Initialized {self.__class__.__name__} '{simulator_id}'")

    @abstractmethod
    def _load_config(self, config: Dict[str, Any]):
        """Load simulator-specific configuration"""
        pass

    @abstractmethod
    def update(self, delta_time: float):
        """
        Update simulator state based on elapsed time.
        Called periodically by the simulation engine.

        Args:
            delta_time: Time elapsed since last update (seconds)
        """
        pass

    @abstractmethod
    def read_inputs(self, gpio_driver, adc_drivers: Dict[int, Any]):
        """
        Read values from hardware inputs (GPIO, ADC).

        Args:
            gpio_driver: GPIO driver instance
            adc_drivers: Dictionary of ADC drivers by I2C address
        """
        pass

    @abstractmethod
    def write_outputs(self, gpio_driver, dac_drivers: Dict[int, Any]):
        """
        Write values to hardware outputs (GPIO, DAC).

        Args:
            gpio_driver: GPIO driver instance
            dac_drivers: Dictionary of DAC drivers by I2C address
        """
        pass

    @abstractmethod
    def get_display_data(self) -> Dict[str, Any]:
        """
        Get current state data for display in UI.

        Returns:
            Dictionary with display values
        """
        pass

    def allocate_io(self, io_name: str, pin: IOPin):
        """Allocate an I/O pin for this simulator"""
        self.io_pins[io_name] = pin
        logger.debug(f"{self.id}: Allocated {io_name} -> {pin.to_dict()}")

    def link_instrument(self, link_name: str, instrument: 'BaseSimulator'):
        """Link this simulator to another instrument for data sharing"""
        self.linked_instruments[link_name] = instrument
        logger.info(f"{self.id}: Linked '{link_name}' to {instrument.id}")

    def get_linked_value(self, link_name: str, value_name: str) -> Optional[Any]:
        """Get a value from a linked instrument"""
        if link_name in self.linked_instruments:
            linked = self.linked_instruments[link_name]
            return linked.state.get(value_name)
        return None

    def set_parameter(self, param_name: str, value: Any):
        """Update a configuration parameter"""
        if param_name in self.config:
            self.config[param_name] = value
            logger.info(f"{self.id}: Parameter '{param_name}' set to {value}")
        else:
            logger.warning(f"{self.id}: Unknown parameter '{param_name}'")

    def get_state(self) -> Dict[str, Any]:
        """Get complete simulator state"""
        with self.update_lock:
            return {
                'id': self.id,
                'type': self.__class__.__name__,
                'config': self.config,
                'state': self.state,
                'io_pins': {name: pin.to_dict() for name, pin in self.io_pins.items()},
                'last_update': self.last_update.isoformat()
            }

    def reset(self):
        """Reset simulator to initial state"""
        self.state.clear()
        self.last_update = datetime.now()
        logger.info(f"{self.id}: Reset to initial state")
