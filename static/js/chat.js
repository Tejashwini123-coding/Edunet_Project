/* ═══════════════════════════════════════════════════════════════
   chat.js – LearnMate AI Chat Interface
   Handles message send/receive, markdown rendering, streaming UX
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  const form       = document.getElementById('chatForm');
  const input      = document.getElementById('chatInput');
  const messages   = document.getElementById('chatMessages');
  const sendBtn    = document.getElementById('sendBtn');
  const typingInd  = document.getElementById('typingIndicator');

  // Configure marked.js for safe markdown rendering
  if (window.marked) {
    marked.setOptions({
      breaks: true,
      gfm: true,
    });
  }

  // ── Render markdown in existing bot bubbles ───────────────────
  function renderExistingBubbles() {
    document.querySelectorAll('.bubble-bot.typed').forEach(bubble => {
      const raw = bubble.dataset.raw || bubble.textContent;
      if (window.marked) {
        bubble.innerHTML = marked.parse(raw);
      }
      bubble.classList.remove('typed');
    });
  }
  renderExistingBubbles();

  // ── Scroll to bottom ─────────────────────────────────────────
  function scrollToBottom(smooth = true) {
    const parent = messages.parentElement;
    parent.scrollTo({
      top: parent.scrollHeight,
      behavior: smooth ? 'smooth' : 'instant',
    });
  }
  scrollToBottom(false);

  // ── Create a message bubble ───────────────────────────────────
  function createBubble(role, content, timestamp = '') {
    const row = document.createElement('div');
    row.className = `msg-row ${role === 'user' ? 'msg-user' : 'msg-bot'}`;

    if (role === 'assistant') {
      row.innerHTML = `
        <div class="msg-avatar-icon"><i class="bi bi-robot"></i></div>
        <div class="msg-bubble bubble-bot"></div>
      `;
    } else {
      // Get avatar colour from sidebar avatar
      const sidebarAvatar = document.getElementById('sidebarAvatar');
      const bg = sidebarAvatar
        ? sidebarAvatar.style.background
        : '#3b82d4';
      const initial = sidebarAvatar
        ? sidebarAvatar.textContent.trim()
        : 'U';
      row.innerHTML = `
        <div class="msg-bubble bubble-user">${escapeHtml(content)}</div>
        <div class="msg-avatar-user" style="background:${bg}">${initial}</div>
      `;
    }

    messages.appendChild(row);
    return row;
  }

  // ── Escape HTML for user messages ────────────────────────────
  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;')
              .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── Type-writer effect for bot responses ─────────────────────
  function typeText(bubbleEl, text, onDone) {
    if (!window.marked) {
      bubbleEl.textContent = text;
      onDone?.();
      return;
    }
    const html = marked.parse(text);
    // Fast render – skip char-by-char for long responses
    bubbleEl.innerHTML = html;
    onDone?.();
  }

  // ── Show / hide typing indicator ────────────────────────────
  function showTyping()  {
    typingInd.style.display = 'flex';
    scrollToBottom();
  }
  function hideTyping()  { typingInd.style.display = 'none'; }

  // ── Send a message ────────────────────────────────────────────
  async function sendMessage(text) {
    if (!text.trim()) return;

    // Disable input
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;

    // Append user bubble
    createBubble('user', text);
    scrollToBottom();
    showTyping();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      hideTyping();

      const botRow = createBubble('assistant', '');
      const bubble = botRow.querySelector('.bubble-bot');
      typeText(bubble, data.reply, () => scrollToBottom());

    } catch (err) {
      hideTyping();
      const botRow = createBubble('assistant', '');
      const bubble = botRow.querySelector('.bubble-bot');
      bubble.innerHTML = `<span style="color:var(--danger)">⚠️ Error: ${err.message}. Please try again.</span>`;
      scrollToBottom();
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  // ── Form submit ───────────────────────────────────────────────
  form?.addEventListener('submit', e => {
    e.preventDefault();
    sendMessage(input.value);
  });

  // ── Enter to send (Shift+Enter for newline) ───────────────────
  input?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input.value);
    }
  });

  // ── Auto-focus input on desktop ───────────────────────────────
  if (window.innerWidth > 768) {
    input?.focus();
  }

});
