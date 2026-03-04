# app.py
from flask import Flask, jsonify
from scrape import run

app = Flask(__name__)

@app.route("/scrape")
def scrape_endpoint():
    try:
        data = run()
        return jsonify({"status": "success", "products": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)