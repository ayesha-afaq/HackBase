// ── AUTH LOGIC ─────────────────────────────────────────────────────────────
async function login(email, password) {
  setState({ loading: true, error: null });
  try {
    const data = await post('/auth/login', { email, password });
    const user = {
      user_id       : data.user_id,
      name          : data.name,
      role          : data.role,
      participant_id: data.participant_id  || null,
      judge_id      : data.judge_id        || null,
      organizer_id  : data.organizer_id    || null,
    };
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(user));
    const defaultPage = {
      admin      : 'admin-users',
      organizer  : 'my-events',
      judge      : 'judge-assigned',
      participant: 'participant-events',
    }[data.role] || 'public-events';
    setState({ token: data.token, user, loading: false, error: null });
    setPage(defaultPage);
  } catch(e) {
    setState({ loading: false, error: e.message });
  }
}

async function register(formData) {
  setState({ loading: true, error: null });
  try {
    await post('/auth/register', formData);
    setState({
      loading: false,
      success: 'Registered successfully! Please log in.',
      data: { ...state.data, authTab: 'login' },
    });
  } catch(e) {
    setState({ loading: false, error: e.message });
  }
}

function logout() {
  localStorage.clear();
  // Reset state and trigger a render immediately so the UI clears,
  // then fetch public events in the background.
  setState({
    token  : null,
    user   : null,
    page   : 'public-events',
    data   : {},
    success: null,
    error  : null,
    modal  : null,
    loading: true,
  });
  get('/public/events')
    .then(data => setState({ data: { events: data }, loading: false }))
    .catch(()  => setState({ loading: false }));
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
      ${state.error   ? `<div class="alert alert-error">${state.error}</div>`     : ''}
      ${state.success ? `<div class="alert alert-success">${state.success}</div>` : ''}
      ${tab === 'login' ? renderLogin() : renderRegister()}
    </div>
  </div>`;
}

function renderLogin() {
  return `
  <form id="login-form">
    <div class="field">
      <label>Email</label>
      <input type="email" name="email" placeholder="you@example.com" required autocomplete="email">
    </div>
    <div class="field">
      <label>Password</label>
      <input type="password" name="password" placeholder="••••••••" required autocomplete="current-password">
    </div>
    <button class="btn btn-primary btn-full mt-3" type="submit" ${state.loading?'disabled':''}>
      ${state.loading ? 'Logging in...' : 'Login'}
    </button>
  </form>`;
}

function renderRegister() {
  return `
  <form id="register-form">
    <div class="field-row">
      <div class="field"><label>First Name</label><input name="firstname" placeholder="Jane" required autocomplete="given-name"></div>
      <div class="field"><label>Last Name</label><input name="lastname" placeholder="Doe" required autocomplete="family-name"></div>
    </div>
    <div class="field">
      <label>Middle Name <span style="color:var(--text3);font-weight:400">(optional)</span></label>
      <input name="middlename" placeholder="Leave blank if none" autocomplete="additional-name">
    </div>
    <div class="field">
      <label>CNIC</label>
      <input name="cnic" placeholder="12345-1234567-1" required
        pattern="\\d{5}-\\d{7}-\\d" title="Format: 12345-1234567-1">
    </div>
    <div class="field">
      <label>Email</label>
      <input type="email" name="email" placeholder="you@example.com" required autocomplete="email">
    </div>
    <div class="field">
      <label>Password</label>
      <input type="password" name="password" placeholder="••••••••" required
        minlength="6" autocomplete="new-password">
    </div>
    <div class="field-row">
      <div class="field"><label>Date of Birth</label><input type="date" name="date_of_birth" autocomplete="bday"></div>
      <div class="field"><label>City</label><input name="city" placeholder="Karachi" autocomplete="address-level2"></div>
    </div>
    <div class="field">
      <label>Institution</label>
      <input name="institution" placeholder="University..." autocomplete="organization">
    </div>
    <button class="btn btn-primary btn-full mt-3" type="submit" ${state.loading?'disabled':''}>
      ${state.loading ? 'Registering...' : 'Create Account'}
    </button>
  </form>`;
}
