from app import app

if __name__ == "__main__":
    # Fallback for local debug (not used in container normally)
    app.run(host="0.0.0.0", port=5000)