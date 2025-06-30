const targetUrl = "https://meghavi-kiosk-outlet.onrender.com/shop/67e22caf39c9f87925bea576/RelaxationTherapy";

// ⏱️ Change this to control how often "left" signals are sent (in milliseconds)
const CHECK_INTERVAL_MS = 2000;

let isOnTarget = false;

setInterval(() => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return;
    const currentUrl = tabs[0].url;

    if (currentUrl === targetUrl) {
      if (!isOnTarget) {
        isOnTarget = true;
        sendStatus("entered", currentUrl);
      }
    } else {
      if (isOnTarget) {
        isOnTarget = false;
      }
      // Send repeated "left" signals
      sendStatus("left", currentUrl);
    }
  });
}, CHECK_INTERVAL_MS);

function sendStatus(status, url) {
  fetch("http://127.0.0.1:5000/url_matched", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, url })
  })
  .then(res => res.text())
  .then(data => console.log(`[${status}] Sent to Flask:`, data))
  .catch(err => console.error("Error sending to Flask:", err));
}
