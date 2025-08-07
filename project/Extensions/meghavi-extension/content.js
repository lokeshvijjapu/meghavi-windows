const targetUrl = "https://outlet.meghaviwellness.co.in/shop/RelaxationTherapy";

if (window.location.href === targetUrl) {
  chrome.runtime.sendMessage({ action: "matched_url", url: window.location.href });
}
