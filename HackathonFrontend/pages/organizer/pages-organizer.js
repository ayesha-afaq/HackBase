// ─────────────────────────── ORGANIZER PAGES ─────────────────────────────
function renderMyEvents() {
  const rows = state.data.events || [];
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">My Events</div><div class="page-sub">${rows.length} events</div></div>
    <button class="btn btn-primary" data-page="create-event">+ Create Event</button>
  </div>
  <div class="grid-2">
    ${rows.map(r=>`
      <div class="card">
        <div class="flex justify-between mb-4">
          <div style="font-weight:600; font-size:15px;">${r.event_name}</div>
          ${statusBadge(r.event_status)}
        </div>
        <div class="text-muted text-sm mb-4">${r.start_date?.slice(0,10)} → ${r.end_date?.slice(0,10)}</div>
        <div class="text-muted text-sm mb-4">Reg deadline: ${r.last_date_of_registration?.slice(0,10)}</div>
        <div class="flex gap-2">
          <button class="btn btn-ghost btn-sm" data-action="event-detail" data-id="${r.event_id}">Manage</button>
          <button class="btn btn-ghost btn-sm" data-action="event-teams" data-id="${r.event_id}">Teams</button>
          <button class="btn btn-ghost btn-sm" data-action="event-projects" data-id="${r.event_id}">Projects</button>
        </div>
      </div>`).join('') || '<div class="empty">No events yet. Create one!</div>'}
  </div>`;
}

function renderCreateEvent() {
  return `
  <div class="page-header"><div class="page-title">Create Event</div></div>
  <div class="card" style="max-width:580px">
    <form id="create-event-form">
      <div class="field"><label>Event Name</label><input name="event_name" placeholder="HackFest 2025" required></div>
      <div class="field-row">
        <div class="field"><label>Start Date</label><input type="date" name="start_date" required></div>
        <div class="field"><label>End Date</label><input type="date" name="end_date" required></div>
      </div>
      <div class="field-row">
        <div class="field"><label>Registration Deadline</label><input type="date" name="last_date_of_registration" required></div>
        <div class="field"><label>Max Team Size</label><input type="number" name="max_team_size" min="1" max="10" required></div>
      </div>
      <div class="field"><label>Event Details</label><textarea name="event_details" placeholder="Describe the hackathon..." required></textarea></div>
      <div class="field-row">
        <div class="field"><label>Budget (PKR)</label><input type="number" name="budget" min="0" required placeholder="0"></div>
        <div class="field"><label>Funding (PKR)</label><input type="number" name="funding" min="0" required placeholder="0"></div>
      </div>
      <div class="field-row">
        <div class="field"><label>1st Prize (PKR)</label><input type="number" name="first_prize" min="0" required placeholder="0"></div>
        <div class="field"><label>2nd Prize (PKR)</label><input type="number" name="second_prize" min="0" required placeholder="0"></div>
      </div>
      <div class="field"><label>3rd Prize (PKR)</label><input type="number" name="third_prize" min="0" required placeholder="0"></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Create Event</button>
    </form>
  </div>`;
}

function renderEventDetail() {
  const ev = state.data.currentEvent;
  if (!ev) return '<div class="empty">No event selected</div>';
  return `
  <div class="page-header flex justify-between">
    <div>
      <div class="page-title">${ev.event_name}</div>
      <div class="page-sub">${statusBadge(ev.event_status)}</div>
    </div>
    <div class="flex gap-2">
      <button class="btn btn-ghost btn-sm" data-page="my-events">← Back to My Events</button>
      <button class="btn btn-ghost btn-sm" data-action="edit-event" data-id="${ev.event_id}">Edit</button>
      <button class="btn btn-ghost btn-sm" data-action="event-teams" data-id="${ev.event_id}">Teams</button>
      <button class="btn btn-ghost btn-sm" data-action="event-registrations" data-id="${ev.event_id}">Registrations</button>
      <button class="btn btn-ghost btn-sm" data-action="event-judges-list" data-id="${ev.event_id}">Judges</button>
      <button class="btn btn-ghost btn-sm" data-action="assign-judge" data-id="${ev.event_id}">+ Assign Judge</button>
    </div>
  </div>
  <div class="grid-4">
    <div class="stat-card"><div class="stat-label">Budget</div><div class="stat-value" style="font-size:18px;">PKR ${ev.budget}</div></div>
    <div class="stat-card"><div class="stat-label">1st Prize</div><div class="stat-value" style="font-size:18px;">PKR ${ev.first_prize}</div></div>
    <div class="stat-card"><div class="stat-label">2nd Prize</div><div class="stat-value" style="font-size:18px;">PKR ${ev.second_prize}</div></div>
    <div class="stat-card"><div class="stat-label">3rd Prize</div><div class="stat-value" style="font-size:18px;">PKR ${ev.third_prize}</div></div>
  </div>
  <div class="card mb-6">
    <div class="card-title">Update Status</div>
    <div class="flex gap-2">
      ${['upcoming','ongoing','completed'].map(s=>`
        <button class="btn ${ev.event_status===s?'btn-primary':'btn-ghost'}" data-action="update-status" data-id="${ev.event_id}" data-status="${s}">${s}</button>
      `).join('')}
    </div>
  </div>
  ${ev.event_details ? `<div class="card"><div class="card-title">Details</div><p style="color:var(--text2); font-size:13px; line-height:1.7">${ev.event_details}</p></div>` : ''}`;
}

function renderEventTeams() {
  const rows = state.data.teams || [];
  const expandedTeamId = state.data.expandedTeamId || null;
  const teamMembers = state.data.teamMembers || {};

  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Teams</div><div class="page-sub">${rows.length} teams registered</div></div>
    <button class="btn btn-ghost btn-sm" data-page="my-events">← Back</button>
  </div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>Team</th><th>Code</th><th>Lead</th><th>Registered</th><th>Actions</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td style="font-weight:500">${r.team_name}</td>
            <td><code class="mono" style="background:var(--bg3);padding:2px 8px;border-radius:4px;font-size:12px;">${r.team_code}</code></td>
            <td class="text-muted">${r.team_lead}</td>
            <td class="text-muted">${r.registration_date?.slice(0,10)}</td>
            <td class="flex gap-2">
              <button class="btn btn-ghost btn-sm" data-action="view-team-members" data-id="${r.team_id}">
                ${expandedTeamId === r.team_id ? 'Hide Members' : 'View Members'}
              </button>
              <button class="btn btn-danger btn-sm" data-action="delete-team" data-id="${r.team_id}">Delete</button>
            </td>
          </tr>
          ${expandedTeamId === r.team_id ? `
          <tr>
            <td colspan="5" style="padding:0;background:var(--bg3);">
              <div style="padding:14px 16px;">
                <div style="font-size:12px;font-weight:600;color:var(--text2);margin-bottom:10px;text-transform:uppercase;letter-spacing:0.07em;">Members</div>
                ${teamMembers[r.team_id] ? `
                  <div style="display:flex;flex-wrap:wrap;gap:10px;">
                    ${teamMembers[r.team_id].map(m=>`
                      <div style="display:flex;align-items:center;gap:8px;background:var(--bg2);border:0.5px solid var(--border);border-radius:8px;padding:8px 12px;">
                        <div class="user-avatar" style="width:26px;height:26px;font-size:10px;">${m.name.split(' ').map(w=>w[0]).slice(0,2).join('')}</div>
                        <div>
                          <div style="font-size:13px;font-weight:500;">${m.name}</div>
                          <div style="font-size:11px;color:var(--text3);">${m.email}</div>
                        </div>
                      </div>`).join('')}
                  </div>
                ` : '<div class="text-muted text-sm">Loading...</div>'}
              </div>
            </td>
          </tr>` : ''}
        `).join('') || '<tr><td colspan="5" class="empty">No teams yet</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderEventRegistrations() {
  const rows = state.data.registrations || [];
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Registrations</div><div class="page-sub">${rows.length} participants</div></div>
    <button class="btn btn-ghost btn-sm" data-page="my-events">← Back</button>
  </div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>Name</th><th>Email</th><th>Registered On</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td style="font-weight:500">${r.name}</td>
            <td class="text-muted">${r.email}</td>
            <td class="text-muted">${r.registration_date?.slice(0,10)}</td>
          </tr>`).join('') || '<tr><td colspan="3" class="empty">No registrations</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderEventProjects() {
  const rows = state.data.projects || [];
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Submitted Projects</div><div class="page-sub">${rows.length} submissions</div></div>
    <button class="btn btn-ghost btn-sm" data-page="my-events">← Back</button>
  </div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>Project</th><th>Team</th><th>Status</th><th>GitHub</th><th>Submitted</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td style="font-weight:500">${r.project_name}</td>
            <td class="text-muted">${r.team_name}</td>
            <td>${statusBadge(r.status)}</td>
            <td>${r.github_link?`<a href="${r.github_link}" target="_blank" style="color:var(--info)">View</a>`:'—'}</td>
            <td class="text-muted">${r.submission_date?.slice(0,10)}</td>
          </tr>`).join('') || '<tr><td colspan="5" class="empty">No projects yet</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderEventJudgesList() {
  const rows = state.data.eventJudges || [];
  const eid = state.data.currentEventId;
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Assigned Judges</div><div class="page-sub">${rows.length} judges</div></div>
    <div class="flex gap-2">
      <button class="btn btn-primary btn-sm" data-action="assign-judge" data-id="${eid}">+ Assign Judge</button>
      <button class="btn btn-ghost btn-sm" data-page="my-events">← Back</button>
    </div>
  </div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Assigned Date</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.judge_id}</td>
            <td style="font-weight:500">${r.name}</td>
            <td class="text-muted">${r.email}</td>
            <td class="text-muted">${r.assigned_date?.slice(0,10)}</td>
          </tr>`).join('') || '<tr><td colspan="4" class="empty">No judges assigned</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderAssignJudge() {
  const eid = state.data.currentEventId;
  return `
  <div class="page-header"><div class="page-title">Assign Judge</div></div>
  <div class="card" style="max-width:400px">
    <form id="assign-judge-form">
      <input type="hidden" name="event_id" value="${eid}">
      <div class="field"><label>Judge ID</label><input type="number" name="judge_id" placeholder="Enter judge ID" required></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Assign</button>
    </form>
  </div>`;
}

function renderUpdateEvent() {
  const ev = state.data.currentEvent;
  if (!ev) return '<div class="empty">No event selected. <button class="btn btn-ghost btn-sm" data-page="my-events">Go to My Events</button></div>';
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Edit Event</div><div class="page-sub">${ev.event_name}</div></div>
    <button class="btn btn-ghost btn-sm" data-action="event-detail" data-id="${ev.event_id}">← Back to Detail</button>
  </div>
  <div class="card" style="max-width:580px">
    <form id="update-event-form">
      <input type="hidden" name="event_id" value="${ev.event_id}">
      <div class="field">
        <label>Event Name</label>
        <input name="event_name" value="${ev.event_name}" required>
      </div>
      <div class="field-row">
        <div class="field">
          <label>Registration Deadline</label>
          <input type="date" name="last_date_of_registration" value="${ev.last_date_of_registration?.slice(0,10)}">
        </div>
        <div class="field">
          <label>Max Team Size</label>
          <input type="number" name="max_team_size" min="1" max="10" value="${ev.max_team_size}">
        </div>
      </div>
      <div class="field">
        <label>Event Details</label>
        <textarea name="event_details">${ev.event_details || ''}</textarea>
      </div>
      <div class="field-row">
        <div class="field"><label>Budget (PKR)</label><input type="number" name="budget" min="0" value="${ev.budget}"></div>
        <div class="field"><label>Funding (PKR)</label><input type="number" name="funding" min="0" value="${ev.funding}"></div>
      </div>
      <div class="field-row">
        <div class="field"><label>1st Prize</label><input type="number" name="first_prize" min="0" value="${ev.first_prize}"></div>
        <div class="field"><label>2nd Prize</label><input type="number" name="second_prize" min="0" value="${ev.second_prize}"></div>
      </div>
      <div class="field">
        <label>3rd Prize</label>
        <input type="number" name="third_prize" min="0" value="${ev.third_prize}">
      </div>
      <div class="alert alert-info" style="font-size:12px; margin-bottom:12px;">
        Start date and end date cannot be changed after creation.
      </div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Save Changes</button>
    </form>
  </div>`;
}
