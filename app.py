from flask import Flask, request, jsonify
from functools import wraps
from db_config import get_connection
from auth_utils import generate_token, verify_token
import jwt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
AUTH_SECRET = "your_auth_secret"

# TOKEN DECORATOR
def require_token(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                try:
                    token = request.headers['Authorization'].split()[1]
                except IndexError:
                    return jsonify({'message': 'Token format invalid'}), 401
            if not token:
                return jsonify({'message': 'Token is missing'}), 401

            try:
                payload = jwt.decode(token, AUTH_SECRET, algorithms=["HS256"])
                request.user = payload
                if role and payload['role'] != role:
                    return jsonify({'message': 'Access denied for this role'}), 403
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'message': 'Invalid token'}), 401

            return f(*args, **kwargs)
        return wrapper
    return decorator

# MANUFACTURER ROUTES

@app.route("/blankets", methods=["GET", "POST", "PUT", "DELETE"])
@require_token(role="manufacturer")
def blankets():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "GET":
        cur.execute("SELECT * FROM blankets")
        return jsonify(cur.fetchall())

    data = request.json
    if request.method == "POST":
        cur.execute("INSERT INTO blankets (name, material, stock, min_stock) VALUES (%s, %s, %s, %s)",
                    (data["name"], data["material"], data["stock"], data["min_stock"]))
        conn.commit()
        return jsonify({"msg": "Blanket created"}), 201

    if request.method == "PUT":
        cur.execute("UPDATE blankets SET name=%s, material=%s, stock=%s, min_stock=%s WHERE id=%s",
                    (data["name"], data["material"], data["stock"], data["min_stock"], data["id"]))
        conn.commit()
        return jsonify({"msg": "Blanket updated"})

    if request.method == "DELETE":
        cur.execute("DELETE FROM blankets WHERE id=%s", (data["id"],))
        conn.commit()
        return jsonify({"msg": "Blanket deleted"})

    return "", 400

@app.route("/orders", methods=["GET", "PUT"])
@require_token(role="manufacturer")
def manufacturer_orders():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "GET":
        cur.execute("SELECT * FROM manufacturer_orders")
        return jsonify(cur.fetchall())

    data = request.json
    if request.method == "PUT":
        cur.execute("UPDATE manufacturer_orders SET status=%s WHERE id=%s",
                    (data["status"], data["id"]))
        conn.commit()
        return jsonify({"msg": "Order status updated"})

    return "", 400

@app.route("/order_request", methods=["POST"])
@require_token(role="distributor")
def distributor_order_request():
    data = request.json
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO manufacturer_orders (blanket_name, quantity, distributor) VALUES (%s, %s, %s)",
                (data["blanket_name"], data["quantity"], data["distributor"]))
    conn.commit()
    return jsonify({"msg": "Order request submitted"}), 201

# MAIN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
