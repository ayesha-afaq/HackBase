// ── HANDLE ACTION ─────────────────────────────────────────────────────────
async function handleAction(action, dataset) {
  const id = parseInt(dataset.id);
  setState({ error: null, success: null });
  try {
    // ── Admin ─────────────────────────────────────────────────────────────
    if (action === 'delete-user') {
      if (!confirm('Delete this user? This cannot be undone.')) return;
      setState({ loading: true });
      await del(`/admin/delete-user/${id}`);
      setState({ loading: false, success: 'User deleted' });
      loadPage('admin-users');

    } else if (action === 'view-user') {
      setState({ loading: true, data: { ...state.data, currentUserId: id } });
      const userDetail = await get('/admin/users/' + id);
      setState({ loading: false, page: 'admin-user-detail', data: { ...state.data, userDetail, currentUserId: id } });

    } else if (action === 'edit-judge') {
      setState({ page: 'admin-edit-judge', data: { ...state.data, editJudgeId: id } });

    } else if (action === 'edit-organizer') {
      setState({ page: 'admin-edit-organizer', data: { ...state.data, editOrganizerId: id } });

    // ── Organizer ─────────────────────────────────────────────────────────
    } else if (action === 'event-detail') {
      setState({ loading: true });
      const ev = await get('/organizer/event-detail/' + id);
      setState({ loading: false, page: 'event-detail', data: { ...state.data, currentEvent: ev, currentEventId: id } });

    } else if (action === 'edit-event') {
      setState({ loading: true });
      const ev = await get('/organizer/event-detail/' + id);
      setState({ loading: false, page: 'update-event', data: { ...state.data, currentEvent: ev, currentEventId: id } });

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
      setState({ loading: false, success: 'Team deleted', data: { ...state.data, teams, expandedTeamId: null } });

    } else if (action === 'view-team-members') {
      // Toggle: if already expanded, collapse it
      if (state.data.expandedTeamId === id) {
        setState({ data: { ...state.data, expandedTeamId: null } });
        return;
      }
      // Fetch members if not already loaded
      const teamMembers = state.data.teamMembers || {};
      if (!teamMembers[id]) {
        setState({ data: { ...state.data, expandedTeamId: id } });
        try {
          const members = await get('/organizer/team-members/' + id);
          setState({ data: { ...state.data, expandedTeamId: id, teamMembers: { ...state.data.teamMembers, [id]: members } } });
        } catch(e) {
          setState({ error: e.message, data: { ...state.data, expandedTeamId: null } });
        }
      } else {
        setState({ data: { ...state.data, expandedTeamId: id } });
      }

    // ── Judge ─────────────────────────────────────────────────────────────
    } else if (action === 'evaluate') {
      setState({ modal: { type: 'evaluate', id, name: dataset.name } });

    } else if (action === 'update-feedback') {
      // Find current feedback from loaded projects so we can pre-fill the textarea
      const projects = state.data.projects || [];
      const proj = projects.find(p => p.project_id === id);
      setState({ modal: { type: 'update-feedback', id, currentFeedback: proj?.my_feedback || '' } });

    } else if (action === 'judge-leaderboard') {
      setState({ loading: true });
      const res = await get('/judge/event-leaderboard/' + id);
      // Backend returns array when ready, or { message, leaderboard: [] } when not
      const leaderboard = Array.isArray(res) ? res : (res.leaderboard || []);
      const leaderboardReady = Array.isArray(res) && res.length > 0;
      const leaderboardMessage = !Array.isArray(res) ? res.message : null;
      setState({ loading: false, page: 'judge-leaderboard', data: { ...state.data, leaderboard, leaderboardReady, leaderboardMessage, leaderboardEvent: dataset.name } });

    } else if (action === 'view-project-detail') {
      setState({ loading: true });
      const projectDetail = await get('/judge/project-detail/' + id);
      setState({ loading: false, page: 'judge-project-detail', data: { ...state.data, projectDetail } });

    // ── Participant ───────────────────────────────────────────────────────
    } else if (action === 'register-event') {
      if (!confirm('Register for this event?')) return;
      setState({ loading: true });
      const res = await post('/participant/register-event', { event_id: id });
      setState({ loading: false, success: res.message });
      loadPage('participant-events');

    } else if (action === 'switch-team-event') {
      // Switch which event's team is shown on the my-team page
      setState({ data: { ...state.data, selectedTeamEventId: id } });
      loadPage('participant-my-team');

    } else if (action === 'public-leaderboard') {
      setState({ loading: true });
      const res = await get('/public/event-results/' + id);
      // Backend returns { results_ready, leaderboard, message } or similar
      const leaderboard = Array.isArray(res) ? res : (res.leaderboard || []);
      const leaderboardReady = res.results_ready !== false;
      const leaderboardMessage = res.message || null;
      setState({ loading: false, page: 'public-event-results', data: { ...state.data, leaderboard, leaderboardReady, leaderboardMessage, leaderboardEvent: dataset.name } });
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

  // Score bar live preview inside evaluate modal
  const scoreInput = document.querySelector('#evaluate-form input[name="score"]');
  const scoreBar   = document.getElementById('score-bar-preview');
  if (scoreInput && scoreBar) {
    scoreInput.addEventListener('input', () => {
      scoreBar.style.width = Math.min(Math.max(parseFloat(scoreInput.value)||0, 0), 100) + '%';
    });
  }

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

  // ── Admin: create-judge form ──────────────────────────────────────────
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
      e.target.reset();
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Admin: create-organizer form ──────────────────────────────────────
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
      e.target.reset();
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Admin: edit-judge form ────────────────────────────────────────────
  const ejf = document.getElementById('edit-judge-form');
  if (ejf) ejf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const body = {};
      if (d.firstname)           body.firstname           = d.firstname;
      if (d.lastname)            body.lastname            = d.lastname;
      if (d.email)               body.email               = d.email;
      if (d.password)            body.password            = d.password;
      if (d.commission_per_eval) body.commission_per_eval = parseFloat(d.commission_per_eval);
      if (d.phones)              body.phone_numbers       = d.phones.split(',').map(s=>s.trim()).filter(Boolean);
      if (d.degrees)             body.degrees             = d.degrees.split(',').map(s=>s.trim()).filter(Boolean);
      await put('/admin/update-judge/' + d.judge_id, body);
      setState({ loading: false, success: 'Judge updated successfully!' });
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Admin: edit-organizer form ────────────────────────────────────────
  const eof = document.getElementById('edit-organizer-form');
  if (eof) eof.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const body = {};
      if (d.firstname)  body.firstname     = d.firstname;
      if (d.lastname)   body.lastname      = d.lastname;
      if (d.email)      body.email         = d.email;
      if (d.password)   body.password      = d.password;
      if (d.salary)     body.salary        = parseFloat(d.salary);
      if (d.phones)     body.phone_numbers = d.phones.split(',').map(s=>s.trim()).filter(Boolean);
      await put('/admin/update-organizer/' + d.organizer_id, body);
      setState({ loading: false, success: 'Organizer updated successfully!' });
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Organizer: create event form ──────────────────────────────────────
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
      e.target.reset();
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Organizer: update event form ──────────────────────────────────────
  const uef = document.getElementById('update-event-form');
  if (uef) uef.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const body = {};
      if (d.event_name)                body.event_name                = d.event_name;
      if (d.last_date_of_registration) body.last_date_of_registration = d.last_date_of_registration;
      if (d.max_team_size)             body.max_team_size             = parseInt(d.max_team_size);
      if (d.event_details)             body.event_details             = d.event_details;
      if (d.budget    !== '')          body.budget                    = Number(d.budget);
      if (d.funding   !== '')          body.funding                   = Number(d.funding);
      if (d.first_prize  !== '')       body.first_prize               = Number(d.first_prize);
      if (d.second_prize !== '')       body.second_prize              = Number(d.second_prize);
      if (d.third_prize  !== '')       body.third_prize               = Number(d.third_prize);
      const eid = parseInt(d.event_id);
      await put('/organizer/update-event/' + eid, body);
      const ev = await get('/organizer/event-detail/' + eid);
      setState({ loading: false, success: 'Event updated!', page: 'event-detail', data: { ...state.data, currentEvent: ev, currentEventId: eid } });
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Organizer: assign judge form ──────────────────────────────────────
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

  // ── Judge: evaluate form ──────────────────────────────────────────────
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

  // ── Judge: update feedback form ───────────────────────────────────────
  const uff = document.getElementById('update-feedback-form');
  if (uff) uff.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      await put('/judge/update-feedback', { project_id: parseInt(d.project_id), feedback: d.feedback });
      setState({ loading: false, modal: null, success: 'Feedback updated!' });
      loadPage('judge-assigned');
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Participant: create team form ─────────────────────────────────────
  const ctf = document.getElementById('create-team-form');
  if (ctf) ctf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const res = await post('/participant/create-team', { event_id: parseInt(d.event_id), team_name: d.team_name });
      setState({ loading: false, success: `Team created! Your code: ${res.team_code}` });
      setPage('participant-my-team');
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Participant: join team form ───────────────────────────────────────
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

  // ── Participant: submit project form ──────────────────────────────────
  const spf = document.getElementById('submit-project-form');
  if (spf) spf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const res = await post('/participant/submit-project', {
        team_id: parseInt(d.team_id),
        project_name: d.project_name,
        github_link: d.github_link || null,
        description: d.description || null
      });
      setState({ loading: false, success: res.message || 'Project submitted!' });
      setPage('participant-my-team');
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Participant: update profile form ──────────────────────────────────
  const upf = document.getElementById('update-profile-form');
  if (upf) upf.addEventListener('submit', async e => {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.target));
    setState({ loading: true, error: null });
    try {
      const body = {};
      if (d.firstname)     body.firstname     = d.firstname;
      if (d.middlename)    body.middlename    = d.middlename;
      if (d.lastname)      body.lastname      = d.lastname;
      if (d.email)         body.email         = d.email;
      if (d.password)      body.password      = d.password;
      if (d.date_of_birth) body.date_of_birth = d.date_of_birth;
      if (d.city)          body.city          = d.city;
      if (d.institution)   body.institution   = d.institution;
      const pid = state.user.participant_id;
      await put('/participant/update-profile/' + pid, body);
      setState({ loading: false, success: 'Profile updated!' });
      loadPage('participant-profile');
    } catch(err) { setState({ loading: false, error: err.message }); }
  });

  // ── Participant: leave team button ────────────────────────────────────
  const leaveBtn = document.getElementById('leave-team-btn');
  if (leaveBtn) leaveBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to leave this team?')) return;
    const teamId = parseInt(leaveBtn.dataset.teamId);
    setState({ loading: true, error: null });
    try {
      await del('/participant/leave-team', { team_id: teamId });
      setState({ loading: false, success: 'Left team successfully', data: { ...state.data, selectedTeamEventId: null } });
      setPage('participant-my-team');
    } catch(err) {
      setState({ loading: false, error: err.message });
    }
  });

  // ── Participant: delete team button (team lead only) ──────────────────
  const deleteTeamBtn = document.getElementById('delete-team-btn');
  if (deleteTeamBtn) deleteTeamBtn.addEventListener('click', async () => {
    if (!confirm('Delete your team? This will remove all members and any submitted project. This cannot be undone.')) return;
    const teamId = parseInt(deleteTeamBtn.dataset.teamId);
    setState({ loading: true, error: null });
    try {
      await del('/participant/delete-team/' + teamId);
      setState({ loading: false, success: 'Team deleted successfully', data: { ...state.data, selectedTeamEventId: null } });
      setPage('participant-my-team');
    } catch(err) {
      setState({ loading: false, error: err.message });
    }
  });
}
