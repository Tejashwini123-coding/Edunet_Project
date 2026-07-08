/* ═══════════════════════════════════════════════════════════════
   main.js – LearnMate global JavaScript
   Sidebar toggle, dark/light theme, global helpers
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Theme toggle ─────────────────────────────────────────────
  const THEME_KEY = 'lm_theme';
  const htmlEl    = document.documentElement;
  const themeBtn  = document.getElementById('themeToggle');
  const themeIcon = document.getElementById('themeIcon');

  function applyTheme(theme) {
    htmlEl.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    if (themeIcon) {
      themeIcon.className = theme === 'dark'
        ? 'bi bi-moon-stars-fill'
        : 'bi bi-sun-fill';
    }
  }

  const savedTheme = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(savedTheme);

  themeBtn?.addEventListener('click', () => {
    const current = htmlEl.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });

  // ── Sidebar open / close ─────────────────────────────────────
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebarOverlay');
  const openBtn  = document.getElementById('sidebarOpen');
  const closeBtn = document.getElementById('sidebarClose');

  function openSidebar() {
    sidebar?.classList.add('open');
    overlay?.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('open');
    document.body.style.overflow = '';
  }

  openBtn?.addEventListener('click', openSidebar);
  closeBtn?.addEventListener('click', closeSidebar);
  overlay?.addEventListener('click', closeSidebar);

  // Close on wide screens when nav link clicked
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 992) closeSidebar();
    });
  });

  // ── Auto-resize textareas ─────────────────────────────────────
  document.querySelectorAll('textarea').forEach(ta => {
    function resize() {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
    }
    ta.addEventListener('input', resize);
  });

  // ── Char counter for chat input ───────────────────────────────
  const chatInput = document.getElementById('chatInput');
  const charCount = document.getElementById('charCount');
  if (chatInput && charCount) {
    chatInput.addEventListener('input', () => {
      const len = chatInput.value.length;
      charCount.textContent = `${len}/2000`;
      charCount.style.color = len > 1800 ? 'var(--danger)' : '';
    });
  }

  // ── Fetch progress stats and update sidebar streak ────────────
  fetch('/api/progress')
    .then(r => r.json())
    .then(data => {
      const streakEl = document.getElementById('sidebarStreak');
      if (streakEl) streakEl.textContent = data.streak || 0;
      const statStreak = document.getElementById('statStreak');
      if (statStreak) statStreak.textContent = data.streak || 0;
    })
    .catch(() => {});

  // ── Utility: show toast notification ────────────────────────
  window.showToast = function(message, type = 'info') {
    const container = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    const colorMap = {
      success: 'var(--success)',
      error:   'var(--danger)',
      warning: 'var(--warning)',
      info:    'var(--accent)',
    };
    toast.style.cssText = `
      background: var(--surface);
      border: 1px solid ${colorMap[type] || colorMap.info};
      border-left: 4px solid ${colorMap[type] || colorMap.info};
      border-radius: 10px;
      padding: 12px 18px;
      font-size: 13px;
      color: var(--text);
      box-shadow: var(--shadow);
      animation: fadeSlideUp .3s ease both;
      max-width: 340px;
    `;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  };

  function createToastContainer() {
    const div = document.createElement('div');
    div.id = 'toastContainer';
    div.style.cssText = `
      position: fixed; bottom: 20px; right: 20px;
      display: flex; flex-direction: column; gap: 8px; z-index: 9999;
    `;
    document.body.appendChild(div);
    return div;
  }

  // ── Bookmark buttons (dynamic) ────────────────────────────────
  document.querySelectorAll('[data-bookmark]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const course = btn.dataset.bookmark;
      const res = await fetch('/api/bookmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ course }),
      });
      const data = await res.json();
      showToast(data.action === 'added'
        ? `📌 Bookmarked: ${course}`
        : `🗑️ Removed bookmark: ${course}`, 'success');
      btn.classList.toggle('active', data.action === 'added');
    });
  });

});
