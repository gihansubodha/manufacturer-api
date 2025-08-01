# auth_utils.py

import jwt
import datetime
import os
from flask import request, jsonify
import mysql.connector
from functools import wraps

SECRET_KEY = "cozy_secret"  # Consider moving to environment variable for production

# ✅ Token generation
def generate_token(user):
    payload = {
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=9999)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# ✅ Token verification
def verify_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ✅ Decorator to protect routes
def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token[7:]
        else:
            return jsonify({'error': 'Authorization token required'}), 401

        user = verify_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401

        request.user = user
        return f(*args, **kwargs)
    return decorated

# ✅ Get database connection
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "defaultdb")
    )
