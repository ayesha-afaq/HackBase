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
        <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Role</th><th>Actions</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.user_id}</td>
            <td>${r.firstname} ${r.lastname}</td>
            <td class="text-muted">${r.email}</td>
            <td>${statusBadge(r.role)}</td>
            <td class="flex gap-2">
              <button class="btn btn-ghost btn-sm" data-action="view-user" data-id="${r.user_id}">View</button>
              <button class="btn btn-danger btn-sm" data-action="delete-user" data-id="${r.user_id}">Delete</button>
            </td>
          </tr>`).join('') || '<tr><td colspan="5" class="empty">No users found</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>`;
}

function renderAdminUserDetail() {
  const u = state.data.userDetail;
  if (!u) return '<div class="empty">No user selected</div>';
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">${u.firstname} ${u.lastname}</div><div class="page-sub">${statusBadge(u.role)}</div></div>
    <button class="btn btn-ghost btn-sm" data-page="admin-users">← Back</button>
  </div>
  <div class="card" style="max-width:560px">
    <div class="field-row">
      <div class="field"><label>First Name</label><input value="${u.firstname}" readonly></div>
      <div class="field"><label>Last Name</label><input value="${u.lastname}" readonly></div>
    </div>
    ${u.middlename ? `<div class="field"><label>Middle Name</label><input value="${u.middlename}" readonly></div>` : ''}
    <div class="field"><label>Email</label><input value="${u.email}" readonly></div>
    <div class="field"><label>CNIC</label><input value="${u.cnic}" readonly></div>
    <div class="field"><label>Member Since</label><input value="${u.created_at?.slice(0,10)}" readonly></div>
    ${u.phone_numbers?.length ? `<div class="field"><label>Phone Numbers</label><div class="text-muted text-sm">${u.phone_numbers.join(', ')}</div></div>` : ''}
    ${u.role === 'judge' ? `
      <div class="sep"></div>
      <div class="card-title">Judge Details</div>
      <div class="field"><label>Commission / Eval</label><input value="PKR ${u.commission_per_eval}" readonly></div>
      ${u.degrees?.length ? `<div class="field"><label>Degrees</label><div class="flex gap-2" style="flex-wrap:wrap">${u.degrees.map(d=>`<span class="badge badge-blue">${d}</span>`).join('')}</div></div>` : ''}
      <button class="btn btn-ghost btn-sm mt-2" data-action="edit-judge" data-id="${u.judge_id}">Edit Judge</button>
    ` : ''}
    ${u.role === 'organizer' ? `
      <div class="sep"></div>
      <div class="card-title">Organizer Details</div>
      <div class="field"><label>Salary</label><input value="${u.salary ? 'PKR '+u.salary : '—'}" readonly></div>
      <button class="btn btn-ghost btn-sm mt-2" data-action="edit-organizer" data-id="${u.organizer_id}">Edit Organizer</button>
    ` : ''}
    ${u.role === 'participant' ? `
      <div class="sep"></div>
      <div class="card-title">Participant Details</div>
      <div class="field-row">
        <div class="field"><label>Date of Birth</label><input value="${u.date_of_birth||'—'}" readonly></div>
        <div class="field"><label>City</label><input value="${u.city||'—'}" readonly></div>
      </div>
      <div class="field"><label>Institution</label><input value="${u.institution||'—'}" readonly></div>
    ` : ''}
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
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Commission / Eval</th><th>Degrees</th><th>Action</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.judge_id}</td>
            <td>${r.name}</td>
            <td class="text-muted">${r.email}</td>
            <td class="mono">PKR ${r.commission_per_eval}</td>
            <td>${r.degrees?.length ? r.degrees.map(d=>`<span class="badge badge-blue" style="margin-right:3px">${d}</span>`).join('') : '—'}</td>
            <td><button class="btn btn-ghost btn-sm" data-action="edit-judge" data-id="${r.judge_id}">Edit</button></td>
          </tr>`).join('') || '<tr><td colspan="6" class="empty">No judges found</td></tr>'}
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
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Salary</th><th>Action</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.organizer_id}</td>
            <td>${r.name}</td>
            <td class="text-muted">${r.email}</td>
            <td class="mono">${r.salary ? 'PKR '+r.salary : '—'}</td>
            <td><button class="btn btn-ghost btn-sm" data-action="edit-organizer" data-id="${r.organizer_id}">Edit</button></td>
          </tr>`).join('') || '<tr><td colspan="5" class="empty">No organizers</td></tr>'}
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
        <thead><tr><th>ID</th><th>Name</th><th>Organizer</th><th>Start</th><th>End</th><th>Status</th></tr></thead>
        <tbody>${rows.map(r=>`
          <tr>
            <td class="mono text-muted">${r.event_id}</td>
            <td>${r.event_name}</td>
            <td class="mono text-muted">${r.organizer_id}</td>
            <td class="text-muted">${r.start_date?.slice(0,10)}</td>
            <td class="text-muted">${r.end_date?.slice(0,10)}</td>
            <td>${statusBadge(r.event_status)}</td>
          </tr>`).join('') || '<tr><td colspan="6" class="empty">No events</td></tr>'}
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
      <div class="field"><label>Phone Numbers <span class="text-muted">(comma-separated)</span></label><input name="phones" placeholder="03001234567, 03211234567"></div>
      <div class="field"><label>Degrees <span class="text-muted">(comma-separated)</span></label><input name="degrees" placeholder="PhD CS, MSc AI"></div>
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
      <div class="field"><label>Salary <span class="text-muted">(optional, PKR)</span></label><input type="number" name="salary" min="0" step="0.01"></div>
      <div class="field"><label>Phone Numbers <span class="text-muted">(comma-separated)</span></label><input name="phones" placeholder="03001234567"></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Create Organizer</button>
    </form>
  </div>`;
}

function renderEditJudge() {
  const jid = state.data.editJudgeId;
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Edit Judge</div><div class="page-sub">Only fill fields you want to change</div></div>
    <button class="btn btn-ghost btn-sm" data-page="admin-judges">← Back</button>
  </div>
  <div class="card" style="max-width:520px">
    <form id="edit-judge-form">
      <input type="hidden" name="judge_id" value="${jid}">
      <div class="field-row">
        <div class="field"><label>First Name</label><input name="firstname" placeholder="Leave blank to keep"></div>
        <div class="field"><label>Last Name</label><input name="lastname" placeholder="Leave blank to keep"></div>
      </div>
      <div class="field"><label>Email</label><input type="email" name="email" placeholder="Leave blank to keep"></div>
      <div class="field"><label>New Password</label><input type="password" name="password" placeholder="Leave blank to keep"></div>
      <div class="field"><label>Commission per Evaluation (PKR)</label><input type="number" name="commission_per_eval" min="0" step="0.01" placeholder="Leave blank to keep"></div>
      <div class="field"><label>Phone Numbers <span class="text-muted">(replaces existing, comma-separated)</span></label><input name="phones" placeholder="Leave blank to keep"></div>
      <div class="field"><label>Degrees <span class="text-muted">(replaces existing, comma-separated)</span></label><input name="degrees" placeholder="Leave blank to keep"></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Save Changes</button>
    </form>
  </div>`;
}

function renderEditOrganizer() {
  const oid = state.data.editOrganizerId;
  return `
  <div class="page-header flex justify-between">
    <div><div class="page-title">Edit Organizer</div><div class="page-sub">Only fill fields you want to change</div></div>
    <button class="btn btn-ghost btn-sm" data-page="admin-organizers">← Back</button>
  </div>
  <div class="card" style="max-width:520px">
    <form id="edit-organizer-form">
      <input type="hidden" name="organizer_id" value="${oid}">
      <div class="field-row">
        <div class="field"><label>First Name</label><input name="firstname" placeholder="Leave blank to keep"></div>
        <div class="field"><label>Last Name</label><input name="lastname" placeholder="Leave blank to keep"></div>
      </div>
      <div class="field"><label>Email</label><input type="email" name="email" placeholder="Leave blank to keep"></div>
      <div class="field"><label>New Password</label><input type="password" name="password" placeholder="Leave blank to keep"></div>
      <div class="field"><label>Salary (PKR)</label><input type="number" name="salary" min="0" step="0.01" placeholder="Leave blank to keep"></div>
      <div class="field"><label>Phone Numbers <span class="text-muted">(replaces existing, comma-separated)</span></label><input name="phones" placeholder="Leave blank to keep"></div>
      <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>Save Changes</button>
    </form>
  </div>`;
}
