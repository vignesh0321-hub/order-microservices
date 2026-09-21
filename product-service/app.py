from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# RDS database configuration
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
    return "Product Microservice is running!"


@app.route("/products", methods=["GET"])
def get_products():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()

        return jsonify(products)

    finally:
        connection.close()


@app.route("/products", methods=["POST"])
def add_product():
    data = request.get_json()

    name = data["name"]
    price = data["price"]
    quantity = data["quantity"]

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO products (name, price, quantity)
                VALUES (%s, %s, %s)
            """

            cursor.execute(sql, (name, price, quantity))

        connection.commit()

        return jsonify({
            "message": "Product added successfully"
        }), 201

    finally:
        connection.close()

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM products WHERE id = %s",
                (product_id,)
            )
            product = cursor.fetchone()

        if product:
            return jsonify(product)

        return jsonify({"message": "Product not found"}), 404

    finally:
        connection.close()
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json()

    name = data["name"]
    price = data["price"]
    quantity = data["quantity"]

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE products
                SET name = %s, price = %s, quantity = %s
                WHERE id = %s
            """

            cursor.execute(sql, (name, price, quantity, product_id))

        connection.commit()

        return jsonify({
            "message": "Product updated successfully"
        })

    finally:
        connection.close()
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM products WHERE id = %s"
            cursor.execute(sql, (product_id,))

        connection.commit()

        return jsonify({
            "message": "Product deleted successfully"
        })

    finally:
        connection.close()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
