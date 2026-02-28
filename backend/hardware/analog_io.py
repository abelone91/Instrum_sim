"""
Analog I/O drivers for MCP4725 DAC and ADS1115 ADC.
Supports both real hardware and mock for development.
"""
import logging
from typing import Optional
import time

logger = logging.getLogger(__name__)

# Try to import real hardware libraries
try:
    import board
    import busio
    from adafruit_mcp4725 import MCP4725
    from adafruit_ads1x15.ads1115 import ADS1115
    import adafruit_ads1x15.analog_in as AnalogIn
    HAS_I2C_HARDWARE = True
    logger.info("I2C hardware libraries imported successfully")
except (ImportError, NotImplementedError):
    HAS_I2C_HARDWARE = False
    logger.warning("I2C hardware not available, using mock analog I/O")

class MockDAC:
    """Mock MCP4725 for development"""
    def __init__(self, i2c, address=0x60):
        self.address = address
        self._value = 0
        logger.info(f"MockDAC initialized at address 0x{address:02X}")

    @property
    def normalized_value(self):
        return self._value / 4095.0

    @normalized_value.setter
    def normalized_value(self, value):
        self._value = int(value * 4095)
        logger.debug(f"MockDAC[0x{self.address:02X}] set to {value:.3f} ({self._value}/4095)")

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val
        logger.debug(f"MockDAC[0x{self.address:02X}] raw value set to {val}")

class MockADC:
    """Mock ADS1115 for development"""
    def __init__(self, i2c, address=0x48):
        self.address = address
        self._channels = [0.0] * 4
        logger.info(f"MockADC initialized at address 0x{address:02X}")

    def read_channel(self, channel: int) -> float:
        """Read voltage from channel (0-3)"""
        value = self._channels[channel]
        logger.debug(f"MockADC[0x{self.address:02X}] channel {channel} read: {value:.3f}V")
        return value

    def set_channel_value(self, channel: int, voltage: float):
        """Set mock channel value for testing"""
        self._channels[channel] = voltage

class DACDriver:
    """
    MCP4725 DAC driver for 4-20mA output (via external converter circuit).
    12-bit resolution (0-4095).
    """

    def __init__(self, i2c_address: int = 0x60):
        self.address = i2c_address

        if HAS_I2C_HARDWARE:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.dac = MCP4725(i2c, address=i2c_address)
                self.is_mock = False
                logger.info(f"Real MCP4725 DAC initialized at 0x{i2c_address:02X}")
            except Exception as e:
                logger.error(f"Failed to initialize real DAC: {e}, using mock")
                self.dac = MockDAC(None, i2c_address)
                self.is_mock = True
        else:
            self.dac = MockDAC(None, i2c_address)
            self.is_mock = True

    def set_voltage(self, voltage: float, max_voltage: float = 3.3):
        """
        Set output voltage (0 to max_voltage).
        For 4-20mA: Use external converter circuit.
        """
        normalized = max(0.0, min(1.0, voltage / max_voltage))
        self.dac.normalized_value = normalized

    def set_current_ma(self, current_ma: float):
        """
        Set 4-20mA output.
        Assumes external circuit: 0-3.3V -> 4-20mA converter
        4mA = 0V, 20mA = 3.3V
        """
        if current_ma < 4.0:
            current_ma = 4.0
        if current_ma > 20.0:
            current_ma = 20.0

        # Map 4-20mA to 0-3.3V
        voltage = ((current_ma - 4.0) / 16.0) * 3.3
        self.set_voltage(voltage, 3.3)

    def set_raw(self, value: int):
        """Set raw 12-bit DAC value (0-4095)"""
        self.dac.value = max(0, min(4095, value))

class ADCDriver:
    """
    ADS1115 ADC driver for reading analog inputs.
    16-bit resolution, 4 channels.
    """

    def __init__(self, i2c_address: int = 0x48):
        self.address = i2c_address

        if HAS_I2C_HARDWARE:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.adc = ADS1115(i2c, address=i2c_address)
                self.is_mock = False
                logger.info(f"Real ADS1115 ADC initialized at 0x{i2c_address:02X}")
            except Exception as e:
                logger.error(f"Failed to initialize real ADC: {e}, using mock")
                self.adc = MockADC(None, i2c_address)
                self.is_mock = True
        else:
            self.adc = MockADC(None, i2c_address)
            self.is_mock = True

    def read_voltage(self, channel: int) -> float:
        """Read voltage from channel 0-3"""
        if self.is_mock:
            return self.adc.read_channel(channel)
        else:
            # For real hardware
            from adafruit_ads1x15.analog_in import AnalogIn
            pin_map = [0, 1, 2, 3]
            analog_in = AnalogIn(self.adc, pin_map[channel])
            return analog_in.voltage

    def read_current_ma(self, channel: int) -> float:
        """
        Read 4-20mA input (assumes external converter circuit).
        0V = 4mA, 3.3V = 20mA
        """
        voltage = self.read_voltage(channel)
        current_ma = 4.0 + (voltage / 3.3) * 16.0
        return current_ma
