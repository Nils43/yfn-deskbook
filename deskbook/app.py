import os
from functools import wraps
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///deskbook.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# In Production: SECRET_KEY kommt aus Environment-Variable.
# Lokal: fallback auf dev-secret.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(500), default="")

    def to_dict(self):
        return {
            "id": self.id,
            "table_id": self.table_id,
            "user_id": self.user_id,
            "date": self.date,
            "time_slot": self.time_slot,
            "notes": self.notes,
        }


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "name": self.name}


# --- Auth Helpers + Decorators ---------------------------------------------

def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return User.query.get(user_id)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user() is None:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# --- Routes: Tables & Reservations -----------------------------------------

@app.route("/")
def hello():
    return redirect(url_for("login"))


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
@login_required
def create_reservation():
    user = current_user()
    data = request.get_json()

    table = Table.query.get(data.get("table_id"))
    if table is None:
        return jsonify({"error": "Table not found"}), 404

    reservation = Reservation(
        table_id=data.get("table_id"),
        user_id=user.id,
        date=data.get("date"),
        time_slot=data.get("time_slot"),
        notes=data.get("notes", ""),
    )
    db.session.add(reservation)
    db.session.commit()
    return jsonify(reservation.to_dict()), 201


@app.route("/api/reservations")
@login_required
def get_reservations():
    user = current_user()
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    return jsonify([r.to_dict() for r in reservations])


@app.route("/api/reservations/<int:reservation_id>", methods=["DELETE"])
@login_required
def delete_reservation(reservation_id):
    user = current_user()
    reservation = Reservation.query.get(reservation_id)
    if reservation is None:
        return jsonify({"error": "Reservation not found"}), 404
    if reservation.user_id != user.id:
        return jsonify({"error": "Forbidden"}), 403
    db.session.delete(reservation)
    db.session.commit()
    return jsonify({"deleted": reservation_id}), 200


# --- Routes: Auth ----------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", error=None)

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    name = request.form.get("name", "").strip()

    if not email or not password or not name:
        return render_template("register.html", error="All fields are required."), 400

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters."), 400

    existing = User.query.filter_by(email=email).first()
    if existing is not None:
        return render_template("register.html", error="Email already registered."), 400

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    return redirect(url_for("me"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if current_user() is not None:
            return redirect(url_for("me"))
        return render_template("login.html", error=None)

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return render_template("login.html", error="Invalid email or password."), 401

    session["user_id"] = user.id
    return redirect(url_for("me"))


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/me")
@login_required
def me():
    user = current_user()
    return render_template("me.html", user=user)


# --- Routes: Pages ---------------------------------------------------------

@app.route("/app")
@login_required
def serve_app():
    return render_template("index.html", user=current_user())


@app.route("/reservations")
@login_required
def reservations_page():
    user = current_user()
    reservations = Reservation.query.filter_by(user_id=user.id).all()
    return render_template("reservations.html", reservations=reservations, user=user)


# --- DB init + seed --------------------------------------------------------

def init_db():
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


# Wird beim Modul-Import ausgefuehrt (gunicorn-Modus, also Production).
# Lokal redundant, weil if-__main__-Block init_db() auch aufruft, aber harmlos.
init_db()


if __name__ == "__main__":
    app.run(debug=True, port=5000)