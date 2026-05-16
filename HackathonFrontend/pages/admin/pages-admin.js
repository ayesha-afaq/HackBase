// ─────────────────────────── ADMIN PAGES ─────────────────────────────────
function renderAdminUsers() {
  const rows = state.data.users || [];
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Users</div><div class="page-sub">${rows.length} total users</div></div>
  </div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Role</th><th>Joined</th><th>Action</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.user_id}</td>
            <td>${r.name}</td>
            <td class="text-muted">${r.email}</td>
            <td>${statusBadge(r.role)}</td>
            <td class="text-muted">${r.created_at?.slice(0,10)}</td>
            <td><button class="btn btn-danger btn-sm" data-action="delete-user" data-id="${r.user_id}">Delete</button></td>
          </tr>`).join('') || '<tr><td colspan="6" class="empty">No users found</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderAdminJudges() {
  const rows = state.data.judges || [];
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Judges</div><div class="page-sub">${rows.length} judges</div></div>
    <button class="btn btn-primary" data-page="admin-create-judge">+ Add Judge</button>
  </div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Commission / Eval</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.judge_id}</td>
            <td>${r.name}</td>
            <td class="text-muted">${r.email}</td>
            <td class="mono">PKR ${r.commission_per_eval}</td>
          </tr>`).join('') || '<tr><td colspan="4" class="empty">No judges found</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderAdminOrganizers() {
  const rows = state.data.organizers || [];
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Organizers</div><div class="page-sub">${rows.length} organizers</div></div>
    <button class="btn btn-primary" data-page="admin-create-organizer">+ Add Organizer</button>
  </div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Salary</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.organizer_id}</td>
            <td>${r.name}</td>
            <td class="text-muted">${r.email}</td>
            <td class="mono">${r.salary ? 'PKR '+r.salary : '—'}</td>
          </tr>`).join('') || '<tr><td colspan="4" class="empty">No organizers</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderAdminEvents() {
  const rows = state.data.events || [];
  return `
  <div class="page-header"><div class="page-title">All Events</div><div class="page-sub">${rows.length} events</div></div>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Start</th><th>End</th><th>Status</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.event_id}</td>
            <td>${r.event_name}</td>
            <td class="text-muted">${r.start_date?.slice(0,10)}</td>
            <td class="text-muted">${r.end_date?.slice(0,10)}</td>
            <td>${statusBadge(r.event_status)}</td>
          </tr>`).join('') || '<tr><td colspan="5" class="empty">No events</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderCreateJudge() {
  return `
  <div class="page-header"><div class="page-title">Add Judge</div></div>
  <div class="card" style="max-width:520px">
    <form id="create-judge-form">
      <div class="field-row">
        <div class="field"><label>First Name</label><input name="firstname" required></div>
        <div class="field"><label>Last Name</label><input name="lastname" required></div>
      </div>
      <div class="field"><label>CNIC</label><input name="cnic" placeholder="12345-1234567-1" required></div>
      <div class="field"><label>Email</label><input type="email" name="email" required></div>
      <div class="field"><label>Password</label><input type="password" name="password" required></div>
      <div class="field"><label>Commission per Evaluation (PKR)</label><input type="number" name="commission_per_eval" min="0" step="0.01" required></div>
      <div class="field"><label>Phone Numbers (comma-separated)</label><input name="phones" placeholder="03001234567, 03211234567"></div>
      <div class="field"><label>Degrees (comma-separated)</label><input name="degrees" placeholder="PhD CS, MSc AI"></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Create Judge</button>
    </form>
  </div>`;
}

function renderCreateOrganizer() {
  return `
  <div class="page-header"><div class="page-title">Add Organizer</div></div>
  <div class="card" style="max-width:520px">
    <form id="create-organizer-form">
      <div class="field-row">
        <div class="field"><label>First Name</label><input name="firstname" required></div>
        <div class="field"><label>Last Name</label><input name="lastname" required></div>
      </div>
      <div class="field"><label>CNIC</label><input name="cnic" placeholder="12345-1234567-1" required></div>
      <div class="field"><label>Email</label><input type="email" name="email" required></div>
      <div class="field"><label>Password</label><input type="password" name="password" required></div>
      <div class="field"><label>Salary (optional, PKR)</label><input type="number" name="salary" min="0" step="0.01"></div>
      <div class="field"><label>Phone Numbers (comma-separated)</label><input name="phones" placeholder="03001234567"></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Create Organizer</button>
    </form>
  </div>`;
}