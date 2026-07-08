/* ═══════════════════════════════════════════════════════════════
   roadmap.js – LearnMate Roadmap Page Logic
   Handles roadmap generation, progress tracking, milestone toggle
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  const generateBtn  = document.getElementById('generateBtn');
  const loadingEl    = document.getElementById('roadmapLoading');
  const contentEl    = document.getElementById('roadmapContent');
  const emptyEl      = document.getElementById('emptyState');
  const progressBar  = document.getElementById('roadmapProgressBar');
  const progressPct  = document.getElementById('roadmapPct');

  // ── Milestone storage ─────────────────────────────────────────
  const MILESTONES_KEY = 'lm_milestones';

  function loadMilestones() {
    try { return JSON.parse(localStorage.getItem(MILESTONES_KEY) || '{}'); }
    catch { return {}; }
  }
  function saveMilestones(data) {
    localStorage.setItem(MILESTONES_KEY, JSON.stringify(data));
  }

  // ── Restore previously checked milestones ────────────────────
  function restoreMilestones() {
    const saved = loadMilestones();
    document.querySelectorAll('.milestone-item').forEach(item => {
      const key = item.textContent.trim();
      if (saved[key]) item.classList.add('done');
    });
    updateProgress();
  }

  // ── Toggle a milestone ────────────────────────────────────────
  window.toggleMilestone = function(el) {
    el.classList.toggle('done');
    const saved = loadMilestones();
    const key = el.textContent.trim();
    saved[key] = el.classList.contains('done');
    saveMilestones(saved);
    updateProgress();
  };

  // ── Calculate and animate progress bar ───────────────────────
  function updateProgress() {
    const all  = document.querySelectorAll('.milestone-item').length;
    const done = document.querySelectorAll('.milestone-item.done').length;
    if (all === 0) return;
    const pct = Math.round((done / all) * 100);
    if (progressBar) progressBar.style.width = pct + '%';
    if (progressPct) progressPct.textContent = pct + '%';
  }

  // ── Generate / regenerate roadmap ────────────────────────────
  generateBtn?.addEventListener('click', async () => {
    const domain = document.getElementById('rmDomain')?.value || '';
    const level  = document.getElementById('rmLevel')?.value || '';
    const goal   = document.getElementById('rmGoal')?.value.trim() || '';
    const hours  = parseInt(document.getElementById('rmHours')?.value) || 0;

    const payload = {};
    if (domain) payload.domain = domain;
    if (level)  payload.experience_level = level;
    if (goal)   payload.career_goal = goal;
    if (hours)  payload.weekly_hours = hours;

    // Show loading
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating…';
    if (loadingEl) loadingEl.style.display = 'block';
    if (contentEl) contentEl.style.display = 'none';
    if (emptyEl)   emptyEl.style.display = 'none';

    try {
      const res = await fetch('/api/generate-roadmap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Generation failed');
      // Reload the page to render the new roadmap via Jinja
      window.location.reload();

    } catch (err) {
      if (loadingEl) loadingEl.style.display = 'none';
      if (contentEl) contentEl.style.display = 'block';
      generateBtn.disabled = false;
      generateBtn.innerHTML = '<i class="bi bi-magic me-1"></i>Regenerate';
      window.showToast?.('Failed to generate roadmap: ' + err.message, 'error');
    }
  });

  // ── Phase collapse chevron rotation ──────────────────────────
  document.querySelectorAll('.phase-toggle').forEach(btn => {
    const target = document.querySelector(btn.dataset.bsTarget);
    if (!target) return;
    target.addEventListener('show.bs.collapse', () => {
      btn.querySelector('i').style.transform = 'rotate(0deg)';
    });
    target.addEventListener('hide.bs.collapse', () => {
      btn.querySelector('i').style.transform = 'rotate(-90deg)';
    });
  });

  // ── Initialise ────────────────────────────────────────────────
  restoreMilestones();

  // If roadmap data exists, show the content area
  if (window.ROADMAP_DATA) {
    if (contentEl) contentEl.style.display = 'block';
    if (emptyEl)   emptyEl.style.display = 'none';
    // Animate progress bar
    setTimeout(updateProgress, 600);
  }

  // ── Roadmap chart (phases doughnut) ──────────────────────────
  const chartCanvas = document.getElementById('roadmapChart');
  if (chartCanvas && window.ROADMAP_DATA?.phases) {
    const phases = window.ROADMAP_DATA.phases;
    const labels = phases.map(p => p.phase);
    const data   = phases.map(p => {
      const weeks = p.weeks?.split('-').map(Number) || [1, 4];
      return (weeks[1] || 4) - (weeks[0] || 1) + 1;
    });

    new Chart(chartCanvas, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: ['rgba(59,130,212,.8)', 'rgba(227,179,65,.8)', 'rgba(46,160,67,.8)'],
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '65%',
        plugins: {
          legend: { position: 'bottom', labels: { color: '#8b949e', boxWidth: 12 } },
        }
      }
    });
  }

});
