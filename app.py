from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import os
import yaml


app = FastAPI()


DEBUG= os.getenv("DEBUG", "false").lower() == "true"
ELEMENT_SERVER_URL = os.getenv("ELEMENT_SERVER_URL", "https://element.example.com")
PORT = int(os.getenv("PORT", 80))


CONFIG_FILE = "config/room_config.yml"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config_data = yaml.safe_load(f)
        ROOM_CONFIGS = {room["id"]: room for room in config_data.get("element_rooms_configs", [])}
else:
    ROOM_CONFIGS = {}

@app.post('/to/{room_id}')
def send_to_element(room_id: str, incoming_data: dict):

    room_config = ROOM_CONFIGS.get(room_id)
    if not room_config:
        return jsonify({"error": "Room not found"}), 404


    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid authorization header"}), 403

    provided_token = auth_header.split(" ")[1]
    if provided_token != room_config["bearer_token"]:
        return jsonify({"error": "Invalid Bearer Token"}), 403


    incoming_data = request.get_json()
    alerts = incoming_data.get("alerts", [])
    message = "🔔 Monitoring\n\n"

    for alert in alerts:
        status = alert.get("status", "")
        labels = alert.get("labels", {})
        severity = labels.get("severity", "")

        if status == "firing":
            symbol = "‼️" if severity == "critical" else "⚠️" if severity == "warning" else "❕"
        else:
            symbol = "✔️"

        description = alert["annotations"].get("description", "")
        summary = alert["annotations"].get("summary", "")
        message += f"{symbol} {summary}\n{description}\n\n"


    headers = {"Content-Type": "application/json"}
    matrix_data = {"msgtype": "m.text", "body": message}
    element_url = f"{ELEMENT_SERVER_URL}/_matrix/client/r0/rooms/{room_config['room_id']}/send/m.room.message?access_token={room_config['access_token']}"

    response = requests.post(element_url, json=matrix_data, headers=headers)

    return jsonify({
        "room_id": room_id,
        "message": message,
        "matrix_response_status": response.status_code
    }), response.status_code

@app.get('/liveness')
def liveness():
    return "OK"

@app.get('/readiness')
def readiness():
    return "OK"
