"""
Main FastAPI Application
Provides REST API and WebSocket interface for the simulator.
"""
import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any, List
from pathlib import Path
import json

from .config.config_manager import ConfigManager
from .simulation_engine import SimulationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PLC Instrument Simulator",
    description="Raspberry Pi-based industrial instrument simulator for PLC testing",
    version="1.0.0"
)

# CORS middleware for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global simulation engine
config_path = Path(__file__).parent.parent / "config" / "instruments.yaml"
config_manager = ConfigManager(str(config_path))
simulation_engine = None

# WebSocket clients
websocket_clients: List[WebSocket] = []

@app.on_event("startup")
async def startup():
    """Initialize simulator on startup"""
    global simulation_engine

    logger.info("Starting PLC Instrument Simulator...")

    # Load configuration
    if not config_manager.initialize():
        logger.error("Failed to initialize configuration")
        return

    # Create simulation engine
    simulation_engine = SimulationEngine(config_manager)
    simulation_engine.initialize_hardware()
    simulation_engine.start()

    logger.info("Simulator started successfully")

    # Start WebSocket broadcast task
    asyncio.create_task(broadcast_updates())

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global simulation_engine

    logger.info("Shutting down simulator...")

    if simulation_engine:
        simulation_engine.cleanup()

    logger.info("Shutdown complete")

# REST API Endpoints

@app.get("/api/status")
async def get_status():
    """Get simulator status"""
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    return {
        "status": "running" if simulation_engine.is_running else "stopped",
        "statistics": simulation_engine.get_statistics()
    }

@app.get("/api/simulators")
async def get_simulators():
    """Get list of all configured simulators"""
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    simulators = simulation_engine.simulators
    return {
        "simulators": [
            {
                "id": sim_id,
                "type": sim.__class__.__name__,
                "config": sim.config
            }
            for sim_id, sim in simulators.items()
        ]
    }

@app.get("/api/simulators/{simulator_id}")
async def get_simulator(simulator_id: str):
    """Get detailed information about a specific simulator"""
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    simulator = simulation_engine.simulators.get(simulator_id)
    if not simulator:
        raise HTTPException(status_code=404, detail=f"Simulator '{simulator_id}' not found")

    return simulator.get_state()

@app.get("/api/data")
async def get_all_data():
    """Get display data from all simulators"""
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    return simulation_engine.get_all_display_data()

@app.get("/api/data/{simulator_id}")
async def get_simulator_data(simulator_id: str):
    """Get display data from a specific simulator"""
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    simulator = simulation_engine.simulators.get(simulator_id)
    if not simulator:
        raise HTTPException(status_code=404, detail=f"Simulator '{simulator_id}' not found")

    return simulator.get_display_data()

@app.post("/api/simulators/{simulator_id}/parameter")
async def set_parameter(simulator_id: str, param_name: str, value: Any):
    """Set a parameter on a simulator"""
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    simulator = simulation_engine.simulators.get(simulator_id)
    if not simulator:
        raise HTTPException(status_code=404, detail=f"Simulator '{simulator_id}' not found")

    simulator.set_parameter(param_name, value)
    return {"status": "ok", "simulator_id": simulator_id, "parameter": param_name, "value": value}

@app.post("/api/simulators")
async def add_simulator(instrument_config: Dict[str, Any]):
    """Add a new simulator"""
    global simulation_engine

    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    try:
        # Add to config data
        config_manager.config_data.setdefault('instruments', []).append(instrument_config)

        # Reinitialize simulation engine
        simulation_engine.stop()
        config_manager.create_simulators()
        config_manager.allocate_io()
        config_manager.create_links()

        simulation_engine = SimulationEngine(config_manager)
        simulation_engine.initialize_hardware()
        simulation_engine.start()

        # Save config
        config_manager.save_config()

        return {"status": "added", "id": instrument_config.get('id')}

    except Exception as e:
        logger.error(f"Failed to add simulator: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/simulators/{simulator_id}")
async def delete_simulator(simulator_id: str):
    """Delete a simulator"""
    global simulation_engine

    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    try:
        # Remove from config data
        instruments = config_manager.config_data.get('instruments', [])
        config_manager.config_data['instruments'] = [
            inst for inst in instruments if inst.get('id') != simulator_id
        ]

        # Reinitialize simulation engine
        simulation_engine.stop()
        config_manager.create_simulators()
        config_manager.allocate_io()
        config_manager.create_links()

        simulation_engine = SimulationEngine(config_manager)
        simulation_engine.initialize_hardware()
        simulation_engine.start()

        # Save config
        config_manager.save_config()

        return {"status": "deleted", "id": simulator_id}

    except Exception as e:
        logger.error(f"Failed to delete simulator: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/simulators/{simulator_id}")
async def update_simulator(simulator_id: str, instrument_config: Dict[str, Any]):
    """Update a simulator configuration"""
    global simulation_engine

    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    try:
        # Find and update in config data
        instruments = config_manager.config_data.get('instruments', [])
        found = False
        for i, inst in enumerate(instruments):
            if inst.get('id') == simulator_id:
                instruments[i] = instrument_config
                found = True
                break

        if not found:
            raise HTTPException(status_code=404, detail=f"Simulator '{simulator_id}' not found")

        # Reinitialize simulation engine
        simulation_engine.stop()
        config_manager.create_simulators()
        config_manager.allocate_io()
        config_manager.create_links()

        simulation_engine = SimulationEngine(config_manager)
        simulation_engine.initialize_hardware()
        simulation_engine.start()

        # Save config
        config_manager.save_config()

        return {"status": "updated", "id": simulator_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update simulator: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/instrument-types")
async def get_instrument_types():
    """Get available instrument types and their parameter schemas"""
    return {
        "types": {
            "level": {
                "name": "Level Simulator",
                "description": "Tank level measurement with 4-20mA output and HH alarm",
                "parameters": {
                    "tank_height_mm": {"type": "number", "default": 2000, "label": "Tank Height (mm)"},
                    "height_100_percent": {"type": "number", "default": 2000, "label": "100% Height (mm)"},
                    "height_hh_alarm": {"type": "number", "default": 1800, "label": "HH Alarm Height (mm)"},
                    "tank_volume_m3": {"type": "number", "default": 10.0, "label": "Tank Volume (m³)"}
                },
                "io_types": ["level_output:analog_out", "hh_alarm_output:digital_out"],
                "link_types": ["flowmeter"]
            },
            "valve": {
                "name": "Valve Simulator",
                "description": "On/off valve with configurable speeds",
                "parameters": {
                    "open_speed_sec": {"type": "number", "default": 5.0, "label": "Open Speed (sec)"},
                    "close_speed_sec": {"type": "number", "default": 5.0, "label": "Close Speed (sec)"},
                    "has_hold_solenoid": {"type": "boolean", "default": False, "label": "Hold Solenoid"},
                    "has_return_spring": {"type": "boolean", "default": False, "label": "Return Spring"},
                    "valve_type": {"type": "select", "default": "import", "options": ["import", "export"], "label": "Valve Type"}
                },
                "io_types": ["open_input:digital_in", "close_input:digital_in", "hold_input:digital_in"],
                "link_types": []
            },
            "pump": {
                "name": "Pump Simulator",
                "description": "Centrifugal pump with pressure and flow",
                "parameters": {
                    "control_type": {"type": "select", "default": "digital", "options": ["digital", "analog"], "label": "Control Type"},
                    "max_pressure_bar": {"type": "number", "default": 10.0, "label": "Max Pressure (bar)"},
                    "set_pressure_bar": {"type": "number", "default": 8.0, "label": "Set Pressure (bar)"},
                    "max_flow_lpm": {"type": "number", "default": 100.0, "label": "Max Flow (L/min)"},
                    "ramp_time_sec": {"type": "number", "default": 5.0, "label": "Ramp Time (sec)"}
                },
                "io_types": ["enable_input:digital_in", "speed_input:analog_in", "running_output:digital_out", "fault_output:digital_out", "feedback_output:analog_out"],
                "link_types": ["reg_valve"]
            },
            "flow": {
                "name": "Flow Meter Simulator",
                "description": "Flow meter with pulse output",
                "parameters": {
                    "unit": {"type": "select", "default": "L/min", "options": ["L/sec", "L/min"], "label": "Unit"},
                    "pulse_type": {"type": "select", "default": "quadrature", "options": ["single", "quadrature"], "label": "Pulse Type"},
                    "velocity_ms": {"type": "number", "default": 1.5, "label": "Velocity (m/s)"},
                    "noise_enabled": {"type": "boolean", "default": False, "label": "Noise Enabled"},
                    "pulses_per_liter": {"type": "number", "default": 100, "label": "Pulses per Liter"}
                },
                "io_types": ["pulse_a_output:digital_out", "pulse_b_output:digital_out", "start_input:digital_in", "reset_input:digital_in"],
                "link_types": ["pump"]
            },
            "reg_valve": {
                "name": "Regulating Valve",
                "description": "Modulating control valve",
                "parameters": {
                    "valve_type": {"type": "select", "default": "LVRA", "options": ["LVRA", "LVRD"], "label": "Valve Type"},
                    "open_speed_sec": {"type": "number", "default": 10.0, "label": "Open Speed (sec)"},
                    "close_speed_sec": {"type": "number", "default": 10.0, "label": "Close Speed (sec)"},
                    "min_position_20_pct": {"type": "boolean", "default": False, "label": "20% Minimum"},
                    "feedback_type": {"type": "select", "default": "analog", "options": ["analog", "switch"], "label": "Feedback Type"}
                },
                "io_types": ["position_input:analog_in", "open_input:digital_in", "hold_input:digital_in", "closed_limit_output:digital_out", "position_output:analog_out"],
                "link_types": []
            },
            "tankbil": {
                "name": "Tank Truck Simulator",
                "description": "Safety interlock system",
                "parameters": {
                    "deadman_enabled": {"type": "boolean", "default": True, "label": "Deadman Enabled"}
                },
                "io_types": ["ground_ok_input:digital_in", "overfill_ok_input:digital_in", "deadman_input:digital_in", "test_ground_output:digital_out", "test_overfill_output:digital_out", "deadman_warning_output:digital_out"],
                "link_types": []
            }
        }
    }

@app.post("/api/control/start")
async def start_simulation():
    """Start the simulation"""
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    simulation_engine.start()
    return {"status": "started"}

@app.post("/api/control/stop")
async def stop_simulation():
    """Stop the simulation"""
    if not simulation_engine:
        raise HTTPException(status_code=503, detail="Simulation engine not initialized")

    simulation_engine.stop()
    return {"status": "stopped"}

# WebSocket for real-time updates

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time simulator data"""
    await websocket.accept()
    websocket_clients.append(websocket)

    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Received: {data}")

    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        logger.info("WebSocket client disconnected")

async def broadcast_updates():
    """
    Periodically broadcast simulator data to all connected WebSocket clients.
    """
    while True:
        await asyncio.sleep(0.1)  # 10Hz update rate

        if not simulation_engine or not websocket_clients:
            continue

        try:
            # Get current data
            data = simulation_engine.get_all_display_data()
            message = json.dumps({"type": "update", "data": data})

            # Broadcast to all clients
            disconnected = []
            for client in websocket_clients:
                try:
                    await client.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    disconnected.append(client)

            # Remove disconnected clients
            for client in disconnected:
                if client in websocket_clients:
                    websocket_clients.remove(client)

        except Exception as e:
            logger.error(f"Error broadcasting updates: {e}")

# Serve static frontend files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists() and (frontend_path / "index.html").exists():
    # Serve static files
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(frontend_path / "index.html")

    @app.get("/style.css")
    async def serve_css():
        return FileResponse(frontend_path / "style.css")

    @app.get("/app.js")
    async def serve_js():
        return FileResponse(frontend_path / "app.js")

else:
    @app.get("/")
    async def root():
        return {
            "message": "PLC Instrument Simulator API",
            "version": "1.0.0",
            "docs": "/docs",
            "note": "Frontend files not found. Check frontend/ directory."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
