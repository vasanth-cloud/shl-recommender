from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from models.schemas import ChatRequest, ChatResponse
from services.intent_router import detect_intent
from services.recommendation_agent import (
    build_recommendations,
    refine_recommendations,
    confirm_recommendations
)
from services.comparison_agent import compare_assessments
from services.refusal_agent import refuse


app = FastAPI(title="SHL Assessment Recommender")


@app.get("/", response_class=HTMLResponse)
def chat_page():
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SHL Assessment Recommender</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f7f9;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #64748b;
      --line: #d9e2ec;
      --brand: #0f766e;
      --brand-dark: #115e59;
      --user: #dcfce7;
      --assistant: #eef2ff;
      --danger: #b91c1c;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }

    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr auto;
      max-width: 1080px;
      margin: 0 auto;
      padding: 20px;
      gap: 14px;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 2px;
    }

    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 750;
      letter-spacing: 0;
    }

    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 14px;
      white-space: nowrap;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 0 4px #dcfce7;
    }

    main {
      min-height: 0;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 16px;
    }

    .chat-panel,
    .side-panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 0;
    }

    .chat-panel {
      display: grid;
      grid-template-rows: 1fr auto;
      overflow: hidden;
    }

    .messages {
      padding: 18px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .message {
      max-width: 82%;
      padding: 12px 14px;
      border-radius: 8px;
      line-height: 1.45;
      font-size: 15px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .message.user {
      align-self: flex-end;
      background: var(--user);
      border: 1px solid #bbf7d0;
    }

    .message.assistant {
      align-self: flex-start;
      background: var(--assistant);
      border: 1px solid #dbe4ff;
    }

    .composer {
      border-top: 1px solid var(--line);
      padding: 14px;
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 10px;
      background: #fbfdff;
    }

    textarea {
      min-height: 48px;
      max-height: 140px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      font: inherit;
      line-height: 1.35;
      outline: none;
    }

    textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px #ccfbf1;
    }

    button {
      border: 0;
      border-radius: 8px;
      padding: 0 16px;
      min-width: 88px;
      font: inherit;
      font-weight: 650;
      cursor: pointer;
      background: var(--brand);
      color: white;
    }

    button:hover { background: var(--brand-dark); }
    button:disabled { opacity: 0.58; cursor: not-allowed; }

    .secondary {
      background: #e2e8f0;
      color: #0f172a;
    }

    .secondary:hover { background: #cbd5e1; }

    .side-panel {
      padding: 16px;
      overflow-y: auto;
    }

    .side-panel h2 {
      margin: 0 0 12px;
      font-size: 16px;
      letter-spacing: 0;
    }

    .hint {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }

    .rec-list {
      display: grid;
      gap: 10px;
    }

    .rec {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfdff;
    }

    .rec a {
      color: var(--brand-dark);
      font-weight: 700;
      text-decoration: none;
    }

    .rec a:hover { text-decoration: underline; }

    .type {
      margin-top: 8px;
      display: inline-flex;
      color: #334155;
      background: #e2e8f0;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
    }

    .error {
      color: var(--danger);
      font-weight: 650;
    }

    @media (max-width: 860px) {
      .shell { padding: 12px; }
      header { align-items: flex-start; flex-direction: column; }
      main { grid-template-columns: 1fr; }
      .side-panel { min-height: 220px; }
      .composer { grid-template-columns: 1fr; }
      button { min-height: 44px; }
      .message { max-width: 94%; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <h1>SHL Assessment Recommender</h1>
      </div>
      <div class="status"><span class="dot"></span><span>Connected to /chat</span></div>
    </header>

    <main>
      <section class="chat-panel" aria-label="Chat">
        <div id="messages" class="messages"></div>
        <form id="form" class="composer">
          <textarea id="input" placeholder="Describe the role, skills, seniority, or ask to compare assessments..." autofocus></textarea>
          <button id="send" type="submit">Send</button>
          <button id="reset" class="secondary" type="button">Reset</button>
        </form>
      </section>

      <aside class="side-panel" aria-label="Recommendations">
        <h2>Recommendations</h2>
        <div id="recommendations" class="hint">Shortlists will appear here after the agent has enough context.</div>
      </aside>
    </main>
  </div>

  <script>
    const messagesEl = document.getElementById("messages");
    const recsEl = document.getElementById("recommendations");
    const form = document.getElementById("form");
    const input = document.getElementById("input");
    const send = document.getElementById("send");
    const reset = document.getElementById("reset");
    const history = [];

    function addMessage(role, content) {
      const node = document.createElement("div");
      node.className = `message ${role}`;
      node.textContent = content;
      messagesEl.appendChild(node);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function renderRecommendations(items) {
      if (!items || items.length === 0) {
        recsEl.className = "hint";
        recsEl.textContent = "No shortlist for this turn.";
        return;
      }

      recsEl.className = "rec-list";
      recsEl.innerHTML = "";
      items.forEach((item, index) => {
        const row = document.createElement("div");
        row.className = "rec";
        row.innerHTML = `
          <a href="${item.url}" target="_blank" rel="noopener">${index + 1}. ${item.name}</a>
          <div class="type">Type: ${item.test_type}</div>
        `;
        recsEl.appendChild(row);
      });
    }

    async function sendMessage(content) {
      history.push({ role: "user", content });
      addMessage("user", content);
      send.disabled = true;

      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: history })
        });

        if (!response.ok) {
          throw new Error(`Request failed with HTTP ${response.status}`);
        }

        const data = await response.json();
        history.push({ role: "assistant", content: data.reply });
        addMessage("assistant", data.reply);
        renderRecommendations(data.recommendations);
      } catch (error) {
        addMessage("assistant", `Error: ${error.message}`);
        recsEl.className = "hint error";
        recsEl.textContent = "The request failed. Check the server logs and try again.";
      } finally {
        send.disabled = false;
        input.focus();
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const content = input.value.trim();
      if (!content) return;
      input.value = "";
      sendMessage(content);
    });

    reset.addEventListener("click", () => {
      history.length = 0;
      messagesEl.innerHTML = "";
      recsEl.className = "hint";
      recsEl.textContent = "Shortlists will appear here after the agent has enough context.";
      input.focus();
    });

    addMessage("assistant", "Hi. Tell me the role you are hiring for, including skills, seniority, and any traits you want to measure.");
  </script>
</body>
</html>
"""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    intent = detect_intent(request.messages)

    if intent == "refuse":
        return refuse()

    if intent == "clarify":
        return {
            "reply": "Sure. What role are you hiring for, and what skills, seniority level, or traits should the assessment measure?",
            "recommendations": [],
            "end_of_conversation": False
        }

    if intent == "compare":
        return compare_assessments(request.messages)

    if intent == "refine":
        return refine_recommendations(request.messages)

    if intent == "confirm":
        return confirm_recommendations(request.messages)

    return build_recommendations(request.messages)
