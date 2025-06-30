from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/url_matched', methods=['POST'])
def url_matched():
    data = request.get_json()
    status = data.get("status")
    url = data.get("url")
    
    if status == "entered":
        print(f"✅ User ENTERED target page: {url}")
    elif status == "left":
        print(f"🚪 User LEFT target page. Now on: {url}")
    else:
        print(f"⚠️ Unknown status: {data}")
        
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    app.run(port=5000)

