
import os

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "products_db")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "quantity": self.quantity
        }


@app.route("/")
def home():
    return redirect(url_for("products"))


@app.route("/products")
def products():
    all_products = Product.query.order_by(Product.id.desc()).all()
    return render_template("products.html", products=all_products)


@app.route("/products/create", methods=["POST"])
def create_product():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    try:
        price = float(request.form.get("price", ""))
        quantity = int(request.form.get("quantity", ""))
    except (ValueError, TypeError):
        return "Invalid price or quantity", 400

    if not name or not description or price < 0 or quantity < 0:
        return "Invalid product details", 400

    product = Product(
        name=name,
        description=description,
        price=price,
        quantity=quantity
    )

    db.session.add(product)
    db.session.commit()

    return redirect(url_for("products"))


@app.route("/products/update/<int:product_id>", methods=["POST"])
def update_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return "Product not found", 404

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    try:
        price = float(request.form.get("price", ""))
        quantity = int(request.form.get("quantity", ""))
    except (ValueError, TypeError):
        return "Invalid price or quantity", 400

    if not name or not description or price < 0 or quantity < 0:
        return "Invalid product details", 400

    product.name = name
    product.description = description
    product.price = price
    product.quantity = quantity

    db.session.commit()

    return redirect(url_for("products"))


@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return "Product not found", 404

    db.session.delete(product)
    db.session.commit()

    return redirect(url_for("products"))


# JSON API

@app.route("/api/products", methods=["GET"])
def get_products():
    all_products = Product.query.order_by(Product.id.desc()).all()
    return jsonify([product.to_dict() for product in all_products])


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product.to_dict())


@app.route("/api/products", methods=["POST"])
def api_create_product():
    data = request.get_json(silent=True) or {}

    try:
        name = str(data.get("name", "")).strip()
        description = str(data.get("description", "")).strip()
        price = float(data["price"])
        quantity = int(data["quantity"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Invalid product data"}), 400

    if not name or not description or price < 0 or quantity < 0:
        return jsonify({"error": "Invalid product data"}), 400

    product = Product(
        name=name,
        description=description,
        price=price,
        quantity=quantity
    )

    db.session.add(product)
    db.session.commit()

    return jsonify(product.to_dict()), 201


@app.route("/api/products/<int:product_id>", methods=["PUT"])
def api_update_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json(silent=True) or {}

    try:
        name = str(data.get("name", product.name)).strip()
        description = str(
            data.get("description", product.description)
        ).strip()
        price = float(data.get("price", product.price))
        quantity = int(data.get("quantity", product.quantity))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid product data"}), 400

    if not name or not description or price < 0 or quantity < 0:
        return jsonify({"error": "Invalid product data"}), 400

    product.name = name
    product.description = description
    product.price = price
    product.quantity = quantity

    db.session.commit()

    return jsonify(product.to_dict())


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def api_delete_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product deleted successfully"})


@app.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "service": "product-service"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"status": "unhealthy"}), 503


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4001)
