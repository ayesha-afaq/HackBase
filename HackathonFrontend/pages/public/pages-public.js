// ─────────────────────────── PUBLIC PAGES ────────────────────────────────

// FIX #5: The back button in renderPublicEventResults previously hardcoded
// `data-page="public-events"`. That page only exists in the unauthenticated
// (no sidebar) shell. Authenticated users have no "public-events" nav item,
// so the back button dead-ended for every logged-in role.
//
// Fix: derive the correct "events" page from the current user's role so the
// back button always lands somewhere real:
//   - No user (public)  → public-events
//   - participant        → participant-events  (Browse Events in sidebar)
//   - judge             → judge-events         (My Events in sidebar)
//   - organizer/admin   → my-events / admin-events
function publicBackPage() {
  if (!state.user) return 'public-events';
  const map = {
    participant: 'participant-events',
    judge: 'judge-events',
    organizer: 'my-events',
    admin: 'admin-events',
  };
  return map[state.user.role] || 'public-events';
}

function renderPublicEvents() {
  const rows = state.data.events || [];
  return `
  <div class="page-header"><div class="page-title">Events</div></div>
  <div class="grid-2">${rows.map(r=>`
    <div class="card">
      <div class="flex justify-between mb-4">
        <div style="font-weight:600">${r.event_name}</div>
        ${statusBadge(r.status||r.event_status)}
      </div>
      <div class="text-muted text-sm mb-4">${r.start_date?.slice(0,10)} → ${r.end_date?.slice(0,10)}</div>
      <button class="btn btn-ghost btn-sm" data-action="public-leaderboard" data-id="${r.event_id}" data-name="${r.event_name}">Leaderboard</button>
    </div>`).join('') || '<div class="empty">No events</div>'}
  </div>`;
}

function renderPublicEventResults() {
  const rows = state.data.leaderboard || [];
  const eventName = state.data.leaderboardEvent || '';
  const backPage = publicBackPage();
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Results: ${eventName}</div></div>
    <button class="btn btn-ghost btn-sm" data-page="${backPage}">← Back to Events</button>
  </div>
  <div class="card">
    ${rows.map(r => `
      <div class="flex gap-3" style="padding:14px 0;border-bottom:0.5px solid var(--border);align-items:center;">
        <div class="rank-num ${r.rank===1?'gold':r.rank===2?'silver':r.rank===3?'bronze':''}">#${r.rank}</div>
        <div style="flex:1;">
          <div style="font-weight:600;margin-bottom:3px;">${r.team_name}</div>
          <div class="text-muted text-sm">Average score: ${r.average_score} (${r.evaluations} evals)</div>
          <div class="score-bar-wrap" style="margin-top:8px;"><div class="score-bar" style="width:${r.average_score}%"></div></div>
        </div>
        <div class="mono" style="font-size:22px;font-weight:600;color:${r.rank===1?'var(--warn)':'var(--text)'}">${r.average_score}</div>
      </div>`).join('') || '<div class="empty">No results available yet</div>'}
  </div>`;
}