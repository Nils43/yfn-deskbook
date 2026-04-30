from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///deskbook.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# --- Models ----------------------------------------------------------------

class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.String(10), nullable=False)
    free = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "seats": self.seats,
            "floor": self.floor,
            "free": self.free,
        }


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey("table.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(500), default="")

    def to_dict(self):
        return {
            "id": self.id,
            "table_id": self.table_id,
            "name": self.name,
            "email": self.email,
            "date": self.date,
            "time_slot": self.time_slot,
            "notes": self.notes,
        }


# --- Routes ----------------------------------------------------------------

@app.route("/")
def hello():
    return "DeskBook backend is running 🚀"


@app.route("/api/tables")
def get_tables():
    tables = Table.query.all()
    return jsonify([t.to_dict() for t in tables])


@app.route("/api/tables/<int:table_id>")
def get_table(table_id):
    table = Table.query.get(table_id)
    if table is None:
        return jsonify({"error": "Table not found"}), 404
    return jsonify(table.to_dict())


@app.route("/api/reservations", methods=["POST"])
def create_reservation():
    data = request.get_json()

    # Sanity check: existiert der Tisch ueberhaupt?
    table = Table.query.get(data.get("table_id"))
    if table is None:
        return jsonify({"error": "Table not found"}), 404

    reservation = Reservation(
        table_id=data.get("table_id"),
        name=data.get("name"),
        email=data.get("email"),
        date=data.get("date"),
        time_slot=data.get("time_slot"),
        notes=data.get("notes", ""),
    )
    db.session.add(reservation)
    db.session.commit()
    return jsonify(reservation.to_dict()), 201


@app.route("/api/reservations")
def get_reservations():
    reservations = Reservation.query.all()
    return jsonify([r.to_dict() for r in reservations])


@app.route("/api/reservations/<int:reservation_id>", methods=["DELETE"])
def delete_reservation(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if reservation is None:
        return jsonify({"error": "Reservation not found"}), 404
    db.session.delete(reservation)
    db.session.commit()
    return jsonify({"deleted": reservation_id}), 200


@app.route("/app")
def serve_app():
    return render_template("index.html")


@app.route("/reservations")
def reservations_page():
    reservations = Reservation.query.all()
    return render_template("reservations.html", reservations=reservations)


# --- DB init + seed --------------------------------------------------------

def init_db():
    """Erzeugt Tabellen und seedet Tische beim ersten Start."""
    with app.app_context():
        db.create_all()
        if Table.query.count() == 0:
            initial_tables = [
                Table(name="Table A1", type="Single", seats=1, floor="EG", free=True),
                Table(name="Table A2", type="Single", seats=1, floor="EG", free=True),
                Table(name="Table A3", type="Single", seats=1, floor="EG", free=True),
                Table(name="Table A4", type="Single", seats=1, floor="EG", free=True),
            ]
            db.session.add_all(initial_tables)
            db.session.commit()
            print("Seeded 4 tables.")


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)