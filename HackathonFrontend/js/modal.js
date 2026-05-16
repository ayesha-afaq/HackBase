// ── MODAL ─────────────────────────────────────────────────────────────────
function renderModal() {
  const m = state.modal;
  if (m.type === 'evaluate') {
    return `<div class="modal-overlay" id="modal-overlay">
      <div class="modal">
        <div class="modal-title">Evaluate: ${m.name}</div>
        <form id="evaluate-form">
          <input type="hidden" name="project_id" value="${m.id}">
          <div class="field">
            <label>Score (0–100)</label>
            <input type="number" name="score" min="0" max="100" required>
          </div>
          <div class="field">
            <label>Feedback (optional)</label>
            <textarea name="feedback" placeholder="Write feedback..."></textarea>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-primary" type="submit">Submit</button>
            <button class="btn btn-ghost" type="button" id="close-modal">Cancel</button>
          </div>
        </form>
      </div>
    </div>`;
  }
  if (m.type === 'update-feedback') {
    return `<div class="modal-overlay" id="modal-overlay">
      <div class="modal">
        <div class="modal-title">Update Feedback</div>
        <form id="update-feedback-form">
          <input type="hidden" name="project_id" value="${m.id}">
          <div class="field"><label>Feedback</label><textarea name="feedback" rows="4"></textarea></div>
          <div class="flex gap-2">
            <button class="btn btn-primary" type="submit">Update</button>
            <button class="btn btn-ghost" type="button" id="close-modal">Cancel</button>
          </div>
        </form>
      </div>
    </div>`;
  }
  return '';
}