from flask import Flask, jsonify

app = Flask(__name__)

# Die Tische (erstmal hardgecoded, später kommt die DB)
TABLES = [
    {"id": 1, "name": "Table A1", "type": "Single", "seats": 1, "floor": "EG", "free": True},
    {"id": 2, "name": "Table A2", "type": "Single", "seats": 1, "floor": "EG", "free": True},
    {"id": 3, "name": "Table A3", "type": "Single", "seats": 1, "floor": "EG", "free": True},
    {"id": 4, "name": "Table A4", "type": "Single", "seats": 1, "floor": "EG", "free": True},
]

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

if __name__ == "__main__":
    app.run(debug=True, port=5000)