from flask import Flask, jsonify, request

app = Flask(__name__)

# Die Tische
TABLES = [
    {"id": 1, "name": "Table A1", "type": "Single", "seats": 1, "floor": "EG", "free": True},
    {"id": 2, "name": "Table A2", "type": "Single", "seats": 1, "floor": "EG", "free": True},
    {"id": 3, "name": "Table A3", "type": "Single", "seats": 1, "floor": "EG", "free": True},
    {"id": 4, "name": "Table A4", "type": "Single", "seats": 1, "floor": "EG", "free": True},
]

# Reservierungen (in-memory, wird beim Serverstart zurückgesetzt — später DB)
RESERVATIONS = []

@app.route("/")
def hello():
    return "DeskBook backend is running 🚀"

@app.route("/api/tables")
def get_tables():
    return jsonify(TABLES)

@app.route("/api/tables/<int:table_id>")
def get_table(table_id):
    table = next((t for t in TABLES if t["id"] == table_id), None)
    if table is None:
        return jsonify({"error": "Table not found"}), 404
    return jsonify(table)

@app.route("/api/reservations", methods=["POST"])
def create_reservation():
    data = request.get_json()
    reservation = {
        "id": len(RESERVATIONS) + 1,
        "table_id": data.get("table_id"),
        "name": data.get("name"),
        "email": data.get("email"),
        "date": data.get("date"),
        "time_slot": data.get("time_slot"),
        "notes": data.get("notes", ""),
    }
    RESERVATIONS.append(reservation)
    return jsonify(reservation), 201

@app.route("/api/reservations")
def get_reservations():
    return jsonify(RESERVATIONS)

from flask import send_from_directory

@app.route("/app")
def serve_app():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)

