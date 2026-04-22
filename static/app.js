/**
 * ShadowSync — Kinetic Ledger Frontend v3.0

 * Omni-Category Supply Chain Intelligence Dashboard
 * Handles: WebSocket, Charts, CRUD, PDF/CSV export, feedback, side-panel
 */

// ══════════════════════════════════════════════
//  GLOBAL STATE
// ══════════════════════════════════════════════
const state = {
    simulatorRunning: true,
    dataMode: 'synthetic',
    feedEvents: [],
    ws: null,
    wsRetries: 0,
    maxRetries: 20,
    charts: {},
    toastTimer: null,
    shadowFilter: '',
    txnFilter: '',
    lastStats: null,
};

// ══════════════════════════════════════════════
//  INITIALIZATION
// ══════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    connectWebSocket();
    fetchAllData();
});

function fetchAllData() {
    // Note: Backend handles auth redirects for the root route.
    // Client-side document.cookie check fails for HttpOnly tokens.
    console.log('[INIT] Fetching enterprise supply chain data...');
    fetchStats();
    fetchShadows();
    fetchTransactions();
    fetchProcurement();
    fetchVendors();
    fetchInventory();
    fetchRecommendations();
    fetchAuditLog();
    fetchOpsInsights();
    fetchPriorityQueue(); // Also fetch for urgent actions panel
    fetchTrends(); // Trend insights dashboard
}

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/login';
    } catch (e) {
        window.location.href = '/login';
    }
}

// ══════════════════════════════════════════════
//  TAB NAVIGATION
// ══════════════════════════════════════════════
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const tab = document.getElementById(`tab-${tabName}`);
    if (tab) tab.classList.add('active');

    const navItems = document.querySelectorAll('.nav-item');
    const tabIndex = ['overview', 'priority', 'shadows', 'transactions', 'procurement', 'vendors', 'inventory', 'audit'];
    const idx = tabIndex.indexOf(tabName);
    if (idx >= 0 && navItems[idx]) navItems[idx].classList.add('active');

    // Load priority-specific data if priority tab
    if (tabName === 'priority') {
        fetchPriorityQueue();
        fetchRootCause();
        fetchActionQueue();
    }
}

// ══════════════════════════════════════════════
//  WEBSOCKET
// ══════════════════════════════════════════════
function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${location.host}/ws`);
    state.ws = ws;

    ws.onopen = () => {
        state.wsRetries = 0;
        console.log('[WS] Connected');
        updateLiveBadge(true);
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWSMessage(data);
        } catch (e) {
            console.warn('[WS] Parse error:', e);
        }
    };

    ws.onclose = () => {
        updateLiveBadge(false);
        if (state.wsRetries < state.maxRetries) {
            state.wsRetries++;
            setTimeout(connectWebSocket, Math.min(2000 * state.wsRetries, 15000));
        }
    };

    ws.onerror = () => ws.close();
}

function handleWSMessage(data) {
    if (data.type === 'stats_update' || data.type === 'stats') {
        updateStats(data.data);
    } else if (data.type === 'new_shadow') {
        const s = data.data;
        addFeedEvent('<span class="material-icons-outlined" style="font-size:16px;color:var(--accent-red)">gpp_maybe</span>', `Integrity Alert: <strong>${s.vendor}</strong> — $${Number(s.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}`);

        fetchShadows();
        fetchStats();
    } else if (data.type === 'alert') {
        const msg = typeof data.data === 'string' ? data.data : (data.data?.message || 'System alert');
        addFeedEvent('<span class="material-icons-outlined" style="font-size:16px;color:var(--accent-amber)">warning_amber</span>', msg);
    } else if (data.type === 'new_transaction') {
        addFeedEvent('<span class="material-icons-outlined" style="font-size:16px;color:var(--brand-primary-light)">receipt_long</span>', `Transaction: <strong>${data.data.vendor || 'Unknown'}</strong> — $${Number(data.data.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`);
    } else if (data.type === 'connection_info') {
        const el = document.getElementById('clientCount');
        if (el) el.textContent = `${data.data.clients} connected`;
        state.simulatorRunning = data.data.simulator;
        updateLiveBadge(true);
    } else if (data.type === 'recommendations') {
        renderRecommendations(data.data);
    } else if (data.type === 'pong') {
        const el = document.getElementById('clientCount');
        if (el) el.textContent = `${data.data.clients} connected`;
    }
}

function updateLiveBadge(live) {
    const dot = document.getElementById('pulseDot');
    const label = document.getElementById('liveLabel');
    if (dot) { dot.className = `pulse-dot ${live ? 'live' : 'stopped'}`; }
    if (label) { label.textContent = live && state.simulatorRunning ? 'LIVE' : 'PAUSED'; }
}

// ══════════════════════════════════════════════
//  SIMULATOR TOGGLE
// ══════════════════════════════════════════════
async function toggleSimulator() {
    try {
        const action = state.simulatorRunning ? 'stop' : 'start';
        const res = await fetch(`/api/simulator/${action}`, { method: 'POST' });
        const data = await res.json();
        state.simulatorRunning = !state.simulatorRunning;
        updateLiveBadge(state.ws && state.ws.readyState === WebSocket.OPEN);
        showToast(state.simulatorRunning ? 'Simulator started' : 'Simulator paused', 'info');
    } catch (e) {
        console.warn('[SIM] Toggle failed:', e);
        // Toggle locally anyway
        state.simulatorRunning = !state.simulatorRunning;
        updateLiveBadge(state.ws && state.ws.readyState === WebSocket.OPEN);
    }
}

// ══════════════════════════════════════════════
//  DATA MODE TOGGLE
// ══════════════════════════════════════════════
async function setDataMode(mode) {
    state.dataMode = mode;
    const items = document.querySelectorAll('#modeToggle .toggle-item');
    items.forEach(i => i.classList.remove('active', 'prod'));
    if (mode === 'real') {
        items[1].classList.add('active', 'prod');
    } else {
        items[0].classList.add('active');
    }

    try {
        const res = await fetch('/api/set-mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode })
        });
        const data = await res.json();
        
        if (mode === 'real') {
            showToast('PRODUCTION TELEMETRY ACTIVATED: SF Infrastructure protocols engaged.', 'success');
            addFeedEvent('<span class="material-icons-outlined" style="font-size:16px;color:var(--brand-secondary)">security</span>', 'System entering Production Mode: High-fidelity SF dataset active.');
        } else {
            showToast('Restored Synthetic Modeling state.', 'info');
            addFeedEvent('<span class="material-icons-outlined" style="font-size:16px;color:var(--brand-secondary)">science</span>', 'System entering Synthetic Mode: Sandbox dataset active.');
        }
        
        setTimeout(fetchAllData, 1500);
    } catch (e) {
        showToast('Mode switch failed', 'error');
    }
}

// ══════════════════════════════════════════════
//  STATS
// ══════════════════════════════════════════════
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        updateStats(data);
    } catch (e) { console.warn('[STATS] Fetch failed:', e); }
}

function updateStats(data) {
    state.lastStats = data;
    const exposure = data.total_exposure ?? data.exposure ?? 0;
    const shadowRate = data.shadow_rate ?? 0;
    const dq = data.detection_quality || data.avg_risk_score || 'High';
    const invHealth = data.inventory_health || data.pending_actions || '—';

    animateValue('stat-exposure', `$${Number(exposure).toLocaleString('en-US', { minimumFractionDigits: 2 })}`);
    animateValue('stat-shadow-rate', `${(Number(shadowRate) * 100).toFixed(1)}%`);

    const dqEl = document.getElementById('stat-dq');
    if (dqEl) {
        if (typeof dq === 'number') {
            dqEl.textContent = dq > 0.7 ? 'High' : dq > 0.4 ? 'Medium' : 'Low';
        } else {
            dqEl.textContent = dq;
        }
    }

    const invEl = document.getElementById('stat-inv');
    if (invEl) {
        if (typeof invHealth === 'number') {
            invEl.textContent = `${invHealth} pending`;
        } else {
            invEl.textContent = invHealth;
        }
    }

    // Chart updates
    updateRiskTrendChart(exposure);
}

function animateValue(elementId, targetText) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = targetText;
    el.style.transition = 'transform 0.3s ease';
    el.style.transform = 'scale(1.05)';
    setTimeout(() => { el.style.transform = 'scale(1)'; }, 300);
}

// ══════════════════════════════════════════════
//  CHARTS
// ══════════════════════════════════════════════
const chartColors = {
    navy: 'rgba(0, 35, 75, 0.8)',
    navyBg: 'rgba(0, 35, 75, 0.08)',
    indigo: 'rgba(0, 35, 75, 0.8)',
    indigoBg: 'rgba(0, 35, 75, 0.08)',
    teal: 'rgba(0, 106, 106, 0.8)',
    tealBg: 'rgba(0, 106, 106, 0.08)',
    emerald: 'rgba(0, 106, 106, 0.8)',
    emeraldBg: 'rgba(0, 106, 106, 0.08)',
    purple: 'rgba(103, 80, 164, 0.8)',
    purpleBg: 'rgba(103, 80, 164, 0.08)',
    red: 'rgba(186, 26, 26, 0.8)',
    redBg: 'rgba(186, 26, 26, 0.08)',
    amber: 'rgba(255, 191, 0, 0.85)',
    amberBg: 'rgba(255, 191, 0, 0.1)',
    blue: 'rgba(59, 130, 246, 0.8)',
    blueBg: 'rgba(59, 130, 246, 0.08)',
    cyan: 'rgba(0, 106, 106, 0.7)',
    rose: 'rgba(186, 26, 26, 0.8)',
    slate: 'rgba(116, 119, 127, 0.3)',
};

Chart.defaults.color = '#74777f';
Chart.defaults.borderColor = 'rgba(25, 28, 29, 0.06)';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 8;
Chart.defaults.plugins.legend.labels.padding = 16;

function initCharts() {
    if (typeof Chart === 'undefined') {
        console.warn('[CHARTS] Chart.js not loaded. Visualizations disabled.');
        return;
    }
    try {
    // Risk Trend (Line)
    state.charts.riskTrend = new Chart(document.getElementById('chartRiskTrend'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Exposure ($)',
                data: [],
                borderColor: chartColors.navy,
                backgroundColor: chartColors.navyBg,
                fill: true, tension: 0.4, pointRadius: 3, pointHoverRadius: 6,
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(25, 28, 29, 0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });

    // Shadow Ratio (Doughnut)
    state.charts.shadowRatio = new Chart(document.getElementById('chartShadowRatio'), {
        type: 'doughnut',
        data: {
            labels: ['Matched', 'Shadow', 'Resolved'],
            datasets: [{
                data: [60, 30, 10],
                backgroundColor: [chartColors.teal, chartColors.red, chartColors.navy],
                borderWidth: 0, hoverOffset: 8,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: { legend: { position: 'bottom' } }
        }
    });

    // Department Risk (Bar)
    state.charts.deptRisk = new Chart(document.getElementById('chartDeptRisk'), {
        type: 'bar',
        data: {
            labels: ['Maintenance', 'Production', 'Engineering', 'Admin', 'Logistics'],
            datasets: [{
                label: 'Shadow Count',
                data: [0, 0, 0, 0, 0],
                backgroundColor: [chartColors.red, chartColors.amber, chartColors.navy, chartColors.purple, chartColors.teal],
                borderRadius: 6, borderSkipped: false, maxBarThickness: 40,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true, grid: { color: 'rgba(25, 28, 29, 0.05)' } },
                y: { grid: { display: false } }
            }
        }
    });

    // Categories (Polar)
    state.charts.categories = new Chart(document.getElementById('chartCategories'), {
        type: 'polarArea',
        data: {
            labels: ['Pumps', 'Electrical', 'Safety', 'Tools', 'Fasteners'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    'rgba(0,35,75,0.45)', 'rgba(255,191,0,0.5)',
                    'rgba(0,106,106,0.45)', 'rgba(186,26,26,0.45)',
                    'rgba(103,80,164,0.45)'
                ],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { font: { size: 10 } } } },
            scales: { r: { grid: { color: 'rgba(25, 28, 29, 0.06)' }, ticks: { display: false } } }
        }
    });
    } catch (e) {
        console.error('[CHARTS] Initialization failed:', e);
    }
}

function updateRiskTrendChart(exposure) {
    const chart = state.charts.riskTrend;
    if (!chart) return;
    const now = new Date();
    const label = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(Number(exposure));
    if (chart.data.labels.length > 20) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update('none');
}

function updateChartsFromData(shadows, transactions) {
    // Shadow Ratio
    if (state.charts.shadowRatio && transactions) {
        const matched = transactions.filter(t => t.matched_po_id && t.matched_po_id !== 'DISMISSED' && !t.is_shadow).length;
        const shadow = transactions.filter(t => t.is_shadow).length;
        const resolved = shadows ? shadows.filter(s => s.status === 'Resolved').length : 0;
        state.charts.shadowRatio.data.datasets[0].data = [matched, shadow, resolved];
        state.charts.shadowRatio.update('none');
    }

    // Department Risk
    if (state.charts.deptRisk && shadows) {
        const deptMap = {};
        shadows.filter(s => s.status === 'Pending').forEach(s => {
            const dept = s.department || 'Unknown';
            deptMap[dept] = (deptMap[dept] || 0) + 1;
        });
        const sortedDepts = Object.entries(deptMap).sort((a, b) => b[1] - a[1]).slice(0, 5);
        state.charts.deptRisk.data.labels = sortedDepts.map(d => d[0]);
        state.charts.deptRisk.data.datasets[0].data = sortedDepts.map(d => d[1]);
        state.charts.deptRisk.update('none');
    }

    // Categories
    if (state.charts.categories && shadows) {
        const catMap = {};
        shadows.forEach(s => {
            const cat = s.item_category || 'General';
            catMap[cat] = (catMap[cat] || 0) + 1;
        });
        const sortedCats = Object.entries(catMap).sort((a, b) => b[1] - a[1]).slice(0, 6);
        state.charts.categories.data.labels = sortedCats.map(c => c[0]);
        state.charts.categories.data.datasets[0].data = sortedCats.map(c => c[1]);
        state.charts.categories.update('none');
    }
}

// ══════════════════════════════════════════════
//  LIVE FEED
// ══════════════════════════════════════════════
function addFeedEvent(icon, text) {
    const now = new Date();
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

    state.feedEvents.unshift({ icon, text, time });
    if (state.feedEvents.length > 50) state.feedEvents.pop();

    const feed = document.getElementById('activityFeed');
    if (!feed) return;

    const el = document.createElement('div');
    el.className = 'feed-item';
    el.innerHTML = `
        <span class="feed-time">${time}</span>
        <span class="feed-icon">${icon}</span>
        <span class="feed-text">${text}</span>
    `;

    if (feed.children.length === 1 && feed.children[0].textContent.includes('Waiting')) {
        feed.innerHTML = '';
    }

    feed.insertBefore(el, feed.firstChild);
    if (feed.children.length > 30) feed.removeChild(feed.lastChild);

    const counter = document.getElementById('feedCount');
    if (counter) counter.textContent = `${Math.min(state.feedEvents.length, 30)} events`;
}

// ══════════════════════════════════════════════
//  SHADOW DETECTIONS
// ══════════════════════════════════════════════
let allShadowsCache = [];

async function fetchShadows() {
    try {
        const res = await fetch('/api/shadows');
        const data = await res.json();
        allShadowsCache = data;
        renderShadowTable(data);
        return data;
    } catch (e) {
        console.warn('[SHADOWS] Fetch failed');
        return [];
    }
}

function renderShadowTable(shadows) {
    const tbody = document.getElementById('shadow-table-body');
    if (!tbody) return;

    const filtered = shadows.filter(s => {
        if (!state.shadowFilter) return true;
        const q = state.shadowFilter.toLowerCase();
        return (s.vendor || '').toLowerCase().includes(q) ||
               (s.description || '').toLowerCase().includes(q) ||
               (s.item_category || '').toLowerCase().includes(q);
    });

    tbody.innerHTML = filtered.map(s => {
        const risk = Number(s.risk_score || 0);
        const conf = Number(s.confidence_score || 0.8);
        const riskClass = risk > 0.6 ? 'high' : risk > 0.35 ? 'medium' : 'low';
        const statusClass = s.status === 'Pending' ? 'pending' : s.status === 'Resolved' ? 'resolved' : 'matched';
        const isPending = s.status === 'Pending';

        // Premium Risk Formatting
        const riskLabel = riskClass.charAt(0).toUpperCase() + riskClass.slice(1);
        const riskColor = riskClass === 'high' ? 'var(--accent-red)' : riskClass === 'medium' ? 'var(--accent-amber)' : 'var(--accent-emerald)';
        const riskMarkup = `
            <div style="display:flex; align-items:center; gap:6px;">
                <div style="width:8px;height:8px;border-radius:50%;background:${riskColor};box-shadow:0 0 8px ${riskColor}"></div>
                <span style="font-weight:600;font-size:12px;color:var(--text-base)">${riskLabel}</span>
            </div>
        `;

        // Modern Confidence Bar
        const confColor = conf > 0.8 ? 'var(--accent-emerald)' : 'var(--accent-amber)';
        const confMarkup = `
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:40px;height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden;">
                    <div style="width:${conf*100}%;height:100%;background:${confColor};border-radius:2px;"></div>
                </div>
                <span style="font-size:11px;color:var(--text-muted)">${(conf * 100).toFixed(0)}%</span>
            </div>
        `;

        return `<tr>
            <td>${s.date || '—'}</td>
            <td><span class="text-truncate">${s.vendor || '—'}</span></td>
            <td><span class="text-truncate" style="max-width:200px">${s.description || '—'}</span></td>
            <td class="amount">$${Number(s.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td>${riskMarkup}</td>
            <td>${confMarkup}</td>
            <td><span style="font-size:11px;color:var(--text-muted)">${s.item_category || 'General'}</span></td>
            <td><span class="badge badge-${statusClass}">${s.status}</span></td>
            <td class="action-buttons">
                ${isPending ? `
                    <div style="display:flex; gap:4px; align-items:center;">
                        <button class="btn btn-xs btn-primary" onclick="resolveShadow(${s.id})" title="Approve & Covert">Approve</button>
                        <button class="btn btn-xs" style="background:var(--bg-card);border:1px solid rgba(255,255,255,0.1);" onclick="openDecisionPanel(${s.id})" title="Review details">Review</button>
                        <button class="btn btn-xs btn-ghost" style="color:var(--text-muted); padding:0 6px;" onclick="dismissShadow(${s.id})" title="Dismiss Record">Reject</button>
                    </div>
                ` : `<span style="font-size:10px;color:var(--text-subtle)">${s.resolved_po_id || '—'}</span>`}
            </td>
        </tr>`;
    }).join('');

    // Update chart with shadow data
    fetchTransactions().then(txns => typeof updateChartsFromData === 'function' && updateChartsFromData(shadows, txns));
}


function filterShadows(val) {
    state.shadowFilter = val.toLowerCase();
    renderShadowTable(allShadowsCache);
}

// ══════════════════════════════════════════════
//  TRANSACTIONS
// ══════════════════════════════════════════════
async function fetchTransactions() {
    try {
        const res = await fetch('/api/transactions');
        const data = await res.json();
        renderTransactionTable(data);
        return data;
    } catch (e) {
        console.warn('[TXN] Fetch failed');
        return [];
    }
}

let allTxnsCache = [];
function renderTransactionTable(txns) {
    const tbody = document.getElementById('txn-table-body');
    if (!tbody) return;

    allTxnsCache = txns;
    const filtered = txns.filter(t => {
        if (!state.txnFilter) return true;
        const q = state.txnFilter.toLowerCase();
        return (t.vendor || '').toLowerCase().includes(q) ||
               (t.description || '').toLowerCase().includes(q) ||
               (t.department || '').toLowerCase().includes(q) ||
               (t.id || '').toLowerCase().includes(q);
    });

    tbody.innerHTML = filtered.map(t => {
        let statusBadge;
        if (t.is_shadow) {
            statusBadge = '<span class="badge badge-shadow">Shadow</span>';
        } else if (t.matched_po_id === 'DISMISSED') {
            statusBadge = '<span class="badge" style="background:rgba(113,113,122,0.1);color:var(--text-subtle)">Dismissed</span>';
        } else if (t.matched_po_id) {
            statusBadge = '<span class="badge badge-matched">Matched</span>';
        } else {
            statusBadge = '<span class="badge" style="background:rgba(255,255,255,0.03);color:var(--text-subtle)">Unprocessed</span>';
        }

        return `<tr>
            <td style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text-subtle)">${t.id}</td>
            <td>${t.date || '—'}</td>
            <td>${t.vendor || '—'}</td>
            <td><span class="text-truncate" style="max-width:200px">${t.description || '—'}</span></td>
            <td class="amount">$${Number(t.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td>${t.department || '—'}</td>
            <td style="font-size:11px">${t.payment_type || '—'}</td>
            <td>${statusBadge}</td>
        </tr>`;
    }).join('');
}

function filterTransactions(val) {
    state.txnFilter = val.toLowerCase();
    renderTransactionTable(allTxnsCache);
}

// ══════════════════════════════════════════════
//  PRIORITY QUEUE ENGINE
// ══════════════════════════════════════════════
async function fetchPriorityQueue() {
    try {
        const res = await fetch('/api/priority-queue?limit=20');
        const data = await res.json();
        renderPriorityTable(data.items || []);
        updatePrioritySummary(data);
        renderUrgentActions(data.items || []); // Also update urgent panel
    } catch (e) {
        console.warn('[PRIORITY] Fetch failed:', e);
    }
}

async function fetchTrends() {
    try {
        const res = await fetch('/api/trends?period=week');
        const data = await res.json();
        renderTrends(data);
    } catch (e) {
        console.warn('[TRENDS] Fetch failed:', e);
    }
}

function renderTrends(data) {
    const elThisWeek = document.getElementById('trend-this-week');
    const elWeekChange = document.getElementById('trend-week-change');
    const elTopVendor = document.getElementById('trend-top-vendor');
    const elTopDept = document.getElementById('trend-top-dept');
    const elInsight = document.getElementById('trend-insight');
    const elUpdated = document.getElementById('trend-updated');

    if (!elThisWeek) return;

    // Update metrics
    elThisWeek.textContent = (data.this_week_count || 0).toLocaleString();

    const changePct = data.week_over_week_change_pct || 0;
    elWeekChange.textContent = `${changePct > 0 ? '+' : ''}${changePct}%`;
    elWeekChange.style.color = changePct > 0 ? 'var(--accent-red)' : changePct < 0 ? 'var(--accent-emerald)' : 'var(--text-muted)';

    // Top vendor
    const vendorBreakdown = data.shadow_by_vendor || {};
    const topVendor = Object.keys(vendorBreakdown).sort((a,b) => vendorBreakdown[b] - vendorBreakdown[a])[0];
    const topVendorCount = topVendor ? vendorBreakdown[topVendor] : 0;
    elTopVendor.textContent = topVendor ? `${topVendor} (${topVendorCount} items)` : '—';

    // Top department
    const deptBreakdown = data.shadow_by_department || {};
    const topDept = Object.keys(deptBreakdown).sort((a,b) => deptBreakdown[b] - deptBreakdown[a])[0];
    const topDeptCount = topDept ? deptBreakdown[topDept] : 0;
    elTopDept.textContent = topDept ? `${topDept} (${topDeptCount} items)` : '—';

    // Generate insight text
    if (changePct > 20) {
        elInsight.textContent = `Shadow activity increased ${changePct}% compared to last week. Immediate review recommended.`;
    } else if (changePct < -20) {
        elInsight.textContent = `Shadow procurement decreased ${Math.abs(changePct)}% — controls are working effectively.`;
    } else {
        elInsight.textContent = `Shadow activity is stable (${changePct}% change). Continue monitoring top vendors and departments.`;
    }

    if (elUpdated) {
        const now = new Date();
        elUpdated.textContent = `Updated ${now.toLocaleTimeString()}`;
    }
}

function renderPriorityTable(items) {
    const tbody = document.getElementById('priority-table-body');
    if (!tbody) return;

    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No pending items in priority queue</td></tr>';
        return;
    }

    tbody.innerHTML = items.map(item => {
        const priorityClass = item.priority_label === 'Critical' ? 'critical' :
                              item.priority_label === 'High' ? 'high' :
                              item.priority_label === 'Medium' ? 'medium' : 'low';
        const riskPct = ((item.risk_score || 0) * 100).toFixed(0);
        const priorityScore = ((item.priority_score || 0) * 100).toFixed(0);
        const loss = Number(item.estimated_loss || 0);

        const riskLevel = riskPct > 60 ? 'High' : riskPct > 35 ? 'Medium' : 'Low';
        const riskColor = riskPct > 60 ? 'var(--accent-red)' : riskPct > 35 ? 'var(--accent-amber)' : 'var(--accent-emerald)';
        const riskMarkup = `
            <div style="display:flex; align-items:center; gap:6px;">
                <div style="width:8px;height:8px;border-radius:50%;background:${riskColor};box-shadow:0 0 8px ${riskColor}"></div>
                <span style="font-weight:600;font-size:12px;color:var(--text-base)">${riskLevel}</span>
            </div>
        `;

        const priorityColor = priorityClass === 'critical' ? 'var(--accent-red)' : priorityClass === 'high' ? 'var(--accent-amber)' : 'var(--accent-emerald)';
        const priorityScoreMarkup = `
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:40px;height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden;">
                    <div style="width:${priorityScore}%;height:100%;background:${priorityColor};border-radius:2px;"></div>
                </div>
                <span style="font-size:11px;color:var(--text-muted)">${priorityScore}</span>
            </div>`;

        return `<tr>
            <td><span class="badge badge-${priorityClass}">${item.priority_label || 'Low'}</span></td>
            <td>${item.date || '—'}</td>
            <td><span class="text-truncate">${item.vendor || '—'}</span></td>
            <td><span class="text-truncate" style="max-width:200px">${item.description || '—'}</span></td>
            <td class="amount">$${Number(item.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td>${riskMarkup}</td>
            <td>${priorityScoreMarkup}</td>
            <td class="amount" style="color:${loss > 1000 ? 'var(--accent-red)' : 'var(--text-muted)'}">$${loss.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td style="text-align:center">${item.frequency || 1}×</td>
            <td class="action-buttons">
                <div style="display:flex; gap:4px; align-items:center;">
                    <button class="btn btn-xs btn-primary" onclick="takeAction(${item.id}, 'convert_to_po')" title="Convert to Procurement Order">Approve</button>
                    <button class="btn btn-xs" style="background:var(--bg-card);border:1px solid rgba(255,255,255,0.1);" onclick="takeAction(${item.id}, 'escalate_audit')" title="Escalate for Audit">Escalate</button>
                    <button class="btn btn-xs btn-ghost" style="color:var(--text-muted); padding:0 6px;" onclick="takeAction(${item.id}, 'mark_justified')" title="Mark as Justified">Justify</button>
                </div>
            </td>
        </tr>`;
    }).join('');
}

// ══════════════════════════════════════════════
//  URGENT ACTIONS PANEL
// ══════════════════════════════════════════════
function renderUrgentActions(items) {
    const container = document.getElementById('urgent-actions-list');
    if (!container) return;

    const urgent = items.filter(i => i.priority_label === 'Critical' || i.priority_label === 'High').slice(0, 5);
    if (!urgent.length) {
        // Fall back to top 5 regardless of label
        const top5 = items.slice(0, 5);
        if (!top5.length) {
            container.innerHTML = '<div class="text-muted small text-center" style="padding: 20px;">No urgent actions at this time — all clear ✓</div>';
            return;
        }
        container.innerHTML = top5.map(item => {
            const loss = Number(item.estimated_loss || 0);
            return `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; margin-bottom: 4px; background: var(--bg-card); border-radius: var(--radius-sm); border-left: 3px solid ${item.priority_label === 'Critical' ? 'var(--accent-red)' : 'var(--accent-amber)'};">
                <div style="flex: 1; overflow: hidden;">
                    <div style="font-size: 13px; font-weight: 600;">${item.vendor || 'Unknown'}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">${item.description || item.item_category || ''}</div>
                </div>
                <div style="text-align: right; margin-left: 10px;">
                    <div style="font-size: 14px; font-weight: 700;">$${Number(item.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                    <div style="font-size: 10px; color: var(--text-muted);">Est. loss: $${loss.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                </div>
                <div style="margin-left: 10px; display: flex; gap: 6px;">
                    <button class="btn btn-xs btn-primary" onclick="event.stopPropagation(); takeAction(${item.id}, 'convert_to_po')" title="Convert to PO">Approve</button>
                    <button class="btn btn-xs btn-ghost" style="background:var(--bg-card); border:1px solid rgba(255,255,255,0.2); color:var(--text-heading); min-width:60px" onclick="event.stopPropagation(); takeAction(${item.id}, 'escalate_audit')" title="Escalate">Review</button>
                </div>
            </div>`;
        }).join('');
        return;
    }

    container.innerHTML = urgent.map(item => {
        const loss = Number(item.estimated_loss || 0);
        return `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; margin-bottom: 4px; background: var(--bg-card); border-radius: var(--radius-sm); border-left: 3px solid ${item.priority_label === 'Critical' ? 'var(--accent-red)' : 'var(--accent-amber)'};">
            <div style="flex: 1; overflow: hidden;">
                <div style="font-size: 13px; font-weight: 600;">${item.vendor || 'Unknown'}</div>
                <div style="font-size: 11px; color: var(--text-muted);">${item.description || item.item_category || ''}</div>
            </div>
            <div style="text-align: right; margin-left: 10px;">
                <div style="font-size: 14px; font-weight: 700;">$${Number(item.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                <div style="font-size: 10px; color: var(--text-muted);">Est. loss: $${loss.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
            </div>
            <div style="margin-left: 10px; display: flex; gap: 6px;">
                <button class="btn btn-xs btn-primary" onclick="event.stopPropagation(); takeAction(${item.id}, 'convert_to_po')" title="Convert to PO">Approve</button>
                <button class="btn btn-xs btn-ghost" style="background:var(--bg-card); border:1px solid rgba(255,255,255,0.2); color:var(--text-heading); min-width:60px" onclick="event.stopPropagation(); takeAction(${item.id}, 'escalate_audit')" title="Escalate">Review</button>
            </div>
        </div>`;
    }).join('');
}

function updatePrioritySummary(data) {
    if (document.getElementById('critical-count')) {
        document.getElementById('critical-count').textContent = data.critical_count || 0;
    }
    if (document.getElementById('high-count')) {
        document.getElementById('high-count').textContent = data.high_count || 0;
    }
}

async function takeAction(shadowId, actionType, notes = '') {
    console.log(`[ACTION] Initiating: ${actionType} for Shadow ID: ${shadowId}`);
    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ shadow_id: shadowId, action_type: actionType, notes: notes })
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast(`Action "${actionType.replace('_', ' ')}" completed`, 'info');
            // Refresh all relevant queues
            fetchPriorityQueue();
            fetchProcurement();
            fetchRootCause();
        } else {
            showToast('Action failed', 'error');
        }
    } catch (e) {
        console.warn('[ACTION] Failed:', e);
        showToast('Action request failed', 'error');
    }
}

// ══════════════════════════════════════════════
//  ROOT CAUSE ANALYSIS
// ══════════════════════════════════════════════
async function fetchRootCause() {
    try {
        const res = await fetch('/api/root-cause');
        const data = await res.json();
        renderRootCauseSummary(data);
    } catch (e) {
        console.warn('[ROOT-CAUSE] Fetch failed:', e);
    }
}

function renderRootCauseSummary(data) {
    const container = document.getElementById('root-cause-summary');
    if (!container) return;

    const pv = data.primary_source || {};
    const pd = data.primary_department || {};
    const pc = data.primary_category || {};

    container.innerHTML = `
        <div style="padding: 15px;">
            <div style="margin-bottom: 15px; padding: 12px; background: rgba(239, 68, 68, 0.05); border-radius: var(--radius-md); border: 1px solid rgba(239, 68, 68, 0.1);">
                <div style="font-size: 10px; color: var(--accent-red); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Primary Source</div>
                <div style="font-size: 13px; color: var(--text-base); font-weight: 600;">${pv.vendor || 'N/A'}</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">${pv.percentage || 0}% of all shadow purchases ($${Number(pv.total_amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2})})</div>
            </div>

            <div style="margin-bottom: 15px; padding: 12px; background: rgba(245, 158, 11, 0.05); border-radius: var(--radius-md); border: 1px solid rgba(245, 158, 11, 0.1);">
                <div style="font-size: 10px; color: var(--accent-amber); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Primary Department</div>
                <div style="font-size: 13px; color: var(--text-base); font-weight: 600;">${pd.name || 'N/A'}</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">${pd.percentage || 0}% of shadow activity</div>
            </div>

            <div style="margin-bottom: 15px; padding: 12px; background: rgba(168, 85, 247, 0.05); border-radius: var(--radius-md); border: 1px solid rgba(168, 85, 247, 0.1);">
                <div style="font-size: 10px; color: var(--accent-purple); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Primary Category</div>
                <div style="font-size: 13px; color: var(--text-base); font-weight: 600;">${pc.name || 'N/A'}</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">${pc.percentage || 0}% of flagged items</div>
            </div>

            ${data.vendor_breakdown && data.vendor_breakdown.length > 0 ? `
            <div style="margin-top: 10px;">
                <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-bottom: 8px;">Vendor Breakdown</div>
                ${data.vendor_breakdown.slice(0, 5).map(v => `
                    <div style="display: flex; justify-content: space-between; padding: 4px 0; font-size: 11px;">
                        <span style="color: var(--text-base);">${v.vendor}</span>
                        <span style="color: var(--text-muted);">${v.count} items — $${Number(v.amount).toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
                    </div>
                `).join('')}
            </div>
            ` : ''}
        </div>
    `;
}

async function fetchActionQueue() {
    try {
        const res = await fetch('/api/action-queue');
        const data = await res.json();
        // Could render in a dedicated panel if desired
        state.actionQueue = data.actions || [];
    } catch (e) {
        console.warn('[ACTION-QUEUE] Fetch failed:', e);
    }
}

async function openHistoryPanel(shadowId) {
    try {
        const res = await fetch(`/api/history/${shadowId}`);
        const data = await res.json();
        // Show in decision panel or modal
        showHistoryModal(data);
    } catch (e) {
        console.warn('[HISTORY] Fetch failed:', e);
    }
}

function showHistoryModal(data) {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center;';
    const panel = document.createElement('div');
    panel.style.cssText = 'background:var(--bg-panel-solid);border-radius:var(--radius-lg);max-width:600px;width:90%;max-height:80vh;overflow-y:auto;border:1px solid var(--border-medium);';
    panel.innerHTML = `
        <div style="padding:20px;border-bottom:1px solid var(--border-subtle);">
            <h3 style="font-size:16px;margin:0;">Transaction History — Shadow #${data.shadow_id}</h3>
            <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Current Status: <strong>${data.status}</strong> | Risk Score: <strong>${data.original_risk}</strong></div>
        </div>
        <div style="padding:20px;">
            ${data.actions && data.actions.length > 0 ? `
                <h4 style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">Actions Taken (${data.total_actions})</h4>
                ${data.actions.map(a => `
                    <div style="padding:8px;margin-bottom:6px;background:var(--bg-card);border-radius:var(--radius-sm);border-left:3px solid var(--brand-primary);">
                        <div style="font-size:12px;font-weight:600;">${a.type.replace('_', ' ').toUpperCase()}</div>
                        <div style="font-size:10px;color:var(--text-muted);">${a.timestamp} — by ${a.user}</div>
                        ${a.notes ? `<div style="font-size:11px;color:var(--text-subtle);margin-top:2px;">${a.notes}</div>` : ''}
                    </div>
                `).join('')}
            ` : '<div style="font-size:11px;color:var(--text-muted);padding:10px;">No actions recorded yet.</div>'}
            ${data.feedbacks && data.feedbacks.length > 0 ? `
                <h4 style="font-size:12px;color:var(--text-muted);margin:15px 0 10px;">Feedback (${data.total_feedbacks})</h4>
                ${data.feedbacks.map(f => `
                    <div style="padding:8px;margin-bottom:6px;background:var(--bg-card);border-radius:var(--radius-sm);border-left:3px solid var(--accent-amber);">
                        <div style="font-size:12px;font-weight:600;">${f.type}</div>
                        <div style="font-size:10px;color:var(--text-muted);">${f.submitted_at}</div>
                        ${f.notes ? `<div style="font-size:11px;color:var(--text-subtle);margin-top:2px;">${f.notes}</div>` : ''}
                    </div>
                `).join('')}
            ` : ''}
        </div>
        <div style="padding:15px;border-top:1px solid var(--border-subtle);text-align:right;">
            <button class="close-history-btn" style="background:var(--bg-card);color:var(--text-base);border:1px solid var(--border-medium);padding:6px 16px;border-radius:var(--radius-sm);cursor:pointer;">Close</button>
        </div>
    `;
    overlay.appendChild(panel);
    panel.querySelector('.close-history-btn').addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    document.body.appendChild(overlay);
}

async function downloadPriorityQueue() {
    try {
        const res = await fetch('/api/priority-queue?limit=50');
        const data = await res.json();
        const items = data.items || [];

        let csv = 'Priority,Date,Vendor,Description,Amount,Risk Score,Priority Score,Est. Loss,Frequencyn';
        items.forEach(item => {
            csv += `"${item.priority_label}","${item.date}","${item.vendor || ''}","${item.description || ''}",${item.amount || 0},${item.risk_score || 0},${item.priority_score || 0},${item.estimated_loss || 0},${item.frequency || 1}n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ShadowSync_PriorityQueue_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Priority queue exported', 'info');
    } catch (e) {
        console.warn('[EXPORT] Priority queue export failed:', e);
        showToast('Export failed', 'error');
    }
}

// ══════════════════════════════════════════════
//  PROCUREMENT
// ══════════════════════════════════════════════
async function fetchProcurement() {
    try {
        const res = await fetch('/api/procurement');
        const data = await res.json();
        renderProcurementTable(data);
    } catch (e) { console.warn('[PO] Fetch failed'); }
}

function renderProcurementTable(pos) {
    const tbody = document.getElementById('po-table-body');
    if (!tbody) return;

    tbody.innerHTML = pos.map(p => {
        const statusClass = (p.status || '').includes('Resolved') ? 'resolved'
            : (p.status || '').includes('Received') ? 'received'
            : (p.status || '').includes('Ordered') ? 'ordered' : 'matched';

        return `<tr>
            <td style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--brand-secondary)">${p.id}</td>
            <td>${p.date || '—'}</td>
            <td>${p.vendor_name || '—'}</td>
            <td><span class="text-truncate">${p.item || '—'}</span></td>
            <td class="amount">$${Number(p.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td>${p.quantity || 1}</td>
            <td><span class="badge badge-${statusClass}">${p.status || '—'}</span></td>
            <td style="font-size:11px;color:var(--text-subtle)">${p.source || 'Manual'}</td>
            <td><button class="btn btn-xs btn-download" onclick="downloadPO('${p.id}')">📄 PDF</button></td>
        </tr>`;
    }).join('');
}

// ══════════════════════════════════════════════
//  VENDORS
// ══════════════════════════════════════════════
async function fetchVendors() {
    try {
        const res = await fetch('/api/vendors');
        const data = await res.json();
        renderVendorTable(data);
        renderOpsInsights(data);
    } catch (e) { console.warn('[VENDORS] Fetch failed'); }
}

function renderVendorTable(vendors) {
    const tbody = document.getElementById('vendor-table-body');
    if (!tbody) return;

    tbody.innerHTML = vendors.map(v => {
        const riskClass = v.risk_level === 'High' ? 'high' : v.risk_level === 'Medium' ? 'medium' : 'low';
        const trust = Number(v.trust_score || 0);
        const trustColor = trust > 70 ? 'var(--accent-emerald)' : trust > 40 ? 'var(--accent-amber)' : 'var(--accent-red)';

        return `<tr>
            <td><strong>${v.name || '—'}</strong></td>
            <td style="font-size:12px">${v.category || '—'}</td>
            <td><span class="badge badge-${riskClass}">${v.risk_level}</span></td>
            <td>
                <span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:${trustColor}">${trust.toFixed(0)}%</span>
                <div class="trust-bar"><div class="trust-fill" style="width:${trust}%;background:${trustColor}"></div></div>
            </td>
            <td>${v.approved ? '<span style="color:var(--accent-emerald)">✓ Yes</span>' : '<span style="color:var(--accent-red)">✕ No</span>'}</td>
        </tr>`;
    }).join('');
}

function renderOpsInsights(vendors) {
    const el = document.getElementById('ops-insights-list');
    if (!el) return;

    const highRisk = vendors.filter(v => v.risk_level === 'High').length;
    const unapproved = vendors.filter(v => !v.approved).length;
    const avgTrust = vendors.length ? vendors.reduce((sum, v) => sum + (v.trust_score || 0), 0) / vendors.length : 0;

    el.innerHTML = `
        <div class="insight-row">
            <div class="insight-meta">
                <span style="font-size:13px;color:var(--text-base);font-weight:600">High-Risk Vendors</span>
                <span style="font-size:11px;color:var(--text-subtle)">Require periodic audit review</span>
            </div>
            <div class="insight-stat">
                <span style="font-size:22px;font-weight:800;font-family:'Outfit',sans-serif;color:var(--accent-red)">${highRisk}</span>
            </div>
        </div>
        <div class="insight-row">
            <div class="insight-meta">
                <span style="font-size:13px;color:var(--text-base);font-weight:600">Unapproved Vendors</span>
                <span style="font-size:11px;color:var(--text-subtle)">Missing MSA documentation</span>
            </div>
            <div class="insight-stat">
                <span style="font-size:22px;font-weight:800;font-family:'Outfit',sans-serif;color:var(--accent-amber)">${unapproved}</span>
            </div>
        </div>
        <div class="insight-row">
            <div class="insight-meta">
                <span style="font-size:13px;color:var(--text-base);font-weight:600">Average Trust Score</span>
                <span style="font-size:11px;color:var(--text-subtle)">Across all registered vendors</span>
            </div>
            <div class="insight-stat">
                <span style="font-size:22px;font-weight:800;font-family:'Outfit',sans-serif;color:${avgTrust > 60 ? 'var(--accent-emerald)' : 'var(--accent-amber)'}">${avgTrust.toFixed(0)}%</span>
            </div>
        </div>
        <div class="insight-row">
            <div class="insight-meta">
                <span style="font-size:13px;color:var(--text-base);font-weight:600">Total Vendors Tracked</span>
                <span style="font-size:11px;color:var(--text-subtle)">In procurement registry</span>
            </div>
            <div class="insight-stat">
                <span style="font-size:22px;font-weight:800;font-family:'Outfit',sans-serif;color:var(--brand-secondary)">${vendors.length}</span>
            </div>
        </div>
    `;
}

// ══════════════════════════════════════════════
//  INVENTORY
// ══════════════════════════════════════════════
async function fetchInventory() {
    try {
        const res = await fetch('/api/inventory');
        const data = await res.json();
        renderInventoryGrid(data);
    } catch (e) { console.warn('[INV] Fetch failed'); }
}

function renderInventoryGrid(items) {
    const grid = document.getElementById('inv-grid-body');
    if (!grid) return;

    if (!items.length) {
        grid.innerHTML = '<div class="text-muted text-center p-20" style="grid-column:1/-1">No inventory items yet. Resolve shadow purchases to populate inventory.</div>';
        return;
    }

    const invEl = document.getElementById('stat-inv');
    const lowStock = items.filter(i => i.quantity <= (i.reorder_level || 1)).length;
    if (invEl) {
        invEl.textContent = lowStock > 0 ? `${lowStock} Low` : `${items.length} OK`;
        invEl.style.color = lowStock > 0 ? 'var(--accent-red)' : '';
    }

    grid.innerHTML = items.map(item => {
        const isLow = item.quantity <= (item.reorder_level || 1);
        const healthPct = Math.min(100, (item.quantity / Math.max(item.reorder_level || 1, 1)) * 50);
        const color = isLow ? 'var(--accent-red)' : 'var(--accent-emerald)';

        return `<div class="card inv-card ${isLow ? 'low-stock' : ''}">
            <div class="flex-between mb-5">
                <strong style="font-size:14px">${item.name || '—'}</strong>
                <span class="badge ${isLow ? 'badge-low-stock' : 'badge-in-stock'}">${isLow ? 'Low Stock' : 'In Stock'}</span>
            </div>
            <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px">
                SKU: ${item.sku || '—'} · ${item.category || 'General'} · ${item.location || '—'}
            </div>
            <div class="flex-between" style="margin-bottom:6px">
                <span style="font-size:11px;color:var(--text-subtle)">Qty: <strong class="${isLow ? 'text-red' : 'text-emerald'}">${item.quantity}</strong> / Reorder: ${item.reorder_level || 1}</span>
                <span class="amount">$${Number(item.unit_price || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            </div>
            <div class="health-bar-bg">
                <div class="health-bar-fill" style="width:${healthPct}%;background:${color}"></div>
            </div>
        </div>`;
    }).join('');
}

// ══════════════════════════════════════════════
//  RECOMMENDATIONS
// ══════════════════════════════════════════════
async function fetchRecommendations() {
    try {
        const res = await fetch('/api/recommendations');
        const data = await res.json();
        renderRecommendations(data);
    } catch (e) { console.warn('[RECS] Fetch failed'); }
}

function renderRecommendations(recs) {
    const el = document.getElementById('recommendations-list');
    if (!el) return;

    if (!recs.length) {
        el.innerHTML = '<div class="text-muted small text-center p-20">No pending recommendations</div>';
        return;
    }

    el.innerHTML = recs.slice(0, 6).map(r => {
        const prioClass = r.priority === 'critical' ? 'critical' : r.priority === 'high' ? 'high' : 'medium';
        return `<div class="rec-card rec-${prioClass}">
            <div class="rec-header">
                <span class="badge badge-${prioClass}">${r.priority}</span>
                <strong style="font-size:13px">${r.title || ''}</strong>
            </div>
            <div class="rec-body">${r.explanation || ''}</div>
            <div class="rec-footer">
                ${r.action === 'resolve' && r.target_id ? `<button class="btn btn-xs btn-resolve" onclick="resolveShadow(${r.target_id})">✓ Convert to PO</button>` : ''}
                ${r.action === 'review' && r.target_id ? `<button class="btn btn-xs btn-ghost" onclick="openDecisionPanel(${r.target_id})">🧠 Analyze</button>` : ''}
                ${r.action === 'vendor_review' && r.vendor_name ? `<button class="btn btn-xs btn-outline" onclick="switchTab('vendors')">View Vendor</button>` : ''}
            </div>
        </div>`;
    }).join('');
}

// ══════════════════════════════════════════════
//  AUDIT LOG
// ══════════════════════════════════════════════
async function fetchAuditLog() {
    try {
        const res = await fetch('/api/audit');
        const data = await res.json();
        renderAuditTable(data);
    } catch (e) { console.warn('[AUDIT] Fetch failed'); }
}

function renderAuditTable(logs) {
    const tbody = document.getElementById('audit-table-body');
    if (!tbody) return;

    tbody.innerHTML = logs.map(log => {
        const actType = (log.action || '').toLowerCase();
        const actClass = actType.includes('rectif') || actType.includes('resolve') ? 'act-rectify'
            : actType.includes('dismiss') ? 'act-dismiss'
            : actType.includes('feedback') ? 'act-feedback'
            : actType.includes('export') ? 'act-export'
            : actType.includes('mode') ? 'act-mode' : '';

        return `<tr>
            <td style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text-subtle)">${log.timestamp || '—'}</td>
            <td style="font-size:12px">${log.user || 'System'}</td>
            <td><span class="act-badge ${actClass}">${log.action || '—'}</span></td>
            <td style="font-size:12px">${log.target || '—'}</td>
            <td style="font-size:11px;color:var(--text-muted);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${log.details || '—'}</td>
        </tr>`;
    }).join('');
}

// ══════════════════════════════════════════════
//  ACTIONS: RESOLVE / DISMISS
// ══════════════════════════════════════════════
async function resolveShadow(id) {
    try {
        const res = await fetch(`/api/resolve/${id}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(`✅ Resolved → ${data.po_id} | Vendor: ${data.vendor}`, 'success');
            addFeedEvent('✅', `Shadow #${id} resolved → <strong>${data.po_id}</strong>`);
            fetchAllData();
        } else {
            showToast(`Error: ${data.error || 'Unknown'}`, 'error');
        }
    } catch (e) {
        showToast('Resolution failed', 'error');
    }
}

async function dismissShadow(id) {
    try {
        const res = await fetch(`/api/dismiss/${id}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(`Shadow #${id} dismissed`, 'info');
            addFeedEvent('🗑️', `Shadow #${id} dismissed by analyst`);
            fetchAllData();
        } else {
            showToast(`Error: ${data.error || 'Unknown'}`, 'error');
        }
    } catch (e) {
        showToast('Dismiss failed', 'error');
    }
}

// ══════════════════════════════════════════════
//  DECISION SUPPORT PANEL
// ══════════════════════════════════════════════
async function openDecisionPanel(shadowId) {
    const panel = document.getElementById('decisionPanel');
    const content = document.getElementById('decisionContent');
    const footer = document.getElementById('decisionFooter');

    panel.classList.add('show');
    content.innerHTML = '<div class="ds-loading"><div class="spinner" style="margin:0 auto 12px"></div>Analyzing with AI...</div>';
    footer.innerHTML = '';

    try {
        const res = await fetch(`/api/decision-support/${shadowId}`);
        const data = await res.json();

        if (data.error) {
            content.innerHTML = `<div class="ds-loading" style="color:var(--accent-red)">${data.error}</div>`;
            return;
        }

        const risk = Number(data.risk_score || 0);
        const conf = Number(data.confidence || 0.7);
        const riskColor = risk > 0.6 ? 'var(--accent-red)' : risk > 0.35 ? 'var(--accent-amber)' : 'var(--accent-emerald)';

        content.innerHTML = `
            <div class="ds-card">
                <div class="ds-id">SHADOW-${shadowId} · ${data.category || 'General'}</div>

                <div class="ds-confidence">
                    <div class="ds-value" style="color:${riskColor}">${(risk * 100).toFixed(0)}%</div>
                    <div style="font-size:12px;color:var(--text-muted);margin-top:4px">Risk Score · Confidence: ${(conf * 100).toFixed(0)}%</div>
                    <div style="margin-top:8px">
                        <span class="badge badge-${data.severity || 'medium'}" style="font-size:12px;padding:5px 14px">${(data.severity || 'medium').toUpperCase()}</span>
                    </div>
                </div>

                <div class="ds-section">
                    <h4>Evidence (XAI Factors)</h4>
                    <ul class="ds-evidence">
                        ${(data.factors || ['No factors available']).map(f => `<li>${f}</li>`).join('')}
                    </ul>
                </div>

                <div class="ds-section">
                    <h4>Recommendation</h4>
                    <div class="ds-rec">${data.recommendation || 'No recommendation available'}</div>
                </div>

                <div class="ds-section">
                    <h4>Model Information</h4>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;color:var(--text-muted)">
                        <div>Engine: <strong style="color:var(--text-base)">${data.model_version || 'IsolationForest-v3'}</strong></div>
                        <div>Feedback Applied: <strong style="color:var(--text-base)">${data.feedback_adjustments_applied || 0}</strong></div>
                    </div>
                </div>
            </div>
        `;

        footer.innerHTML = `
            <div style="display:flex;gap:8px">
                <button class="btn btn-primary" style="flex:1" onclick="resolveShadow(${shadowId}); closeDecisionPanel()">✓ Convert to PO</button>
                <button class="btn btn-danger btn-sm" onclick="dismissShadow(${shadowId}); closeDecisionPanel()">✕ Dismiss</button>
                <button class="btn btn-ghost btn-sm" onclick="openFeedbackModal(${shadowId}); closeDecisionPanel()">💬</button>
            </div>
        `;
    } catch (e) {
        content.innerHTML = '<div class="ds-loading" style="color:var(--accent-red)">Failed to load analysis</div>';
    }
}

function closeDecisionPanel() {
    document.getElementById('decisionPanel').classList.remove('show');
}

// ══════════════════════════════════════════════
//  FEEDBACK MODAL
// ══════════════════════════════════════════════
function openFeedbackModal(shadowId) {
    document.getElementById('feedbackShadowId').value = shadowId;
    document.getElementById('feedbackType').value = 'confirm';
    document.getElementById('feedbackCorrRisk').value = '';
    document.getElementById('feedbackNotes').value = '';
    document.getElementById('feedbackModal').classList.add('show');
}

function closeFeedbackModal() {
    document.getElementById('feedbackModal').classList.remove('show');
}

async function submitFeedback() {
    const shadowId = document.getElementById('feedbackShadowId').value;
    const fbType = document.getElementById('feedbackType').value;
    const corrRisk = parseFloat(document.getElementById('feedbackCorrRisk').value) || null;
    const notes = document.getElementById('feedbackNotes').value;

    try {
        const res = await fetch(`/api/feedback/${shadowId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                feedback_type: fbType,
                corrected_risk: corrRisk,
                notes: notes
            })
        });
        const data = await res.json();

        if (data.status === 'success' || data.feedback_applied) {
            showToast('✅ Feedback submitted — AI recalibrated', 'success');
            addFeedEvent('🧠', `Human feedback on Shadow #${shadowId}: ${fbType}`);
            closeFeedbackModal();
            fetchAllData();
        } else {
            showToast(`Feedback error: ${data.error || 'Unknown'}`, 'error');
        }
    } catch (e) {
        showToast('Feedback submission failed', 'error');
    }
}

// ══════════════════════════════════════════════
//  DOWNLOADS: PDF & CSV
// ══════════════════════════════════════════════
// Removed redundant downloadPO definition since it is defined below at line 1416

// ══════════════════════════════════════════════
//  EXPORTS & REPORTING (Stable Blob Engine)
// ══════════════════════════════════════════════

/**
 * Robust helper for file downloads with verification and filename preservation.
 */
async function verifiedDownload(url, defaultName = 'Document.pdf', toastInfo = 'Preparing Document...') {
    try {
        if (toastInfo) showToast(toastInfo, 'info');
        
        const res = await fetch(url);
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `HTTP ${res.status}`);
        }

        const disposition = res.headers.get('Content-Disposition');
        let filename = defaultName;
        if (disposition && disposition.indexOf('filename') !== -1) {
            const filenameRegex = /filename[^;=n]*=((['"]).*?2|[^;n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }

        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;
        document.body.appendChild(link); 
        link.click();
        
        setTimeout(() => {
            link.remove();
            URL.revokeObjectURL(blobUrl);
        }, 100);

        showToast('Document securely generated', 'success');
        return true;
    } catch (e) {
        console.error('[Download Error]', e);
        showToast(`Download failed: ${e.message}`, 'error');
        return false;
    }
}

async function downloadExecReport() {
    const success = await verifiedDownload('/api/pdf/dashboard-report', 'Nexus_Executive_Summary.pdf', 'Compiling Executive Risk Profile... 📊');
    if (success) addFeedEvent('<span class="material-icons-outlined" style="font-size:16px;color:var(--brand-primary)">analytics</span>', 'Executive risk report generated.');
}

async function exportExcel(type = 'audit') {
    let url;
    if (type === 'comprehensive') url = '/api/export/comprehensive';
    else if (type === 'audit') url = '/api/procurement/export-excel';
    else url = `/api/export/excel/${type}`;

    const success = await verifiedDownload(url, `ShadowSync_${type.toUpperCase()}_Report.xlsx`, `Preparing Enterprise ${type.toUpperCase()} Excel... ⚡`);
    if (success) addFeedEvent('<span class="material-icons-outlined" style="font-size:16px;color:var(--brand-secondary)">description</span>', `Exported ${type} Excel workbook.`);
}

async function exportCSV(type) {
    const success = await verifiedDownload(`/api/export/${type}`, `ShadowSync_${type}_Ledger.csv`, `Streaming ${type.toUpperCase()} Ledger...`);
    if (success) addFeedEvent('<span class="material-icons-outlined" style="font-size:16px">insert_drive_file</span>', `Exported ${type} CSV ledger.`);
}

async function downloadPO(poId) {
    const isBulk = (poId === 'all' || !poId);
    const url = isBulk ? '/api/pdf/bulk-procurement' : `/api/pdf/${poId}`;
    await verifiedDownload(url, isBulk ? 'Procurement_Audit_Log.pdf' : `PO_${poId}.pdf`, isBulk ? 'Compiling procurement index...' : `Generating PO-${poId}...`);
}

// Unified Blob Trigger removed. Native browser navigation handles attachments natively.

// Add prototype helper for capitalization
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
};



// filterShadows is defined above (line ~508); duplicate removed.


function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

async function fetchOpsInsights() {
    try {
        const res = await fetch('/api/operational-insights');
        if (res.status === 401) { window.location.href = '/login'; return; }
        const data = await res.json();
        const container = document.getElementById('ops-insights-list');
        if (!container) return;
        
        container.innerHTML = data.behaviors.map(b => `
            <div class="insight-card" style="padding:12px; background:rgba(255,255,255,0.03); border-radius:10px; margin-bottom:8px; border-left:3px solid ${b.risk_level === 'High' ? 'var(--accent-red)' : 'var(--brand-primary)'}">
                <div style="font-weight:600; font-size:13px">${b.employee_id} (${b.department})</div>
                <div style="color:var(--text-muted); font-size:11px">${b.shadow_count} shadows detected · Risk: ${b.risk_level}</div>
            </div>
        `).join('');
    } catch (e) {
        console.warn('Ops insights fetch failed');
    }
}

async function fetchTrends() {
    try {
        const res = await fetch('/api/trends');
        if (!res.ok) return;
        const data = await res.json();
        
        const chart = state.charts.riskTrend;
        if (chart && data.dates && data.dates.length > 0) {
            chart.data.labels = data.dates;
            chart.data.datasets[0].data = data.exposure;
            chart.update();
        }
        
        const timestamp = document.getElementById('trend-updated');
        if (timestamp) timestamp.textContent = `Last sync: ${new Date().toLocaleTimeString()}`;
    } catch (e) {
        console.warn('Trends fetch failed');
    }
}

// ══════════════════════════════════════════════
//  AI COPILOT (Groq + Cohere Integration)
// ══════════════════════════════════════════════

const aiState = {
    isOpen: false,
    history: [],
    isProcessing: false,
};

function toggleAICopilot() {
    const panel = document.getElementById('aiCopilotPanel');
    const toggle = document.getElementById('aiToggle');
    if (!panel) return;

    aiState.isOpen = !aiState.isOpen;
    if (aiState.isOpen) {
        panel.classList.add('show');
        toggle.style.display = 'none';
        const input = document.getElementById('aiChatInput');
        if (input) setTimeout(() => input.focus(), 300);
    } else {
        panel.classList.remove('show');
        toggle.style.display = 'flex';
    }
}

function addAIMessage(content, role = 'assistant') {
    const container = document.getElementById('aiChatMessages');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `ai-message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'ai-msg-avatar';
    avatar.textContent = role === 'user' ? 'You' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'ai-msg-content';
    
    // Simple markdown-like formatting
    let formatted = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/^### (.*$)/gm, '<strong style="font-size:14px;display:block;margin:8px 0 4px">$1</strong>')
        .replace(/^## (.*$)/gm, '<strong style="font-size:15px;display:block;margin:10px 0 6px">$1</strong>')
        .replace(/^# (.*$)/gm, '<strong style="font-size:16px;display:block;margin:12px 0 6px">$1</strong>')
        .replace(/^- (.*$)/gm, '• $1')
        .replace(/^\d+\. (.*$)/gm, '<span style="display:block;padding-left:16px;text-indent:-16px">$&</span>')
        .replace(/\n/g, '<br>');
    
    contentDiv.innerHTML = formatted;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(contentDiv);
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
    const container = document.getElementById('aiChatMessages');
    if (!container) return;

    const typing = document.createElement('div');
    typing.className = 'ai-message assistant';
    typing.id = 'aiTypingIndicator';
    typing.innerHTML = `
        <div class="ai-msg-avatar">🤖</div>
        <div class="ai-msg-content">
            <div class="ai-typing">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
    const typing = document.getElementById('aiTypingIndicator');
    if (typing) typing.remove();
}

async function sendAIMessage() {
    const input = document.getElementById('aiChatInput');
    if (!input || !input.value.trim() || aiState.isProcessing) return;

    const message = input.value.trim();
    input.value = '';
    aiState.isProcessing = true;

    // Add user message
    addAIMessage(message, 'user');
    aiState.history.push({ role: 'user', content: message });

    // Show typing indicator
    showTypingIndicator();

    // Disable send button
    const sendBtn = document.querySelector('.ai-send-btn');
    if (sendBtn) sendBtn.disabled = true;

    try {
        const res = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: aiState.history.slice(-10),
            }),
        });

        removeTypingIndicator();

        if (!res.ok) {
            const errorText = await res.text();
            addAIMessage(`⚠️ Error: ${res.status} — ${errorText}`, 'assistant');
        } else {
            const data = await res.json();
            const response = data.response || 'No response received.';
            addAIMessage(response, 'assistant');
            aiState.history.push({ role: 'assistant', content: response });
        }
    } catch (e) {
        removeTypingIndicator();
        addAIMessage(`⚠️ Connection error: ${e.message}. Please check the server.`, 'assistant');
    }

    aiState.isProcessing = false;
    if (sendBtn) sendBtn.disabled = false;
    input.focus();
}

async function checkAIHealth() {
    addAIMessage('Checking AI provider connectivity...', 'user');
    showTypingIndicator();

    try {
        const res = await fetch('/api/ai/health');
        removeTypingIndicator();

        if (!res.ok) {
            addAIMessage('⚠️ Could not reach AI health endpoint.', 'assistant');
            return;
        }

        const data = await res.json();
        const groqStatus = data.groq?.status || 'unknown';
        const cohereStatus = data.cohere?.status || 'unknown';

        const groqIcon = groqStatus === 'connected' ? '✅' : groqStatus === 'error' ? '❌' : '⚠️';
        const cohereIcon = cohereStatus === 'connected' ? '✅' : cohereStatus === 'error' ? '❌' : '⚠️';

        addAIMessage(
            `**AI Provider Status**\n\n` +
            `${groqIcon} **Groq** (llama-3.3-70b): ${groqStatus}${data.groq?.error ? ' — ' + data.groq.error : ''}\n` +
            `${cohereIcon} **Cohere** (command-r-plus): ${cohereStatus}${data.cohere?.error ? ' — ' + data.cohere.error : ''}\n\n` +
            `${groqStatus === 'connected' && cohereStatus === 'connected' ? '🟢 All systems operational!' : '🟡 Some providers may be unavailable.'}`,
            'assistant'
        );

        // Update provider dots
        const groqDot = document.querySelector('.ai-provider-dot.groq');
        const cohereDot = document.querySelector('.ai-provider-dot.cohere');
        if (groqDot) groqDot.style.background = groqStatus === 'connected' ? '#10b981' : '#ef4444';
        if (cohereDot) cohereDot.style.background = cohereStatus === 'connected' ? '#3b82f6' : '#ef4444';
    } catch (e) {
        removeTypingIndicator();
        addAIMessage(`⚠️ Health check failed: ${e.message}`, 'assistant');
    }
}

async function aiSummarizeRisks() {
    addAIMessage('Generate executive risk summary', 'user');
    showTypingIndicator();

    try {
        const res = await fetch('/api/ai/summarize');
        removeTypingIndicator();

        if (!res.ok) {
            addAIMessage('⚠️ Risk summary generation failed.', 'assistant');
            return;
        }

        const data = await res.json();
        addAIMessage(
            `**📊 Executive Risk Summary** (Cohere)\n\n${data.summary || 'No summary available.'}`,
            'assistant'
        );
    } catch (e) {
        removeTypingIndicator();
        addAIMessage(`⚠️ Summarization failed: ${e.message}`, 'assistant');
    }
}

async function aiAnalyzeShadow(shadowId) {
    addAIMessage(`Analyze shadow purchase #${shadowId}`, 'user');
    showTypingIndicator();

    try {
        const res = await fetch(`/api/ai/analyze/${shadowId}`);
        removeTypingIndicator();

        if (!res.ok) {
            addAIMessage(`⚠️ Analysis failed for shadow #${shadowId}.`, 'assistant');
            return;
        }

        const data = await res.json();
        addAIMessage(
            `**🧠 Deep Analysis — Shadow #${shadowId}** (Groq)\n\n${data.response || 'No analysis available.'}`,
            'assistant'
        );
    } catch (e) {
        removeTypingIndicator();
        addAIMessage(`⚠️ Analysis failed: ${e.message}`, 'assistant');
    }
}
