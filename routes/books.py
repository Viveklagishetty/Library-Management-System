from flask import Blueprint, request, jsonify
from mysql.connector import Error
from config import get_db_connection

books_bp = Blueprint("books", __name__)
def success_response(message, data=None, status=200):
    return jsonify({
        "success": True,
        "message": message,
        "data": data
    }), status

def error_response(message, status=400, errors=None):
    response = {
        "success": False,
        "message": message,
        "data": None
    }
    if errors:
        response["errors"] = errors
    return jsonify(response), status


@books_bp.route("/books", methods=["GET"])
def get_books():
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, author, genre, isbn,
                   total_copies, available_copies, added_on
            FROM books
            ORDER BY id DESC
        """)
        return success_response(
            "Books fetched successfully",
            cursor.fetchall()
        )
    except Error as exc:
        return error_response(f"Unable to fetch books: {exc}", 400)
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id):
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()

        if not book:
            return error_response("Book not found", 404)

        return success_response("Book fetched successfully", book)
    except Error as exc:
        return error_response(f"Unable to fetch book: {exc}", 400)
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@books_bp.route("/book", methods=["POST"])
def add_book():
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    author = str(data.get("author", "")).strip()
    genre = str(data.get("genre", "")).strip() or None
    isbn = str(data.get("isbn", "")).strip() or None
    total_copies = data.get("total_copies", 1)

    errors = {}

    if not title:
        errors["title"] = "Title is required."

    if not author:
        errors["author"] = "Author is required."

    try:
        total_copies = int(total_copies)
        if total_copies < 0:
            errors["total_copies"] = "Total copies cannot be negative."
    except (TypeError, ValueError):
        errors["total_copies"] = "Total copies must be a whole number."

    if errors:
        return error_response("Validation failed", 400, errors)

    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO books
            (title, author, genre, isbn, total_copies, available_copies)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            title,
            author,
            genre,
            isbn,
            total_copies,
            total_copies
        ))
        book_id = cursor.lastrowid
        db.commit()

        return success_response(
            "Book added successfully",
            {
                "id": book_id,
                "title": title,
                "author": author,
                "genre": genre,
                "isbn": isbn,
                "total_copies": total_copies,
                "available_copies": total_copies
            },
            201
        )
    except Error as exc:
        if db:
            db.rollback()
        if exc.errno == 1062:
            return error_response("ISBN already exists", 409)
        return error_response(f"Unable to add book: {exc}", 400)
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@books_bp.route("/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    data = request.get_json(silent=True) or {}
    db = cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM books WHERE id = %s FOR UPDATE",
            (book_id,)
        )
        book = cursor.fetchone()

        if not book:
            return error_response("Book not found", 404)

        title = str(data.get("title", book["title"])).strip()
        author = str(data.get("author", book["author"])).strip()
        genre = data.get("genre", book["genre"])
        isbn = data.get("isbn", book["isbn"])

        errors = {}

        if not title:
            errors["title"] = "Title is required."

        if not author:
            errors["author"] = "Author is required."

        try:
            new_total = int(
                data.get("total_copies", book["total_copies"])
            )
            if new_total < 0:
                errors["total_copies"] = (
                    "Total copies cannot be negative."
                )
        except (TypeError, ValueError):
            errors["total_copies"] = (
                "Total copies must be a whole number."
            )
            new_total = book["total_copies"]

        if errors:
            return error_response("Validation failed", 400, errors)

        borrowed_copies = (
            book["total_copies"] - book["available_copies"]
        )

        if new_total < borrowed_copies:
            return error_response(
                "Total copies cannot be less than currently borrowed copies.",
                409
            )

        new_available = new_total - borrowed_copies

        cursor.execute("""
            UPDATE books
            SET title = %s,
                author = %s,
                genre = %s,
                isbn = %s,
                total_copies = %s,
                available_copies = %s
            WHERE id = %s
        """, (
            title,
            author,
            genre,
            isbn,
            new_total,
            new_available,
            book_id
        ))

        db.commit()

        return success_response(
            "Book updated successfully",
            {
                "id": book_id,
                "title": title,
                "author": author,
                "genre": genre,
                "isbn": isbn,
                "total_copies": new_total,
                "available_copies": new_available,
                "borrowed_copies": borrowed_copies
            }
        )
    except Error as exc:
        if db:
            db.rollback()
        if exc.errno == 1062:
            return error_response("ISBN already exists", 409)
        return error_response(f"Unable to update book: {exc}", 400)
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@books_bp.route("/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    db = cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
        if not cursor.fetchone():
            return error_response("Book not found", 404)

        cursor.execute("""
            SELECT COUNT(*) AS active_count
            FROM borrows
            WHERE book_id = %s AND status = 'active'
        """, (book_id,))

        if cursor.fetchone()["active_count"] > 0:
            return error_response(
                "Cannot delete a book with active borrow records.",
                409
            )

        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        db.commit()
        return success_response("Book deleted successfully")

    except Error as exc:
        if db:
            db.rollback()
        if exc.errno == 1451:
            return error_response(
                "This book has borrowing history and cannot be deleted.",
                409
            )
        return error_response(f"Unable to delete book: {exc}", 400)
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@books_bp.route("/search", methods=["GET"])
def search_books():
    query = request.args.get("q", "").strip()

    if not query:
        return error_response("Search query is required", 400)

    value = f"%{query}%"
    db = cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, author, genre, isbn,
                   total_copies, available_copies, added_on
            FROM books
            WHERE title LIKE %s
               OR author LIKE %s
               OR genre LIKE %s
               OR isbn LIKE %s
            ORDER BY title ASC
        """, (value, value, value, value))

        return success_response(
            "Search completed successfully",
            cursor.fetchall()
        )
    except Error as exc:
        return error_response(f"Unable to search books: {exc}", 400)
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
