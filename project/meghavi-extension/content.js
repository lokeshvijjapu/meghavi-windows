const targetUrl = "https://meghavi-kiosk-outlet.onrender.com/shop/67e22caf39c9f87925bea576/RelaxationTherapy";

if (window.location.href === targetUrl) {
  chrome.runtime.sendMessage({ action: "matched_url", url: window.location.href });
}
