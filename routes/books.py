from flask import Blueprint, request, jsonify
from config import DB_TYPE, get_db_connection

books_bp = Blueprint("books", __name__)


def is_mysql():
    return DB_TYPE == "mysql"


def get_cursor(conn):
    if is_mysql():
        return conn.cursor(dictionary=True)
    return conn.cursor()


def sql_query(query):
    return query if is_mysql() else query.replace("%s", "?")


def row_to_dict(cursor, row):
    if row is None or isinstance(row, dict):
        return row
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def rows_to_dicts(cursor, rows):
    return [row_to_dict(cursor, r) for r in rows]


# -----------------------------
# Helper Responses
# -----------------------------
def success_response(message, data=None, status=200):
    return jsonify({
        "success": True,
        "message": message,
        "data": data
    }), status


def error_response(message, status=400):
    return jsonify({
        "success": False,
        "message": message,
        "data": None
    }), status


# =============================
# GET ALL BOOKS
# =============================
@books_bp.route("/books", methods=["GET"])
def get_books():
    db, cursor = None, None
    try:
        db = get_db_connection()
        cursor = get_cursor(db)
        cursor.execute(sql_query("""
            SELECT id, title, author, genre, isbn, total_copies, available_copies
            FROM books
            ORDER BY id DESC
        """))
        books = rows_to_dicts(cursor, cursor.fetchall())
        return success_response("Books fetched successfully", books)
    except Exception as e:
        return error_response(str(e))
    finally:
        if cursor: cursor.close()
        if db: db.close()


# =============================
# GET SINGLE BOOK
# =============================
@books_bp.route("/books/<int:id>", methods=["GET"])
def get_single_book(id):
    db, cursor = None, None
    try:
        db = get_db_connection()
        cursor = get_cursor(db)
        cursor.execute(sql_query("SELECT * FROM books WHERE id=%s"), (id,))
        book = row_to_dict(cursor, cursor.fetchone())
        if not book:
            return error_response("Book not found", 404)
        return success_response("Book found", book)
    except Exception as e:
        return error_response(str(e))
    finally:
        if cursor: cursor.close()
        if db: db.close()


# =============================
# ADD BOOK
# =============================
@books_bp.route("/books", methods=["POST"])
def add_book():
    data = request.json or {}
    title = data.get("title")
    author = data.get("author")
    genre = data.get("genre")
    isbn = data.get("isbn")
    total = data.get("total_copies")

    if not title or not author or total is None:
        return error_response("Title, Author and Total Copies required")

    db, cursor = None, None
    try:
        db = get_db_connection()
        cursor = get_cursor(db)
        cursor.execute(sql_query("""
            INSERT INTO books (title, author, genre, isbn, total_copies, available_copies)
            VALUES (%s, %s, %s, %s, %s, %s)
        """), (title, author, genre, isbn, total, total))
        db.commit()
        last_id = cursor.lastrowid
        return success_response("Book added successfully", {"id": last_id}, 201)
    except Exception as e:
        if db: db.rollback()
        return error_response(str(e))
    finally:
        if cursor: cursor.close()
        if db: db.close()


# =============================
# UPDATE BOOK
# =============================
@books_bp.route("/books/<int:id>", methods=["PUT"])
def update_book(id):
    data = request.json or {}
    title = data.get("title")
    author = data.get("author")
    genre = data.get("genre")
    isbn = data.get("isbn")
    total = data.get("total_copies")

    db, cursor = None, None
    try:
        db = get_db_connection()
        cursor = get_cursor(db)
        cursor.execute(sql_query("""
            UPDATE books
            SET title=%s, author=%s, genre=%s, isbn=%s, total_copies=%s
            WHERE id=%s
        """), (title, author, genre, isbn, total, id))
        db.commit()
        return success_response("Book updated successfully")
    except Exception as e:
        if db: db.rollback()
        return error_response(str(e))
    finally:
        if cursor: cursor.close()
        if db: db.close()


# =============================
# DELETE BOOK
# =============================
@books_bp.route("/books/<int:id>", methods=["DELETE"])
def delete_book(id):
    db, cursor = None, None
    try:
        db = get_db_connection()
        cursor = get_cursor(db)
        cursor.execute(sql_query("DELETE FROM books WHERE id=%s"), (id,))
        db.commit()
        return success_response("Book deleted successfully")
    except Exception as e:
        if db: db.rollback()
        return error_response(str(e))
    finally:
        if cursor: cursor.close()
        if db: db.close()


# =============================
# SEARCH BOOK
# =============================
@books_bp.route("/books/search", methods=["GET"])
def search_books():
    keyword = request.args.get("q")
    if not keyword:
        return get_books()

    value = f"%{keyword}%"
    db, cursor = None, None
    try:
        db = get_db_connection()
        cursor = get_cursor(db)
        cursor.execute(sql_query("""
            SELECT id, title, author, genre, isbn, total_copies, available_copies
            FROM books
            WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s OR genre LIKE %s
            ORDER BY id DESC
        """), (value, value, value, value))
        books = rows_to_dicts(cursor, cursor.fetchall())
        return success_response("Search completed", books)
    except Exception as e:
        return error_response(str(e))
    finally:
        if cursor: cursor.close()
        if db: db.close()
