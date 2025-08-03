from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from db_config import get_db_connection

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# ✅ GET All Blanket Models
@app.route('/blankets', methods=['GET'])
def get_blankets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM manufacturer_blankets")
    blankets = cursor.fetchall()
    conn.close()
    return jsonify(blankets)

# ✅ ADD New Blanket Model
@app.route('/blankets', methods=['POST'])
def add_blanket():
    data = request.json
    model = data['model']
    material = data['material']
    quantity = data['quantity']
    production_days = data['production_days']
    min_required = data.get('min_required', 20)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO manufacturer_blankets (model, material, quantity, production_days, min_required)
                      VALUES (%s, %s, %s, %s, %s)""",
                   (model, material, quantity, production_days, min_required))
    conn.commit()
    conn.close()

    return jsonify({"msg": "Blanket model added"})

# ✅ UPDATE Blanket Stock Quantity (Edit)
@app.route('/blankets/<int:blanket_id>', methods=['PUT'])
def update_blanket_quantity(blanket_id):
    data = request.json
    quantity = data['quantity']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("UPDATE manufacturer_blankets SET quantity=%s WHERE id=%s", (quantity, blanket_id))
    conn.commit()

    cursor.execute("SELECT model, quantity, min_required FROM manufacturer_blankets WHERE id=%s", (blanket_id,))
    blanket = cursor.fetchone()
    conn.close()

    if blanket['quantity'] < blanket['min_required']:
        return jsonify({"msg": "Stock updated", "alert": "Start Production, Low Stock!", "model": blanket['model']})

    return jsonify({"msg": "Stock updated"})

# ✅ DELETE Blanket Model
@app.route('/blankets/<int:blanket_id>', methods=['DELETE'])
def delete_blanket(blanket_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM manufacturer_blankets WHERE id=%s", (blanket_id,))
    conn.commit()
    conn.close()
    return jsonify({"msg": "Blanket model deleted"})

# ✅ GET Distributor Requests
@app.route('/distributor-requests', methods=['GET'])
def get_distributor_requests():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT dr.id, dr.distributor_id, dr.blanket_model, dr.quantity, dr.status, u.username AS distributor_name
        FROM distributor_requests dr
        JOIN users u ON dr.distributor_id = u.id
        ORDER BY dr.created_at DESC
    """)
    requests = cursor.fetchall()
    conn.close()
    return jsonify(requests)

# ✅ UPDATE Distributor Request Status + Move to History if Completed/Denied
@app.route('/distributor-requests/<int:request_id>', methods=['PUT'])
def update_distributor_request_status(request_id):
    data = request.json
    status = data['status']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the request details before updating
    cursor.execute("SELECT * FROM distributor_requests WHERE id=%s", (request_id,))
    request_data = cursor.fetchone()

    if not request_data:
        conn.close()
        return jsonify({"msg": "Request not found"}), 404

    # Update status
    cursor.execute("UPDATE distributor_requests SET status=%s WHERE id=%s", (status, request_id))
    conn.commit()

    # Move to history if completed or denied
    if status.lower() in ["completed", "denied"]:
        cursor.execute("""
            INSERT INTO distributor_request_history (distributor_id, blanket_model, quantity, status)
            VALUES (%s, %s, %s, %s)
        """, (request_data['distributor_id'], request_data['blanket_model'], request_data['quantity'], status))
        cursor.execute("DELETE FROM distributor_requests WHERE id=%s", (request_id,))
        conn.commit()

    conn.close()
    return jsonify({"msg": "Distributor request status updated"})

# ✅ GET Distributor Request History
@app.route('/distributor-request-history', methods=['GET'])
def get_distributor_request_history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT h.id, h.distributor_id, h.blanket_model, h.quantity, h.status, u.username AS distributor_name
        FROM distributor_request_history h
        JOIN users u ON h.distributor_id = u.id
        ORDER BY h.id DESC
    """)
    history = cursor.fetchall()
    conn.close()
    return jsonify(history)

# ✅ CHECK All Low Stock Items
@app.route('/check-low-stock', methods=['GET'])
def check_low_stock():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT model, quantity, min_required FROM manufacturer_blankets WHERE quantity < min_required")
    low_stock_items = cursor.fetchall()
    conn.close()
    return jsonify({"low_stock": low_stock_items})

# ✅ Health Check
@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "Manufacturer Service Running"})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
