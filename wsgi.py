from app import app

if __name__ == "__main__":
    # Only used for local development
    # In production, this file is loaded by Gunicorn
    app.run(host="0.0.0.0", port=5000)