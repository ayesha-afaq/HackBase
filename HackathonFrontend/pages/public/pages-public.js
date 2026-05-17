// ─────────────────────────── PUBLIC PAGES ────────────────────────────────

// Derive the correct back-page based on the current user's role so the
// back button always lands somewhere real regardless of who is viewing.
function publicBackPage() {
  if (!state.user) return 'public-events';
  const map = {
    participant: 'participant-events',
    judge      : 'judge-events',
    organizer  : 'my-events',
    admin      : 'admin-events',
  };
  return map[state.user.role] || 'public-events';
}

function renderPublicEvents() {
  const rows = state.data.events || [];
  return `
  <div class="page-header"><div class="page-title">Events</div><div class="page-sub">${rows.length} hackathons</div></div>
  <div class="grid-2">${rows.map(r=>`
    <div class="card">
      <div class="flex justify-between mb-4">
        <div style="font-weight:600">${r.event_name}</div>
        ${statusBadge(r.status)}
      </div>
      <div class="text-muted text-sm mb-4">${r.start_date?.slice(0,10)} → ${r.end_date?.slice(0,10)}</div>
      ${r.details ? `<div style="font-size:12px;color:var(--text3);margin-bottom:12px;">${r.details}</div>` : ''}
      <button class="btn btn-ghost btn-sm" data-action="public-leaderboard" data-id="${r.event_id}" data-name="${r.event_name}">Leaderboard</button>
    </div>`).join('') || '<div class="empty">No events</div>'}
  </div>`;
}

function renderPublicEventResults() {
  const rows = state.data.leaderboard || [];
  const eventName = state.data.leaderboardEvent || '';
  const notReady = state.data.leaderboardReady === false;
  const message = state.data.leaderboardMessage;
  const backPage = publicBackPage();
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Results: ${eventName}</div></div>
    <button class="btn btn-ghost btn-sm" data-page="${backPage}">← Back to Events</button>
  </div>
  <div class="card">
    ${notReady && message
      ? `<div class="alert alert-info">${message}</div>`
      : ''}
    ${rows.map(r => `
      <div class="flex gap-3" style="padding:14px 0;border-bottom:0.5px solid var(--border);align-items:center;">
        <div class="rank-num ${r.rank===1?'gold':r.rank===2?'silver':r.rank===3?'bronze':''}">#${r.rank}</div>
        <div style="flex:1;">
          <div style="font-weight:600;margin-bottom:3px;">${r.team_name}</div>
          <div class="text-muted text-sm">Average score: ${r.average_score} · ${r.evaluations} eval${r.evaluations!==1?'s':''}</div>
          <div class="score-bar-wrap" style="margin-top:8px;"><div class="score-bar" style="width:${r.average_score}%"></div></div>
        </div>
        <div class="mono" style="font-size:22px;font-weight:600;color:${r.rank===1?'var(--warn)':'var(--text)'}">${r.average_score}</div>
      </div>`).join('') || (!notReady ? '<div class="empty">No results available yet</div>' : '')}
  </div>`;
}
