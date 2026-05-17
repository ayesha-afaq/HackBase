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
        <div class="text-muted text-sm mb-2">${r.start_date?.slice(0,10)} → ${r.end_date?.slice(0,10)}</div>
        <div class="text-muted text-sm mb-4">Reg deadline: ${r.last_date_of_registration?.slice(0,10)}</div>
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
  // Use registered events as a dropdown if available
  const myEvents = state.data.events || [];
  const eventOptions = myEvents.length
    ? myEvents.map(e=>`<option value="${e.event_id}">${e.event_name} (${e.event_status})</option>`).join('')
    : '<option value="">No registered events found</option>';
  return `
  <div class="page-header"><div class="page-title">Create Team</div></div>
  <div class="card" style="max-width:420px">
    <form id="create-team-form">
      <div class="field">
        <label>Event</label>
        ${myEvents.length
          ? `<select name="event_id" required>${eventOptions}</select>`
          : `<input type="number" name="event_id" placeholder="Enter event ID" required>`}
      </div>
      <div class="field"><label>Team Name</label><input name="team_name" placeholder="Team Alpha" required></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Create Team</button>
    </form>
  </div>`;
}

function renderJoinTeam() {
  const myEvents = state.data.events || [];
  const eventOptions = myEvents.length
    ? myEvents.map(e=>`<option value="${e.event_id}">${e.event_name} (${e.event_status})</option>`).join('')
    : '<option value="">No registered events found</option>';
  return `
  <div class="page-header"><div class="page-title">Join Team</div></div>
  <div class="card" style="max-width:420px">
    <form id="join-team-form">
      <div class="field">
        <label>Event</label>
        ${myEvents.length
          ? `<select name="event_id" required>${eventOptions}</select>`
          : `<input type="number" name="event_id" required>`}
      </div>
      <div class="field">
        <label>Team Code</label>
        <input name="team_code" placeholder="ABC123" required style="font-family:var(--mono);letter-spacing:0.1em;text-transform:uppercase">
      </div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Join Team</button>
    </form>
  </div>`;
}

function renderSubmitProject() {
  // Pre-fill team_id if we already have team data loaded
  const team = state.data.team;
  const teamId = team?.team_id || '';
  const teamName = team?.team_name || '';
  return `
  <div class="page-header"><div class="page-title">Submit Project</div></div>
  <div class="card" style="max-width:520px">
    ${teamId
      ? `<div class="alert alert-info" style="margin-bottom:12px;">Submitting for team: <strong>${teamName}</strong></div>`
      : `<div class="alert alert-info" style="margin-bottom:12px;">Go to <strong>My Team</strong> first to load your team, or enter your team ID manually.</div>`}
    <form id="submit-project-form">
      <div class="field">
        <label>Team ID</label>
        <input type="number" name="team_id" value="${teamId}" ${teamId?'readonly':''} placeholder="Your team's ID" required>
      </div>
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
  const myEvents = state.data.myEvents || [];
  const selectedEventId = state.data.selectedTeamEventId;

  if (!team) return '<div class="empty">Loading...</div>';
  if (team.message) return `<div class="alert alert-info">${team.message}</div>`;

  // Event switcher — only shown when registered in multiple events
  const eventSwitcher = myEvents.length > 1 ? `
    <div class="card" style="margin-bottom:16px;">
      <div class="card-title">Select Event</div>
      <div class="flex gap-2" style="flex-wrap:wrap;">
        ${myEvents.map(e=>`
          <button class="btn ${e.event_id===selectedEventId?'btn-primary':'btn-ghost'} btn-sm"
            data-action="switch-team-event" data-id="${e.event_id}">
            ${e.event_name}
          </button>`).join('')}
      </div>
    </div>` : '';

  return `
  ${eventSwitcher}
  <div class="page-header flex justify-between">
    <div><div class="page-title">${team.team_name}</div></div>
    <button class="btn btn-ghost btn-sm" data-page="participant-events">← Back</button>
  </div>
  <div class="card" style="max-width:620px">
    <div class="flex gap-3 mb-4" style="align-items:center; flex-wrap:wrap;">
      <div class="text-muted text-sm">Team Code:</div>
      <code class="mono" style="background:var(--bg3);padding:4px 12px;border-radius:6px;font-size:16px;letter-spacing:0.12em;">${team.team_code}</code>
      <div class="text-muted text-sm" style="margin-left:auto;">Share this code with teammates</div>
    </div>
    <div class="sep"></div>
    <div class="card-title">Members (${team.members?.length || 0})</div>
    ${team.members?.map(m => `
      <div class="flex gap-3" style="padding:10px 0;border-bottom:0.5px solid var(--border);align-items:center;">
        <div class="user-avatar">${m.name.split(' ').map(w=>w[0]).slice(0,2).join('')}</div>
        <div><div style="font-weight:500">${m.name}</div><div class="text-muted text-sm">${m.email}</div></div>
      </div>`).join('') || '<div class="text-muted text-sm">No members</div>'}
    ${project ? `
      <div class="sep"></div>
      <div class="card-title">Submitted Project</div>
      <div class="field"><label>Project Name</label><input value="${project.project_name}" readonly></div>
      ${project.github_link ? `<div class="field"><label>GitHub</label><a href="${project.github_link}" target="_blank" style="color:var(--info)">${project.github_link}</a></div>` : ''}
      ${project.description ? `<div class="field"><label>Description</label><div class="text-muted text-sm">${project.description}</div></div>` : ''}
      <div class="field"><label>Status</label>${statusBadge(project.status)}</div>
      <div class="field"><label>Submitted</label><div class="text-muted text-sm">${project.submission_date?.slice(0,10)}</div></div>
    ` : `
      <div class="sep"></div>
      <div class="alert alert-info" style="margin-top:12px;">No project submitted yet.</div>
      <button class="btn btn-primary btn-sm" style="margin-top:10px;" data-page="participant-submit">Submit Project</button>
    `}
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
    <div class="sep"></div>
    <div class="card-title">Edit Profile</div>
    <form id="update-profile-form">
      <div class="field-row">
        <div class="field"><label>First Name</label><input name="firstname" placeholder="Leave blank to keep"></div>
        <div class="field"><label>Last Name</label><input name="lastname" placeholder="Leave blank to keep"></div>
      </div>
      <div class="field"><label>Middle Name</label><input name="middlename" placeholder="Leave blank to keep"></div>
      <div class="field"><label>Email</label><input type="email" name="email" placeholder="Leave blank to keep"></div>
      <div class="field"><label>New Password</label><input type="password" name="password" placeholder="Leave blank to keep"></div>
      <div class="field-row">
        <div class="field"><label>Date of Birth</label><input type="date" name="date_of_birth"></div>
        <div class="field"><label>City</label><input name="city" placeholder="Leave blank to keep"></div>
      </div>
      <div class="field"><label>Institution</label><input name="institution" placeholder="Leave blank to keep"></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Save Changes</button>
    </form>
  </div>`;
}

function renderParticipantResults() {
  const results = state.data.results || [];
  if (results.length === 0) {
    return `
    <div class="page-header"><div class="page-title">My Results</div></div>
    <div class="empty">No results yet. Register for an event to get started.</div>`;
  }
  return `
  <div class="page-header"><div class="page-title">My Results</div><div class="page-sub">${results.length} event${results.length!==1?'s':''}</div></div>
  ${results.map(ev=>`
    <div class="card" style="margin-bottom:16px;">
      <div class="flex justify-between mb-4">
        <div>
          <div style="font-weight:600;font-size:15px;">${ev.event_name}</div>
          <div class="text-muted text-sm">${statusBadge(ev.event_status)}</div>
        </div>
        ${ev.results_ready
          ? '<span class="badge badge-green">Results Ready</span>'
          : '<span class="badge badge-amber">Evaluation in Progress</span>'}
      </div>
      ${!ev.results_ready
        ? `<div class="alert alert-info">${ev.message}</div>`
        : ev.leaderboard.length === 0
          ? '<div class="text-muted text-sm">No submissions evaluated yet.</div>'
          : ev.leaderboard.map(r=>`
            <div class="flex gap-3" style="padding:12px 0;border-bottom:0.5px solid var(--border);align-items:center;">
              <div class="rank-num ${r.rank===1?'gold':r.rank===2?'silver':r.rank===3?'bronze':''}">#${r.rank}</div>
              <div style="flex:1;">
                <div style="font-weight:600;margin-bottom:2px;">${r.team_name}</div>
                <div class="text-muted text-sm">${r.project_name}</div>
                <div class="score-bar-wrap" style="margin-top:6px;"><div class="score-bar" style="width:${r.average_score}%"></div></div>
              </div>
              <div class="mono" style="font-size:20px;font-weight:600;color:${r.rank===1?'var(--warn)':'var(--text)'}">${r.average_score}</div>
            </div>`).join('')}
    </div>`).join('')}`;
}
