"""
GPIO abstraction layer for Raspberry Pi.
Falls back to mock implementation when not running on actual Pi hardware.
"""
import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class PinMode(Enum):
    INPUT = "input"
    OUTPUT = "output"

class PullMode(Enum):
    NONE = "none"
    UP = "up"
    DOWN = "down"

# Try to import RPi.GPIO, fall back to mock if not available
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
    logger.info("RPi.GPIO imported successfully")
except (ImportError, RuntimeError):
    HAS_GPIO = False
    logger.warning("RPi.GPIO not available, using mock GPIO")

class MockGPIO:
    """Mock GPIO for development/testing on non-Pi hardware"""
    BCM = "BCM"
    BOARD = "BOARD"
    OUT = "OUT"
    IN = "IN"
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"
    PUD_OFF = "PUD_OFF"
    HIGH = 1
    LOW = 0

    def __init__(self):
        self.mode = None
        self.pins: Dict[int, dict] = {}
        logger.info("MockGPIO initialized")

    def setmode(self, mode):
        self.mode = mode
        logger.debug(f"GPIO mode set to {mode}")

    def setup(self, pin, mode, pull_up_down=None):
        self.pins[pin] = {
            'mode': mode,
            'pull': pull_up_down,
            'value': 0
        }
        logger.debug(f"Pin {pin} setup as {mode}, pull={pull_up_down}")

    def output(self, pin, value):
        if pin in self.pins:
            self.pins[pin]['value'] = value
        logger.debug(f"Pin {pin} set to {value}")

    def input(self, pin):
        value = self.pins.get(pin, {}).get('value', 0)
        logger.debug(f"Pin {pin} read as {value}")
        return value

    def cleanup(self):
        self.pins.clear()
        logger.info("GPIO cleanup complete")

class GPIODriver:
    """
    Unified GPIO driver that works on both Raspberry Pi and development machines.
    Automatically uses real GPIO when available, otherwise uses mock.
    """

    def __init__(self, use_bcm_numbering: bool = True):
        if HAS_GPIO:
            self.gpio = GPIO
            GPIO.setmode(GPIO.BCM if use_bcm_numbering else GPIO.BOARD)
        else:
            self.gpio = MockGPIO()
            self.gpio.setmode(MockGPIO.BCM if use_bcm_numbering else MockGPIO.BOARD)

        self.is_mock = not HAS_GPIO
        self.configured_pins: Dict[int, str] = {}

    def setup_output(self, pin: int, initial_value: int = 0):
        """Configure a pin as digital output"""
        self.gpio.setup(pin, self.gpio.OUT)
        self.gpio.output(pin, initial_value)
        self.configured_pins[pin] = 'output'
        logger.info(f"Pin {pin} configured as OUTPUT (initial={initial_value})")

    def setup_input(self, pin: int, pull_mode: PullMode = PullMode.NONE):
        """Configure a pin as digital input"""
        pull_map = {
            PullMode.UP: self.gpio.PUD_UP,
            PullMode.DOWN: self.gpio.PUD_DOWN,
            PullMode.NONE: getattr(self.gpio, 'PUD_OFF', None)
        }
        pull = pull_map[pull_mode]

        if pull is not None:
            self.gpio.setup(pin, self.gpio.IN, pull_up_down=pull)
        else:
            self.gpio.setup(pin, self.gpio.IN)

        self.configured_pins[pin] = 'input'
        logger.info(f"Pin {pin} configured as INPUT (pull={pull_mode.value})")

    def write(self, pin: int, value: bool):
        """Write digital output"""
        self.gpio.output(pin, self.gpio.HIGH if value else self.gpio.LOW)

    def read(self, pin: int) -> bool:
        """Read digital input"""
        return bool(self.gpio.input(pin))

    def cleanup(self):
        """Clean up GPIO resources"""
        self.gpio.cleanup()
        self.configured_pins.clear()
        logger.info("GPIO driver cleaned up")

    def __del__(self):
        try:
            self.cleanup()
        except:
            pass
