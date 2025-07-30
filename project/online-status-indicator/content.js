const statusDiv = document.createElement("div");
statusDiv.id = "connection-status";
statusDiv.innerHTML = `
  <span class="status-dot"></span>
  <span id="status-text">Checking...</span>
`;
document.body.appendChild(statusDiv);

const statusText = document.getElementById("status-text");
const statusDot = document.querySelector(".status-dot");

// Create Wi-Fi settings button
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
  window.location.href = "ms-settings:network-wifi";
});

function updateConnectionStatus() {
  if (navigator.onLine) {
    statusText.textContent = "Online";
    statusDot.classList.add("online");
    statusDot.classList.remove("offline");

    // Hide Wi-Fi button when online
    if (wifiButton && wifiButton.parentElement) {
      wifiButton.remove();
    }
  } else {
    statusText.textContent = "Offline";
    statusDot.classList.add("offline");
    statusDot.classList.remove("online");

    // Show Wi-Fi button only if not already shown
    if (!document.getElementById("wifi-settings-button")) {
      statusDiv.appendChild(wifiButton);
    }
  }
}

window.addEventListener("online", updateConnectionStatus);
window.addEventListener("offline", updateConnectionStatus);
updateConnectionStatus();
