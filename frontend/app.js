// PLC Simulator Frontend Application

class SimulatorApp {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.simulators = {};

        this.init();
    }

    init() {
        // Set up event listeners
        document.getElementById('btn-start').addEventListener('click', () => this.startSimulation());
        document.getElementById('btn-stop').addEventListener('click', () => this.stopSimulation());
        document.getElementById('btn-refresh').addEventListener('click', () => this.loadSimulators());

        // Connect to WebSocket
        this.connectWebSocket();

        // Load initial data
        this.loadSimulators();
        this.loadStatus();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);

            if (this.reconnectInterval) {
                clearInterval(this.reconnectInterval);
                this.reconnectInterval = null;
            }
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'update') {
                    this.updateSimulatorData(message.data);
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);

            // Attempt to reconnect
            if (!this.reconnectInterval) {
                this.reconnectInterval = setInterval(() => {
                    console.log('Attempting to reconnect...');
                    this.connectWebSocket();
                }, 3000);
            }
        };
    }

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        if (connected) {
            statusEl.textContent = 'Connected';
            statusEl.className = 'status-connected';
        } else {
            statusEl.textContent = 'Disconnected';
            statusEl.className = 'status-disconnected';
        }
    }

    async loadSimulators() {
        try {
            const response = await fetch('/api/simulators');
            const data = await response.json();

            this.simulators = {};
            data.simulators.forEach(sim => {
                this.simulators[sim.id] = sim;
            });

            this.renderSimulators();
        } catch (error) {
            console.error('Failed to load simulators:', error);
        }
    }

    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            document.getElementById('sim-status').textContent = data.status;
            document.getElementById('update-rate').textContent =
                `${data.statistics.update_rate.toFixed(1)} Hz`;
        } catch (error) {
            console.error('Failed to load status:', error);
        }

        // Refresh every 2 seconds
        setTimeout(() => this.loadStatus(), 2000);
    }

    async startSimulation() {
        try {
            await fetch('/api/control/start', { method: 'POST' });
            console.log('Simulation started');
        } catch (error) {
            console.error('Failed to start simulation:', error);
        }
    }

    async stopSimulation() {
        try {
            await fetch('/api/control/stop', { method: 'POST' });
            console.log('Simulation stopped');
        } catch (error) {
            console.error('Failed to stop simulation:', error);
        }
    }

    renderSimulators() {
        const container = document.getElementById('simulators');
        container.innerHTML = '';

        Object.entries(this.simulators).forEach(([id, sim]) => {
            const card = this.createSimulatorCard(id, sim);
            container.appendChild(card);
        });
    }

    createSimulatorCard(id, sim) {
        const card = document.createElement('div');
        card.className = 'simulator-card';
        card.id = `sim-${id}`;

        const typeName = this.getTypeName(sim.type);

        card.innerHTML = `
            <div class="simulator-header">
                <div class="simulator-title">${id}</div>
                <div class="simulator-type">${typeName}</div>
            </div>
            <div class="simulator-data" id="data-${id}">
                <!-- Data will be populated here -->
            </div>
        `;

        return card;
    }

    getTypeName(type) {
        const typeMap = {
            'LevelSimulator': 'Level',
            'ValveSimulator': 'Valve',
            'PumpSimulator': 'Pump',
            'FlowSimulator': 'Flow',
            'RegValveSimulator': 'Reg Valve',
            'TankbilSimulator': 'Tank Truck'
        };
        return typeMap[type] || type;
    }

    updateSimulatorData(data) {
        Object.entries(data).forEach(([id, simData]) => {
            const dataEl = document.getElementById(`data-${id}`);
            if (!dataEl) return;

            const html = this.renderSimulatorData(simData);
            dataEl.innerHTML = html;
        });
    }

    renderSimulatorData(simData) {
        switch (simData.type) {
            case 'level':
                return this.renderLevelData(simData);
            case 'valve':
                return this.renderValveData(simData);
            case 'pump':
                return this.renderPumpData(simData);
            case 'flow':
                return this.renderFlowData(simData);
            case 'reg_valve':
                return this.renderRegValveData(simData);
            case 'tankbil':
                return this.renderTankbilData(simData);
            default:
                return `<pre>${JSON.stringify(simData, null, 2)}</pre>`;
        }
    }

    renderLevelData(data) {
        const alarmPos = (data.config.height_hh_alarm / data.config.tank_height_mm) * 100;

        return `
            <div class="level-display">
                <div class="level-fill" style="height: ${data.level_percent}%"></div>
                <div class="level-alarm-line" style="bottom: ${alarmPos}%"></div>
            </div>
            <div class="data-row">
                <span class="data-label">Level</span>
                <span class="data-value">${data.level_mm.toFixed(0)} mm (${data.level_percent.toFixed(1)}%)</span>
            </div>
            <div class="data-row">
                <span class="data-label">Volume</span>
                <span class="data-value">${data.volume_m3.toFixed(2)} m³</span>
            </div>
            <div class="data-row">
                <span class="data-label">HH Alarm</span>
                <span class="data-value">
                    ${data.hh_alarm ? 'ACTIVE' : 'OK'}
                    <span class="indicator ${data.hh_alarm ? 'indicator-alarm' : 'indicator-off'}"></span>
                </span>
            </div>
        `;
    }

    renderValveData(data) {
        let status = 'Closed';
        let statusClass = 'valve-closed';

        if (data.position_percent >= 95) {
            status = 'Open';
            statusClass = 'valve-open';
        } else if (data.position_percent > 5) {
            status = `${data.position_percent.toFixed(0)}%`;
            statusClass = 'valve-partial';
        }

        return `
            <div class="valve-display">
                <div class="valve-indicator ${statusClass}">${status}</div>
            </div>
            <div class="data-row">
                <span class="data-label">Position</span>
                <span class="data-value">${data.position_percent.toFixed(1)}%</span>
            </div>
            <div class="data-row">
                <span class="data-label">Status</span>
                <span class="data-value">${data.status}</span>
            </div>
            <div class="data-row">
                <span class="data-label">Commands</span>
                <span class="data-value">
                    O<span class="indicator ${data.open_cmd ? 'indicator-on' : 'indicator-off'}"></span>
                    C<span class="indicator ${data.close_cmd ? 'indicator-on' : 'indicator-off'}"></span>
                    H<span class="indicator ${data.hold_cmd ? 'indicator-on' : 'indicator-off'}"></span>
                </span>
            </div>
        `;
    }

    renderPumpData(data) {
        return `
            <div class="pump-display">
                <div class="pump-icon ${data.running ? 'pump-running' : ''}">⚙</div>
            </div>
            <div class="data-row">
                <span class="data-label">Running</span>
                <span class="data-value">
                    ${data.running ? 'YES' : 'NO'}
                    <span class="indicator ${data.running ? 'indicator-on' : 'indicator-off'}"></span>
                </span>
            </div>
            <div class="data-row">
                <span class="data-label">Speed</span>
                <span class="data-value">${data.speed_percent.toFixed(1)}%</span>
            </div>
            <div class="data-row">
                <span class="data-label">Pressure</span>
                <span class="data-value">${data.pressure_bar.toFixed(2)} bar</span>
            </div>
            <div class="data-row">
                <span class="data-label">Flow</span>
                <span class="data-value">${data.flow_lpm.toFixed(1)} L/min</span>
            </div>
            <div class="data-row">
                <span class="data-label">Fault</span>
                <span class="data-value">
                    ${data.fault ? 'FAULT' : 'OK'}
                    <span class="indicator ${data.fault ? 'indicator-alarm' : 'indicator-off'}"></span>
                </span>
            </div>
        `;
    }

    renderFlowData(data) {
        return `
            <div class="data-row">
                <span class="data-label">Flow Rate</span>
                <span class="data-value">${data.flow_lpm.toFixed(2)} L/min</span>
            </div>
            <div class="data-row">
                <span class="data-label">Progress</span>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(100, (data.flow_lpm / 100) * 100)}%">
                        ${data.flow_lpm.toFixed(1)} L/min
                    </div>
                </div>
            </div>
            <div class="data-row">
                <span class="data-label">Total Volume</span>
                <span class="data-value">${data.total_volume_liters.toFixed(1)} L</span>
            </div>
            <div class="data-row">
                <span class="data-label">Pulse Count</span>
                <span class="data-value">${data.pulse_count}</span>
            </div>
            <div class="data-row">
                <span class="data-label">Started</span>
                <span class="data-value">
                    <span class="indicator ${data.start_enabled ? 'indicator-on' : 'indicator-off'}"></span>
                </span>
            </div>
        `;
    }

    renderRegValveData(data) {
        return `
            <div class="data-row">
                <span class="data-label">Position</span>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.position_percent}%">
                        ${data.position_percent.toFixed(1)}%
                    </div>
                </div>
            </div>
            <div class="data-row">
                <span class="data-label">Setpoint</span>
                <span class="data-value">${data.setpoint_percent.toFixed(1)}%</span>
            </div>
            <div class="data-row">
                <span class="data-label">Pressure Drop</span>
                <span class="data-value">${data.pressure_bar.toFixed(2)} bar</span>
            </div>
            <div class="data-row">
                <span class="data-label">Closed Limit</span>
                <span class="data-value">
                    <span class="indicator ${data.at_closed_limit ? 'indicator-on' : 'indicator-off'}"></span>
                </span>
            </div>
        `;
    }

    renderTankbilData(data) {
        return `
            <div class="data-row">
                <span class="data-label">Grounding</span>
                <span class="data-value">
                    ${data.ground_ok ? 'OK' : 'NOT OK'}
                    <span class="indicator ${data.ground_ok ? 'indicator-on' : 'indicator-alarm'}"></span>
                </span>
            </div>
            <div class="data-row">
                <span class="data-label">Overfill</span>
                <span class="data-value">
                    ${data.overfill_ok ? 'OK' : 'NOT OK'}
                    <span class="indicator ${data.overfill_ok ? 'indicator-on' : 'indicator-alarm'}"></span>
                </span>
            </div>
            <div class="data-row">
                <span class="data-label">Dead Man</span>
                <span class="data-value">
                    ${data.deadman_pressed ? 'PRESSED' : 'RELEASED'}
                    <span class="indicator ${data.deadman_pressed ? 'indicator-on' : 'indicator-off'}"></span>
                </span>
            </div>
            <div class="data-row">
                <span class="data-label">Warning</span>
                <span class="data-value">
                    ${data.deadman_warning ? 'ACTIVE' : 'OK'}
                    <span class="indicator ${data.deadman_warning ? 'indicator-alarm' : 'indicator-off'}"></span>
                </span>
            </div>
            <div class="data-row">
                <span class="data-label">System Safe</span>
                <span class="data-value">
                    ${data.system_safe ? 'SAFE' : 'NOT SAFE'}
                    <span class="indicator ${data.system_safe ? 'indicator-on' : 'indicator-alarm'}"></span>
                </span>
            </div>
        `;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new SimulatorApp();
});
