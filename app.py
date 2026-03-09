# app.py
from flask import Flask, jsonify
from scrape import run
from sheets import save_to_sheets

app = Flask(__name__)

@app.route("/scrape")
def scrape_endpoint():
    try:
        data = run()
        if data:
            rows_saved = save_to_sheets(data)
            return jsonify({
                "status": "success",
                "products_scraped": len(data),
                "rows_saved_to_sheets": rows_saved
            })
        else:
            return jsonify({
                "status": "success",
                "products_scraped": 0,
                "message": "No products found."
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
