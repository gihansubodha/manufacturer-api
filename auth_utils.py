# auth_utils.py

import jwt
import datetime
import os
from flask import request, jsonify
import mysql.connector
from functools import wraps

SECRET_KEY = "cozy_secret"  # ✅ Consider moving this to an environment variable

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


# ✅ Role-based decorator
def require_token(role=None):
    def decorator(f):
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

            if role and user['role'] != role:
                return jsonify({'error': 'Forbidden: Incorrect role'}), 403

            request.user = user
            return f(*args, **kwargs)
        return decorated
    return decorator


# ✅ Database connection using Aiven MySQL (with SSL)
def get_db():
    return mysql.connector.connect(
        host="cozycomfort-gihansubodha-soc.c.aivencloud.com",
        port=26728,
        user="avnadmin",
        password="AVNS_i33CBpI3jeyig2mnoMR",
        database="defaultdb",
        ssl_disabled=False  # 🔐 Required for Aiven
    )
