"""
Configuration Manager
Loads and manages instrument configurations from YAML files.
Handles I/O pin allocation and inter-instrument linking.
"""
import logging
import yaml
from typing import Dict, Any, List
from pathlib import Path

from ..simulators.base import BaseSimulator, IOPin
from ..simulators.level_simulator import LevelSimulator
from ..simulators.valve_simulator import ValveSimulator
from ..simulators.pump_simulator import PumpSimulator
from ..simulators.flow_simulator import FlowSimulator
from ..simulators.reg_valve_simulator import RegValveSimulator
from ..simulators.tankbil_simulator import TankbilSimulator

logger = logging.getLogger(__name__)

# Map simulator types to classes
SIMULATOR_CLASSES = {
    'level': LevelSimulator,
    'valve': ValveSimulator,
    'pump': PumpSimulator,
    'flow': FlowSimulator,
    'reg_valve': RegValveSimulator,
    'tankbil': TankbilSimulator
}

class ConfigManager:
    """
    Manages loading and parsing of simulator configurations.
    """

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.simulators: Dict[str, BaseSimulator] = {}
        self.config_data: Dict[str, Any] = {}

    def load_config(self) -> bool:
        """
        Load configuration from YAML file.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f)

            logger.info(f"Loaded configuration from {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False

    def create_simulators(self) -> Dict[str, BaseSimulator]:
        """
        Create simulator instances from configuration.

        Returns:
            Dictionary of simulators by ID
        """
        self.simulators.clear()

        instruments = self.config_data.get('instruments', [])

        for inst_config in instruments:
            inst_id = inst_config.get('id')
            inst_type = inst_config.get('type')

            if not inst_id or not inst_type:
                logger.warning(f"Skipping instrument with missing id or type: {inst_config}")
                continue

            if inst_type not in SIMULATOR_CLASSES:
                logger.warning(f"Unknown instrument type '{inst_type}' for {inst_id}")
                continue

            # Create simulator instance
            sim_class = SIMULATOR_CLASSES[inst_type]
            params = inst_config.get('parameters', {})

            try:
                simulator = sim_class(inst_id, params)
                self.simulators[inst_id] = simulator
                logger.info(f"Created simulator '{inst_id}' of type '{inst_type}'")

            except Exception as e:
                logger.error(f"Failed to create simulator '{inst_id}': {e}")

        return self.simulators

    def allocate_io(self):
        """
        Allocate I/O pins to simulators based on configuration.
        """
        instruments = self.config_data.get('instruments', [])

        for inst_config in instruments:
            inst_id = inst_config.get('id')

            if inst_id not in self.simulators:
                continue

            simulator = self.simulators[inst_id]
            io_config = inst_config.get('io', {})

            # Allocate each I/O pin
            for io_name, io_spec in io_config.items():
                pin_type = io_spec.get('type')
                pin_number = io_spec.get('pin')
                i2c_address = io_spec.get('i2c_address')
                channel = io_spec.get('channel')

                io_pin = IOPin(
                    pin_type=pin_type,
                    pin_number=pin_number,
                    i2c_address=i2c_address,
                    channel=channel
                )

                simulator.allocate_io(io_name, io_pin)

        logger.info("I/O allocation complete")

    def create_links(self):
        """
        Create inter-instrument data links based on configuration.
        """
        instruments = self.config_data.get('instruments', [])

        for inst_config in instruments:
            inst_id = inst_config.get('id')

            if inst_id not in self.simulators:
                continue

            simulator = self.simulators[inst_id]
            links = inst_config.get('links', {})

            # Create each link
            for link_name, target_id in links.items():
                if target_id in self.simulators:
                    target_sim = self.simulators[target_id]
                    simulator.link_instrument(link_name, target_sim)
                else:
                    logger.warning(f"Link target '{target_id}' not found for {inst_id}")

        logger.info("Inter-instrument linking complete")

    def initialize(self) -> bool:
        """
        Complete initialization: load config, create simulators, allocate I/O, create links.

        Returns:
            True if successful
        """
        if not self.load_config():
            return False

        self.create_simulators()
        self.allocate_io()
        self.create_links()

        logger.info(f"Initialized {len(self.simulators)} simulators")
        return True

    def get_simulator(self, inst_id: str) -> BaseSimulator:
        """Get simulator by ID"""
        return self.simulators.get(inst_id)

    def get_all_simulators(self) -> Dict[str, BaseSimulator]:
        """Get all simulators"""
        return self.simulators

    def save_config(self, output_path: str = None):
        """
        Save current configuration to YAML file.

        Args:
            output_path: Output file path (defaults to original config path)
        """
        if output_path is None:
            output_path = self.config_path

        try:
            with open(output_path, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Saved configuration to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
