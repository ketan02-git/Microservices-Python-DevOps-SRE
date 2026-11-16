
import os

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "users_db")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role
        }


@app.route("/")
def home():
    return redirect(url_for("users"))


@app.route("/users")
def users():
    all_users = User.query.order_by(User.id.desc()).all()
    return render_template("users.html", users=all_users)


@app.route("/users/create", methods=["POST"])
def create_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    role = request.form.get("role", "").strip()

    if not all([name, email, role]):
        return "All fields are required", 400

    user = User(name=name, email=email, role=role)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return "Could not create user. Check whether email already exists.", 400

    return redirect(url_for("users"))


@app.route("/users/update/<int:user_id>", methods=["POST"])
def update_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        return "User not found", 404

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    role = request.form.get("role", "").strip()

    if not all([name, email, role]):
        return "All fields are required", 400

    user.name = name
    user.email = email
    user.role = role

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return "Could not update user. Check email uniqueness.", 400

    return redirect(url_for("users"))


@app.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        return "User not found", 404

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("users"))


# JSON API

@app.route("/api/users", methods=["GET"])
def get_users():
    all_users = User.query.order_by(User.id.desc()).all()
    return jsonify([user.to_dict() for user in all_users])


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())


@app.route("/api/users", methods=["POST"])
def api_create_user():
    data = request.get_json(silent=True) or {}

    if not all(str(data.get(k, "")).strip() for k in ("name", "email", "role")):
        return jsonify({"error": "name, email and role are required"}), 400

    user = User(
        name=data["name"].strip(),
        email=data["email"].strip(),
        role=data["role"].strip()
    )

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not create user"}), 400

    return jsonify(user.to_dict()), 201


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def api_update_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}

    for field in ("name", "email", "role"):
        if field in data:
            value = str(data[field]).strip()
            if not value:
                return jsonify({"error": f"{field} cannot be empty"}), 400
            setattr(user, field, value)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not update user"}), 400

    return jsonify(user.to_dict())


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def api_delete_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"})


@app.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "service": "user-service"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"status": "unhealthy"}), 503


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
