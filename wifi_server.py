
from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ Add this
import subprocess
import os
import datetime

app = Flask(__name__)
CORS(app)  # ✅ Allow requests from your Chrome extension


def log(content):
    with open(os.path.expanduser("~\\wifi_connect_log.txt"), "a") as f:
        f.write(f"[{datetime.datetime.now()}] {content}\n")

@app.route("/connect", methods=["POST"])
def connect():
    data = request.json
    ssid = data.get("ssid", "")
    password = data.get("password", "")

    profile = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig><SSID><name>{ssid}</name></SSID></SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>'''

    path = os.path.join(os.getenv("TEMP"), "wifi_profile.xml")
    with open(path, "w") as f:
        f.write(profile)

    add_result = subprocess.run(["netsh", "wlan", "add", "profile", f"filename={path}"],
                                capture_output=True, text=True)
    connect_result = subprocess.run(["netsh", "wlan", "connect", f"name={ssid}"],
                                    capture_output=True, text=True)

    log("SSID: " + ssid)
    log("Add: " + add_result.stdout + add_result.stderr)
    log("Connect: " + connect_result.stdout + connect_result.stderr)

    success = "completed successfully" in connect_result.stdout.lower()
    return jsonify({"success": success})

if __name__ == "__main__":
    app.run(port=5050)
