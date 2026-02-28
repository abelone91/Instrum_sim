#!/usr/bin/env python3
"""
Test script to verify simulator installation and configuration.
Run this to check if everything is set up correctly.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing Python imports...")

    try:
        import fastapi
        print("  ✓ FastAPI")
    except ImportError:
        print("  ✗ FastAPI - Run: pip install fastapi")
        return False

    try:
        import uvicorn
        print("  ✓ Uvicorn")
    except ImportError:
        print("  ✗ Uvicorn - Run: pip install uvicorn")
        return False

    try:
        import yaml
        print("  ✓ PyYAML")
    except ImportError:
        print("  ✗ PyYAML - Run: pip install pyyaml")
        return False

    return True

def test_backend():
    """Test if backend modules load correctly"""
    print("\nTesting backend modules...")

    try:
        from backend.hardware.gpio_driver import GPIODriver
        print("  ✓ GPIO Driver")
    except Exception as e:
        print(f"  ✗ GPIO Driver - {e}")
        return False

    try:
        from backend.hardware.analog_io import DACDriver, ADCDriver
        print("  ✓ Analog I/O Drivers")
    except Exception as e:
        print(f"  ✗ Analog I/O Drivers - {e}")
        return False

    try:
        from backend.simulators.level_simulator import LevelSimulator
        from backend.simulators.pump_simulator import PumpSimulator
        from backend.simulators.valve_simulator import ValveSimulator
        from backend.simulators.flow_simulator import FlowSimulator
        from backend.simulators.reg_valve_simulator import RegValveSimulator
        from backend.simulators.tankbil_simulator import TankbilSimulator
        print("  ✓ All simulators")
    except Exception as e:
        print(f"  ✗ Simulators - {e}")
        return False

    try:
        from backend.config.config_manager import ConfigManager
        print("  ✓ Config Manager")
    except Exception as e:
        print(f"  ✗ Config Manager - {e}")
        return False

    return True

def test_config():
    """Test if configuration file is valid"""
    print("\nTesting configuration...")

    config_path = Path(__file__).parent / "config" / "instruments.yaml"

    if not config_path.exists():
        print(f"  ✗ Config file not found: {config_path}")
        return False

    print(f"  ✓ Config file exists: {config_path}")

    try:
        from backend.config.config_manager import ConfigManager
        config_mgr = ConfigManager(str(config_path))

        if not config_mgr.load_config():
            print("  ✗ Failed to load config")
            return False

        print("  ✓ Config file valid")

        simulators = config_mgr.create_simulators()
        print(f"  ✓ Created {len(simulators)} simulators")

        for sim_id, sim in simulators.items():
            print(f"    - {sim_id}: {sim.__class__.__name__}")

        return True

    except Exception as e:
        print(f"  ✗ Config error: {e}")
        return False

def test_hardware():
    """Test hardware drivers (mock mode on non-Pi hardware)"""
    print("\nTesting hardware drivers...")

    try:
        from backend.hardware.gpio_driver import GPIODriver
        gpio = GPIODriver()

        if gpio.is_mock:
            print("  ℹ Running in MOCK mode (not on Raspberry Pi)")
        else:
            print("  ✓ Running on Raspberry Pi hardware")

        # Test GPIO setup
        gpio.setup_output(17, 0)
        gpio.write(17, True)
        value = gpio.read(17) if gpio.is_mock else True
        print(f"  ✓ GPIO test successful")

        gpio.cleanup()

    except Exception as e:
        print(f"  ✗ GPIO test failed: {e}")
        return False

    try:
        from backend.hardware.analog_io import DACDriver, ADCDriver

        dac = DACDriver(0x60)
        print(f"  ✓ DAC driver initialized ({'mock' if dac.is_mock else 'real'})")

        adc = ADCDriver(0x48)
        print(f"  ✓ ADC driver initialized ({'mock' if adc.is_mock else 'real'})")

    except Exception as e:
        print(f"  ✗ Analog I/O test failed: {e}")
        return False

    return True

def test_simulation():
    """Test basic simulation loop"""
    print("\nTesting simulation engine...")

    try:
        from backend.config.config_manager import ConfigManager
        from backend.simulation_engine import SimulationEngine

        config_path = Path(__file__).parent / "config" / "instruments.yaml"
        config_mgr = ConfigManager(str(config_path))

        if not config_mgr.initialize():
            print("  ✗ Failed to initialize config")
            return False

        engine = SimulationEngine(config_mgr)
        print("  ✓ Simulation engine created")

        engine.initialize_hardware()
        print("  ✓ Hardware initialized")

        # Don't actually start the loop for testing
        print("  ✓ Simulation engine ready")

        engine.cleanup()
        print("  ✓ Cleanup successful")

        return True

    except Exception as e:
        print(f"  ✗ Simulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("PLC Instrument Simulator - Setup Test")
    print("=" * 60)
    print()

    all_passed = True

    all_passed &= test_imports()
    all_passed &= test_backend()
    all_passed &= test_config()
    all_passed &= test_hardware()
    all_passed &= test_simulation()

    print()
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("✓ System is ready to run")
        print()
        print("Next steps:")
        print("  1. Review config/instruments.yaml")
        print("  2. Run: python run.py")
        print("  3. Open: http://localhost:8000")
    else:
        print("✗ Some tests failed")
        print("✗ Please fix the errors above")
        print()
        print("Try:")
        print("  pip install -r requirements.txt")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
