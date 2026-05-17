// ── ICONS ─────────────────────────────────────────────────────────────────
const icons = {
  users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  judge: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  org: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`,
  events: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>`,
  projects: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
  eval: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>`,
  team: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><circle cx="19" cy="7" r="2"/><path d="M23 21v-1.5a2 2 0 0 0-1.5-1.93"/></svg>`,
  profile: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
  rank: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`,
};

function navItem(page, icon, label) {
  const active = state.page === page ? 'active' : '';
  return `<div class="nav-item ${active}" data-page="${page}">${icon}<span>${label}</span></div>`;
}

function renderNav(role) {
  if (role === 'admin') return `
    <div class="nav-section">Overview</div>
    ${navItem('admin-users', icons.users, 'Users')}
    ${navItem('admin-judges', icons.judge, 'Judges')}
    ${navItem('admin-organizers', icons.org, 'Organizers')}
    ${navItem('admin-events', icons.events, 'Events')}
    <div class="nav-section">Create</div>
    ${navItem('admin-create-judge', icons.plus, 'Add Judge')}
    ${navItem('admin-create-organizer', icons.plus, 'Add Organizer')}`;

  if (role === 'organizer') return `
    <div class="nav-section">Events</div>
    ${navItem('my-events', icons.events, 'My Events')}
    ${navItem('create-event', icons.plus, 'Create Event')}`;

  if (role === 'judge') return `
    <div class="nav-section">Work</div>
    ${navItem('judge-assigned', icons.projects, 'All Projects')}
    ${navItem('judge-pending', icons.eval, 'Pending')}
    ${navItem('judge-evals', icons.eval, 'My Evaluations')}
    <div class="nav-section">Info</div>
    ${navItem('judge-events', icons.events, 'My Events')}
    ${navItem('judge-profile', icons.profile, 'Profile')}`;

  if (role === 'participant') return `
    <div class="nav-section">Events</div>
    ${navItem('participant-events', icons.events, 'Browse Events')}
    ${navItem('participant-my-events', icons.events, 'My Events')}
    <div class="nav-section">Team</div>
    ${navItem('participant-my-team', icons.team, 'My Team')}
    ${navItem('participant-create-team', icons.plus, 'Create Team')}
    ${navItem('participant-join-team', icons.team, 'Join Team')}
    ${navItem('participant-submit', icons.projects, 'Submit Project')}
    <div class="nav-section">Results</div>
    ${navItem('participant-results', icons.rank, 'My Results')}
    <div class="nav-section">Profile</div>
    ${navItem('participant-profile', icons.profile, 'Profile')}`;

  return '';
}

// ── RENDER ─────────────────────────────────────────────────────────────────
function render() {
  document.getElementById('app').innerHTML = !state.token ? renderAuth() : renderApp();
  bindEvents();
}

function renderApp() {
  const u = state.user;
  const initials = u.name.split(' ').map(w=>w[0]).slice(0,2).join('').toUpperCase();
  return `
  <div class="app">
    <div class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-text">&gt; hms</div>
        <div class="logo-role">${u.role}</div>
      </div>
      <nav class="sidebar-nav">
        ${renderNav(u.role)}
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">${initials}</div>
          <div>
            <div class="user-name">${u.name}</div>
            <div class="user-email">${u.role}</div>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm" id="logout-btn" style="width:100%; justify-content:center; margin-top:6px;">Logout</button>
      </div>
    </div>
    <main class="main">
      ${state.error ? `<div class="alert alert-error">${state.error}</div>` : ''}
      ${state.success ? `<div class="alert alert-success">${state.success}</div>` : ''}
      ${state.loading ? '<div class="loading">Loading</div>' : renderPage()}
    </main>
  </div>
  ${state.modal ? renderModal() : ''}`;
}

function renderPage() {
  switch(state.page) {
    // PUBLIC
    case 'public-events': return renderPublicEvents();
    case 'public-event-results': return renderPublicEventResults();
    // ADMIN
    case 'admin-users': return renderAdminUsers();
    case 'admin-user-detail': return renderAdminUserDetail();
    case 'admin-judges': return renderAdminJudges();
    case 'admin-organizers': return renderAdminOrganizers();
    case 'admin-events': return renderAdminEvents();
    case 'admin-create-judge': return renderCreateJudge();
    case 'admin-create-organizer': return renderCreateOrganizer();
    case 'admin-edit-judge': return renderEditJudge();
    case 'admin-edit-organizer': return renderEditOrganizer();
    // ORGANIZER
    case 'my-events': return renderMyEvents();
    case 'create-event': return renderCreateEvent();
    case 'update-event': return renderUpdateEvent();
    case 'event-detail': return renderEventDetail();
    case 'event-teams': return renderEventTeams();
    case 'event-registrations': return renderEventRegistrations();
    case 'event-projects': return renderEventProjects();
    case 'event-judges-list': return renderEventJudgesList();
    case 'assign-judge': return renderAssignJudge();
    // JUDGE
    case 'judge-assigned': return renderJudgeAssigned();
    case 'judge-pending': return renderJudgePending();
    case 'judge-evals': return renderJudgeEvals();
    case 'judge-events': return renderJudgeEvents();
    case 'judge-profile': return renderJudgeProfile();
    case 'judge-leaderboard': return renderJudgeLeaderboard();
    case 'judge-project-detail': return renderJudgeProjectDetail();
    // PARTICIPANT
    case 'participant-events': return renderParticipantEvents();
    case 'participant-my-events': return renderParticipantMyEvents();
    case 'participant-create-team': return renderCreateTeam();
    case 'participant-join-team': return renderJoinTeam();
    case 'participant-submit': return renderSubmitProject();
    case 'participant-my-team': return renderMyTeam();
    case 'participant-profile': return renderParticipantProfile();
    case 'participant-results': return renderParticipantResults();
    default: return `<div class="empty">Page not found</div>`;
  }
}