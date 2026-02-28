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
