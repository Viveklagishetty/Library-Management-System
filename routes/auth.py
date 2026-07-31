import os
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import DB_TYPE, get_db_connection

auth_bp = Blueprint("auth", __name__)


def get_db_cursor(connection):
    if DB_TYPE == "mysql":
        return connection.cursor(dictionary=True)
    return connection.cursor()


def execute_query(connection, query, params=None):
    cursor = get_db_cursor(connection)
    sql = query if DB_TYPE == "mysql" else query.replace("%s", "?")
    if params is None:
        cursor.execute(sql)
    else:
        cursor.execute(sql, params)
    return cursor


def fetch_one(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    if cursor.description is None:
        return row
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


def fetch_all(cursor):
    rows = cursor.fetchall()
    if not rows:
        return []
    if isinstance(rows[0], dict):
        return rows
    if cursor.description is None:
        return rows
    return [{column[0]: row[index] for index, column in enumerate(cursor.description)} for row in rows]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            user_role = session["user"].get("role", "member")
            if user_role not in roles:
                flash("You do not have access to that page.", "danger")
                return redirect(url_for("auth.dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "member").strip() or "member"

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        connection = get_db_connection()
        cursor = execute_query(connection, "SELECT id FROM users WHERE username = %s OR email = %s LIMIT 1", (username, email))
        existing_user = fetch_one(cursor)
        connection.close()

        if existing_user:
            flash("A user with that username or email already exists.", "danger")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        connection = get_db_connection()
        cursor = execute_query(
            connection,
            "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, role),
        )
        connection.commit()
        if role == "member":
            new_user_id = cursor.lastrowid
            execute_query(
                connection,
                "INSERT INTO members (user_id, full_name, email) VALUES (%s, %s, %s)",
                (new_user_id, username, email),
            )
            connection.commit()
        connection.close()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html")

        connection = get_db_connection()
        cursor = execute_query(connection, "SELECT * FROM users WHERE username = %s LIMIT 1", (username,))
        user = fetch_one(cursor)
        connection.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
            }
            flash("Login successful.", "success")
            return redirect(url_for("auth.dashboard"))

        flash("Invalid username or password.", "danger")
        return render_template("login.html")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

def get_member_for_user(user_id, username=None, email=None):
    connection = get_db_connection()
    cursor = execute_query(connection, "SELECT * FROM members WHERE user_id = %s LIMIT 1", (user_id,))
    member = fetch_one(cursor)

    if not member and username and email:
        execute_query(
            connection,
            "INSERT INTO members (user_id, full_name, email) VALUES (%s, %s, %s)",
            (user_id, username, email),
        )
        connection.commit()
        cursor = execute_query(connection, "SELECT * FROM members WHERE user_id = %s LIMIT 1", (user_id,))
        member = fetch_one(cursor)

    connection.close()
    return member


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    user = session["user"]
    if user["role"] == "admin":
        return render_template("admin_dashboard.html", user=user)
    if user["role"] == "librarian":
        return render_template("librarian_dashboard.html", user=user)
    member = get_member_for_user(user["id"], user.get("username"), user.get("email"))
    return render_template("member_dashboard.html", user=user, member=member)


@auth_bp.route("/admin-dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html", user=session["user"])


@auth_bp.route("/librarian-dashboard")
@login_required
@role_required("librarian")
def librarian_dashboard():
    return render_template("librarian_dashboard.html", user=session["user"])


@auth_bp.route("/member-dashboard")
@login_required
@role_required("member")
def member_dashboard():
    user = session["user"]
    member = get_member_for_user(user["id"], user.get("username"), user.get("email"))
    return render_template("member_dashboard.html", user=user, member=member)
