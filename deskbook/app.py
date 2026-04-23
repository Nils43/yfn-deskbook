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

if __name__ == "__main__":
    app.run(debug=True, port=5000)