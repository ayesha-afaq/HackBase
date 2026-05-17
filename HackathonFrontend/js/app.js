async function boot() {
  if (!state.token) {
    state.page = 'public-events';
    try {
      const data = await get('/public/events');
      setState({ data: { events: data }, loading: false });
    } catch {
      setState({ loading: false });
    }
  } else {
    const role = state.user?.role;
    const defaultPage = {
      admin      : 'admin-users',
      organizer  : 'my-events',
      judge      : 'judge-assigned',
      participant: 'participant-events',
    }[role] || 'public-events';
    state.page = defaultPage;
    await loadPage(defaultPage);
  }
}

boot();
