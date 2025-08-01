# manufacturer_service/app.py
from flask import Flask, request, jsonify
import mysql.connector, jwt
from auth_utils import require_token,get_db

app = Flask(__name__)

@app.route("/blankets", methods=["GET","POST","PUT","DELETE"])
@require_token(role="manufacturer")
def blankets():
    conn,cur=get_db(),get_db().cursor(dictionary=True)
    user = request.user
    if request.method=="GET":
        cur.execute("SELECT * FROM blankets"); data=cur.fetchall()
        return jsonify(data)
    d=request.json
    if request.method=="POST":
        cur.execute("INSERT INTO blankets(name,material,stock,min_stock) VALUES(%s,%s,%s,%s)",
                    (d["name"],d["material"],d["stock"],d["min_stock"]))
        conn.commit(); return jsonify({"msg":"Created"}),201
    if request.method=="PUT":
        cur.execute("UPDATE blankets SET name=%s,material=%s,stock=%s,min_stock=%s WHERE id=%s",
                    (d["name"],d["material"],d["stock"],d["min_stock"],d["id"]))
        conn.commit(); return jsonify({"msg":"Updated"})
    if request.method=="DELETE":
        cur.execute("DELETE FROM blankets WHERE id=%s",(d["id"],))
        conn.commit(); return jsonify({"msg":"Deleted"})
    return "",400

@app.route("/orders", methods=["GET","PUT"])
@require_token(role="manufacturer")
def man_orders():
    conn,cur=get_db(),get_db().cursor(dictionary=True)
    if request.method=="GET":
        cur.execute("SELECT * FROM manufacturer_orders"); return jsonify(cur.fetchall())
    d=request.json
    if request.method=="PUT":
        cur.execute("UPDATE manufacturer_orders SET status=%s WHERE id=%s",(d["status"],d["id"]))
        conn.commit(); return jsonify({"msg":"Status updated"})
    return "",400

@app.route("/order_request", methods=["POST"])
@require_token(role="distributor")
def req_order():
    d=request.json
    conn,cur=get_db(),get_db().cursor()
    cur.execute("INSERT INTO manufacturer_orders(blanket_name,quantity,distributor) VALUES(%s,%s,%s)",
                (d["blanket_name"],d["quantity"],d["distributor"]))
    conn.commit(); return jsonify({"msg":"Requested"}),201

if __name__=="__main__":
    app.run(debug=True)
