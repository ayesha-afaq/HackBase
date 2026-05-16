// ── AUTH LOGIC ─────────────────────────────────────────────────────────────
async function login(email, password) {
  setState({ loading: true, error: null });
  try {
    const data = await post('/auth/login', { email, password });
    const user = {
      user_id: data.user_id, name: data.name, role: data.role,
      participant_id: data.participant_id, judge_id: data.judge_id, organizer_id: data.organizer_id
    };
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(user));
    const defaultPage = { admin: 'admin-users', organizer: 'my-events', judge: 'judge-assigned', participant: 'participant-events' }[data.role] || 'events';
    setState({ token: data.token, user, loading: false });
    setPage(defaultPage);
  } catch(e) { setState({ loading: false, error: e.message }); }
}

async function register(formData) {
  setState({ loading: true, error: null });
  try {
    await post('/auth/register', formData);
    setState({ loading: false, success: 'Registered successfully! Please log in.' });
  } catch(e) { setState({ loading: false, error: e.message }); }
}

function logout() {
  localStorage.clear();
  // FIX #4: After logout, load public events without needing a user object.
  // We call loadPage directly here since state.user is now null.
  Object.assign(state, { token: null, user: null, page: 'public-events', data: {}, success: null, error: null, modal: null, loading: true });
  get('/public/events')
    .then(data => setState({ data: { events: data }, loading: false }))
    .catch(() => setState({ loading: false }));
}

// ── AUTH VIEWS ─────────────────────────────────────────────────────────────
function renderAuth() {
  const tab = state.data.authTab || 'login';
  return `
  <div class="auth-wrap">
    <div class="auth-card">
      <div class="auth-logo">&gt; hackathon_mgmt</div>
      <div class="auth-sub">Management System v1.0</div>
      <div class="auth-tabs">
        <div class="auth-tab ${tab==='login'?'active':''}" data-tab="login">Login</div>
        <div class="auth-tab ${tab==='register'?'active':''}" data-tab="register">Register</div>
      </div>
      ${state.error ? `<div class="alert alert-error">${state.error}</div>` : ''}
      ${state.success ? `<div class="alert alert-success">${state.success}</div>` : ''}
      ${tab === 'login' ? renderLogin() : renderRegister()}
    </div>
  </div>`;
}

function renderLogin() {
  return `
  <form id="login-form">
    <div class="field"><label>Email</label><input type="email" name="email" placeholder="you@example.com" required></div>
    <div class="field"><label>Password</label><input type="password" name="password" placeholder="••••••••" required></div>
    <button class="btn btn-primary btn-full mt-3" type="submit" ${state.loading?'disabled':''}>
      ${state.loading ? 'Logging in...' : 'Login'}
    </button>
  </form>`;
}

function renderRegister() {
  return `
  <form id="register-form">
    <div class="field-row">
      <div class="field"><label>First Name</label><input name="firstname" placeholder="Jane" required></div>
      <div class="field"><label>Last Name</label><input name="lastname" placeholder="Doe" required></div>
    </div>
    <div class="field"><label>CNIC</label><input name="cnic" placeholder="12345-1234567-1" required></div>
    <div class="field"><label>Email</label><input type="email" name="email" placeholder="you@example.com" required></div>
    <div class="field"><label>Password</label><input type="password" name="password" placeholder="••••••••" required></div>
    <div class="field-row">
      <div class="field"><label>Date of Birth</label><input type="date" name="date_of_birth"></div>
      <div class="field"><label>City</label><input name="city" placeholder="Karachi"></div>
    </div>
    <div class="field"><label>Institution</label><input name="institution" placeholder="University..."></div>
    <button class="btn btn-primary btn-full mt-3" type="submit" ${state.loading?'disabled':''}>
      ${state.loading ? 'Registering...' : 'Create Account'}
    </button>
  </form>`;
}