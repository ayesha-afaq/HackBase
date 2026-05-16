// ── BOOT ──────────────────────────────────────────────────────────────────
// FIX #4: boot() no longer skips the public event fetch when user is null.
// The old code called loadPage('public-events') in the no-token branch, but
// loadPage bailed out immediately because of the `if (!u) return` guard at
// the top. Now the public branch in loadPage runs unconditionally (the guard
// was moved below it), so the events list actually loads for unauthenticated
// visitors.
async function boot() {
  if (!state.token) {
    state.page = 'public-events';
    await get('/public/events')
      .then(data => setState({ data: { events: data }, loading: false }))
      .catch(() => setState({ loading: false }));
  } else {
    const role = state.user?.role;
    const defaultPage = { admin: 'admin-users', organizer: 'my-events', judge: 'judge-assigned', participant: 'participant-events' }[role] || 'events';
    state.page = defaultPage;
    await loadPage(defaultPage);
  }
  render();
}

boot();