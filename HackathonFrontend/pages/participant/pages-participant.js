// ─────────────────────────── PARTICIPANT PAGES ────────────────────────────
function renderParticipantEvents() {
  const rows = state.data.events || [];
  return `
  <div class="page-header"><div class="page-title">Browse Events</div><div class="page-sub">${rows.length} hackathons</div></div>
  <div class="grid-2">
    ${rows.map(r=>`
      <div class="card">
        <div class="flex justify-between mb-4">
          <div style="font-weight:600;font-size:15px;">${r.event_name}</div>
          ${statusBadge(r.event_status)}
        </div>
        <div class="text-muted text-sm mb-4">${r.start_date?.slice(0,10)} → ${r.end_date?.slice(0,10)}</div>
        <div class="text-muted text-sm mb-4">Reg deadline: ${r.last_date_of_registration?.slice(0,10)} · Max ${r.max_team_size} per team</div>
        <div class="flex gap-2" style="margin-bottom:12px;">
          <div class="stat-card" style="padding:8px 12px;flex:1;"><div class="stat-label" style="font-size:10px">1st</div><div class="mono" style="font-size:13px">PKR ${r.first_prize}</div></div>
          <div class="stat-card" style="padding:8px 12px;flex:1;"><div class="stat-label" style="font-size:10px">2nd</div><div class="mono" style="font-size:13px">PKR ${r.second_prize}</div></div>
          <div class="stat-card" style="padding:8px 12px;flex:1;"><div class="stat-label" style="font-size:10px">3rd</div><div class="mono" style="font-size:13px">PKR ${r.third_prize}</div></div>
        </div>
        ${r.event_details ? `<div style="font-size:12px;color:var(--text3);margin-bottom:12px;">${r.event_details}</div>` : ''}
        <div class="flex gap-2">
          ${r.event_status==='upcoming' ? `<button class="btn btn-primary btn-sm" data-action="register-event" data-id="${r.event_id}">Register</button>` : ''}
          <button class="btn btn-ghost btn-sm" data-action="public-leaderboard" data-id="${r.event_id}" data-name="${r.event_name}">Leaderboard</button>
        </div>
      </div>`).join('') || '<div class="empty">No events available</div>'}
  </div>`;
}

function renderParticipantMyEvents() {
  const rows = state.data.events || [];
  return `
  <div class="page-header"><div class="page-title">My Events</div><div class="page-sub">${rows.length} registered</div></div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>Event</th><th>Start</th><th>End</th><th>Status</th><th>Registered</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td style="font-weight:500">${r.event_name}</td>
            <td class="text-muted">${r.start_date?.slice(0,10)}</td>
            <td class="text-muted">${r.end_date?.slice(0,10)}</td>
            <td>${statusBadge(r.event_status)}</td>
            <td class="text-muted">${r.registration_date?.slice(0,10)}</td>
          </tr>`).join('') || '<tr><td colspan="5" class="empty">Not registered in any events</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderCreateTeam() {
  return `
  <div class="page-header"><div class="page-title">Create Team</div></div>
  <div class="card" style="max-width:420px">
    <form id="create-team-form">
      <div class="field"><label>Event ID</label><input type="number" name="event_id" placeholder="Enter event ID" required></div>
      <div class="field"><label>Team Name</label><input name="team_name" placeholder="Team Alpha" required></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Create Team</button>
    </form>
  </div>`;
}

function renderJoinTeam() {
  return `
  <div class="page-header"><div class="page-title">Join Team</div></div>
  <div class="card" style="max-width:420px">
    <form id="join-team-form">
      <div class="field"><label>Event ID</label><input type="number" name="event_id" required></div>
      <div class="field"><label>Team Code</label><input name="team_code" placeholder="ABC123" required style="font-family:var(--mono);letter-spacing:0.1em;text-transform:uppercase"></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Join Team</button>
    </form>
  </div>`;
}

function renderSubmitProject() {
  return `
  <div class="page-header"><div class="page-title">Submit Project</div></div>
  <div class="card" style="max-width:520px">
    <form id="submit-project-form">
      <div class="field"><label>Team ID</label><input type="number" name="team_id" placeholder="Your team's ID" required></div>
      <div class="field"><label>Project Name</label><input name="project_name" placeholder="My Awesome Project" required></div>
      <div class="field"><label>GitHub Link</label><input name="github_link" placeholder="https://github.com/..." type="url"></div>
      <div class="field"><label>Description</label><textarea name="description" placeholder="Briefly describe your project..."></textarea></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Submit Project</button>
    </form>
  </div>`;
}

function renderMyTeam() {
  const team = state.data.team;
  const project = state.data.project;
  if (!team) return '<div class="empty">Not in any team</div>';
  if (team.message) return `<div class="alert alert-info">${team.message}</div>`;

  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">${team.team_name}</div></div>
    <button class="btn btn-ghost btn-sm" data-page="participant-events">← Back</button>
  </div>
  <div class="card" style="max-width:620px">
    <div class="flex gap-3 mb-4" style="align-items:center; flex-wrap:wrap;">
      <div class="text-muted text-sm">Team Code:</div>
      <code class="mono" style="background:var(--bg3);padding:4px 12px;border-radius:6px;font-size:16px;letter-spacing:0.12em;">${team.team_code}</code>
    </div>
    <div class="sep"></div>
    <div class="card-title">Members (${team.members?.length})</div>
    ${team.members?.map(m => `
      <div class="flex gap-3" style="padding:10px 0;border-bottom:0.5px solid var(--border);align-items:center;">
        <div class="user-avatar">${m.name.split(' ').map(w=>w[0]).slice(0,2).join('')}</div>
        <div><div style="font-weight:500">${m.name}</div><div class="text-muted text-sm">${m.email}</div></div>
      </div>`).join('')}
    ${project ? `
      <div class="sep"></div>
      <div class="card-title">Submitted Project</div>
      <div class="field"><label>Project Name</label><input value="${project.project_name}" readonly></div>
      ${project.github_link ? `<div class="field"><label>GitHub</label><a href="${project.github_link}" target="_blank" style="color:var(--info)">${project.github_link}</a></div>` : ''}
      ${project.description ? `<div class="field"><label>Description</label><div class="text-muted text-sm">${project.description}</div></div>` : ''}
      <div class="badge ${project.status === 'evaluated' ? 'badge-green' : 'badge-amber'}">${project.status}</div>
    ` : `<div class="alert alert-info" style="margin-top:12px;">No project submitted yet. Use "Submit Project" page.</div>`}
    <div class="sep"></div>
    <button class="btn btn-danger btn-sm" id="leave-team-btn" data-team-id="${team.team_id}">Leave Team</button>
  </div>`;
}

function renderParticipantProfile() {
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
    <div class="field-row">
      <div class="field"><label>CNIC</label><input value="${p.cnic}" readonly></div>
      <div class="field"><label>City</label><input value="${p.city||'—'}" readonly></div>
    </div>
    <div class="field-row">
      <div class="field"><label>Institution</label><input value="${p.institution||'—'}" readonly></div>
      <div class="field"><label>Date of Birth</label><input value="${p.date_of_birth||'—'}" readonly></div>
    </div>
    <div class="field"><label>Member Since</label><input value="${p.created_at?.slice(0,10)}" readonly></div>
    ${p.phone_numbers?.length ? `<div class="field"><label>Phone Numbers</label><div class="text-muted text-sm">${p.phone_numbers.join(', ')}</div></div>` : ''}
  </div>`;
}