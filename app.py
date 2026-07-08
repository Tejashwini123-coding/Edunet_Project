"""
app.py – LearnMate Flask Application Entry Point
=================================================
Run with:  python app.py
Production: gunicorn -w 4 -b 0.0.0.0:5000 app:app
"""

import os
from pathlib import Path
from flask import Flask
from flask_session import Session
from dotenv import load_dotenv

# Load .env relative to this file's directory, not the working directory.
# This ensures credentials are found whether the app is launched from
# learnmate/, the repo root, or any other directory.
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Secret key ────────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    # ── Server-side session (filesystem) ──────────────────────────────────────
    session_dir = os.getenv("SESSION_FILE_DIR", "./flask_session")
    os.makedirs(session_dir, exist_ok=True)
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = session_dir
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7  # 7 days
    Session(app)

    # ── Register blueprints ───────────────────────────────────────────────────
    from routes import main_bp
    app.register_blueprint(main_bp)

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(debug=debug, host="0.0.0.0", port=5000)
