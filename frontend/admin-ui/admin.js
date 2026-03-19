/* ============================================================
   VoxMail Admin Dashboard — admin.js
   ============================================================ */

'use strict';

// ── DATA ──────────────────────────────────────────────────────────────────────

let users = [];

const activityData = [
  { icon: 'email',  color: '#EBF0F9', stroke: '#2B5FA0', text: '<strong>Kalyan Sagar</strong> sent an email via voice command',         time: '2 min ago' },
  { icon: 'login',  color: '#EBF2EC', stroke: '#3A6B3E', text: '<strong>Priya Sharma</strong> logged in from Chrome',                   time: '11 min ago' },
  { icon: 'warn',   color: '#FAECEA', stroke: '#C84B3C', text: '<strong>Arjun Nair</strong> failed login 3 times — account blocked',    time: '34 min ago' },
  { icon: 'email',  color: '#EBF0F9', stroke: '#2B5FA0', text: '<strong>Sneha Reddy</strong> sent an email via voice command',          time: '1 hr ago' },
  { icon: 'user',   color: '#FDF3E3', stroke: '#A0620E', text: '<strong>Kiran Patil</strong> registered a new account',                 time: '2 hr ago' },
  { icon: 'email',  color: '#EBF0F9', stroke: '#2B5FA0', text: '<strong>Divya Menon</strong> opened inbox — read 2 emails',            time: '3 hr ago' },
  { icon: 'system', color: '#EBF2EC', stroke: '#3A6B3E', text: 'System health check passed — all services normal',                     time: '6 hr ago' },
];

// ── STATE ─────────────────────────────────────────────────────────────────────
let pendingDeleteId = null;
let currentSearch   = '';
let toastTimer      = null;

// ── SVG ICONS FOR ACTIVITY ────────────────────────────────────────────────────
const ACTIVITY_ICONS = {
  email: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>`,
  login: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
            <polyline points="10 17 15 12 10 7"/>
            <line x1="15" y1="12" x2="3" y2="12"/>
          </svg>`,
  warn:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>`,
  user:  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>`,
  system:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>`,
};

// Total Users


function getActivityIcon(type) {
  return ACTIVITY_ICONS[type] || ACTIVITY_ICONS.system;
}

// ── RENDER: USER TABLE ────────────────────────────────────────────────────────
async function loadUsers() {

  try {

    const res = await fetch("/admin/users");

    if (!res.ok) {
      throw new Error("Failed to fetch users");
    }

    const data = await res.json();

    users = data.users.map((u, index) => ({
      id: index + 1,
      name: u.username,
      email: u.email,
      role: u.role,
      status: u.status || "active",
      emails: 0,
      joined: new Date(u.created_at).toLocaleDateString(),
      initials: u.username.slice(0,2).toUpperCase(),
      color: "#3A6B3E"
    }));

    renderUsers();

  } catch (err) {

    console.error("Error loading users:", err);

  }

}

function renderUsers(filter = '') {
  const tbody    = document.getElementById('user-tbody');
  const filtered = users
  .filter(u => u.role != "admin")
  .filter(u =>
    u.name.toLowerCase().includes(filter.toLowerCase()) ||
    u.email.toLowerCase().includes(filter.toLowerCase())
  );

  tbody.innerHTML = filtered.map(u => {
    const statusBadge = {
      active:  `<span class="badge badge-active"><span class="badge-dot"></span>Active</span>`,
      idle:    `<span class="badge badge-idle"><span class="badge-dot"></span>Idle</span>`,
      blocked: `<span class="badge badge-blocked"><span class="badge-dot"></span>Blocked</span>`,
    }[u.status] || '';

    const roleBadge = u.role === 'admin'
      ? `<span class="badge badge-admin">Admin</span>`
      : `<span style="font-size:12px;color:var(--hint)">User</span>`;

    // Inline SVGs for action buttons
    const iconView = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
    const iconBlock = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>`;
    const iconDelete = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>`;

    return `
      <tr class="user-row" id="user-row-${u.id}">
        <td>
          <div class="user-info">
            <div class="user-avatar" style="background:${u.color}20;color:${u.color}">${u.initials}</div>
            <div>
              <div class="user-name">${u.name}</div>
              <div class="user-email">${u.email}</div>
            </div>
          </div>
        </td>
        <td>${roleBadge}</td>
        <td>${statusBadge}</td>
        <td><span class="mono">${u.emails}</span></td>
        <td style="color:var(--hint);font-size:12px">${u.joined}</td>
        <td>
          <div class="action-btns">
            <button class="btn-icon" title="View user"
              onclick="showToast('Viewing ${u.name}')">
              ${iconView}
            </button>
            <button class="btn-icon" title="${u.status === 'blocked' ? 'Unblock user' : 'Block user'}"
              onclick="toggleBlock(${u.id})">
              ${iconBlock}
            </button>
            <button class="btn-icon danger" title="Remove user"
              onclick="openDeleteModal(${u.id})">
              ${iconDelete}
            </button>
          </div>
        </td>
      </tr>`;
  }).join('');

  // sync badge + metric card
  const totalNormalUsers = users.filter(u => u.role == "user").length;

  document.getElementById('user-count-badge').textContent = totalNormalUsers;
  document.getElementById('totalUsers').textContent          = totalNormalUsers;
}

// ── RENDER: ACTIVITY FEED ─────────────────────────────────────────────────────
function renderActivity() {
  const feed = document.getElementById('activity-feed');

  if (!activityData.length) {
    feed.innerHTML = `
      <div style="padding:24px;text-align:center;color:var(--hint);font-size:13px">
        No recent activity
      </div>`;
    return;
  }

  feed.innerHTML = activityData.map(a => `
    <div class="activity-item">
      <div class="act-dot" style="background:${a.color};color:${a.stroke}">
        ${getActivityIcon(a.icon)}
      </div>
      <div class="act-body">
        <div class="act-text">${a.text}</div>
        <div class="act-time">${a.time}</div>
      </div>
    </div>
  `).join('');
}

// ── RENDER: HEALTH METRICS ────────────────────────────────────────────────────
function updateHealth() {
  const cpu  = Math.round(18 + Math.random() * 22);
  const mem  = Math.round(44 + Math.random() * 18);
  const resp = Math.round(80 + Math.random() * 60);

  document.getElementById('h-cpu').textContent  = cpu  + '%';
  document.getElementById('h-mem').textContent  = mem  + '%';
  document.getElementById('h-resp').textContent = resp + 'ms';

  document.getElementById('h-cpu-bar').style.width = cpu + '%';
  document.getElementById('h-mem-bar').style.width = mem + '%';

  // Colour CPU bar by load level
  const cpuBar = document.getElementById('h-cpu-bar');
  if (cpu > 75) {
    cpuBar.style.background = 'var(--red)';
  } else if (cpu > 50) {
    cpuBar.style.background = '#A0620E';
  } else {
    cpuBar.style.background = 'var(--accent2)';
  }
}

// ── SEARCH / FILTER ───────────────────────────────────────────────────────────
function filterUsers(val) {
  currentSearch = val;
  renderUsers(val);
}

// ── BLOCK / UNBLOCK USER ──────────────────────────────────────────────────────
async function toggleBlock(id) {

  const u = users.find(x => x.id === id);
  if (!u) return;

  const newStatus = u.status === "blocked" ? "active" : "blocked";

  try {

    const res = await fetch("/admin/users/status", {
      method: "PATCH",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: u.email,
        status: newStatus
      })
    });

    if (!res.ok) {
      throw new Error("Failed to update status");
    }

    u.status = newStatus;

    renderUsers(currentSearch);

    showToast(u.name + (newStatus === "blocked" ? " blocked" : " unblocked"));

  } catch (err) {

    console.error(err);

    showToast("Error updating user status");

  }

}

// ── DELETE MODAL ──────────────────────────────────────────────────────────────
function openDeleteModal(id) {
  const u = users.find(x => x.id === id);
  if (!u) return;

  pendingDeleteId = id;
  document.getElementById('modal-user-name').textContent = u.name + ' (' + u.email + ')';
  document.getElementById('delete-modal').classList.add('open');
}

function closeModal() {
  document.getElementById('delete-modal').classList.remove('open');
  pendingDeleteId = null;
}

async function confirmDelete() {
  const u = users.find(x => x.id === pendingDeleteId);
  if (!u) return;
  try {

    const res = await fetch(`/admin/users/${encodeURIComponent(u.email)}`, {
      method: "DELETE"
    });

    if (!res.ok) {
      throw new Error("Failed to delete user");
    }

    // Remove from local array
    users = users.filter(x => x.id !== pendingDeleteId);

    closeModal();

    renderUsers(currentSearch);

    showToast(u.name + " removed");

  } catch (err) {

    console.error(err);

    showToast("Error deleting user");

  }
  
}

// ── TOAST NOTIFICATION ────────────────────────────────────────────────────────
function showToast(msg) {
  const toast = document.getElementById('toast');
  document.getElementById('toast-msg').textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

// ── CLEAR ACTIVITY ────────────────────────────────────────────────────────────
function clearActivity() {
  activityData.length = 0;
  renderActivity();
  showToast('Activity log cleared');
}

// ── NAV TAB SWITCH ────────────────────────────────────────────────────────────
function switchTab(tab, el) {
  document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
  if (el) el.classList.add('active');

  const titles = {
    dashboard: 'Overview',
    users:     'User Management',
    activity:  'Activity Log',
    health:    'System Health',
    settings:  'Settings',
  };

  document.getElementById('page-title').textContent = titles[tab] || 'Admin';
}

// ── DATE DISPLAY ──────────────────────────────────────────────────────────────
function updateDate() {
  const d = new Date();
  document.getElementById('topbar-date').textContent = d.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

// ── CLOSE MODAL ON BACKDROP CLICK ─────────────────────────────────────────────
document.getElementById('delete-modal').addEventListener('click', function (e) {
  if (e.target === this) closeModal();
});

// ── KEYBOARD: ESC CLOSES MODAL ────────────────────────────────────────────────
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') closeModal();
});

// ── INITIALISE ────────────────────────────────────────────────────────────────
(function init() {
  updateDate();
  loadUsers();
  renderActivity();
  updateHealth();

  // Refresh health every 5 seconds
  setInterval(updateHealth, 5000);
})();

// document.addEventListener("DOMContentLoaded", () => {

//   loadTotalUsers();

// });

async function logoutAdmin() {
  try {
    const res = await fetch("/admin/logout", {
      method: "POST",
      credentials: "same-origin"
    });

    if (!res.ok) throw new Error("Logout failed");

    window.location.href = "/";

  } catch (err) {
    console.error(err);
    showToast("Logout failed");
  }
}