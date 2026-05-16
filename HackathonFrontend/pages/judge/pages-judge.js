// ─────────────────────────── JUDGE PAGES ─────────────────────────────────
function renderJudgeAssigned() {
  const rows = state.data.projects || [];
  const pending = rows.filter(r=>!r.already_evaluated).length;
  return `
  <div class="page-header"><div class="page-title">All Projects</div><div class="page-sub">${rows.length} total — ${pending} pending</div></div>
  <div class="grid-2">
    ${rows.map(r=>`
      <div class="card" style="border-color:${r.already_evaluated?'var(--border)':'var(--accent-glow)'}">
        <div class="flex justify-between mb-4">
          <div style="font-weight:600">${r.project_name}</div>
          ${r.already_evaluated ? '<span class="badge badge-green">✓ Evaluated</span>' : '<span class="badge badge-amber">Pending</span>'}
        </div>
        <div class="text-muted text-sm mb-4">${r.team_name} · ${r.event_name}</div>
        ${r.already_evaluated ? `
          <div class="flex gap-2 mb-4">
            <div class="stat-card" style="flex:1;padding:10px 12px;">
              <div class="stat-label">Your Score</div>
              <div class="mono" style="font-size:20px;font-weight:600;color:var(--accent)">${r.my_score ?? '—'}</div>
            </div>
          </div>
          ${r.my_feedback ? `<div style="font-size:12px;color:var(--text3);margin-bottom:12px;">${r.my_feedback}</div>` : ''}
          <button class="btn btn-ghost btn-sm" data-action="update-feedback" data-id="${r.project_id}">Edit Feedback</button>
        ` : `
          <button class="btn btn-primary btn-sm" data-action="evaluate" data-id="${r.project_id}" data-name="${r.project_name}">Evaluate</button>
        `}
      </div>`).join('') || '<div class="empty">No projects assigned</div>'}
  </div>`;
}

function renderJudgePending() {
  const rows = state.data.projects || [];
  return `
  <div class="page-header"><div class="page-title">Pending Projects</div><div class="page-sub">${rows.length} awaiting evaluation</div></div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>Project</th><th>Team</th><th>Event</th><th>Submitted</th><th>Action</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td style="font-weight:500">${r.project_name}</td>
            <td class="text-muted">${r.team_name}</td>
            <td class="text-muted">${r.event_name}</td>
            <td class="text-muted">${r.submission_date?.slice(0,10)}</td>
            <td><button class="btn btn-primary btn-sm" data-action="evaluate" data-id="${r.project_id}" data-name="${r.project_name}">Evaluate</button></td>
          </tr>`).join('') || '<tr><td colspan="5" class="empty">All caught up!</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderJudgeEvals() {
  const rows = state.data.evals || [];
  return `
  <div class="page-header"><div class="page-title">My Evaluations</div><div class="page-sub">${rows.length} submitted</div></div>
  <div class="grid-2">
    ${rows.map(r=>`
      <div class="card">
        <div class="flex justify-between mb-4">
          <div style="font-weight:600">${r.project_name}</div>
          <div class="mono" style="font-size:20px;color:var(--accent)">${r.score}</div>
        </div>
        <div class="text-muted text-sm mb-4">${r.team_name} · ${r.event_name}</div>
        <div class="score-bar-wrap"><div class="score-bar" style="width:${r.score}%"></div></div>
        ${r.feedback ? `<div style="font-size:12px;color:var(--text3);margin-top:10px;">${r.feedback}</div>` : ''}
      </div>`).join('') || '<div class="empty">No evaluations submitted yet</div>'}
  </div>`;
}

function renderJudgeEvents() {
  const rows = state.data.events || [];
  return `
  <div class="page-header"><div class="page-title">My Events</div><div class="page-sub">${rows.length} events</div></div>
  <div class="grid-2">
    ${rows.map(r=>`
      <div class="card">
        <div class="flex justify-between mb-4">
          <div style="font-weight:600">${r.event_name}</div>
          ${statusBadge(r.event_status)}
        </div>
        <div class="text-muted text-sm mb-4">${r.start_date?.slice(0,10)} → ${r.end_date?.slice(0,10)}</div>
        <div class="grid-3" style="gap:8px;margin-bottom:12px;">
          <div class="stat-card" style="padding:10px 12px;"><div class="stat-label">Total</div><div class="mono" style="font-size:16px">${r.total_projects}</div></div>
          <div class="stat-card" style="padding:10px 12px;"><div class="stat-label">Done</div><div class="mono" style="font-size:16px;color:var(--accent)">${r.evaluated_by_me}</div></div>
          <div class="stat-card" style="padding:10px 12px;"><div class="stat-label">Pending</div><div class="mono" style="font-size:16px;color:var(--warn)">${r.pending}</div></div>
        </div>
        <button class="btn btn-ghost btn-sm" data-action="judge-leaderboard" data-id="${r.event_id}" data-name="${r.event_name}">Leaderboard</button>
      </div>`).join('') || '<div class="empty">Not assigned to any events</div>'}
  </div>`;
}

function renderJudgeProfile() {
  const p = state.data.profile;
  if (!p) return '<div class="empty">Profile not found</div>';
  return `
  <div class="page-header"><div class="page-title">My Profile</div></div>
  <div class="card" style="max-width:520px">
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;">
      <div class="user-avatar" style="width:48px;height:48px;font-size:16px;">${p.name.split(' ').map(w=>w[0]).slice(0,2).join('')}</div>
      <div>
        <div style="font-size:18px;font-weight:600">${p.name}</div>
        <div class="text-muted text-sm">${p.email}</div>
      </div>
    </div>
    <div class="sep"></div>
    <div class="grid-3" style="gap:10px;margin-bottom:16px;">
      <div class="stat-card" style="padding:12px;"><div class="stat-label">Commission</div><div class="mono" style="font-size:15px">PKR ${p.commission_per_eval}</div></div>
    </div>
    <div class="field"><label>CNIC</label><input value="${p.cnic}" readonly></div>
    <div class="field"><label>Member Since</label><input value="${p.created_at?.slice(0,10)}" readonly></div>
    ${p.degrees?.length ? `<div class="field"><label>Degrees</label><div class="flex gap-2" style="flex-wrap:wrap">${p.degrees.map(d=>`<span class="badge badge-blue">${d}</span>`).join('')}</div></div>` : ''}
    ${p.phone_numbers?.length ? `<div class="field"><label>Phone Numbers</label><div class="text-muted text-sm">${p.phone_numbers.join(', ')}</div></div>` : ''}
  </div>`;
}

function renderJudgeLeaderboard() {
  const rows = state.data.leaderboard || [];
  const ename = state.data.leaderboardEvent || '';
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Leaderboard</div><div class="page-sub">${ename}</div></div>
    <button class="btn btn-ghost btn-sm" data-page="judge-events">← Back</button>
  </div>
  <div class="card">
    ${rows.map(r=>`
      <div class="flex gap-3" style="padding:14px 0;border-bottom:0.5px solid var(--border);align-items:center;">
        <div class="rank-num ${r.rank===1?'gold':r.rank===2?'silver':r.rank===3?'bronze':''}">#${r.rank}</div>
        <div style="flex:1;">
          <div style="font-weight:600;margin-bottom:3px;">${r.team_name}</div>
          <div class="text-muted text-sm">${r.project_name} · ${r.total_evaluations} eval${r.total_evaluations!==1?'s':''}</div>
          <div class="score-bar-wrap" style="margin-top:8px;"><div class="score-bar" style="width:${r.average_score}%"></div></div>
        </div>
        <div class="mono" style="font-size:22px;font-weight:600;color:${r.rank===1?'var(--warn)':'var(--text)'}">${r.average_score}</div>
      </div>`).join('') || '<div class="empty">No results yet</div>'}
  </div>`;
}