const statusDiv = document.createElement("div");
statusDiv.id = "connection-status";
statusDiv.innerHTML = `
  <span class="status-dot"></span>
  <span id="status-text">Checking...</span>
`;
document.body.appendChild(statusDiv);

const statusText = document.getElementById("status-text");
const statusDot = document.querySelector(".status-dot");

const wifiButton = document.createElement("button");
wifiButton.id = "wifi-settings-button";
wifiButton.innerHTML = "📶";
wifiButton.title = "Wi‑Fi Settings";
wifiButton.style.marginLeft = "20px";
wifiButton.style.padding = "4px 6px";
wifiButton.style.fontSize = "22px";
wifiButton.style.background = "none";
wifiButton.style.border = "none";
wifiButton.style.cursor = "pointer";
wifiButton.style.color = "black";

wifiButton.addEventListener("click", () => {
  const modal = document.createElement("div");
  modal.id = "wifi-modal";
  modal.style.position = "fixed";
  modal.style.top = "0";
  modal.style.left = "0";
  modal.style.width = "100%";
  modal.style.height = "100%";
  modal.style.backgroundColor = "rgba(0, 0, 0, 0.6)";
  modal.style.display = "flex";
  modal.style.alignItems = "center";
  modal.style.justifyContent = "center";
  modal.style.zIndex = "1000";

  const modalContent = document.createElement("div");
  modalContent.style.backgroundColor = "#fff";
  modalContent.style.padding = "20px";
  modalContent.style.borderRadius = "10px";
  modalContent.style.boxShadow = "0 0 10px rgba(0, 0, 0, 0.25)";
  modalContent.innerHTML = `
    <h2>Enter Wi-Fi Credentials</h2>
    <label>SSID:</label>
    <input type="text" id="ssid" readonly placeholder="SSID" />

    <label>Password:</label>
    <div style="display: flex; align-items: center;">
      <input type="password" id="password" readonly placeholder="Password" style="flex: 1;" />
      <button id="toggle-password" title="Show/Hide Password" style="margin-left: 5px;">👁️</button>
    </div>

    <br>
    <button id="submit-credentials">Connect</button>
    <button id="cancel-modal">Cancel</button>
    <p id="connect-status" style="font-size: 14px; margin-top: 10px; color: #555;"></p>
  `;

  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  // Input focus tracking
  let focusedInputId = null;
  document.getElementById("ssid").addEventListener("click", () => focusedInputId = "ssid");
  document.getElementById("password").addEventListener("click", () => focusedInputId = "password");

  // Toggle password visibility
  document.getElementById("toggle-password").addEventListener("click", () => {
    const pwdInput = document.getElementById("password");
    pwdInput.type = pwdInput.type === "password" ? "text" : "password";
  });

  // Add keyboard
  const keyboard = createQwertyKeyboard(() => focusedInputId);
  modalContent.appendChild(keyboard);

  // Cancel
  document.getElementById("cancel-modal").addEventListener("click", () => {
    document.body.removeChild(modal);
  });

  // Submit (Connect)
  document.getElementById("submit-credentials").addEventListener("click", () => {
    const ssid = document.getElementById("ssid").value;
    const password = document.getElementById("password").value;
    const statusMsg = document.getElementById("connect-status");
    statusMsg.innerHTML = "🔄 Connecting...";
    statusMsg.style.color = "#333";

    fetch("http://127.0.0.1:5050/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ssid, password })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          statusMsg.style.color = "green";
          statusMsg.innerHTML = "✅ Connected Successfully";
        } else {
          statusMsg.style.color = "red";
          statusMsg.innerHTML = "❌ Failed to Connect";
        }
        setTimeout(() => document.body.contains(modal) && document.body.removeChild(modal), 3000);
      })
      .catch(err => {
        statusMsg.style.color = "red";
        statusMsg.innerHTML = "❌ Error: " + err.message;
      });
  });
});

function updateConnectionStatus() {
  if (navigator.onLine) {
    statusText.textContent = "Online";
    statusDot.classList.add("online");
    statusDot.classList.remove("offline");
    if (wifiButton && wifiButton.parentElement) wifiButton.remove();
  } else {
    statusText.textContent = "Offline";
    statusDot.classList.add("offline");
    statusDot.classList.remove("online");
    if (!document.getElementById("wifi-settings-button")) {
      statusDiv.appendChild(wifiButton);
    }
  }
}

window.addEventListener("online", updateConnectionStatus);
window.addEventListener("offline", updateConnectionStatus);
updateConnectionStatus();


// =============================
// QWERTY On-Screen Keyboard
// =============================
function createQwertyKeyboard(getFocusedInputId) {
  let isCapsLock = false;
  let showSymbols = false;

  const rowsAlpha = [
    ['q','w','e','r','t','y','u','i','o','p'],
    ['a','s','d','f','g','h','j','k','l'],
    ['caps','z','x','c','v','b','n','m','backspace'],
    ['123','space','clear','symbols']
  ];

  const rowsNumbers = [
    ['1','2','3','4','5','6','7','8','9','0'],
    ['-','=','_','+','(',')','[',']','\\'],
    ['!','@','#','$','%','^','&','*','backspace'],
    ['abc','space','clear','symbols']
  ];

  const keyboardDiv = document.createElement("div");
  keyboardDiv.className = "keyboard";

  function render() {
    keyboardDiv.innerHTML = "";
    const rows = showSymbols ? rowsNumbers : rowsAlpha;

    rows.forEach(row => {
      const rowDiv = document.createElement("div");
      rowDiv.className = "keyboard-row";

      row.forEach(key => {
        const btn = document.createElement("button");

        // Label
        if (key === "space") btn.textContent = "␣";
        else if (key === "backspace") btn.textContent = "⌫";
        else if (key === "clear") btn.textContent = "🧹";
        else if (key === "caps") btn.textContent = "⇪";
        else if (key === "symbols") btn.textContent = "@#";
        else if (key === "abc") btn.textContent = "abc";
        else if (key === "123") btn.textContent = "123";
        else btn.textContent = isCapsLock && key.length === 1 ? key.toUpperCase() : key;

        // Action
        btn.addEventListener("click", () => {
          const inputId = getFocusedInputId();
          if (!inputId) return;
          const input = document.getElementById(inputId);

          switch (key) {
            case "backspace":
              input.value = input.value.slice(0, -1);
              break;
            case "space":
              input.value += " ";
              break;
            case "clear":
              input.value = "";
              break;
            case "caps":
              isCapsLock = !isCapsLock;
              render();
              break;
            case "symbols":
              showSymbols = true;
              render();
              break;
            case "abc":
              showSymbols = false;
              render();
              break;
            case "123":
              showSymbols = true;
              render();
              break;
            default:
              input.value += isCapsLock && key.length === 1 ? key.toUpperCase() : key;
          }
        });

        rowDiv.appendChild(btn);
      });

      keyboardDiv.appendChild(rowDiv);
    });
  }

  render();
  return keyboardDiv;
}
