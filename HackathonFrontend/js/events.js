// ── HANDLE ACTION ─────────────────────────────────────────────────────────
async function handleAction(action, dataset) {
  const id = parseInt(dataset.id);
  setState({ error: null, success: null });
  try {
    if (action === 'delete-user') {
      if (!confirm('Delete this user?')) return;
      setState({ loading: true });
      await del(`/admin/delete-user/${id}`);
      setState({ loading: false, success: 'User deleted' });
      loadPage('admin-users');

    } else if (action === 'event-detail') {
      setState({ loading: true });
      const ev = await get('/organizer/event-detail/' + id);
      setState({ loading: false, page: 'event-detail', data: { ...state.data, currentEvent: ev, currentEventId: id } });

    } else if (action === 'event-teams') {
      setState({ loading: true });
      const teams = await get('/organizer/event-teams/' + id);
      setState({ loading: false, page: 'event-teams', data: { ...state.data, teams, currentEventId: id } });

    } else if (action === 'event-registrations') {
      setState({ loading: true });
      const registrations = await get('/organizer/event-registrations/' + id);
      setState({ loading: false, page: 'event-registrations', data: { ...state.data, registrations, currentEventId: id } });

    } else if (action === 'event-projects') {
      setState({ loading: true });
      const projects = await get('/organizer/submitted-projects/' + id);
      setState({ loading: false, page: 'event-projects', data: { ...state.data, projects, currentEventId: id } });

    } else if (action === 'event-judges-list') {
      setState({ loading: true });
      const eventJudges = await get('/organizer/event-judges/' + id);
      setState({ loading: false, page: 'event-judges-list', data: { ...state.data, eventJudges, currentEventId: id } });

    } else if (action === 'assign-judge') {
      setState({ page: 'assign-judge', data: { ...state.data, currentEventId: id } });

    } else if (action === 'update-status') {
      setState({ loading: true });
      await put('/organizer/update-event-status', { event_id: id, event_status: dataset.status });
      const ev = await get('/organizer/event-detail/' + id);
      setState({ loading: false, success: 'Status updated', page: 'event-detail', data: { ...state.data, currentEvent: ev, currentEventId: id } });

    } else if (action === 'delete-team') {
      if (!confirm('Delete this team?')) return;
      setState({ loading: true });
      await del(`/organizer/delete-team/${id}`);
      const eid = state.data.currentEventId;
      const teams = await get('/organizer/event-teams/' + eid);
      setState({ loading: false, success: 'Team deleted', data: { ...state.data, teams } });

    } else if (action === 'evaluate') {
      setState({ modal: { type: 'evaluate', id, name: dataset.name } });

    } else if (action === 'update-feedback') {
      setState({ modal: { type: 'update-feedback', id } });

    } else if (action === 'judge-leaderboard') {
      setState({ loading: true });
      const leaderboard = await get('/judge/event-leaderboard/' + id);
      setState({ loading: false, page: 'judge-leaderboard', data: { ...state.data, leaderboard, leaderboardEvent: dataset.name } });

    } else if (action === 'register-event') {
      setState({ loading: true });
      const res = await post('/participant/register-event', { event_id: id });
      setState({ loading: false, success: res.message });

    } else if (action === 'public-leaderboard') {
      setState({ loading: true });
      const leaderboard = await get('/public/event-results/' + id);
      setState({ loading: false, page: 'public-event-results', data: { ...state.data, leaderboard, leaderboardEvent: dataset.name } });
    }
  } catch(e) {
    setState({ loading: false, error: e.message });
  }
}

// ── EVENT BINDING ─────────────────────────────────────────────────────────
function bindEvents() {
  // Auth tabs
  document.querySelectorAll('[data-tab]').forEach(el => {
    el.addEventListener('click', () => setState({ data: { ...state.data, authTab: el.dataset.tab }, error: null, success: null }));
  });

  // Nav items / buttons that change page
  document.querySelectorAll('[data-page]').forEach(el => {
    el.addEventListener('click', () => setPage(el.dataset.page));
  });

  // Logout
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);

  // Modal close
  const closeModal = document.getElementById('close-modal');
  if (closeModal) closeModal.addEventListener('click', () => setState({ modal: null }));
  const overlay = document.getElementById('modal-overlay');
  if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay) setState({ modal: null }); });

  // Login form
  const loginForm = document.getElementById('login-form');
  if (loginForm) loginForm.addEventListener('submit', e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    login(d.email, d.password);
  });

  // Register form
  const regForm = document.getElementById('register-form');
  if (regForm) regForm.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    await register(d);
  });

  // Action buttons (data-action)
  document.querySelectorAll('[data-action]').forEach(el => {
    el.addEventListener('click', () => handleAction(el.dataset.action, el.dataset));
  });

  // Admin create-judge form
  const cjf = document.getElementById('create-judge-form');
  if (cjf) cjf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const phones = d.phones ? d.phones.split(',').map(s=>s.trim()).filter(Boolean) : [];
      const degrees = d.degrees ? d.degrees.split(',').map(s=>s.trim()).filter(Boolean) : [];
      await post('/admin/create-judge', { ...d, phone_numbers: phones, degrees, commission_per_eval: parseFloat(d.commission_per_eval) });
      setState({ loading: false, success: 'Judge created successfully!' });
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // Admin create-organizer form
  const cof = document.getElementById('create-organizer-form');
  if (cof) cof.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const phones = d.phones ? d.phones.split(',').map(s=>s.trim()).filter(Boolean) : [];
      const body = { ...d, phone_numbers: phones };
      if (d.salary) body.salary = parseFloat(d.salary);
      await post('/admin/create-organizer', body);
      setState({ loading: false, success: 'Organizer created successfully!' });
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // Create event form
  const cef = document.getElementById('create-event-form');
  if (cef) cef.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const numFields = ['max_team_size','budget','funding','first_prize','second_prize','third_prize'];
      numFields.forEach(k => { if (d[k] !== undefined) d[k] = Number(d[k]); });
      const res = await post('/organizer/create-event', d);
      setState({ loading: false, success: `Event created! ID: ${res.event_id}` });
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // Assign judge form
  const ajf = document.getElementById('assign-judge-form');
  if (ajf) ajf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      await post('/organizer/assign-judge', { event_id: parseInt(d.event_id), judge_id: parseInt(d.judge_id) });
      setState({ loading: false, success: 'Judge assigned!' });
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // Evaluate form
  const evf = document.getElementById('evaluate-form');
  if (evf) evf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      await post('/judge/evaluate', { project_id: parseInt(d.project_id), score: parseFloat(d.score), feedback: d.feedback || null });
      setState({ loading: false, modal: null, success: 'Evaluation submitted!' });
      loadPage('judge-assigned');
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // FIX #7: Update feedback success now calls loadPage('judge-assigned') so
  // the projects list refreshes and shows the new feedback — previously the
  // modal closed and success was shown but the stale card remained visible.
  const uff = document.getElementById('update-feedback-form');
  if (uff) uff.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      await put('/judge/update-feedback', { project_id: parseInt(d.project_id), feedback: d.feedback });
      setState({ loading: false, modal: null, success: 'Feedback updated!' });
      loadPage('judge-assigned'); // refresh so updated feedback is visible
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // Create team form
  const ctf = document.getElementById('create-team-form');
  if (ctf) ctf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const res = await post('/participant/create-team', { event_id: parseInt(d.event_id), team_name: d.team_name });
      setState({ loading: false, success: `Team created! Code: ${res.team_code}` });
      setPage('participant-my-team');
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // Join team form
  const jtf = document.getElementById('join-team-form');
  if (jtf) jtf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const res = await post('/participant/join-team', { event_id: parseInt(d.event_id), team_code: d.team_code.toUpperCase() });
      setState({ loading: false, success: res.message });
      setPage('participant-my-team');
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // Submit project form
  const spf = document.getElementById('submit-project-form');
  if (spf) spf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const res = await post('/participant/submit-project', { team_id: parseInt(d.team_id), project_name: d.project_name, github_link: d.github_link || null, description: d.description || null });
      setState({ loading: false, success: res.message || 'Project submitted!' });
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // Leave team button
  const leaveBtn = document.getElementById('leave-team-btn');
  if (leaveBtn) leaveBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to leave this team?')) return;
    const teamId = parseInt(leaveBtn.dataset.teamId);
    setState({ loading: true, error: null });
    try {
      await del('/participant/leave-team', { team_id: teamId });
      setState({ loading: false, success: 'Left team successfully' });
      setPage('participant-my-team');
    } catch(err) {
      setState({ loading: false, error: err.message });
    }
  });
}