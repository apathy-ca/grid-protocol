import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

GRID_SERVER_URL = os.environ.get("GRID_SERVER_URL")

@app.route("/resource", methods=["POST"])
def access_resource():
    auth_request = {
        "input": {
            "principal": request.json.get("principal"),
            "action": {"operation": "access"},
            "resource": {"id": "protected-resource"}
        }
    }

    try:
        response = requests.post(GRID_SERVER_URL, json=auth_request)
        response.raise_for_status()
        decision = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

    if decision.get("result", False):
        return jsonify({"message": "Access granted"}), 200
    else:
        return jsonify({"message": "Access denied"}), 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)