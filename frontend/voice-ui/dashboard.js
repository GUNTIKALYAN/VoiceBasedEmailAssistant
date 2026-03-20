/* ═══════════════════════════════════════════
   VoxMail · dashboard.js
   Full app logic — voice, panels, log, nav
═══════════════════════════════════════════ */

const BASE = "http://127.0.0.1:8000";

/* ── State ── */
const S = {
  recording: false,
  abortCtrl: null,
  panelOpen: false,
  sidebarOpen: false,
  inbox: [],
};

/* ═══════════════════════════
   WAVEFORM
═══════════════════════════ */
function buildWave() {
  const c = document.getElementById("waveBars");
  if (!c) return;
  for (let i = 0; i < 58; i++) {
    const b = document.createElement("div");
    b.className = "w-bar";
    b.style.setProperty("--spd", (0.3 + Math.random() * 0.65).toFixed(2) + "s");
    b.style.setProperty("--dly", (Math.random() * 0.55).toFixed(2) + "s");
    c.appendChild(b);
  }
}

/* ═══════════════════════════
   STATUS
═══════════════════════════ */
function setStatus(label, live = false) {
  const orb = document.getElementById("statusOrb");
  const txt = document.getElementById("statusTxt");
  const lorb = document.getElementById("logOrb");
  const nliv = document.getElementById("navLive");

  if (orb) orb.className = "status-orb" + (live ? " on" : "");
  if (txt) txt.textContent = label;
  if (lorb) lorb.className = "log-orb" + (live ? " on" : "");
  if (nliv) nliv.className = "nav-live" + (live ? " on" : "");
}

/* ═══════════════════════════
   LOG
═══════════════════════════ */
function log(type, msg) {
  const feed = document.getElementById("logFeed");
  const empty = document.getElementById("logEmpty");
  if (!feed) return;
  if (empty) empty.remove();

  const now = new Date();
  const ts = now.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const MAP = {
    user: { cls: "you", label: "You" },
    sys: { cls: "sys", label: "Sys" },
    error: { cls: "err", label: "Err" },
    // wa:    { cls: "wa",  label: "WA"  }
  };

  const B = MAP[type] || MAP.sys;

  const el = document.createElement("div");
  el.className = "log-entry";
  el.innerHTML = `
    <span class="le-tag ${B.cls}">${B.label}</span>
    <div class="le-body">
      <div class="le-ts">${ts}</div>
      <div class="le-text ${type === "sys" ? "hi" : ""}">${msg.replace(/\n/g, "<br>")}</div>
    </div>`;

  feed.appendChild(el);

  feed.scrollTop = feed.scrollHeight;
}

async function fetchLogs() {
  if (!S.recording) return;

  try {
    const res = await fetch(BASE + "/logs");
    const data = await res.json();

    if (!data.logs || data.logs.length === 0) return;

    data.logs.forEach((entry) => {
      if (entry.type === "user") {
        log("user", entry.text);
      } else {
        log("sys", entry.text);
      }
    });
  } catch {
    log("error", "Log stream failed.");
  }
}

function clearLog() {
  const feed = document.getElementById("logFeed");
  if (!feed) return;
  while (feed.firstChild) feed.removeChild(feed.firstChild);

  const empty = document.createElement("div");
  empty.className = "log-empty";
  empty.id = "logEmpty";
  empty.innerHTML = `
    <span class="empty-glyph">◌</span>
    <p>No activity yet — tap the mic or type a command.</p>`;
  feed.appendChild(empty);
}

/* ═══════════════════════════
   PANEL
═══════════════════════════ */
function openPanel(title, html) {
  document.getElementById("panelTitle").textContent = title;
  document.getElementById("panelBody").innerHTML = html;
  document.getElementById("panel").classList.add("show");
  document.getElementById("overlay").classList.add("show");
  S.panelOpen = true;
}

function closePanel() {
  document.getElementById("panel").classList.remove("show");
  document.getElementById("overlay").classList.remove("show");
  S.panelOpen = false;
}

/* ═══════════════════════════
   PANEL HTML BUILDERS
═══════════════════════════ */

function htmlSend() {
  return `
    <div class="tip-box">
      <span class="tip-icon">
        <i class="fa-regular fa-paper-plane"></i>
      </span>
      <div>Say <strong>"Send email to [name] about [topic]"</strong> to auto-fill via voice.</div>
    </div>

    <label class="pf-label">To</label>
    <input class="pf-field" id="pTo" type="email" placeholder="recipient@email.com" />

    <label class="pf-label">CC</label>
    <input class="pf-field" type="email" placeholder="cc@email.com (optional)" />

    <label class="pf-label">Subject</label>
    <input class="pf-field" id="pSubj" type="text" placeholder="Subject line…" />

    <label class="pf-label">Body</label>

    <!-- ✅ MIRROR WRAPPER -->
    <div class="editor-wrapper">

      <!-- 🔥 MIRROR TEXT (shows suggestion) -->
      <div id="mirrorBox"></div>

      <!-- 🔥 ACTUAL INPUT -->
      <textarea 
        class="pf-field" 
        id="pBody" 
        placeholder="Your message…"
      ></textarea>

    </div>

    <button class="pf-btn" onclick="App.doSendEmail()">Send Email ↗</button>
  `;
}

function htmlCompose() {
  return `
    <div class="tip-box">
      <span class="tip-icon">
      <i class="fa-regular fa-pen-to-square"></i>
      </span>
      <div>Say <strong>"Compose email"</strong> then dictate hands-free.</div>
    </div>
    <label class="pf-label">To</label>
    <input  class="pf-field" type="email" placeholder="recipient@email.com" />
    <label class="pf-label">Subject</label>
    <input  class="pf-field" type="text"  placeholder="Subject…" />
    <label class="pf-label">Body</label>
    <textarea class="pf-field" style="min-height:150px" placeholder="Your message…"></textarea>
    <div class="pf-row">
      <button class="pf-btn ghost" onclick="App.log('sys','Draft saved ✓'); App.closePanel()">Save Draft</button>
      <button class="pf-btn"       onclick="App.log('sys','Email queued ✓'); App.closePanel()">Send ↗</button>
    </div>`;
}

async function htmlInbox() {
  try {
    const res = await fetch(BASE + "/emails/primary");
    const data = await res.json();
    const emails = data.emails;
    S.inbox = emails;

    const rows = emails
      .map(
        (m) => `
      <div class="mail-row ${m.unread ? "unread" : ""}">
        <div class="mail-top">
          <div class="mail-sender">
            ${m.unread ? '<span class="mail-pip"></span>' : ""}
            ${m.sender}
          </div>
          <span class="mail-time">${m.time || ""}</span>
        </div>
        <div class="mail-subj">${m.subject}</div>
        <div class="mail-snippet">${m.snippet || ""}</div>
      </div>`,
      )
      .join("");

    return `
      <div class="tip-box">
        <span class="tip-icon">
        <i class="fa-regular fa-envelope-open"></i>
        </span>
        <div>Your latest <strong>primary</strong> emails. Say <strong>"read inbox"</strong> to hear them aloud.</div>
      </div>
      ${rows}`;
  } catch {
    return `<p style="font-size:0.8rem;color:var(--t3);padding:1rem 0">Could not load inbox — backend unreachable.</p>`;
  }
}

function htmlWhatsApp() {
  const cmds = [
    "read inbox",
    "send email to [name]",
    "compose email",
    "search [keyword]",
    "read drafts",
    "reply to [name]",
  ];
  return `
    <div class="tip-box tip-box-wa">
      <span class="tip-icon">
        <svg viewBox="0 0 24 24" fill="#25d366" width="18" height="18">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
      </span>
      <div style="color:var(--t2)">
        Control <strong style="color:var(--wa)">VoxMail</strong> through WhatsApp.
        Send voice commands directly from your phone.
      </div>
    </div>
    <label class="pf-label">Your WhatsApp Number</label>
    <input class="pf-field" type="tel" placeholder="+91 98765 43210" />
    <label class="pf-label">Bot Number</label>
    <input class="pf-field" type="tel" placeholder="+1 555 000 0000" />
    <button
      class="pf-btn"
      style="background:#25d366;color:#fff;margin-bottom:1.25rem"
      onclick="App.doConnectWA()">
      Connect WhatsApp ↗
    </button>
    <label class="pf-label">Available Commands</label>
    ${cmds.map((c) => `<div class="cmd-pill">/ ${c}</div>`).join("")}`;
}

function htmlSearch() {
  return `
    <div class="tip-box">
      <span class="tip-icon">
      <i class="fa-solid fa-magnifying-glass"></i>
      </span>
      <div>Search your inbox by sender name or subject keyword.</div>
    </div>
    <label class="pf-label">Search</label>
    <div class="tts-group" style="margin-bottom:0.9rem;border-radius:var(--r)">
      <input
        class="tts-input"
        id="searchQ"
        type="text"
        placeholder="e.g. Stripe, Project…"
        style="width:100%"
        onkeydown="if(event.key==='Enter') App.runSearch()"
      />
      <button class="tts-btn" onclick="App.runSearch()">
      <i class="fa-solid fa-magnifying-glass"></i>
      </button>
    </div>
    <div id="searchResults"></div>`;
}

/* ═══════════════════════════
   MIC UI
═══════════════════════════ */
function setMicUI(on) {
  const btn = document.getElementById("micBtn");
  const glyph = document.getElementById("micGlyph");
  const bars = document.getElementById("waveBars");
  const sub = document.getElementById("micSub");
  const state = document.getElementById("waveState");

  if (on) {
    btn.classList.add("on");
    glyph.innerHTML = '<i class="fa-solid fa-stop"></i>';
    bars.classList.add("active");
    sub.textContent = "Tap to stop";
    state.textContent = "Listening · speak your command now";
    setStatus("Listening", true);
  } else {
    btn.classList.remove("on");
    glyph.innerHTML = '<i class="fa-solid fa-microphone"></i>';
    bars.classList.remove("active");
    sub.textContent = "Tap to speak";
    state.textContent = "Ready · waiting for input";
    setStatus("Standby", false);
  }
}

/* ═══════════════════════════
   APP OBJECT
═══════════════════════════ */
const App = {
  log,
  closePanel,

  logout() {
    window.location.href = "/auth/logout";
  },

  /* ── Nav click ── */
  navClick(btn) {
    const tool = btn.dataset.tool;

    document
      .querySelectorAll(".nav-btn")
      .forEach((b) => b.classList.remove("active"));

    btn.classList.add("active");

    if (tool === "assistant") {
      App.toggleMic();
      return;
    }

    if (tool === "inbox") {
      htmlInbox().then((html) => openPanel("Primary Inbox", html));
      return;
    }

    if (tool === "send") {
      openPanel("Send Email", htmlSend());

      // 🔥 THIS IS REQUIRED
      setTimeout(() => App.initEmailSuggestions(), 100);

      return;
    }
    if (tool === "compose") {
      openPanel("Compose", htmlCompose());
      return;
    }
    if (tool === "search") {
      openPanel("Search Emails", htmlSearch());
      return;
    }
    if (tool === "whatsapp") {
      openPanel("WhatsApp Access", htmlWhatsApp());
      return;
    }
  },

  /* ── Toggle mic ── */

  toggleMic() {
    if (!S.recording) {
      console.log("Starting assistant...");

      S.recording = true;

      setMicUI(true);
      log("sys", "Assistant started.");

      // 🚀 START BACKEND THREAD
      fetch(BASE + "/voice-loop", { method: "POST" })
        .then(() => console.log("Backend started"))
        .catch(() => log("error", "Failed to start assistant"));

      // 🔁 START LOG STREAM
      if (!S.logInterval) {
        S.logInterval = setInterval(fetchLogs, 600);
      }

      startLogStream();
    } else {
      console.log("Stopping assistant...");

      S.recording = false;

      fetch(BASE + "/assistant-exit", { method: "POST" }).catch(() => {});

      if (S.abortCtrl) {
        S.abortCtrl.abort();
        S.abortCtrl = null;
      }

      if (S.logInterval) {
        clearInterval(S.logInterval);
        S.logInterval = null;
      }

      setMicUI(false);
      log("sys", "Assistant stopped.");
    }
  },

  initEmailSuggestions() {
  const textarea = document.getElementById("pBody");
  const mirrorBox = document.getElementById("mirrorBox");

  if (!textarea || !mirrorBox) return;

  let typingTimer;
  let currentSuggestion = "";

  textarea.addEventListener("input", () => {
    clearTimeout(typingTimer);

    const text = textarea.value;

    // clear mirror immediately while typing
    mirrorBox.innerText = text;

    typingTimer = setTimeout(async () => {

      if (text.length < 5) {
        mirrorBox.innerText = text;
        return;
      }

      const res = await fetch("/email/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();

      const fullSuggestion = data.suggestion || "";

      // 🔥 remove already typed part
      let remaining = fullSuggestion;

      if (fullSuggestion.toLowerCase().startsWith(text.toLowerCase())) {
        remaining = fullSuggestion.slice(text.length);
      }

      const words = remaining.trim().split(" ");

      currentSuggestion = "";
      let i = 0;

      // clear previous animation
      if (window.suggestInterval) {
        clearInterval(window.suggestInterval);
      }

      // 🔥 STREAMING (correct way)
      window.suggestInterval = setInterval(() => {

        if (i >= words.length) {
          clearInterval(window.suggestInterval);
          return;
        }

        currentSuggestion += words[i] + " ";

        // ✅ show typed + suggestion together
        mirrorBox.innerText = textarea.value + currentSuggestion;

        i++;

      }, 80);

    }, 500);
  });


  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Tab" && currentSuggestion) {
      e.preventDefault();

      textarea.value += " " + currentSuggestion.trim();

      currentSuggestion = "";
      mirrorBox.innerText = textarea.value;
    }
  });

  // optional cleanup
  textarea.addEventListener("blur", () => {
    suggestionBox.innerText = "";
    currentSuggestion = "";
  });
},
  // toggleMic() {
  //   if (!S.recording) {
  //     console.log("Starting assistant...");
  //     S.recording = true;
  //     setMicUI(true);
  //     log("sys", "Assistant started.");
  //     if(!S.logInterval){
  //       S.logInterval = setInterval(fetchLogs, 600);
  //     }
  //     startLogStream();
  //     App._voiceLoop();
  //   } else {
  //     S.recording = false;
  //     fetch(BASE + "/assistant-exit", { method: "POST" }).catch(() => {});
  //     if (S.abortCtrl) { S.abortCtrl.abort(); S.abortCtrl = null; }
  //     if(S.logInterval){
  //       clearInterval(S.logInterval);
  //       S.logInterval = null;
  //     }
  //     setMicUI(false);
  //     log("sys", "Assistant stopped.");
  //   }
  // },

  /* ── Voice loop ── */
  // async _voiceLoop() {
  //   if (S.abortCtrl) return;
  //   S.abortCtrl = new AbortController();

  //   try {
  //     const res  = await fetch(BASE + "/voice-loop", {
  //       method: "POST",
  //       signal: S.abortCtrl.signal
  //     });
  //     const data = await res.json();
  //     log("user", `Heard: "${data.recognized_text}"`);
  //     log("sys",  `Response: ${data.response}`);
  //   } catch (err) {
  //     if (err.name !== "AbortError") log("error", "Backend unreachable.");
  //   } finally {
  //     S.abortCtrl = null;
  //   }
  // },

  async _voiceLoop() {
    if (S.abortCtrl) return;

    S.abortCtrl = new AbortController();

    try {
      const res = await fetch(BASE + "/voice-loop", {
        method: "POST",
        signal: S.abortCtrl.signal,
      });

      const data = await res.json();

      // if (data.logs && Array.isArray(data.logs)){

      //   data.logs.forEach(entry => {

      //     if(entry.type === "user"){
      //       log("user",entry.text);
      //     }

      //     else if(entry.type === "sys"){
      //       log("sys",entry.text);
      //     }
      //   });
      // }

      /* 🚨 IMPORTANT FIX */
      if (data.response === "terminated" || data.response === "stopped") {
        S.recording = false;
        setMicUI(false);

        log("sys", "Assistant stopped.");

        return;
      }
    } catch (err) {
      if (err.name !== "AbortError") log("error", "Backend unreachable.");
    } finally {
      S.abortCtrl = null;
    }
  },

  /* ── Command bar ── */
  sendCmd() {
    const inp = document.getElementById("cmdInput");
    const text = (inp?.value || "").trim();
    if (!text) return;
    log("user", text);
    inp.value = "";
    App._processText(text);
  },

  _processText(text) {
    const t = text.toLowerCase();
    if (t.includes("inbox") || t.includes("read")) {
      htmlInbox().then((html) => {
        openPanel("Primary Inbox", html);
        App.readAloud();
      });
    } else if (t.includes("send")) {
      openPanel("Send Email", htmlSend());
      const m = text.match(/to\s+(\S+)/i);
      if (m)
        setTimeout(() => {
          const el = document.getElementById("pTo");
          if (el) el.value = m[1];
        }, 80);
    } else if (t.includes("compose")) {
      openPanel("Compose", htmlCompose());
    } else if (t.includes("search")) {
      openPanel("Search Emails", htmlSearch());
    } else if (t.includes("whatsapp")) {
      openPanel("WhatsApp Access", htmlWhatsApp());
    } else if (t.includes("stop") || t.includes("cancel")) {
      if (S.recording) App.toggleMic();
    } else {
      log("sys", `Processing: "${text}"…`);
      setTimeout(() => log("sys", "Done ✓"), 650);
    }
  },

  /* ── TTS ── */
  async speakText() {
    const inp = document.getElementById("ttsInput");
    const text = (inp?.value || "").trim();
    if (!text) return;
    log("user", `<i class="fa-solid fa-volume-high"></i>  "${text}"`);
    try {
      await fetch(BASE + "/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      log("sys", "Spoken ✓");
    } catch {
      log("error", "Could not reach /speak endpoint.");
    }
    inp.value = "";
  },

  /* ── Send email (panel) ── */
  async doSendEmail() {
    const to = (document.getElementById("pTo")?.value || "").trim();
    const subj = (document.getElementById("pSubj")?.value || "").trim();
    const body = (document.getElementById("pBody")?.value || "").trim();

    if (!to) {
      log("error", "Recipient required.");
      return;
    }

    log("user", `Sending email to: ${to}`);
    try {
      await fetch(BASE + "/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to, subject: subj, body }),
      });
      log("sys", `Email sent to ${to} ✓`);
    } catch {
      log("error", "Send failed — check backend.");
    }
    closePanel();
  },

  /* ── Read inbox aloud ── */
  async readAloud() {
    if (!S.inbox.length) {
      log("error", "No emails loaded.");
      return;
    }
    log("sys", "Reading top 5 emails aloud…");
    setStatus("Reading", true);
    for (let i = 0; i < Math.min(5, S.inbox.length); i++) {
      const m = S.inbox[i];
      const text = `Email ${i + 1}. From ${m.sender}. Subject: ${m.subject}.`;
      log("sys", `📧 ${m.sender} — "${m.subject}"`);
      try {
        await fetch(BASE + "/speak", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
      } catch {
        /* silent */
      }
      await new Promise((r) => setTimeout(r, 800));
    }
    setStatus("Standby", false);
  },

  /* ── Search ── */
  runSearch() {
    const q = (document.getElementById("searchQ")?.value || "").trim();
    const res = document.getElementById("searchResults");
    if (!q || !res) return;

    log("sys", `Searching: "${q}"…`);
    const hits = S.inbox.filter(
      (m) =>
        m.subject.toLowerCase().includes(q.toLowerCase()) ||
        m.sender.toLowerCase().includes(q.toLowerCase()),
    );

    if (hits.length) {
      res.innerHTML = hits
        .map(
          (m) => `
        <div class="mail-row ${m.unread ? "unread" : ""}">
          <div class="mail-top">
            <div class="mail-sender">
              ${m.unread ? '<span class="mail-pip"></span>' : ""}${m.sender}
            </div>
            <span class="mail-time">${m.time || ""}</span>
          </div>
          <div class="mail-subj">${m.subject}</div>
        </div>`,
        )
        .join("");
      log("sys", `${hits.length} result(s) for "${q}" ✓`);
    } else {
      res.innerHTML = `<p style="font-size:0.78rem;color:var(--t3);margin-top:0.6rem">No emails found for "${q}".</p>`;
      log("sys", `No results for "${q}".`);
    }
  },

  /* ── WhatsApp connect ── */
  doConnectWA() {
    log("wa", "Connecting to WhatsApp gateway…");
    setTimeout(() => {
      log("wa", "WhatsApp linked ✓ — send /help to your bot number.");
      closePanel();
    }, 900);
  },

  /* ── Sidebar toggle (mobile) ── */
  toggleSidebar() {
    S.sidebarOpen = !S.sidebarOpen;
    document.getElementById("sidebar").classList.toggle("show", S.sidebarOpen);
  },
};

/* ═══════════════════════════
   USER INFO FROM localStorage
═══════════════════════════ */
function loadUserInfo() {
  if (!window.USER) return;

  const username = window.USER.username;
  const email = window.USER.email;

  const nameEl = document.getElementById("userName");
  const initialEl = document.getElementById("userInitial");
  const emailEl = document.getElementById("userEmail");

  if (nameEl) nameEl.textContent = username;

  if (initialEl && username)
    initialEl.textContent = username.charAt(0).toUpperCase();

  if (emailEl) emailEl.textContent = email;
}

function logout() {
  // stop voice loop
  if (typeof isVoiceRunning !== "undefined") {
    isVoiceRunning = false;
  }

  // redirect → backend handles everything
  window.location.href = "/auth/logout";
}

/* ═══════════════════════════
   INIT
═══════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
  buildWave();
  setStatus("Standby", false);
  loadUserInfo();

  /* Wire clear button */
  document.getElementById("clearBtn").addEventListener("click", clearLog);

  /* Boot message */
  setTimeout(
    () => log("sys", "VoxMail ready. Tap the mic or type a command to begin."),
    500,
  );

  /* Close sidebar on overlay click (mobile, only when no panel open) */
  document.getElementById("overlay").addEventListener("click", () => {
    if (S.panelOpen) return;
    if (S.sidebarOpen) App.toggleSidebar();
  });
});
