from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", 3306))


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route("/")
def home():
    return "Order Microservice is running!"


# Get all orders
@app.route("/orders", methods=["GET"])
def get_orders():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM orders")
            orders = cursor.fetchall()
    finally:
        connection.close()

    # Get product details from Product Service
    for order in orders:
        response = requests.get(
            f"http://localhost:5000/products/{order['product_id']}"
        )

        if response.status_code == 200:
            product = response.json()
            order["product_name"] = product["name"]
        else:
            order["product_name"] = "Product not found"

    return jsonify(orders)


# Get order by ID
@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM orders WHERE id = %s",
                (order_id,)
            )
            order = cursor.fetchone()

        if order:
            return jsonify(order)

        return jsonify({
            "message": "Order not found"
        }), 404

    finally:
        connection.close()


# Update order
@app.route("/orders/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    data = request.get_json()

    if not data or "quantity" not in data:
        return jsonify({
            "message": "quantity is required"
        }), 400

    quantity = data["quantity"]

    if quantity <= 0:
        return jsonify({
            "message": "quantity must be greater than 0"
        }), 400

    # Get existing order
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM orders WHERE id = %s",
                (order_id,)
            )
            order = cursor.fetchone()

        if not order:
            return jsonify({
                "message": "Order not found"
            }), 404

        product_id = order["product_id"]

    finally:
        connection.close()

    # Get product price from Product Service
    response = requests.get(
        f"http://localhost:5000/products/{product_id}"
    )

    if response.status_code != 200:
        return jsonify({
            "message": "Product not found"
        }), 404

    product = response.json()

    # Recalculate total price
    total_price = float(product["price"]) * quantity

    # Update order
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE orders
                SET quantity = %s, total_price = %s
                WHERE id = %s
            """

            cursor.execute(
                sql,
                (quantity, total_price, order_id)
            )

        connection.commit()

        return jsonify({
            "message": "Order updated successfully",
            "order_id": order_id,
            "product": product["name"],
            "quantity": quantity,
            "total_price": total_price
        })

    finally:
        connection.close()


# Create order
@app.route("/orders", methods=["POST"])
def add_order():
    data = request.get_json()

    # Validate required fields
    if not data or "product_id" not in data or "quantity" not in data:
        return jsonify({
            "message": "product_id and quantity are required"
        }), 400

    product_id = data["product_id"]
    quantity = data["quantity"]

    # Validate quantity
    if quantity <= 0:
        return jsonify({
            "message": "quantity must be greater than 0"
        }), 400

    # Call Product Service
    response = requests.get(
        f"http://localhost:5000/products/{product_id}"
    )

    if response.status_code != 200:
        return jsonify({
            "message": "Product not found"
        }), 404

    product = response.json()

    # Calculate total price
    total_price = float(product["price"]) * quantity

    # Save order in database
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO orders (product_id, quantity, total_price)
                VALUES (%s, %s, %s)
            """

            cursor.execute(
                sql,
                (product_id, quantity, total_price)
            )

        connection.commit()

        return jsonify({
            "message": "Order created successfully",
            "product": product["name"],
            "quantity": quantity,
            "total_price": total_price
        }), 201

    finally:
        connection.close()


# Delete order
@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT * FROM orders WHERE id = %s",
                (order_id,)
            )

            order = cursor.fetchone()

            if not order:
                return jsonify({
                    "message": "Order not found"
                }), 404

            cursor.execute(
                "DELETE FROM orders WHERE id = %s",
                (order_id,)
            )

        connection.commit()

        return jsonify({
            "message": "Order deleted successfully",
            "order_id": order_id
        })

    finally:
        connection.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
