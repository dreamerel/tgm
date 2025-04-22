from backend.app import app
from backend import models, routes

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)