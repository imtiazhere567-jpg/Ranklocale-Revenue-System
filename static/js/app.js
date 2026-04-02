/**
 * Ranklocale Revenue & Client Management System
 * Frontend Application Logic
 */

// ─── State ───
const state = {
    currentPage: 'dashboard',
    dashboardMonth: new Date().toISOString().slice(0, 7),
    // Lookup data
    bdos: [],
    platforms: [],
    platformProfiles: [],
    paymentChannels: [],
    clientTypes: [],
    clients: [],
    contracts: [],
};

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
    // Immediate highlight from localStorage
    const savedPage = localStorage.getItem('ranklocale_current_page') || 'dashboard';
    const initialNav = document.querySelector(`[data-page="${savedPage}"]`);
    if (initialNav) initialNav.classList.add('active');

    // Nav clicks
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            navigateTo(item.dataset.page);
        });
    });

    // Mobile menu
    document.getElementById('mobileMenuBtn').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
    });

    // Modal close
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', e => {
        if (e.target === e.currentTarget) closeModal();
    });

    // Notification banner close
    document.getElementById('notifBannerClose').addEventListener('click', () => {
        document.getElementById('notifBanner').style.display = 'none';
    });

    // Notification Dropdown Toggle and Close-Outside
    const notifBell = document.getElementById('notificationBell');
    const notifDropdown = document.getElementById('notifDropdown');
    
    notifBell.addEventListener('click', (e) => {
        e.stopPropagation();
        if (notifDropdown.style.display === 'block') {
            notifDropdown.style.display = 'none';
        } else {
            notifDropdown.style.display = 'block';
        }
    });

    document.addEventListener('click', (e) => {
        if (notifDropdown && notifDropdown.style.display === 'block') {
            if (!notifDropdown.contains(e.target) && !notifBell.contains(e.target)) {
                notifDropdown.style.display = 'none';
            }
        }
    });

    // Clear notifications
    document.getElementById('notifClearBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        state.overdue = [];
        document.getElementById('notifBadge').style.display = 'none';
        document.getElementById('notifClearBtn').style.display = 'none';
        document.getElementById('notifDropBody').innerHTML = '<div class="notif-drop-empty">No new notifications</div>';
    });

    // Notification bell click (OLD MODAL LOGIC REMOVED)
    // Now handled by the dropdown logic above.

    // Load lookup data then render initial page
    loadLookups().then(() => {
        const lastPage = localStorage.getItem('ranklocale_current_page') || 'dashboard';
        navigateTo(lastPage);
    });
});

// ─── API Helpers ───
async function api(url, opts = {}) {
    try {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...opts.headers },
            ...opts,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    } catch (err) {
        showToast(err.message, 'error');
        throw err;
    }
}

// Debounce helper for auto-filters
let filterTimeout;
function debounceFilter(callback, ms = 300) {
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(callback, ms);
}

async function loadLookups() {
    const [bdos, platforms, profiles, channels, types, clients, contracts] = await Promise.all([
        api('/api/bdos'),
        api('/api/platforms'),
        api('/api/platform-profiles'),
        api('/api/payment-channels'),
        api('/api/client-types'),
        api('/api/clients'),
        api('/api/contracts'),
    ]);
    state.bdos = bdos;
    state.platforms = platforms;
    state.platformProfiles = profiles;
    state.paymentChannels = channels;
    state.clientTypes = types;
    state.clients = clients;
    state.contracts = contracts;
}

// ─── Navigation ───
function navigateTo(page) {
    state.currentPage = page;
    localStorage.setItem('ranklocale_current_page', page);
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`[data-page="${page}"]`);
    if (navItem) navItem.classList.add('active');

    const titles = {
        dashboard: 'Dashboard',
        contracts: 'Contracts',
        clients: 'Clients',
        payments: 'Payments',
        reports: 'Reports',
        settings: 'Settings',
    };
    document.getElementById('pageTitle').textContent = titles[page] || page;

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');

    const renderers = { dashboard: renderDashboard, contracts: renderContracts, clients: renderClients, payments: renderPayments, reports: renderReports, settings: renderSettings };
    if (renderers[page]) renderers[page]();
}

// ─── Toast ───
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// ─── Modal ───
function openModal(title, bodyHTML) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = bodyHTML;
    document.getElementById('modalOverlay').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modalOverlay').style.display = 'none';
}

// ─── Helpers ───
function formatCurrency(n) {
    if (n == null || isNaN(n)) return '$0.00';
    return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(d) {
    if (!d) return '—';
    const date = new Date(d);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function statusBadge(status) {
    const map = {
        'In Progress': 'badge-primary',
        'Completed': 'badge-success',
        'On Hold': 'badge-warning',
        'Cancelled': 'badge-danger',
        'Active': 'badge-success',
        'Inactive': 'badge-gray',
        'Lead': 'badge-info',
    };
    return `<span class="badge ${map[status] || 'badge-gray'}">${status || '—'}</span>`;
}

function deadlineClass(deadline) {
    if (!deadline) return '';
    const d = new Date(deadline);
    const today = new Date();
    today.setHours(0,0,0,0);
    const diff = (d - today) / (1000*60*60*24);
    if (diff < 0) return 'deadline-overdue';
    if (diff <= 3) return 'deadline-overdue';
    if (diff <= 7) return 'deadline-soon';
    return '';
}

function selectOptions(items, valueKey, labelKey, selected, placeholder = 'Select...') {
    let html = `<option value="">${placeholder}</option>`;
    items.forEach(item => {
        const sel = item[valueKey] == selected ? ' selected' : '';
        html += `<option value="${item[valueKey]}"${sel}>${item[labelKey]}</option>`;
    });
    return html;
}

// ─── DASHBOARD ───
async function renderDashboard() {
    const container = document.getElementById('pageContainer');
    container.innerHTML = `
        <div class="flex items-center justify-between mb-6">
            <div>
                <input type="month" class="form-input" id="dashMonth" value="${state.dashboardMonth}"
                       style="width:180px; padding:8px 12px; font-size:13px;">
            </div>
        </div>
        <div class="stats-grid" id="dashStats"></div>
        <div class="section-grid">
            <div class="card" id="dashDeadlines">
                <div class="card-header"><span class="card-title">⚡ Upcoming Deadlines</span></div>
                <div class="card-body"><p class="text-secondary">Loading...</p></div>
            </div>
            <div class="card" id="dashRecent">
                <div class="card-header"><span class="card-title">📋 Recent Contracts</span></div>
                <div class="card-body"><p class="text-secondary">Loading...</p></div>
            </div>
        </div>
    `;

    document.getElementById('dashMonth').addEventListener('change', e => {
        state.dashboardMonth = e.target.value;
        renderDashboard();
    });

    try {
        const data = await api(`/api/dashboard?month=${state.dashboardMonth}`);
        _renderDashboardData(data);
    } catch (e) {
        console.error("Dashboard Render Error:", e);
        showToast("Error loading dashboard data", "danger");
    }
}

function _renderDashboardData(data) {
    const pct = data.total_sales > 0 ? ((data.total_recovered / data.total_sales) * 100).toFixed(0) : 0;
    const progressColor = pct > 70 ? 'green' : pct > 40 ? 'yellow' : 'red';

    // Helper string for month start/end (since dashboard uses month filter)
    const yearMonth = state.dashboardMonth; // e.g. "2026-03"
    let [y, m] = yearMonth.split('-');
    const mStart = `${y}-${m}-01`;
    let nextM = parseInt(m) + 1;
    let nextY = parseInt(y);
    if (nextM > 12) { nextM = 1; nextY++; }
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const mDisplay = `${monthNames[parseInt(m) - 1]} ${y}`;
    const mEnd = `${nextY}-${nextM.toString().padStart(2, '0')}-01`;

    document.getElementById('dashStats').innerHTML = `
        <div class="stat-card primary clickable-card" onclick="openFilteredContracts({dateFrom: '${mStart}', dateTo: '${mEnd}'})">
            <div class="stat-label">Total Sales</div>
            <div class="stat-value">${formatCurrency(data.total_sales)}</div>
            <div class="stat-sub">${data.total_contracts || 0} contracts</div>
        </div>
        <div class="stat-card success clickable-card" onclick="openFilteredContracts({payDateFrom: '${mStart}', payDateTo: '${mEnd}', payment_status: 'recovered'})">
            <div class="stat-label">Total Recovered</div>
            <div class="stat-value" style="font-size: 1.8rem; font-weight: 800; margin-bottom: 8px;">${formatCurrency(data.cash_this_month)}</div>

            <div style="border-top: 1px dashed rgba(255,255,255,0.2); padding: 8px 0 4px 0; font-size: 11px; color: inherit; opacity: 0.9;">
                <span class="legacy-tooltip">
                    Incl. ${formatCurrency(data.cash_this_month - data.total_recovered)} from previous months
                    <div class="legacy-tooltip-content">
                        <div style="margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:4px; font-weight:700;">Recovery Sources (by Month)</div>
                        ${(data.recovered_breakdown || []).map(b => {
                            if (!b.m_val) return '';
                            const [by, bm] = b.m_val.split('-');
                            let nBM = parseInt(bm) + 1;
                            let nBY = parseInt(by);
                            if (nBM > 12) { nBM = 1; nBY++; }
                            const nBMStr = nBM.toString().padStart(2, '0');
                            const be = `${nBY}-${nBMStr}-01`;
                            return `
                                <div class="legacy-breakdown-row" 
                                     style="cursor:pointer; padding:8px 12px; border-radius:4px; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center;"
                                     onclick="event.stopPropagation(); openFilteredContracts({dateFrom: '${b.m_val}-01', dateTo: '${be}', payDateFrom: '${mStart}', payDateTo: '${mEnd}', payment_status: 'recovered'})"
                                     onmouseover="this.style.background='rgba(255,255,255,0.1)'"
                                     onmouseout="this.style.background='transparent'">
                                    <span style="font-size:12px;">${b.month}</span>
                                    <span style="font-weight:700; color:#fff; font-family:monospace;">${formatCurrency(b.amount)}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </span>
            </div>
        </div>

        <div class="stat-card warning clickable-card" onclick="openFilteredContracts({payment_status: 'pending'})">
            <div class="stat-label">Total Pending</div>
            <div class="stat-value" style="font-size: 1.8rem; font-weight: 800; margin-bottom: 8px;">${formatCurrency(data.total_pending + data.legacy_pending)}</div>

            <div style="border-top: 1px dashed rgba(255,255,255,0.2); padding: 8px 0 4px 0; font-size: 11px; color: inherit; opacity: 0.9;">
                <span class="legacy-tooltip">
                    Incl. ${formatCurrency(data.legacy_pending)} from previous months
                    <div class="legacy-tooltip-content">
                        <div style="margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:4px; font-weight:700;">Pending Breakdown</div>
                        ${(data.legacy_breakdown || []).map(b => {
                            if (!b.month_val) return '';
                            return `
                            <div class="legacy-breakdown-row" 
                                 style="cursor:pointer; padding:8px 12px; border-radius:4px; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center;"
                                 onclick="event.stopPropagation(); openFilteredContracts({dateFrom: '${b.month_val}-01', dateTo: '${b.month_val}-31', payment_status: 'pending'})"
                                 onmouseover="this.style.background='rgba(255,255,255,0.1)'"
                                 onmouseout="this.style.background='transparent'">
                                <span style="font-size:12px;">${b.month}</span>
                                <span style="font-weight:700; color:var(--warning); font-family:monospace;">${formatCurrency(b.amount)}</span>
                            </div>
                        `;}).join('')}
                    </div>
                </span>
            </div>
        </div>

        <div class="stat-card info clickable-card" onclick="openFilteredContracts({status: 'In Progress'})">
            <div class="stat-label">Total In Progress</div>
            <div class="stat-value" style="font-size: 1.8rem; font-weight: 800; margin-bottom: 8px;">${data.status_counts?.['In Progress'] || 0}</div>

            <div style="border-top: 1px dashed rgba(255,255,255,0.2); padding: 8px 0 4px 0; font-size: 11px; color: inherit; opacity: 0.9;">
                <span class="legacy-tooltip">
                    Incl. ${data.new_in_progress || 0} started this month
                    <div class="legacy-tooltip-content">
                        <div style="margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:4px; font-weight:700;">Month-wise Active</div>
                        ${(data.in_progress_breakdown || []).map(b => {
                            if (!b.m_val) return '';
                            const [by, bm] = b.m_val.split('-');
                            let nBM = parseInt(bm) + 1; let nBY = parseInt(by);
                            if (nBM > 12) { nBM = 1; nBY++; }
                            const be = `${nBY}-${nBM.toString().padStart(2, '0')}-01`;
                            return `
                                <div class="legacy-breakdown-row" 
                                     style="cursor:pointer; padding:8px 12px; border-radius:4px; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center;"
                                     onclick="event.stopPropagation(); openFilteredContracts({dateFrom: '${b.m_val}-01', dateTo: '${be}', status: 'In Progress'})"
                                     onmouseover="this.style.background='rgba(255,255,255,0.1)'"
                                     onmouseout="this.style.background='transparent'">
                                    <span style="font-size:12px;">${b.month}</span>
                                    <span style="font-weight:700; color:var(--info); font-family:monospace;">${b.count}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </span>
            </div>
        </div>

        <div class="stat-card danger clickable-card" onclick="openFilteredContracts({is_overdue: true})">
            <div class="stat-label">Total Overdue</div>
            <div class="stat-value" style="font-size: 1.8rem; font-weight: 800; margin-bottom: 8px;">${data.overdue?.length || 0}</div>

            <div style="border-top: 1px dashed rgba(255,255,255,0.2); padding: 8px 0 4px 0; font-size: 11px; color: inherit; opacity: 0.9;">
                <span class="legacy-tooltip">
                    ${data.overdue_this_month || 0} due this month
                    <div class="legacy-tooltip-content">
                        <div style="margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.2); padding-bottom:4px; font-weight:700;">Overdue Breakdown</div>
                         ${(data.overdue_breakdown || []).map(b => `
                            <div class="legacy-breakdown-row" 
                                 style="cursor:pointer; padding:8px 12px; border-radius:4px; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center;"
                                 onclick="event.stopPropagation(); openFilteredContracts({is_overdue: true})"
                                 onmouseover="this.style.background='rgba(255,255,255,0.1)'"
                                 onmouseout="this.style.background='transparent'">
                                <span style="font-size:12px;">${b.month}</span>
                                <span style="font-weight:700; color:var(--danger); font-family:monospace;">${b.count}</span>
                            </div>
                        `).join('')}
                    </div>
                </span>
            </div>
        </div>
    `;

    // Deadlines
    const dlCard = document.getElementById('dashDeadlines');
    if (data.upcoming_deadlines?.length) {
        dlCard.querySelector('.card-body').innerHTML = `<div class="table-wrapper"><table>
            <thead><tr><th>Title</th><th>Date</th><th>Client</th></tr></thead>
            <tbody>${data.upcoming_deadlines.map(d => `
                <tr class="clickable-row" onclick="viewContract(${d.contract_id})">
                    <td style="font-weight:600;">${d.title}</td>
                    <td class="${deadlineClass(d.date)}">${formatDate(d.date)}</td>
                    <td>${d.client_name || '—'}</td>
                </tr>
            `).join('')}</tbody>
        </table></div>`;
    } else {
        dlCard.querySelector('.card-body').innerHTML = '<p class="text-secondary text-center" style="padding:20px;">No upcoming deadlines 🎯</p>';
    }

    // Overdue notification banner
    state.overdue = data.overdue || [];
    if (state.overdue.length > 0) {
        const banner = document.getElementById('notifBanner');
        banner.style.display = 'flex';
        banner.className = 'notification-banner danger';
        document.getElementById('notifBannerContent').innerHTML =
            `⚠️ <strong>${state.overdue.length} item(s) overdue!</strong> — ${state.overdue.map(d => d.title).join(', ')}`;
        document.getElementById('notifBadge').style.display = 'flex';
        document.getElementById('notifBadge').textContent = state.overdue.length;
        document.getElementById('notifClearBtn').style.display = 'inline';
        
        // Populate dropdown menu
        const dropBody = document.getElementById('notifDropBody');
        dropBody.innerHTML = state.overdue.map(d => `
            <div class="notif-drop-item" onclick="viewContract(${d.contract_id}); document.getElementById('notifDropdown').style.display='none';">
                <div class="notif-drop-text">
                    <strong>${d.title}</strong>
                    <span class="notif-drop-sub">Overdue: ${formatDate(d.date)}</span>
                </div>
                <div class="notif-drop-arrow">→</div>
            </div>
        `).join('');
    } else {
        document.getElementById('notifBanner').style.display = 'none';
        document.getElementById('notifBadge').style.display = 'none';
        document.getElementById('notifClearBtn').style.display = 'none';
        document.getElementById('notifDropBody').innerHTML = '<div class="notif-drop-empty">No new notifications</div>';
    }

    // Recent
    const recCard = document.getElementById('dashRecent');
    if (data.recent_contracts?.length) {
        recCard.querySelector('.card-body').innerHTML = `<div class="table-wrapper"><table>
            <thead><tr><th>Contract</th><th>Date</th><th>BDO</th><th>Status</th></tr></thead>
            <tbody>${data.recent_contracts.map(c => `
                <tr class="clickable-row" onclick="viewContract(${c.id})">
                    <td style="font-weight:600;">${c.contract_name}</td>
                    <td>${formatDate(c.date)}</td>
                    <td>${c.bdo_name || '—'}</td>
                    <td>${statusBadge(c.status)}</td>
                </tr>
            `).join('')}</tbody>
        </table></div>`;
    } else {
        recCard.querySelector('.card-body').innerHTML = `
            <div class="empty-state">
                <h3>No contracts yet</h3>
                <p>Add your first contract to get started</p>
                <button class="btn btn-primary" onclick="navigateTo('contracts')">Go to Contracts</button>
            </div>
        `;
    }
}

// ─── CONTRACTS ───
async function renderContracts() {
    const container = document.getElementById('pageContainer');
    container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <div></div>
            <button class="btn btn-primary" onclick="openContractForm()">+ New Contract</button>
        </div>
        <div class="filters-bar" id="contractFilters">
            <div class="filter-group">
                <label>Search</label>
                <input type="text" id="fSearch" placeholder="Contract name..." oninput="debounceFilter(loadContracts)">
            </div>
            <div class="filter-group">
                <label>BDO</label>
                <select id="fBdo" onchange="loadContracts()"><option value="">All BDOs</option></select>
            </div>
            <div class="filter-group">
                <label>Client</label>
                <select id="fClient" onchange="loadContracts()"><option value="">All Clients</option></select>
            </div>
            <div class="filter-group">
                <label>Platform</label>
                <select id="fPlatform" onchange="loadContracts()"><option value="">All Platforms</option></select>
            </div>
            <div class="filter-group">
                <label>Client Type</label>
                <select id="fClientType" onchange="loadContracts()"><option value="">All Types</option></select>
            </div>
            <div class="filter-group">
                <label>Status</label>
                <select id="fStatus" onchange="loadContracts()">
                    <option value="">All</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Completed">Completed</option>
                    <option value="On Hold">On Hold</option>
                    <option value="Cancelled">Cancelled</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Payment</label>
                <select id="fPaymentStatus" onchange="loadContracts()">
                    <option value="">All</option>
                    <option value="pending">Pending</option>
                    <option value="recovered">Recovered</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Overdue</label>
                <select id="fOverdue" onchange="loadContracts()">
                    <option value="">All</option>
                    <option value="true">Yes</option>
                </select>
            </div>
            <div class="filter-group">
                <label>From (Contract)</label>
                <input type="date" id="fDateFrom" onchange="loadContracts()">
            </div>
            <div class="filter-group">
                <label>To (Contract)</label>
                <input type="date" id="fDateTo" onchange="loadContracts()">
            </div>
            <div class="filter-group">
                <label>From (Payment)</label>
                <input type="date" id="fPayDateFrom" onchange="loadContracts()" title="Auditing: Only show contracts with payments in this range">
            </div>
            <div class="filter-group">
                <label>To (Payment)</label>
                <input type="date" id="fPayDateTo" onchange="loadContracts()" title="Auditing: Only show contracts with payments in this range">
            </div>
            <button class="btn btn-ghost btn-sm" onclick="clearContractFilters()" style="align-self:flex-end;">Clear</button>
        </div>
        <div class="card">
            <div class="table-wrapper" id="contractsTable">
                <p class="text-secondary text-center" style="padding:40px;">Loading...</p>
            </div>
        </div>
    `;

    // Populate filter dropdowns
    const bS = document.getElementById('fBdo');
    state.bdos.forEach(b => bS.innerHTML += `<option value="${b.id}">${b.name}</option>`);
    const cS = document.getElementById('fClient');
    state.clients.forEach(c => cS.innerHTML += `<option value="${c.id}">${c.name}</option>`);
    const pS = document.getElementById('fPlatform');
    state.platforms.forEach(p => pS.innerHTML += `<option value="${p.id}">${p.name}</option>`);
    const tS = document.getElementById('fClientType');
    state.clientTypes.forEach(t => tS.innerHTML += `<option value="${t.id}">${t.name}</option>`);

    // Handle incoming pending filters (e.g., from Dashboard cards)
    if (state.pendingFilters) {
        if (state.pendingFilters.dateFrom) document.getElementById('fDateFrom').value = state.pendingFilters.dateFrom;
        if (state.pendingFilters.dateTo) document.getElementById('fDateTo').value = state.pendingFilters.dateTo;
        if (state.pendingFilters.payDateFrom) document.getElementById('fPayDateFrom').value = state.pendingFilters.payDateFrom;
        if (state.pendingFilters.payDateTo) document.getElementById('fPayDateTo').value = state.pendingFilters.payDateTo;
        if (state.pendingFilters.status) document.getElementById('fStatus').value = state.pendingFilters.status;
        if (state.pendingFilters.payment_status) document.getElementById('fPaymentStatus').value = state.pendingFilters.payment_status;
        if (state.pendingFilters.is_overdue) document.getElementById('fOverdue').value = 'true';
        state.pendingFilters = null;
    }

    // Enter key triggers filter
    document.getElementById('fSearch').addEventListener('keyup', e => { if (e.key === 'Enter') loadContracts(); });

    loadContracts();
}

function openFilteredContracts(filters) {
    state.pendingFilters = filters;
    navigateTo('contracts');
}

async function loadContracts() {
    const params = new URLSearchParams();
    const fSearch = document.getElementById('fSearch')?.value;
    const fBdo = document.getElementById('fBdo')?.value;
    const fClient = document.getElementById('fClient')?.value;
    const fPlatform = document.getElementById('fPlatform')?.value;
    const fStatus = document.getElementById('fStatus')?.value;
    const fType = document.getElementById('fClientType')?.value;
    const fFrom = document.getElementById('fDateFrom')?.value;
    const fTo = document.getElementById('fDateTo')?.value;
    const fPayFrom = document.getElementById('fPayDateFrom')?.value;
    const fPayTo = document.getElementById('fPayDateTo')?.value;
    const fPaymentStatus = document.getElementById('fPaymentStatus')?.value;
    const fOverdue = document.getElementById('fOverdue')?.value;

    if (fSearch) params.set('search', fSearch);
    if (fBdo) params.set('bdo_id', fBdo);
    if (fClient) params.set('client_id', fClient);
    if (fPlatform) params.set('platform_id', fPlatform);
    if (fStatus) params.set('status', fStatus);
    if (fType) params.set('client_type_id', fType);
    if (fFrom) params.set('date_from', fFrom);
    if (fTo) params.set('date_to', fTo);
    if (fPayFrom) params.set('payment_date_from', fPayFrom);
    if (fPayTo) params.set('payment_date_to', fPayTo);
    if (fPaymentStatus) params.set('payment_status', fPaymentStatus);
    if (fOverdue) params.set('is_overdue', fOverdue);

    const contracts = await api(`/api/contracts?${params}`);

    const isAuditing = fPayFrom || fPayTo;
    const tableDiv = document.getElementById('contractsTable');
    if (contracts.length === 0) {
        tableDiv.innerHTML = '<p class="text-secondary text-center" style="padding:40px;">No contracts found</p>';
        return;
    }
    tableDiv.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Client</th>
                    <th>Contract Name</th>
                    <th>Platform</th>
                    <th>Next Payout</th>
                    <th>Budget</th>
                    <th>Net Rev</th>
                    <th style="color: var(--success);">${isAuditing ? 'Recovered in Period' : 'Recovered'}</th>
                    <th>Pending</th>
                    <th>Status</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                ${contracts.map(c => {
                    const recoveredVal = isAuditing ? (c.period_recovered || 0) : (c.recovered || 0);
                    return `
                    <tr onclick="viewContract(${c.id})" style="cursor:pointer;">
                        <td style="font-weight:600;">${c.client_name || '—'}</td>
                        <td>${c.contract_name}</td>
                        <td style="font-size:12px;">${c.platform_name || '—'}</td>
                        <td style="font-size:11px;">${c.next_milestone_date ? formatDate(c.next_milestone_date) : '—'}</td>
                        <td class="font-mono">${formatCurrency(c.budget)}</td>
                        <td class="font-mono">${formatCurrency(c.estimated_revenue)}</td>
                        <td class="font-mono text-success" title="${isAuditing ? 'Total Recovered: ' + formatCurrency(c.recovered) : ''}">${formatCurrency(recoveredVal)}</td>
                        <td class="font-mono text-danger">${formatCurrency(c.pending)}</td>
                        <td>${statusBadge(c.status)}</td>
                        <td>
                            <button class="btn btn-ghost btn-icon" onclick="event.stopPropagation(); deleteContract(${c.id})">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3,6 5,6 21,6"/><path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a1,2,0,0,1,2,2V6"/></svg>
                            </button>
                        </td>
                    </tr>
                `}).join('')}
            </tbody>
        </table>
    `;
}

function clearContractFilters() {
    ['fSearch','fBdo','fClient', 'fPlatform', 'fStatus', 'fClientType', 'fDateFrom' , 'fDateTo' , 'fPayDateFrom', 'fPayDateTo', 'fPaymentStatus', 'fOverdue'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    loadContracts();
}

function openContractForm(contract = null) {
    const isEdit = !!contract;
    const c = contract || {};
    openModal(isEdit ? 'Edit Contract' : 'New Contract', `
        <form id="contractForm">
            <div class="form-group">
                <label class="form-label">Contract Name *</label>
                <input class="form-input" name="contract_name" value="${c.contract_name || ''}" required>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Date</label>
                    <input type="date" class="form-input" name="date" value="${c.date ? c.date.slice(0,10) : ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">Deadline</label>
                    <input type="date" class="form-input" name="deadline" value="${c.deadline ? c.deadline.slice(0,10) : ''}">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Client</label>
                    <div class="autocomplete-wrapper" id="clientAcWrapper">
                        <input class="form-input" id="clientAcInput" autocomplete="off"
                               placeholder="Type client name..."
                               value="${c.client_name || ''}">
                        <input type="hidden" name="client_id" id="clientAcHidden" value="${c.client_id || ''}">
                        <div class="autocomplete-dropdown" id="clientAcDropdown" style="display:none;"></div>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">BDO</label>
                    <select class="form-select" name="bdo_id">
                        ${selectOptions(state.bdos, 'id', 'name', c.bdo_id, '— Select BDO —')}
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Platform</label>
                    <select class="form-select" name="platform_id" id="contractPlatformSelect">
                        ${selectOptions(state.platforms, 'id', 'name', c.platform_id, '— Select Platform —')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Profile</label>
                    <select class="form-select" name="platform_profile_id" id="contractProfileSelect">
                        <option value="">— Select Profile —</option>
                    </select>
                </div>
            </div>
            <div class="form-row-3">
                <div class="form-group">
                    <label class="form-label">Payment Channel</label>
                    <select class="form-select" name="payment_channel_id">
                        ${selectOptions(state.paymentChannels, 'id', 'name', c.payment_channel_id, '— Select —')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Client Type</label>
                    <select class="form-select" name="client_type_id">
                        ${selectOptions(state.clientTypes, 'id', 'name', c.client_type_id, '— Select —')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Budget (Client Pays)</label>
                    <input type="number" step="0.01" class="form-input" id="contractBudget" name="budget" value="${c.budget || ''}" oninput="calculateNetRevenue()">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Estimated Net Revenue <span id="netRevHelp" style="font-size:11px;color:#888;"></span></label>
                    <input type="number" step="0.01" class="form-input" id="contractNetRevenue" name="estimated_revenue" value="${c.estimated_revenue || ''}" readonly style="background:#f9fafb;">
                </div>
                <div class="form-group">
                    <label class="form-label">Payment Structure</label>
                    <select class="form-select" name="payment_structure" id="paymentStructureSelect" onchange="toggleMilestoneBuilder()">
                        <option value="One-Time" ${c.payment_structure === 'One-Time' ? 'selected' : ''}>One-Time Payment</option>
                        <option value="Milestone" ${c.payment_structure === 'Milestone' ? 'selected' : ''}>Milestones</option>
                    </select>
                </div>
            </div>

            <div id="milestoneBuilderArea" style="display: ${c.payment_structure === 'Milestone' ? 'block' : 'none'}; padding: 12px; background: #fdfdfd; border: 1px dashed var(--border); border-radius: var(--radius-sm); margin-bottom: 16px;">
                <h4 style="font-size:14px; margin-bottom:10px; font-weight:600;">Initial Milestones</h4>
                <div id="milestoneList"></div>
                ${!isEdit ? `<button type="button" class="btn btn-sm btn-outline" onclick="addMilestoneRow()">+ Add Milestone</button>` : `<p style="font-size:12px; color:var(--text-secondary);">Add or manage milestones from the Contract Details page.</p>`}
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Status</label>
                    <select class="form-select" name="status">
                        ${['In Progress','Completed','On Hold','Cancelled'].map(s =>
                            `<option value="${s}" ${c.status === s ? 'selected' : ''}>${s}</option>`
                        ).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Workspace</label>
                    <input class="form-input" name="workspace" value="${c.workspace || ''}">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Approved Date</label>
                    <input type="date" class="form-input" name="approved_date" value="${c.approved_date ? c.approved_date.slice(0,10) : ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">Delay Reason</label>
                    <input class="form-input" name="delay_reason" value="${c.delay_reason || ''}">
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Notes</label>
                <textarea class="form-textarea" name="notes">${c.notes || ''}</textarea>
            </div>
            <div class="modal-footer" style="padding:16px 0 0; border-top:1px solid var(--border-light); margin-top:8px;">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">${isEdit ? 'Update' : 'Create'} Contract</button>
            </div>
        </form>
    `);

    // Platform -> Profile dependency
    const platformSel = document.getElementById('contractPlatformSelect');
    const profileSel = document.getElementById('contractProfileSelect');

    function updateProfiles() {
        const pid = platformSel.value;
        const filtered = state.platformProfiles.filter(p => p.platform_id == pid);
        profileSel.innerHTML = '<option value="">— Select Profile —</option>';
        filtered.forEach(p => {
            const sel = p.id == c.platform_profile_id ? ' selected' : '';
            profileSel.innerHTML += `<option value="${p.id}"${sel}>${p.profile_name}</option>`;
        });
        calculateNetRevenue();
    }

    platformSel.addEventListener('change', updateProfiles);
    if (c.platform_id) updateProfiles();

    // Client autocomplete
    setupClientAutocomplete(c.client_id, c.client_name);

    // Form submit
    document.getElementById('contractForm').addEventListener('submit', async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const body = {};
        fd.forEach((v, k) => body[k] = v || null);
        if (body.estimated_revenue) body.estimated_revenue = parseFloat(body.estimated_revenue);
        if (body.budget) body.budget = parseFloat(body.budget);

        // Collect milestones if any
        if (body.payment_structure === 'Milestone' && !isEdit) {
            const rows = document.querySelectorAll('.milestone-row');
            const milestones = [];
            rows.forEach(row => {
                const desc = row.querySelector('.milestone-desc').value;
                const amount = parseFloat(row.querySelector('.milestone-amount').value);
                const date = row.querySelector('.milestone-date').value;
                if (desc && amount && date) milestones.push({description: desc, amount: amount, due_date: date});
            });
            body.milestones = milestones;
        }

        // Handle client: find or create by name
        const clientInput = document.getElementById('clientAcInput').value.trim();
        const clientHidden = document.getElementById('clientAcHidden').value;
        if (clientInput && !clientHidden) {
            const result = await api('/api/clients/find-or-create', {
                method: 'POST', body: JSON.stringify({ name: clientInput })
            });
            body.client_id = result.id;
            if (result.created) showToast(`Client "${result.name}" created`, 'success');
        } else {
            body.client_id = clientHidden || null;
        }

        if (isEdit) {
            await api(`/api/contracts/${c.id}`, { method: 'PUT', body: JSON.stringify(body) });
            showToast('Contract updated', 'success');
        } else {
            await api('/api/contracts', { method: 'POST', body: JSON.stringify(body) });
            showToast('Contract created', 'success');
        }
        
        closeModal();
        await loadLookups();
        if (state.currentPage === 'contracts') renderContracts();
        else if (state.currentPage === 'contract-detail' && c.id) await viewContract(c.id);
        else if (state.currentPage === 'client-detail') await viewClient(c.client_id);
    });

    // Initial setup for form logic
    setTimeout(() => {
        calculateNetRevenue();
        if (!isEdit && c.payment_structure === 'Milestone') toggleMilestoneBuilder();
    }, 100);
}

function calculateNetRevenue() {
    const budgetEl = document.getElementById('contractBudget');
    if (!budgetEl) return;
    const budgetVal = parseFloat(budgetEl.value);
    const platformId = document.getElementById('contractPlatformSelect')?.value;
    const netRevEl = document.getElementById('contractNetRevenue');
    const helpEl = document.getElementById('netRevHelp');
    
    if (isNaN(budgetVal)) {
        netRevEl.value = '';
        helpEl.innerText = '';
        return;
    }
    
    let fee = 0;
    if (platformId) {
        const platform = state.platforms.find(p => p.id == platformId);
        if (platform) fee = platform.fee_percentage || 0;
    }
    
    if (fee > 0) {
        const net = budgetVal - (budgetVal * (fee / 100));
        netRevEl.value = net.toFixed(2);
        helpEl.innerText = `(-${fee}% fee)`;
    } else {
        netRevEl.value = budgetVal.toFixed(2);
        helpEl.innerText = `(No fee)`;
    }
}

function toggleMilestoneBuilder() {
    const el = document.getElementById('paymentStructureSelect');
    if (!el) return;
    const val = el.value;
    document.getElementById('milestoneBuilderArea').style.display = (val === 'Milestone') ? 'block' : 'none';
    const list = document.getElementById('milestoneList');
    if (val === 'Milestone' && list && list.children.length === 0) {
        addMilestoneRow();
    }
}

function addMilestoneRow() {
    const list = document.getElementById('milestoneList');
    if (!list) return;
    const div = document.createElement('div');
    div.className = 'milestone-row';
    div.style.display = 'flex';
    div.style.gap = '8px';
    div.style.marginBottom = '8px';
    div.innerHTML = `
        <input type="text" class="form-input milestone-desc" placeholder="Desc (e.g. 50% Upfront)" required style="flex:2">
        <input type="number" step="0.01" class="form-input milestone-amount" placeholder="Amount" required style="flex:1">
        <input type="date" class="form-input milestone-date" required style="flex:1">
        <button type="button" class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">&times;</button>
    `;
    list.appendChild(div);
}

// Contract detail view
async function viewContract(id) {
    const c = await api(`/api/contracts/${id}`);
    if (!c) return;

    state.currentPage = 'contract-detail';
    document.getElementById('pageTitle').textContent = `Contract Details`;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('nav-contracts')?.classList.add('active');

    const container = document.getElementById('pageContainer');
    container.innerHTML = `
        <div class="flex items-center justify-between mb-6">
            <button class="btn btn-outline" onclick="navigateTo('contracts')">← Back to Contracts</button>
            <div class="flex gap-10">
                <button class="btn btn-danger" onclick="deleteContract(${c.id})">Delete</button>
                <button class="btn btn-primary" onclick="openContractForm(${JSON.stringify(c).replace(/"/g, '&quot;')})">Edit Contract</button>
            </div>
        </div>

        <div class="card mb-6" style="width: 100%;">
            <div class="card-header"><span class="card-title">${c.contract_name}</span></div>
            <div class="card-body">
                <div class="detail-grid mb-6">
                    <div class="detail-item"><span class="detail-label">Status</span><span class="detail-value">${statusBadge(c.status)}</span></div>
                    <div class="detail-item"><span class="detail-label">Date</span><span class="detail-value">${formatDate(c.date)}</span></div>
                    <div class="detail-item"><span class="detail-label">Deadline</span><span class="detail-value ${deadlineClass(c.deadline)}">${formatDate(c.deadline)}</span></div>
                    <div class="detail-item"><span class="detail-label">Approved Date</span><span class="detail-value">${formatDate(c.approved_date)}</span></div>
                    <div class="detail-item"><span class="detail-label">Client</span><span class="detail-value">${c.client_name || '—'}</span></div>
                    <div class="detail-item"><span class="detail-label">BDO</span><span class="detail-value">${c.bdo_name || '—'}</span></div>
                    <div class="detail-item"><span class="detail-label">Platform</span><span class="detail-value">${c.platform_name || '—'}${c.profile_name ? ' / ' + c.profile_name : ''}</span></div>
                    <div class="detail-item"><span class="detail-label">Payment Channel</span><span class="detail-value">${c.payment_channel_name || '—'}</span></div>
                    <div class="detail-item"><span class="detail-label">Client Type</span><span class="detail-value">${c.client_type_name || '—'}</span></div>
                 <div class="stats-grid mb-6">
                    <div class="stat-card primary" style="padding:16px;">
                        <div class="stat-label">Client Budget</div>
                        <div class="stat-value" style="font-size:20px;">${formatCurrency(c.budget)}</div>
                    </div>
                    <div class="stat-card info" style="padding:16px;">
                        <div class="stat-label">Net Revenue</div>
                        <div class="stat-value" style="font-size:20px;">${formatCurrency(c.estimated_revenue)}</div>
                    </div>
                    <div class="stat-card success" style="padding:16px;">
                        <div class="stat-label">Recovered</div>
                        <div class="stat-value" style="font-size:20px;">${formatCurrency(c.recovered)}</div>
                    </div>
                    <div class="stat-card warning" style="padding:16px;">
                        <div class="stat-label">Pending</div>
                        <div class="stat-value" style="font-size:20px;">${formatCurrency(c.pending)}</div>
                    </div>
                </div>

                ${c.delay_reason ? `<div class="mb-4"><span class="detail-label">Delay Reason</span><p style="margin-top:4px;">${c.delay_reason}</p></div>` : ''}
                ${c.notes ? `<div class="mb-4"><span class="detail-label">Notes</span><p style="margin-top:4px;">${c.notes}</p></div>` : ''}
            </div>
        </div>

        <div class="card mb-6 border-warning" style="border-left: 4px solid var(--warning); width: 100%;">
            <div class="card-header" style="justify-content:space-between; background: rgba(245, 158, 11, 0.05);">
                <span class="card-title" style="color: #b45309; font-size: 1.1rem;">⏳ Pending Payments / Upcoming Milestones (${c.milestones?.filter(m => m.status === 'Pending').length || 0})</span>
                <button class="btn btn-sm btn-outline" style="background: white;" onclick="openAddMilestoneModal(${c.id})">+ Add Milestone</button>
            </div>
            <div class="table-wrapper">
                ${c.milestones?.filter(m => m.status === 'Pending').length ? `<table>
                    <thead><tr><th>Description</th><th>Amount</th><th>Due Date</th><th>Notes</th><th>Action</th></tr></thead>
                    <tbody>${c.milestones.filter(m => m.status === 'Pending').map(m => `
                        <tr>
                            <td style="font-weight:600;">${m.description}</td>
                            <td class="font-mono" style="color:var(--warning); font-weight:700;">${formatCurrency(m.amount)}</td>
                            <td class="${deadlineClass(m.due_date)}">${formatDate(m.due_date)}</td>
                            <td style="font-size:12px; color:var(--text-secondary); max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${m.notes || ''}">${m.notes || '—'}</td>
                            <td>
                                <button class="btn btn-xs btn-success" onclick="markMilestonePaid(${m.id}, ${c.id})">Mark Paid</button>
                                <button class="btn btn-ghost btn-icon" onclick="deleteMilestone(${m.id}, ${c.id})">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3,6 5,6 21,6"/><path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a1,2,0,0,1,2,2V6"/></svg>
                                </button>
                            </td>
                        </tr>
                    `).join('')}</tbody>
                </table>` : '<p class="text-secondary text-center" style="padding:30px; font-style: italic;">No pending milestones or payments scheduled.</p>'}
            </div>
        </div>

        ${c.milestones?.filter(m => m.status === 'Paid').length ? `
        <div class="card mb-6" style="width: 100%;">
            <div class="card-header">
                <span class="card-title">Completed Milestones (Schedule History)</span>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead><tr><th>Description</th><th>Amount</th><th>Completion Date</th><th>Notes</th><th>Status</th></tr></thead>
                    <tbody>${c.milestones.filter(m => m.status === 'Paid').map(m => `
                        <tr>
                            <td style="font-weight:600;">${m.description}</td>
                            <td class="font-mono text-success">${formatCurrency(m.amount)}</td>
                            <td>${formatDate(m.updated_at || m.due_date)}</td>
                            <td style="font-size:12px; color:var(--text-secondary);">${m.notes || '—'}</td>
                            <td><span class="badge badge-success">Paid</span></td>
                        </tr>
                    `).join('')}</tbody>
                </table>
            </div>
        </div>
        ` : ''}

        <div class="card mb-6" style="width: 100%;">
            <div class="card-header" style="justify-content:space-between;">
                <span class="card-title">Payments / Recovery Logs</span>
                <button class="btn btn-sm btn-success" onclick="openPaymentForm(${c.id})">+ Log Payment</button>
            </div>
            <div class="table-wrapper" id="contractPayments">
                ${c.payments?.length ? `<table>
                    <thead><tr><th>Date</th><th>Amount</th><th>Channel</th><th>Notes</th><th></th></tr></thead>
                    <tbody>${c.payments.map(p => `
                        <tr>
                            <td>${formatDate(p.payment_date)}</td>
                            <td class="font-mono text-success">${formatCurrency(p.amount)}</td>
                            <td>${p.channel_name || '—'}</td>
                            <td>${p.notes || '—'}</td>
                            <td><button class="btn btn-ghost btn-icon" onclick="deletePayment(${p.id}, ${c.id})" title="Delete">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3,6 5,6 21,6"/><path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"/></svg>
                            </button></td>
                        </tr>
                    `).join('')}</tbody>
                </table>` : '<p class="text-secondary text-center" style="padding:40px;">No recovery logs yet</p>'}
            </div>
        </div>
    `;
}

async function markMilestonePaid(mid, cid) {
    if (!confirm('Mark this milestone as paid? This will also add a record to Payments.')) return;
    await api(`/api/milestones/${mid}/pay`, { method: 'POST' });
    showToast('Milestone paid and payment logged', 'success');
    viewContract(cid);
}

function openAddMilestoneModal(cid) {
    openModal('Add Milestone', `
        <form id="addMilestoneForm">
            <input type="hidden" name="contract_id" value="${cid}">
            <div class="form-group">
                <label class="form-label">Description *</label>
                <input class="form-input" name="description" placeholder="e.g. 2nd Installment" required>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Amount *</label>
                    <input type="number" step="0.01" class="form-input" name="amount" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Due Date *</label>
                    <input type="date" class="form-input" name="due_date" required>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Notes</label>
                <textarea class="form-textarea" name="notes" placeholder="Optional internal notes..."></textarea>
            </div>
            <div class="modal-footer" style="padding:16px 0 0; border-top:1px solid var(--border-light); margin-top:8px;">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Add Milestone</button>
            </div>
        </form>
    `);
    
    document.getElementById('addMilestoneForm').onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const body = Object.fromEntries(fd.entries());
        body.amount = parseFloat(body.amount);
        
        try {
            await api('/api/milestones', { method: 'POST', body: JSON.stringify(body) });
            showToast('Milestone added', 'success');
            closeModal();
            viewContract(cid);
        } catch (err) {
            console.error(err);
            showToast('Error adding milestone. Please ensure server is running.', 'error');
        }
    };
}

async function deleteMilestone(mid, cid) {
    if (!confirm('Delete this milestone?')) return;
    await api(`/api/milestones/${mid}`, { method: 'DELETE' });
    showToast('Milestone deleted', 'success');
    viewContract(cid);
}

async function deleteContract(id) {
    if (!confirm('Delete this contract and all its payments?')) return;
    await api(`/api/contracts/${id}`, { method: 'DELETE' });
    showToast('Contract deleted', 'success');
    if (state.currentPage === 'contract-detail') navigateTo('contracts');
    else loadContracts();
}

// ─── CLIENTS ───
async function renderClients() {
    const container = document.getElementById('pageContainer');
    container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <div></div>
            <button class="btn btn-primary" onclick="openClientForm()">+ New Client</button>
        </div>
        <div class="card">
            <div class="table-wrapper" id="clientsTable">
                <p class="text-secondary text-center" style="padding:40px;">Loading...</p>
            </div>
        </div>
    `;

    const clients = await api('/api/clients');
    state.clients = clients;
    const tableDiv = document.getElementById('clientsTable');

    if (!clients.length) {
        tableDiv.innerHTML = `<div class="empty-state"><h3>No clients yet</h3><p>Add your first client</p></div>`;
        return;
    }

    tableDiv.innerHTML = `<table>
        <thead><tr><th>Name</th><th>Company</th><th>Email</th><th>Contracts</th><th>Revenue</th><th>Recovered</th><th>Pending</th><th>Status</th><th></th></tr></thead>
        <tbody>${clients.map(c => `
            <tr class="clickable-row" onclick="viewClient(${c.id})">
                <td style="font-weight:600;">${c.name}</td>
                <td>${c.company || '—'}</td>
                <td>${c.email || '—'}</td>
                <td>${c.contract_count}</td>
                <td class="font-mono">${formatCurrency(c.total_revenue)}</td>
                <td class="font-mono text-success">${formatCurrency(c.total_recovered)}</td>
                <td class="font-mono text-danger">${formatCurrency(c.total_pending)}</td>
                <td>${statusBadge(c.status)}</td>
                <td>
                    <button class="btn btn-ghost btn-icon" onclick="event.stopPropagation(); deleteClient(${c.id})" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3,6 5,6 21,6"/><path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"/></svg>
                    </button>
                </td>
            </tr>
        `).join('')}</tbody>
    </table>`;
}

function openClientForm(client = null) {
    const isEdit = !!client;
    const c = client || {};
    openModal(isEdit ? 'Edit Client' : 'New Client', `
        <form id="clientForm">
            <div class="form-group">
                <label class="form-label">Name *</label>
                <input class="form-input" name="name" value="${c.name || ''}" required>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-input" name="email" value="${c.email || ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">Phone</label>
                    <input class="form-input" name="phone" value="${c.phone || ''}">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Company</label>
                    <input class="form-input" name="company" value="${c.company || ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">Status</label>
                    <select class="form-select" name="status">
                        ${['Active','Inactive','Lead'].map(s => `<option value="${s}" ${c.status === s ? 'selected' : ''}>${s}</option>`).join('')}
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Notes</label>
                <textarea class="form-textarea" name="notes">${c.notes || ''}</textarea>
            </div>
            <div class="modal-footer" style="padding:16px 0 0; border-top:1px solid var(--border-light);">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">${isEdit ? 'Update' : 'Create'} Client</button>
            </div>
        </form>
    `);

    document.getElementById('clientForm').addEventListener('submit', async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const body = {};
        fd.forEach((v, k) => body[k] = v || null);

        if (isEdit) {
            await api(`/api/clients/${c.id}`, { method: 'PUT', body: JSON.stringify(body) });
            showToast('Client updated', 'success');
        } else {
            const res = await api('/api/clients', { method: 'POST', body: JSON.stringify(body) });
            body.id = res.id;
            showToast('Client created', 'success');
        }
        closeModal();
        await loadLookups();
        if (state.currentPage === 'clients') renderClients();
        else if (state.currentPage === 'client-detail' && c.id) await viewClient(c.id);
    });
}

async function viewClient(id) {
    const c = await api(`/api/clients/${id}`);
    if (!c) return;

    state.currentPage = 'client-detail';
    document.getElementById('pageTitle').textContent = `Client Details`;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('nav-clients')?.classList.add('active');

    const container = document.getElementById('pageContainer');
    container.innerHTML = `
        <div class="flex items-center justify-between mb-6">
            <button class="btn btn-outline" onclick="navigateTo('clients')">← Back to Clients</button>
            <div class="flex gap-10">
                <button class="btn btn-danger" onclick="deleteClient(${c.id})">Delete</button>
                <button class="btn btn-primary" onclick="openClientForm(${JSON.stringify(c).replace(/"/g, '&quot;')})">Edit Client</button>
            </div>
        </div>

        <div class="card mb-6">
            <div class="card-header"><span class="card-title">${c.name}</span></div>
            <div class="card-body">
                <div class="detail-grid mb-6">
                    <div class="detail-item"><span class="detail-label">Email</span><span class="detail-value">${c.email || '—'}</span></div>
                    <div class="detail-item"><span class="detail-label">Phone</span><span class="detail-value">${c.phone || '—'}</span></div>
                    <div class="detail-item"><span class="detail-label">Company</span><span class="detail-value">${c.company || '—'}</span></div>
                    <div class="detail-item"><span class="detail-label">Status</span><span class="detail-value">${statusBadge(c.status)}</span></div>
                </div>
                ${c.notes ? `<div class="mb-4"><span class="detail-label">Notes</span><p style="margin-top:4px;">${c.notes}</p></div>` : ''}
            </div>
        </div>

        <div class="card mb-6">
            <div class="card-header"><span class="card-title">Contracts (${c.contracts?.length || 0})</span></div>
            <div class="table-wrapper">
                ${c.contracts?.length ? `<table>
                    <thead><tr><th>Name</th><th>Date</th><th>Revenue</th><th>Recovered</th><th>Status</th></tr></thead>
                    <tbody>${c.contracts.map(con => `
                        <tr class="clickable-row" onclick="viewContract(${con.id})">
                            <td style="font-weight:600;">${con.contract_name}</td>
                            <td>${formatDate(con.date)}</td>
                            <td class="font-mono">${formatCurrency(con.estimated_revenue)}</td>
                            <td class="font-mono text-success">${formatCurrency(con.recovered)}</td>
                            <td>${statusBadge(con.status)}</td>
                        </tr>
                    `).join('')}</tbody>
                </table>` : '<p class="text-secondary text-center" style="padding:40px;">No contracts</p>'}
            </div>
        </div>

        <div class="card mb-6">
            <div class="card-header"><span class="card-title">Payment History</span></div>
            <div class="table-wrapper">
                ${c.payments?.length ? `<table>
                    <thead><tr><th>Date</th><th>Contract</th><th>Amount</th><th>Channel</th></tr></thead>
                    <tbody>${c.payments.map(p => `
                        <tr>
                            <td>${formatDate(p.payment_date)}</td>
                            <td>${p.contract_name}</td>
                            <td class="font-mono text-success">${formatCurrency(p.amount)}</td>
                            <td>${p.channel_name || '—'}</td>
                        </tr>
                    `).join('')}</tbody>
                </table>` : '<p class="text-secondary text-center" style="padding:40px;">No payments</p>'}
            </div>
        </div>
    `;
}

async function deleteClient(id) {
    if (!confirm('Delete this client?')) return;
    await api(`/api/clients/${id}`, { method: 'DELETE' });
    showToast('Client deleted', 'success');
    await loadLookups();
    if (state.currentPage === 'client-detail') navigateTo('clients');
    else renderClients();
}

// ─── PAYMENTS ───
async function renderPayments() {
    const container = document.getElementById('pageContainer');
    container.innerHTML = `
        <div class="filters-bar mb-4">
            <div class="filter-group">
                <label>Client</label>
                <select id="pClient" onchange="loadPaymentsList()"><option value="">All Clients</option></select>
            </div>
            <div class="filter-group">
                <label>From</label>
                <input type="date" id="pDateFrom" onchange="loadPaymentsList()">
            </div>
            <div class="filter-group">
                <label>To</label>
                <input type="date" id="pDateTo" onchange="loadPaymentsList()">
            </div>
        </div>
        <div class="card">
            <div class="table-wrapper" id="paymentsTable">
                <p class="text-secondary text-center" style="padding:40px;">Loading...</p>
            </div>
        </div>
    `;

    const cS = document.getElementById('pClient');
    state.clients.forEach(c => cS.innerHTML += `<option value="${c.id}">${c.name}</option>`);

    loadPaymentsList();
}

async function loadPaymentsList() {
    const params = new URLSearchParams();
    const cl = document.getElementById('pClient')?.value;
    const from = document.getElementById('pDateFrom')?.value;
    const to = document.getElementById('pDateTo')?.value;
    if (cl) params.set('client_id', cl);
    if (from) params.set('date_from', from);
    if (to) params.set('date_to', to);

    const payments = await api(`/api/payments?${params}`);
    const tableDiv = document.getElementById('paymentsTable');

    if (!payments.length) {
        tableDiv.innerHTML = `<div class="empty-state"><h3>No payments found</h3><p>Record payments from contract detail views</p></div>`;
        return;
    }

    const total = payments.reduce((s, p) => s + p.amount, 0);

    tableDiv.innerHTML = `<table>
        <thead><tr><th>Date</th><th>Contract</th><th>Client</th><th>Amount</th><th>Channel</th><th>Notes</th></tr></thead>
        <tbody>${payments.map(p => `
            <tr>
                <td>${formatDate(p.payment_date)}</td>
                <td style="font-weight:500;">${p.contract_name}</td>
                <td>${p.client_name || '—'}</td>
                <td class="font-mono text-success">${formatCurrency(p.amount)}</td>
                <td>${p.channel_name || '—'}</td>
                <td>${p.notes || '—'}</td>
            </tr>
        `).join('')}
        <tr style="font-weight:700; background:#f9fafb;">
            <td colspan="3">Total</td>
            <td class="font-mono text-success">${formatCurrency(total)}</td>
            <td colspan="2"></td>
        </tr>
        </tbody>
    </table>`;
}

function openPaymentForm(contractId) {
    openModal('Record Payment', `
        <form id="paymentForm">
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Amount *</label>
                    <input type="number" step="0.01" class="form-input" name="amount" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Date *</label>
                    <input type="date" class="form-input" name="payment_date" value="${new Date().toISOString().slice(0,10)}" required>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Payment Channel</label>
                <select class="form-select" name="payment_channel_id">
                    ${selectOptions(state.paymentChannels, 'id', 'name', null, '— Select —')}
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Notes</label>
                <textarea class="form-textarea" name="notes"></textarea>
            </div>
            <div class="modal-footer" style="padding:16px 0 0; border-top:1px solid var(--border-light);">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-success">Record Payment</button>
            </div>
        </form>
    `);

    document.getElementById('paymentForm').addEventListener('submit', async e => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const body = { contract_id: contractId };
        fd.forEach((v, k) => body[k] = v || null);
        body.amount = parseFloat(body.amount);

        await api('/api/payments', { method: 'POST', body: JSON.stringify(body) });
        showToast('Payment recorded', 'success');
        closeModal();
        viewContract(contractId);
    });
}

async function deletePayment(paymentId, contractId) {
    if (!confirm('Delete this payment?')) return;
    await api(`/api/payments/${paymentId}`, { method: 'DELETE' });
    showToast('Payment deleted', 'success');
    viewContract(contractId);
}

// ─── REPORTS ───
let reportCharts = {};

async function renderReports() {
    const container = document.getElementById('pageContainer');
    container.innerHTML = `
        <div class="report-filters-bar">
            <div class="report-filter-group">
                <label>BDO</label>
                <select id="rfBdo" class="form-select" style="min-width:150px;" onchange="loadAdvancedReports()">
                    <option value="">All BDOs</option>
                    ${state.bdos.map(b => `<option value="${b.id}">${b.name}</option>`).join('')}
                </select>
            </div>
            <div class="report-filter-group">
                <label>Platform</label>
                <select id="rfPlatform" class="form-select" style="min-width:150px;" onchange="loadAdvancedReports()">
                    <option value="">All Platforms</option>
                    ${state.platforms.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
                </select>
            </div>
            <div class="report-filter-group">
                <label>Client</label>
                <select id="rfClient" class="form-select" style="min-width:150px;" onchange="loadAdvancedReports()">
                    <option value="">All Clients</option>
                    ${state.clients.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                </select>
            </div>
            <div class="report-filter-group">
                <label>Contract</label>
                <select id="rfContract" class="form-select" style="min-width:200px;" onchange="loadAdvancedReports()">
                    <option value="">All Contracts</option>
                    ${state.contracts.sort((a,b) => b.id - a.id).map(c => `<option value="${c.id}">${c.client_name} - ${c.contract_name || 'N/A'}</option>`).join('')}
                </select>
            </div>
            <div class="report-filter-group">
                <label>From</label>
                <input type="date" id="rfDateFrom" class="form-input" onchange="loadAdvancedReports()">
            </div>
            <div class="report-filter-group">
                <label>To</label>
                <input type="date" id="rfDateTo" class="form-input" onchange="loadAdvancedReports()">
            </div>
            <div style="flex:1;"></div>
            <div class="flex gap-10">
                <a href="/api/export/contracts" class="btn btn-outline" download>📥 Export CSV</a>
            </div>
        </div>

        <div class="reports-stats-row" id="reportSummaryStats">
            <div class="mini-stat-card info">
                <div class="mini-stat-label">Gross Sales</div>
                <div class="mini-stat-value" id="statGross">$0.00</div>
            </div>
            <div class="mini-stat-card primary">
                <div class="mini-stat-label">Net Revenue</div>
                <div class="mini-stat-value" id="statNet">$0.00</div>
            </div>
            <div class="mini-stat-card success">
                <div class="mini-stat-label">Recovered</div>
                <div class="mini-stat-value" id="statRecovered">$0.00</div>
            </div>
            <div class="mini-stat-card warning">
                <div class="mini-stat-label">Pending Total</div>
                <div class="mini-stat-value" id="statPending">$0.00</div>
            </div>
        </div>

        <div class="reports-grid">
            <div class="report-card">
                <div class="chart-header">
                    <span class="chart-title">📈 Revenue Trend</span>
                </div>
                <div class="chart-container">
                    <canvas id="chartTrend"></canvas>
                </div>
            </div>
            <div class="report-card">
                <div class="chart-header">
                    <span class="chart-title">👥 BDO Performance</span>
                </div>
                <div class="chart-container">
                    <canvas id="chartBdo"></canvas>
                </div>
            </div>
            <div class="report-card" style="grid-column: 1 / -1;">
                <div class="chart-header">
                    <span class="chart-title">🌐 Platform Revenue Distribution</span>
                </div>
                <div class="chart-container" style="height:400px;">
                    <canvas id="chartPlatform"></canvas>
                </div>
            </div>
        </div>
    `;

    setTimeout(loadAdvancedReports, 100);
}

async function loadAdvancedReports() {
    const params = new URLSearchParams();
    const bdo = document.getElementById('rfBdo')?.value;
    const platform = document.getElementById('rfPlatform')?.value;
    const client = document.getElementById('rfClient')?.value;
    const contract = document.getElementById('rfContract')?.value;
    const from = document.getElementById('rfDateFrom')?.value;
    const to = document.getElementById('rfDateTo')?.value;

    if (bdo) params.set('bdo_id', bdo);
    if (platform) params.set('platform_id', platform);
    if (client) params.set('client_id', client);
    if (contract) params.set('contract_id', contract);
    if (from) params.set('date_from', from);
    if (to) params.set('date_to', to);

    const data = await api(`/api/reports/advanced?${params}`);
    if (!data || !data.stats) {
        showToast('Failed to load report data', 'error');
        return;
    }
    
    // Update Stats
    const getEl = id => document.getElementById(id);
    if (getEl('statGross')) getEl('statGross').textContent = formatCurrency(data.stats.total_gross);
    if (getEl('statNet')) getEl('statNet').textContent = formatCurrency(data.stats.total_net);
    if (getEl('statRecovered')) getEl('statRecovered').textContent = formatCurrency(data.stats.total_recovered);
    if (getEl('statPending')) getEl('statPending').textContent = formatCurrency(data.stats.total_pending);

    // Destroy existing charts to prevent memory leaks/glitches
    Object.values(reportCharts).forEach(c => c.destroy());

    // 1. Trend Chart (Line)
    const trendCanvas = document.getElementById('chartTrend');
    if (trendCanvas && data.trend && data.trend.length) {
        const trendCtx = trendCanvas.getContext('2d');
        reportCharts.trend = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: data.trend.map(t => t.month),
                datasets: [
                    {
                        label: 'Net Revenue',
                        data: data.trend.map(t => t.net_revenue),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Recovered',
                        data: data.trend.map(t => t.recovered),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + v.toLocaleString() } } }
            }
        });
    }

    // 2. BDO Performance (Bar)
    const bdoCanvas = document.getElementById('chartBdo');
    if (bdoCanvas && data.bdo_breakdown && data.bdo_breakdown.length) {
        const bdoCtx = bdoCanvas.getContext('2d');
        reportCharts.bdo = new Chart(bdoCtx, {
            type: 'bar',
            data: {
                labels: data.bdo_breakdown.map(b => b.bdo_name),
                datasets: [{
                    label: 'Revenue by BDO',
                    data: data.bdo_breakdown.map(b => b.revenue),
                    backgroundColor: '#6366f1',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + v.toLocaleString() } } }
            }
        });
    }

    // 3. Platform Share (Bar)
    const platCanvas = document.getElementById('chartPlatform');
    if (platCanvas && data.platform_breakdown && data.platform_breakdown.length) {
        const platformCtx = platCanvas.getContext('2d');
        reportCharts.platform = new Chart(platformCtx, {
            type: 'bar',
            data: {
                labels: data.platform_breakdown.map(p => p.platform_name),
                datasets: [{
                    label: 'Revenue',
                    data: data.platform_breakdown.map(p => p.revenue),
                    backgroundColor: [
                        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'
                    ],
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, ticks: { callback: v => '$' + v.toLocaleString() } } }
            }
        });
    }
}

// ─── SETTINGS ───
let activeSettingsTab = 'bdos';

async function renderSettings() {
    const container = document.getElementById('pageContainer');
    container.innerHTML = '<p class="text-secondary">Loading settings...</p>';

    await loadLookups();

    container.innerHTML = `
        <div class="settings-tabs">
            <button class="settings-tab ${activeSettingsTab === 'bdos' ? 'active' : ''}" onclick="switchSettingsTab('bdos')">👥 BDOs</button>
            <button class="settings-tab ${activeSettingsTab === 'platforms' ? 'active' : ''}" onclick="switchSettingsTab('platforms')">🌐 Platforms</button>
            <button class="settings-tab ${activeSettingsTab === 'profiles' ? 'active' : ''}" onclick="switchSettingsTab('profiles')">🔗 Profiles</button>
            <button class="settings-tab ${activeSettingsTab === 'channels' ? 'active' : ''}" onclick="switchSettingsTab('channels')">💳 Payment Channels</button>
            <button class="settings-tab ${activeSettingsTab === 'types' ? 'active' : ''}" onclick="switchSettingsTab('types')">📋 Client Types</button>
        </div>

        <!-- BDOs Tab -->
        <div class="settings-tab-content ${activeSettingsTab === 'bdos' ? 'active' : ''}" id="tab-bdos">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Business Development Officers</span>
                </div>
                <div class="card-body">
                    <p class="text-secondary mb-4" style="font-size:13px;">Manage your team members who bring in clients.</p>
                    <div class="settings-list mb-4">${state.bdos.length ? state.bdos.map(b =>
                        `<div class="settings-tag">${b.name}${b.email ? ' <span class="text-secondary" style="font-size:11px;">' + b.email + '</span>' : ''} <span class="tag-delete" onclick="deleteBdo(${b.id})">&times;</span></div>`
                    ).join('') : '<p class="text-secondary">No BDOs added yet</p>'}</div>
                    <div class="settings-add-form">
                        <input type="text" id="newBdoName" placeholder="BDO name">
                        <input type="text" id="newBdoEmail" placeholder="Email (optional)">
                        <button class="btn btn-sm btn-primary" onclick="addBdo()">Add BDO</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Platforms Tab -->
        <div class="settings-tab-content ${activeSettingsTab === 'platforms' ? 'active' : ''}" id="tab-platforms">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Platforms</span>
                </div>
                <div class="card-body">
                    <p class="text-secondary mb-4" style="font-size:13px;">Freelancing platforms where you get clients from. Set a fee % to automatically calculate your Net Revenue.</p>
                    <div class="settings-list mb-4">${state.platforms.length ? state.platforms.map(p =>
                        `<div class="settings-tag" style="display:flex; align-items:center; gap:8px;">
                            ${p.name}
                            <div style="background:#fff; border-radius:4px; padding:2px 6px; display:flex; align-items:center; border:1px solid var(--border);">
                                <input type="number" step="0.1" min="0" max="100" value="${p.fee_percentage || 0}" style="width:40px; border:none; outline:none; font-size:12px; background:transparent;" oninput="debounceFilter(() => updatePlatformFee(${p.id}, this.value))" title="Fee %"> <span style="font-size:11px; color:#888;">% fee</span>
                            </div>
                            <span class="tag-delete" onclick="deletePlatformSetting(${p.id})">&times;</span>
                        </div>`
                    ).join('') : '<p class="text-secondary">No platforms added yet</p>'}</div>
                    <div class="settings-add-form" style="gap:10px;">
                        <input type="text" id="newPlatformName" placeholder="Platform name" style="flex:1;">
                        <input type="number" id="newPlatformFee" placeholder="Fee %" style="width:80px;" min="0" max="100" step="0.1">
                        <button class="btn btn-sm btn-primary" onclick="addPlatform()">Add Platform</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Profiles Tab -->
        <div class="settings-tab-content ${activeSettingsTab === 'profiles' ? 'active' : ''}" id="tab-profiles">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Platform Profiles</span>
                </div>
                <div class="card-body">
                    <p class="text-secondary mb-4" style="font-size:13px;">Multiple profiles per platform (e.g., two Upwork accounts).</p>
                    <div class="settings-list mb-4">${state.platformProfiles.length ? state.platformProfiles.map(p =>
                        `<div class="settings-tag">${p.platform_name} / ${p.profile_name} <span class="tag-delete" onclick="deleteProfileSetting(${p.id})">&times;</span></div>`
                    ).join('') : '<p class="text-secondary">No profiles added yet</p>'}</div>
                    <div class="settings-add-form">
                        <select id="newProfilePlatform" style="min-width:150px; padding:8px 12px; border:1px solid var(--border); border-radius:var(--radius-xs); font-size:13px; font-family:inherit;">
                            ${selectOptions(state.platforms, 'id', 'name', null, 'Select Platform')}
                        </select>
                        <input type="text" id="newProfileName" placeholder="Profile name">
                        <input type="text" id="newProfileUrl" placeholder="URL (optional)">
                        <button class="btn btn-sm btn-primary" onclick="addProfile()">Add Profile</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Payment Channels Tab -->
        <div class="settings-tab-content ${activeSettingsTab === 'channels' ? 'active' : ''}" id="tab-channels">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Payment Channels</span>
                </div>
                <div class="card-body">
                    <p class="text-secondary mb-4" style="font-size:13px;">Methods through which clients pay you.</p>
                    <div class="settings-list mb-4">${state.paymentChannels.length ? state.paymentChannels.map(c =>
                        `<div class="settings-tag">${c.name} <span class="tag-delete" onclick="deleteChannelSetting(${c.id})">&times;</span></div>`
                    ).join('') : '<p class="text-secondary">No channels added yet</p>'}</div>
                    <div class="settings-add-form">
                        <input type="text" id="newChannelName" placeholder="Channel name">
                        <button class="btn btn-sm btn-primary" onclick="addChannel()">Add Channel</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Client Types Tab -->
        <div class="settings-tab-content ${activeSettingsTab === 'types' ? 'active' : ''}" id="tab-types">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Client Types</span>
                </div>
                <div class="card-body">
                    <p class="text-secondary mb-4" style="font-size:13px;">Categories for your contracts (One-time, Retainer, Hourly, etc.).</p>
                    <div class="settings-list mb-4">${state.clientTypes.length ? state.clientTypes.map(t =>
                        `<div class="settings-tag">${t.name} <span class="tag-delete" onclick="deleteTypeSetting(${t.id})">&times;</span></div>`
                    ).join('') : '<p class="text-secondary">No types added yet</p>'}</div>
                    <div class="settings-add-form">
                        <input type="text" id="newTypeName" placeholder="Type name">
                        <button class="btn btn-sm btn-primary" onclick="addType()">Add Type</button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function switchSettingsTab(tab) {
    activeSettingsTab = tab;
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`.settings-tab-content#tab-${tab}`).classList.add('active');
    // Find the button that matches
    document.querySelectorAll('.settings-tab').forEach(t => {
        if (t.textContent.trim().toLowerCase().includes(tab === 'bdos' ? 'bdo' : tab === 'channels' ? 'payment' : tab === 'types' ? 'client' : tab)) {
            t.classList.add('active');
        }
    });
}

// Settings CRUD
async function addBdo() {
    const name = document.getElementById('newBdoName').value.trim();
    const email = document.getElementById('newBdoEmail').value.trim();
    if (!name) return;
    await api('/api/bdos', { method: 'POST', body: JSON.stringify({ name, email }) });
    showToast('BDO added', 'success');
    renderSettings();
}

async function deleteBdo(id) {
    if (!confirm('Delete this BDO?')) return;
    await api(`/api/bdos/${id}`, { method: 'DELETE' });
    showToast('BDO deleted', 'success');
    renderSettings();
}

async function addPlatform() {
    const name = document.getElementById('newPlatformName').value.trim();
    const fee = parseFloat(document.getElementById('newPlatformFee')?.value) || 0;
    if (!name) return;
    await api('/api/platforms', { method: 'POST', body: JSON.stringify({ name, fee_percentage: fee }) });
    showToast('Platform added', 'success');
    renderSettings();
}

async function updatePlatformFee(id, feeValue) {
    const p = state.platforms.find(x => x.id === id);
    if (!p) return;
    const fee = parseFloat(feeValue) || 0;
    p.fee_percentage = fee; // Update state immediately so UI stays synced if they switch tabs
    await api(`/api/platforms/${id}`, { method: 'PUT', body: JSON.stringify({ name: p.name, fee_percentage: fee }) });
    // showToast('Platform fee updated', 'success'); // Too noisy if debouncing frequently
}

async function deletePlatformSetting(id) {
    if (!confirm('Delete this platform?')) return;
    await api(`/api/platforms/${id}`, { method: 'DELETE' });
    showToast('Platform deleted', 'success');
    renderSettings();
}

async function addProfile() {
    const platform_id = document.getElementById('newProfilePlatform').value;
    const profile_name = document.getElementById('newProfileName').value.trim();
    const profile_url = document.getElementById('newProfileUrl').value.trim();
    if (!platform_id || !profile_name) return;
    await api('/api/platform-profiles', { method: 'POST', body: JSON.stringify({ platform_id, profile_name, profile_url }) });
    showToast('Profile added', 'success');
    renderSettings();
}

async function deleteProfileSetting(id) {
    if (!confirm('Delete this profile?')) return;
    await api(`/api/platform-profiles/${id}`, { method: 'DELETE' });
    showToast('Profile deleted', 'success');
    renderSettings();
}

async function addChannel() {
    const name = document.getElementById('newChannelName').value.trim();
    if (!name) return;
    await api('/api/payment-channels', { method: 'POST', body: JSON.stringify({ name }) });
    showToast('Channel added', 'success');
    renderSettings();
}

async function deleteChannelSetting(id) {
    if (!confirm('Delete this channel?')) return;
    await api(`/api/payment-channels/${id}`, { method: 'DELETE' });
    showToast('Channel deleted', 'success');
    renderSettings();
}

async function addType() {
    const name = document.getElementById('newTypeName').value.trim();
    if (!name) return;
    await api('/api/client-types', { method: 'POST', body: JSON.stringify({ name }) });
    showToast('Type added', 'success');
    renderSettings();
}

async function deleteTypeSetting(id) {
    if (!confirm('Delete this type?')) return;
    await api(`/api/client-types/${id}`, { method: 'DELETE' });
    showToast('Type deleted', 'success');
    renderSettings();
}

// ─── CLIENT AUTOCOMPLETE ───
function setupClientAutocomplete(selectedId, selectedName) {
    const input = document.getElementById('clientAcInput');
    const hidden = document.getElementById('clientAcHidden');
    const dropdown = document.getElementById('clientAcDropdown');
    if (!input || !dropdown) return;

    let highlighted = -1;

    input.addEventListener('input', () => {
        const val = input.value.trim().toLowerCase();
        hidden.value = ''; // Clear hidden when user types
        if (!val) { dropdown.style.display = 'none'; return; }

        const matches = state.clients.filter(c => c.name.toLowerCase().includes(val));
        const exactMatch = matches.find(c => c.name.toLowerCase() === val);
        let html = '';

        matches.slice(0, 8).forEach((c, i) => {
            html += `<div class="autocomplete-item" data-id="${c.id}" data-name="${c.name}">${c.name}</div>`;
        });

        // If no exact match, offer to create new
        if (!exactMatch && val.length > 0) {
            html += `<div class="autocomplete-item" data-id="" data-name="${input.value.trim()}">
                <span>${input.value.trim()}</span>
                <span class="ac-new">+ Create New</span>
            </div>`;
        }

        dropdown.innerHTML = html;
        dropdown.style.display = html ? 'block' : 'none';
        highlighted = -1;

        // Click handlers
        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('mousedown', e => {
                e.preventDefault();
                input.value = item.dataset.name;
                hidden.value = item.dataset.id;
                dropdown.style.display = 'none';
            });
        });
    });

    input.addEventListener('keydown', e => {
        const items = dropdown.querySelectorAll('.autocomplete-item');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            highlighted = Math.min(highlighted + 1, items.length - 1);
            items.forEach((it, i) => it.classList.toggle('highlighted', i === highlighted));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            highlighted = Math.max(highlighted - 1, 0);
            items.forEach((it, i) => it.classList.toggle('highlighted', i === highlighted));
        } else if (e.key === 'Enter' && highlighted >= 0 && items[highlighted]) {
            e.preventDefault();
            input.value = items[highlighted].dataset.name;
            hidden.value = items[highlighted].dataset.id;
            dropdown.style.display = 'none';
        }
    });

    input.addEventListener('blur', () => {
        setTimeout(() => { dropdown.style.display = 'none'; }, 150);
    });

    input.addEventListener('focus', () => {
        if (input.value.trim()) input.dispatchEvent(new Event('input'));
    });
}
