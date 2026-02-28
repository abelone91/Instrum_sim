// Modern PLC Simulator Application

class SimulatorApp {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.simulators = {};
        this.instrumentTypes = {};
        this.currentView = 'dashboard';
        this.editingInstrument = null;

        this.init();
    }

    async init() {
        // Set up navigation
        this.setupNavigation();

        // Set up event listeners
        this.setupEventListeners();

        // Connect to WebSocket
        this.connectWebSocket();

        // Load initial data
        await this.loadInstrumentTypes();
        await this.loadSimulators();
        await this.loadStatus();
    }

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.dataset.view;
                this.switchView(view);
            });
        });
    }

    switchView(view) {
        // Update nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === view) {
                item.classList.add('active');
            }
        });

        // Update view containers
        document.querySelectorAll('.view-container').forEach(container => {
            container.classList.remove('active');
        });
        document.getElementById(`view-${view}`).classList.add('active');

        // Update page title
        const titles = {
            dashboard: 'Dashboard',
            instruments: 'Instruments',
            monitoring: 'Monitoring',
            settings: 'Settings'
        };
        document.getElementById('page-title').textContent = titles[view];

        this.currentView = view;

        // Load view-specific data
        if (view === 'instruments') {
            this.renderInstrumentsTable();
        }
    }

    setupEventListeners() {
        // Control buttons
        document.getElementById('btn-start').addEventListener('click', () => this.startSimulation());
        document.getElementById('btn-stop').addEventListener('click', () => this.stopSimulation());
        document.getElementById('btn-refresh').addEventListener('click', () => this.loadSimulators());
        document.getElementById('btn-add-instrument').addEventListener('click', () => this.showAddInstrumentModal());

        // Modal close buttons
        document.getElementById('modal-close').addEventListener('click', () => this.closeModal('instrument-modal'));
        document.getElementById('btn-cancel').addEventListener('click', () => this.closeModal('instrument-modal'));
        document.getElementById('config-modal-close').addEventListener('click', () => this.closeModal('config-modal'));
        document.getElementById('delete-modal-close').addEventListener('click', () => this.closeModal('delete-modal'));
        document.getElementById('btn-cancel-delete').addEventListener('click', () => this.closeModal('delete-modal'));

        // Form submission
        document.getElementById('instrument-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveInstrument();
        });

        // Type selection
        document.getElementById('input-type').addEventListener('change', (e) => {
            this.updateParameterFields(e.target.value);
        });

        // Click outside modal to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
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
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('connection-text');

        if (connected) {
            indicator.classList.add('connected');
            text.textContent = 'Connected';
        } else {
            indicator.classList.remove('connected');
            text.textContent = 'Disconnected';
        }
    }

    async loadInstrumentTypes() {
        try {
            const response = await fetch('/api/instrument-types');
            const data = await response.json();
            this.instrumentTypes = data.types;
        } catch (error) {
            console.error('Failed to load instrument types:', error);
            this.showToast('Failed to load instrument types', 'error');
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

            document.getElementById('instrument-count').textContent = data.simulators.length;

            this.renderSimulators();

            if (this.currentView === 'instruments') {
                this.renderInstrumentsTable();
            }
        } catch (error) {
            console.error('Failed to load simulators:', error);
            this.showToast('Failed to load simulators', 'error');
        }
    }

    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            document.getElementById('update-rate').textContent = `${data.statistics.update_rate.toFixed(1)} Hz`;
        } catch (error) {
            console.error('Failed to load status:', error);
        }

        // Refresh every 2 seconds
        setTimeout(() => this.loadStatus(), 2000);
    }

    async startSimulation() {
        try {
            await fetch('/api/control/start', { method: 'POST' });
            this.showToast('Simulation started', 'success');
        } catch (error) {
            console.error('Failed to start simulation:', error);
            this.showToast('Failed to start simulation', 'error');
        }
    }

    async stopSimulation() {
        try {
            await fetch('/api/control/stop', { method: 'POST' });
            this.showToast('Simulation stopped', 'info');
        } catch (error) {
            console.error('Failed to stop simulation:', error);
            this.showToast('Failed to stop simulation', 'error');
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
                <div class="data-row">
                    <span class="data-label">Loading...</span>
                </div>
            </div>
            <div class="simulator-actions">
                <button class="btn-small btn-edit" onclick="app.editInstrument('${id}')">
                    <i class="fas fa-edit"></i> Configure
                </button>
                <button class="btn-small btn-delete" onclick="app.confirmDeleteInstrument('${id}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
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
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.speed_percent}%"></div>
                </div>
            </div>
            <div class="data-row">
                <span class="data-label">Pressure</span>
                <span class="data-value">${data.pressure_bar.toFixed(2)} bar</span>
            </div>
            <div class="data-row">
                <span class="data-label">Flow</span>
                <span class="data-value">${data.flow_lpm.toFixed(1)} L/min</span>
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
                    <div class="progress-fill" style="width: ${Math.min(100, (data.flow_lpm / 100) * 100)}%"></div>
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
        `;
    }

    renderRegValveData(data) {
        return `
            <div class="data-row">
                <span class="data-label">Position</span>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.position_percent}%"></div>
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
                <span class="data-label">System Safe</span>
                <span class="data-value">
                    ${data.system_safe ? 'SAFE' : 'NOT SAFE'}
                    <span class="indicator ${data.system_safe ? 'indicator-on' : 'indicator-alarm'}"></span>
                </span>
            </div>
        `;
    }

    // Instruments Table View
    renderInstrumentsTable() {
        const container = document.getElementById('instruments-table-container');

        if (Object.keys(this.simulators).length === 0) {
            container.innerHTML = '<p class="placeholder-content">No instruments configured. Click "Add Instrument" to get started.</p>';
            return;
        }

        let html = '<table class="instruments-table"><thead><tr><th>ID</th><th>Type</th><th>Parameters</th><th>Actions</th></tr></thead><tbody>';

        Object.entries(this.simulators).forEach(([id, sim]) => {
            const typeName = this.getTypeName(sim.type);
            const paramCount = Object.keys(sim.config || {}).length;

            html += `
                <tr>
                    <td><strong>${id}</strong></td>
                    <td><span class="simulator-type">${typeName}</span></td>
                    <td>${paramCount} parameters</td>
                    <td>
                        <button class="btn-small btn-edit" onclick="app.editInstrument('${id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn-small btn-delete" onclick="app.confirmDeleteInstrument('${id}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // Modal Management
    showAddInstrumentModal() {
        this.editingInstrument = null;
        document.getElementById('modal-title').textContent = 'Add Instrument';
        document.getElementById('instrument-form').reset();
        document.getElementById('parameters-fields').innerHTML = '<p class="text-muted">Select an instrument type to configure parameters.</p>';
        document.getElementById('io-fields').innerHTML = '';
        this.openModal('instrument-modal');
    }

    async editInstrument(id) {
        this.editingInstrument = id;
        const sim = this.simulators[id];

        if (!sim) {
            this.showToast('Instrument not found', 'error');
            return;
        }

        // Load full instrument details
        try {
            const response = await fetch(`/api/simulators/${id}`);
            const data = await response.json();

            document.getElementById('modal-title').textContent = `Edit ${id}`;
            document.getElementById('input-id').value = data.id;
            document.getElementById('input-id').disabled = true;

            const type = data.type.replace('Simulator', '').toLowerCase();
            if (type === 'regvalve') {
                document.getElementById('input-type').value = 'reg_valve';
            } else {
                document.getElementById('input-type').value = type;
            }

            this.updateParameterFields(document.getElementById('input-type').value, data.config);

            this.openModal('instrument-modal');
        } catch (error) {
            console.error('Failed to load instrument details:', error);
            this.showToast('Failed to load instrument details', 'error');
        }
    }

    updateParameterFields(type, currentValues = {}) {
        const container = document.getElementById('parameters-fields');
        const ioContainer = document.getElementById('io-fields');

        if (!type || !this.instrumentTypes[type]) {
            container.innerHTML = '<p class="text-muted">Select an instrument type to configure parameters.</p>';
            ioContainer.innerHTML = '';
            return;
        }

        const typeInfo = this.instrumentTypes[type];

        // Render parameter fields
        let html = '';
        Object.entries(typeInfo.parameters).forEach(([paramName, paramInfo]) => {
            const value = currentValues[paramName] !== undefined ? currentValues[paramName] : paramInfo.default;

            html += `<div class="form-group">`;
            html += `<label>${paramInfo.label}</label>`;

            if (paramInfo.type === 'boolean') {
                html += `<input type="checkbox" name="param_${paramName}" ${value ? 'checked' : ''}>`;
            } else if (paramInfo.type === 'select') {
                html += `<select name="param_${paramName}">`;
                paramInfo.options.forEach(opt => {
                    html += `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`;
                });
                html += `</select>`;
            } else {
                html += `<input type="number" name="param_${paramName}" value="${value}" step="any">`;
            }

            html += `</div>`;
        });

        container.innerHTML = html;

        // Render I/O configuration hint
        ioContainer.innerHTML = `
            <p class="text-muted">
                <i class="fas fa-info-circle"></i> I/O configuration will be available in a future update.
                For now, edit the YAML configuration file directly for I/O settings.
            </p>
        `;
    }

    async saveInstrument() {
        const form = document.getElementById('instrument-form');
        const formData = new FormData(form);

        const id = formData.get('id');
        const type = formData.get('type');

        if (!id || !type) {
            this.showToast('Please fill in all required fields', 'error');
            return;
        }

        // Build parameters object
        const parameters = {};
        for (const [key, value] of formData.entries()) {
            if (key.startsWith('param_')) {
                const paramName = key.replace('param_', '');
                const input = form.elements[key];

                if (input.type === 'checkbox') {
                    parameters[paramName] = input.checked;
                } else if (input.type === 'number') {
                    parameters[paramName] = parseFloat(value);
                } else {
                    parameters[paramName] = value;
                }
            }
        }

        const instrument = {
            id: id,
            type: type,
            parameters: parameters,
            io: {},  // Will be configured separately
            links: {}
        };

        try {
            let response;
            if (this.editingInstrument) {
                // Update existing
                response = await fetch(`/api/simulators/${this.editingInstrument}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(instrument)
                });
            } else {
                // Create new
                response = await fetch('/api/simulators', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(instrument)
                });
            }

            if (response.ok) {
                this.closeModal('instrument-modal');
                this.showToast(`Instrument ${this.editingInstrument ? 'updated' : 'added'} successfully`, 'success');
                await this.loadSimulators();
                document.getElementById('input-id').disabled = false;
            } else {
                const error = await response.json();
                this.showToast(`Failed: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Failed to save instrument:', error);
            this.showToast('Failed to save instrument', 'error');
        }
    }

    confirmDeleteInstrument(id) {
        this.editingInstrument = id;
        document.getElementById('delete-instrument-name').textContent = id;
        this.openModal('delete-modal');

        document.getElementById('btn-confirm-delete').onclick = () => this.deleteInstrument(id);
    }

    async deleteInstrument(id) {
        try {
            const response = await fetch(`/api/simulators/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.closeModal('delete-modal');
                this.showToast(`Instrument ${id} deleted`, 'success');
                await this.loadSimulators();
            } else {
                const error = await response.json();
                this.showToast(`Failed: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Failed to delete instrument:', error);
            this.showToast('Failed to delete instrument', 'error');
        }
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                container.removeChild(toast);
            }, 300);
        }, 3000);
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SimulatorApp();
});
