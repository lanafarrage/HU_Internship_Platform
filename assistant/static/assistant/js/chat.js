(function () {
  const root = document.querySelector(".chat");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");
  const log = document.getElementById("chat-log");
  const errorBox = document.getElementById("chat-error");
  const clearBtn = document.getElementById("clear-chat");
  const csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;

  function scrollDown() { log.scrollTop = log.scrollHeight; }

  function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = "msg msg-" + role;
    div.textContent = text;            // textContent: never interprets HTML
    log.appendChild(div);
    scrollDown();
    return div;
  }

  function showError(text) {
    errorBox.textContent = text;
    errorBox.hidden = !text;
  }

  async function post(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: JSON.stringify(body || {}),
    });
    if (res.redirected) {              // session expired: Django sent us to login
      window.location.href = res.url;
      return null;
    }
    let data = {};
    try { data = await res.json(); } catch (e) { /* not JSON */ }
    return { ok: res.ok, data: data };
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    showError("");
    addMessage("user", text);
    input.value = "";
    sendBtn.disabled = true;
    const typing = addMessage("assistant", "Thinking...");
    typing.classList.add("msg-typing");

    try {
      const result = await post(root.dataset.askUrl, { message: text });
      typing.remove();
      if (!result) return;
      if (result.ok && result.data.reply) {
        addMessage("assistant", result.data.reply);
      } else {
        showError(result.data.error || "Something went wrong. Please try again.");
      }
    } catch (e) {
      typing.remove();
      showError("Network problem. Please check your connection and try again.");
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  });

  // Enter sends, Shift+Enter makes a new line
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  clearBtn.addEventListener("click", async function () {
    const result = await post(root.dataset.clearUrl);
    if (result && result.ok) {
      log.innerHTML = "";
      addMessage("assistant", "Chat cleared. How can I help?");
      showError("");
    }
  });

  scrollDown();
})();