
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