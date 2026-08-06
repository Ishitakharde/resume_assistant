let sessionId = null;

const uploadBtn = document.getElementById("upload-btn");
const uploadStatus = document.getElementById("upload-status");
const setupPanel = document.getElementById("setup-panel");
const chatPanel = document.getElementById("chat-panel");
const messagesEl = document.getElementById("messages");
const chatText = document.getElementById("chat-text");
const sendBtn = document.getElementById("send-btn");

uploadBtn.addEventListener("click", async () => {
  const fileInput = document.getElementById("resume-file");
  const jd = document.getElementById("jd-text").value;

  if (!fileInput.files.length) {
    uploadStatus.textContent = "Please choose a resume file first.";
    return;
  }

  const formData = new FormData();
  formData.append("resume", fileInput.files[0]);
  formData.append("job_description", jd);

  uploadStatus.textContent = "Parsing resume...";

  try {
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      uploadStatus.textContent = "Error: " + data.error;
      return;
    }

    sessionId = data.session_id;
    uploadStatus.textContent = "Loaded. Preview:\n" + data.resume_preview;
    chatPanel.classList.remove("hidden");
    addMessage("assistant", "Resume loaded. Ask me anything about it, or use a quick action below.");
  } catch (err) {
    uploadStatus.textContent = "Upload failed: " + err.message;
  }
});

sendBtn.addEventListener("click", sendMessage);
chatText.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

document.querySelectorAll(".quick-actions button").forEach((btn) => {
  btn.addEventListener("click", () => {
    chatText.value = btn.dataset.q;
    sendMessage();
  });
});

async function sendMessage() {
  const message = chatText.value.trim();
  if (!message || !sessionId) return;

  addMessage("user", message);
  chatText.value = "";

  const thinkingId = addMessage("assistant", "Thinking...");

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    const data = await res.json();
    updateMessage(thinkingId, res.ok ? data.reply : "Error: " + data.error);
  } catch (err) {
    updateMessage(thinkingId, "Request failed: " + err.message);
  }
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  div.id = "msg-" + Date.now() + Math.random().toString(36).slice(2);
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div.id;
}

function updateMessage(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
