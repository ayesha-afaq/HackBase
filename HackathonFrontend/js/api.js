// ── API HELPERS ───────────────────────────────────────────────────────────
async function api(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (state.token) opts.headers['Authorization'] = 'Bearer ' + state.token;
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  const json = await r.json();
  if (!r.ok) throw new Error(json.detail || JSON.stringify(json));
  return json;
}

async function get(path) { return api('GET', path); }
async function post(path, body) { return api('POST', path, body); }
async function put(path, body) { return api('PUT', path, body); }
async function del(path, body) { return api('DELETE', path, body); }

// ── PAGE DATA LOADER ──────────────────────────────────────────────────────
// FIX #4: Removed the early `if (!u) return` guard so public pages load
// without requiring a logged-in user. Public pages are explicitly listed
// first; only role-specific pages fall through to the auth check.
async function loadPage(page) {
  setState({ loading: true, error: null });
  try {
    // ── PUBLIC pages — no user required ──────────────────────────────────
    if (page === 'events' || page === 'public-events') {
      const data = await get('/public/events');
      setState({ data: { events: data }, loading: false });
      return;
    }

    // ── All other pages require authentication ────────────────────────────
    const u = state.user;
    if (!u) { setState({ loading: false }); return; }

    if (page === 'admin-users') {
      const data = await get('/admin/users');
      setState({ data: { users: data }, loading: false });

    } else if (page === 'admin-judges') {
      const data = await get('/admin/judges');
      setState({ data: { judges: data }, loading: false });

    } else if (page === 'admin-organizers') {
      const data = await get('/admin/organizers');
      setState({ data: { organizers: data }, loading: false });

    } else if (page === 'admin-events') {
      const data = await get('/admin/events');
      setState({ data: { events: data }, loading: false });

    } else if (page === 'my-events') {
      const data = await get('/organizer/my-events');
      setState({ data: { events: data }, loading: false });

    } else if (page === 'judge-assigned') {
      const data = await get('/judge/assigned-projects');
      setState({ data: { projects: data }, loading: false });

    } else if (page === 'judge-pending') {
      const data = await get('/judge/pending-projects');
      setState({ data: { projects: data }, loading: false });

    } else if (page === 'judge-evals') {
      const data = await get('/judge/my-evaluations');
      setState({ data: { evals: data }, loading: false });

    } else if (page === 'judge-events') {
      const data = await get('/judge/my-events');
      setState({ data: { events: data }, loading: false });

    } else if (page === 'judge-profile') {
      const data = await get('/judge/profile');
      setState({ data: { profile: data }, loading: false });

    } else if (page === 'participant-events') {
      const data = await get('/participant/events');
      setState({ data: { events: data }, loading: false });

    } else if (page === 'participant-my-events') {
      const pid = u.participant_id;
      const data = await get('/participant/my-events/' + pid);
      setState({ data: { events: data }, loading: false });

    } else if (page === 'participant-profile') {
      const pid = u.participant_id;
      const data = await get('/participant/profile/' + pid);
      setState({ data: { profile: data }, loading: false });

    } else if (page === 'participant-my-team') {
      const pid = u.participant_id;
      const myEvents = await get('/participant/my-events/' + pid);
      if (myEvents.length === 0) {
        setState({ data: { team: { message: 'You are not registered for any event yet.' } }, loading: false });
        return;
      }
      const eventId = myEvents[0].event_id;
      const teamData = await get('/participant/my-team/' + pid + '/' + eventId);
      let projectData = null;
      if (teamData.team_id) {
        try {
          projectData = await get('/participant/my-project/' + teamData.team_id);
          if (projectData.message) projectData = null;
        } catch(e) { /* no project yet */ }
      }
      setState({ data: { team: teamData, project: projectData }, loading: false });

    } else {
      setState({ loading: false });
    }
  } catch(e) {
    setState({ loading: false, error: e.message });
  }
}