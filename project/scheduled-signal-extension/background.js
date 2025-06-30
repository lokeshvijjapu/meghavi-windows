function createAlarms() {
  // 5:00 AM alarm
  chrome.alarms.create("fiveAM", {
    when: Date.now() + getDelayUntilHour(5),
    periodInMinutes: 1440 // 24 hours
  });

  // 10:00 PM alarm
  chrome.alarms.create("tenPM", {
    when: Date.now() + getDelayUntilHour(22),
    periodInMinutes: 1440 // 24 hours
  });
}

function getDelayUntilHour(targetHour) {
  const now = new Date();
  const target = new Date();
  target.setHours(targetHour, 0, 0, 0);
  if (target <= now) {
    target.setDate(target.getDate() + 1); // schedule for next day
  }
  return target.getTime() - now.getTime();
}

// Set up alarms when extension is installed or reloaded
chrome.runtime.onInstalled.addListener(() => {
  createAlarms();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "fiveAM" || alarm.name === "tenPM") {
    fetch("http://127.0.0.1:5001/trigger-download", {
      method: "POST"
    })
    .then(res => res.text())
    .then(data => console.log(`[${alarm.name}] Signal sent to Flask:`, data))
    .catch(err => console.error(`[${alarm.name}] Signal failed:`, err));
  }
});

