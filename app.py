import os
from flask import Flask, redirect, url_for

from config import initialize_database
from routes.auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
    app.register_blueprint(auth_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    initialize_database()
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
