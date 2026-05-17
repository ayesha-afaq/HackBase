// ── MODAL ─────────────────────────────────────────────────────────────────
function renderModal() {
  const m = state.modal;

  if (m.type === 'evaluate') {
    return `
    <div class="modal-overlay" id="modal-overlay">
      <div class="modal">
        <div class="modal-title">Evaluate: ${m.name}</div>
        <form id="evaluate-form">
          <input type="hidden" name="project_id" value="${m.id}">
          <div class="field">
            <label>Score <span class="text-muted">(0 – 100)</span></label>
            <input type="number" name="score" min="0" max="100" step="0.1"
              placeholder="e.g. 85" required
              oninput="document.getElementById('score-preview').textContent=this.value||'—'">
            <div style="margin-top:6px;">
              <div class="score-bar-wrap">
                <div class="score-bar" id="score-bar-preview" style="width:0%;transition:width 0.2s"></div>
              </div>
              <div class="text-muted text-sm" style="margin-top:4px;">Preview: <span id="score-preview">—</span> / 100</div>
            </div>
          </div>
          <div class="field">
            <label>Feedback <span class="text-muted">(optional)</span></label>
            <textarea name="feedback" rows="4" placeholder="Write your feedback..."></textarea>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>
              ${state.loading ? 'Submitting...' : 'Submit Evaluation'}
            </button>
            <button class="btn btn-ghost" type="button" id="close-modal">Cancel</button>
          </div>
        </form>
      </div>
    </div>`;
  }

  if (m.type === 'update-feedback') {
    // Escape any HTML in existing feedback before putting it in the textarea
    const existing = (m.currentFeedback || '').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    return `
    <div class="modal-overlay" id="modal-overlay">
      <div class="modal">
        <div class="modal-title">Update Feedback</div>
        <p class="text-muted text-sm" style="margin-bottom:12px;">Score cannot be changed to keep results fair.</p>
        <form id="update-feedback-form">
          <input type="hidden" name="project_id" value="${m.id}">
          <div class="field">
            <label>Feedback</label>
            <textarea name="feedback" rows="5">${existing}</textarea>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-primary" type="submit" ${state.loading?'disabled':''}>
              ${state.loading ? 'Saving...' : 'Save Feedback'}
            </button>
            <button class="btn btn-ghost" type="button" id="close-modal">Cancel</button>
          </div>
        </form>
      </div>
    </div>`;
  }

  return '';
}
