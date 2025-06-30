chrome.runtime.onStartup.addListener(() => {
  chrome.tabs.create({ url: "https://meghavi-kiosk-outlet.onrender.com/shop/67e22caf39c9f87925bea576/RelaxationTherapy" }, function (tab) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        // Wait for the page to load before injecting
        window.addEventListener('load', () => {
          // Create a fullscreen button
          let btn = document.createElement("button");
          btn.innerText = "Enter Fullscreen";
          btn.style.position = "fixed";
          btn.style.top = "40%";
          btn.style.left = "40%";
          btn.style.padding = "20px";
          btn.style.fontSize = "24px";
          btn.style.zIndex = "999999";
          btn.style.cursor = "pointer";
          btn.onclick = () => {
            document.documentElement.requestFullscreen().catch(err => console.log(err));
          };
          document.body.appendChild(btn);

          // Try clicking the button programmatically (may be blocked depending on context)
          setTimeout(() => {
            btn.click();
          }, 100); // small delay
        });
      }
    });
  });
});
