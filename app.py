import os
from flask import Flask, redirect, url_for

from config import initialize_database
from routes.auth import auth_bp
from routes.members import members_bp
from routes.books import books_bp
from routes.borrows import borrows_bp
from routes.fines import fines_bp


def create_app():
    app = Flask(__name__)

    app.secret_key = os.getenv(
        "SECRET_KEY",
        "dev-secret-key"
    )

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(borrows_bp)
    app.register_blueprint(fines_bp)


    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    initialize_database()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
