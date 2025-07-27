from flask import Flask
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Import routes after app is defined
from routes.blanket_routes import *

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # fallback to 10000 if not found
    app.run(host="0.0.0.0", port=port, debug=True)
