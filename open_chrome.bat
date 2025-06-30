@echo off
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --kiosk "https://meghavi-kiosk-outlet.onrender.com/shop/67e22caf39c9f87925bea576/RelaxationTherapy" ^
  --disable-notifications ^
  --disable-infobars ^
  --disable-session-crashed-bubble ^
  --no-first-run ^
  --disable-features=TranslateUI,AutofillKeyboa,NotificationTriggers,PermissionPromptDisplayUi ^
  --disable-popup-blocking ^
  --disable-save-password-bubble ^
  --no-default-browser-check ^
  --disable-component-update ^
  --disable-permissions-api ^
  --use-fake-ui-for-media-stream ^
  --autoplay-policy=no-user-gesture-required
