// ── STATE ─────────────────────────────────────────────────────────────────
const API = 'http://127.0.0.1:8000';

let state = {
  token: localStorage.getItem('token') || null,
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  page: 'events',
  data: {},
  loading: false,
  error: null,
  success: null,
  modal: null,
};

function setState(patch) { Object.assign(state, patch); render(); }
function setPage(page, extra={}) { setState({ page, error: null, success: null, ...extra }); loadPage(page); }

// ── STATUS BADGE ──────────────────────────────────────────────────────────
// FIX #6: Added role entries (admin/judge/organizer/participant) to the badge map
function statusBadge(s) {
  const map = {
    // event statuses
    upcoming: 'badge-blue',
    ongoing: 'badge-green',
    completed: 'badge-gray',
    submitted: 'badge-amber',
    evaluated: 'badge-green',
    // role badges
    admin: 'badge-red',
    judge: 'badge-purple',
    organizer: 'badge-orange',
    participant: 'badge-teal',
  };
  return `<span class="badge ${map[s] || 'badge-gray'}">${s || '—'}</span>`;
}