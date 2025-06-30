const statusDiv = document.createElement("div");
statusDiv.id = "connection-status";
statusDiv.innerHTML = `
  <span class="status-dot"></span>
  <span id="status-text">Checking...</span>
`;
document.body.appendChild(statusDiv);

const statusText = document.getElementById("status-text");
const statusDot = document.querySelector(".status-dot");

function updateConnectionStatus() {
  if (navigator.onLine) {
    statusText.textContent = "Online";
    statusDot.classList.add("online");
    statusDot.classList.remove("offline");
  } else {
    statusText.textContent = "Offline";
    statusDot.classList.add("offline");
    statusDot.classList.remove("online");
  }
}

window.addEventListener("online", updateConnectionStatus);
window.addEventListener("offline", updateConnectionStatus);
updateConnectionStatus();
