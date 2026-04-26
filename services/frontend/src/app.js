"use strict";

const LS_API_KEY    = "erp_assistant_api_key";
const SS_SESSION_ID = "erp_assistant_session_id";
const API_BASE      = "/api";

let isLoading = false;

function generateId() {
  return crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
}

function getApiKey() {
  const stored = localStorage.getItem(LS_API_KEY);
  if (stored && stored.trim()) return stored.trim();
  if (window.APP_CONFIG && window.APP_CONFIG.defaultApiKey) {
    return window.APP_CONFIG.defaultApiKey;
  }
  return "";
}

function getSessionId() {
  let sid = sessionStorage.getItem(SS_SESSION_ID);
  if (!sid) {
    sid = generateId();
    sessionStorage.setItem(SS_SESSION_ID, sid);
  }
  return sid;
}

function newSession() {
  const sid = generateId();
  sessionStorage.setItem(SS_SESSION_ID, sid);
  updateSessionDisplay(sid);
  clearMessages();
  showWelcome(true);
}

function updateSessionDisplay(sid) {
  const el = document.getElementById("session-display");
  if (el) el.textContent = `Sesión: ${sid.slice(0, 8)}…`;
}

function showWelcome(show) {
  const el = document.getElementById("welcome");
  if (el) el.style.display = show ? "flex" : "none";
}

function clearMessages() {
  const container = document.getElementById("messages-container");
  if (container) container.innerHTML = "";
}

function scrollToBottom() {
  const area = document.getElementById("chat-area");
  if (area) area.scrollTop = area.scrollHeight;
}

function renderAssistantBubble(text, toolCalls = [], isError = false) {
  const bubble = document.createElement("div");
  bubble.className = isError ? "bubble error" : "bubble";

  const textEl = document.createElement("div");
  textEl.className = "bubble-text";
  textEl.textContent = text;
  bubble.appendChild(textEl);

  if (!isError && toolCalls && toolCalls.length > 0) {
    const toolsEl = document.createElement("div");
    toolsEl.className = "tool-calls";
    toolCalls.forEach((name) => {
      const badge = document.createElement("span");
      badge.className = "tool-badge";
      badge.textContent = name;
      toolsEl.appendChild(badge);
    });
    bubble.appendChild(toolsEl);
  }

  return bubble;
}

function appendMessage(role, text, toolCalls = [], isError = false) {
  const container = document.getElementById("messages-container");
  if (!container) return;

  const msg = document.createElement("div");
  msg.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "Tú" : "AI";

  let bubble;
  if (role === "user") {
    bubble = document.createElement("div");
    bubble.className = "bubble";
    const textEl = document.createElement("div");
    textEl.className = "bubble-text";
    textEl.textContent = text;
    bubble.appendChild(textEl);
  } else {
    bubble = renderAssistantBubble(text, toolCalls, isError);
  }

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  container.appendChild(msg);
  scrollToBottom();
  return msg;
}

function showLoadingIndicator() {
  const container = document.getElementById("messages-container");
  if (!container) return null;

  const msg = document.createElement("div");
  msg.className = "message assistant loading";
  msg.id = "loading-msg";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const dots = document.createElement("div");
  dots.className = "dots";
  dots.innerHTML = "<span></span><span></span><span></span>";

  const label = document.createElement("span");
  label.textContent = "Consultando el ERP…";

  bubble.appendChild(dots);
  bubble.appendChild(label);
  msg.appendChild(avatar);
  msg.appendChild(bubble);
  container.appendChild(msg);
  scrollToBottom();
  return msg;
}

function removeLoadingIndicator() {
  const el = document.getElementById("loading-msg");
  if (el) el.remove();
}

async function sendQuery(query) {
  const apiKey = getApiKey();
  if (!apiKey) {
    openSettings();
    return;
  }

  const sessionId = getSessionId();

  isLoading = true;
  updateSendButton();
  showWelcome(false);
  appendMessage("user", query);
  showLoadingIndicator();

  try {
    const response = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify({ query, session_id: sessionId }),
    });

    removeLoadingIndicator();

    if (!response.ok) {
      let errorDetail = `Error ${response.status}`;
      try {
        const errData = await response.json();
        errorDetail = errData.detail || errorDetail;
      } catch {}
      appendMessage("assistant", errorDetail, [], true);
      return;
    }

    const data = await response.json();

    if (data.session_id && data.session_id !== sessionId) {
      sessionStorage.setItem(SS_SESSION_ID, data.session_id);
      updateSessionDisplay(data.session_id);
    }

    appendMessage("assistant", data.answer, data.tool_calls_made || [], data.error);

  } catch (err) {
    removeLoadingIndicator();
    appendMessage(
      "assistant",
      "No se pudo contactar con el servidor. Verifica que el stack esté corriendo.",
      [],
      true
    );
    console.error("[app] Error de red:", err);
  } finally {
    isLoading = false;
    updateSendButton();
  }
}

function updateSendButton() {
  const btn = document.getElementById("send-btn");
  const input = document.getElementById("query-input");
  if (!btn || !input) return;
  btn.disabled = isLoading || !input.value.trim().length;
}

function autoResizeTextarea() {
  const textarea = document.getElementById("query-input");
  if (!textarea) return;
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 140) + "px";
}

function openSettings() {
  const overlay = document.getElementById("settings-overlay");
  const input   = document.getElementById("api-key-input");
  if (overlay) overlay.classList.remove("hidden");
  if (input) {
    input.value = getApiKey();
    setTimeout(() => input.focus(), 50);
  }
}

function closeSettings() {
  const overlay = document.getElementById("settings-overlay");
  if (overlay) overlay.classList.add("hidden");
}

function saveSettings() {
  const input = document.getElementById("api-key-input");
  if (!input) return;
  const key = input.value.trim();
  if (key) {
    localStorage.setItem(LS_API_KEY, key);
  } else {
    localStorage.removeItem(LS_API_KEY);
  }
  closeSettings();
}

function init() {
  const sessionId = getSessionId();
  updateSessionDisplay(sessionId);

  if (!getApiKey() || getApiKey() === "change-me-before-going-to-production") {
    openSettings();
  }

  const input = document.getElementById("query-input");
  if (input) {
    input.addEventListener("input", () => {
      autoResizeTextarea();
      updateSendButton();
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
  }

  document.getElementById("send-btn")?.addEventListener("click", handleSend);

  document.getElementById("new-session-btn")?.addEventListener("click", () => {
    if (confirm("¿Iniciar una nueva sesión? Se perderá el historial de esta conversación.")) {
      newSession();
    }
  });

  document.getElementById("open-settings-btn")?.addEventListener("click", openSettings);
  document.getElementById("close-settings")?.addEventListener("click", closeSettings);
  document.getElementById("save-settings")?.addEventListener("click", saveSettings);
  document.getElementById("settings-overlay")?.addEventListener("click", (e) => {
    if (e.target.id === "settings-overlay") closeSettings();
  });
  document.getElementById("api-key-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveSettings();
    if (e.key === "Escape") closeSettings();
  });

  document.querySelectorAll(".suggestion-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const query = chip.dataset.query;
      if (!query) return;
      const inputEl = document.getElementById("query-input");
      if (inputEl) {
        inputEl.value = query;
        autoResizeTextarea();
        updateSendButton();
        inputEl.focus();
      }
    });
  });

  updateSendButton();
}

function handleSend() {
  if (isLoading) return;
  const input = document.getElementById("query-input");
  if (!input) return;
  const query = input.value.trim();
  if (!query) return;

  input.value = "";
  autoResizeTextarea();
  updateSendButton();
  sendQuery(query);
}

document.addEventListener("DOMContentLoaded", init);
