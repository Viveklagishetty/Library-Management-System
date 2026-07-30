from flask import Blueprint, request, jsonify
from mysql.connector import Error
from config import get_db_connection


books_bp = Blueprint("books", __name__)


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

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(dictionary=True)


        cursor.execute("""
            SELECT 
                id,
                title,
                author,
                genre,
                isbn,
                total_copies,
                available_copies
            FROM books
            ORDER BY id DESC
        """)


        books = cursor.fetchall()


        return success_response(
            "Books fetched successfully",
            books
        )


    except Error as e:

        return error_response(
            str(e)
        )


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()






# =============================
# GET SINGLE BOOK
# =============================

@books_bp.route("/books/<int:id>", methods=["GET"])
def get_single_book(id):

    db=None
    cursor=None


    try:

        db=get_db_connection()

        cursor=db.cursor(dictionary=True)


        cursor.execute(
            "SELECT * FROM books WHERE id=%s",
            (id,)
        )


        book=cursor.fetchone()


        if not book:

            return error_response(
                "Book not found",
                404
            )


        return success_response(
            "Book found",
            book
        )



    except Error as e:

        return error_response(
            str(e)
        )


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()







# =============================
# ADD BOOK
# =============================


@books_bp.route("/books", methods=["POST"])
def add_book():


    data=request.json


    title=data.get("title")
    author=data.get("author")
    genre=data.get("genre")
    isbn=data.get("isbn")
    total=data.get("total_copies")



    if not title or not author:

        return error_response(
            "Title and Author required"
        )



    db=None
    cursor=None


    try:


        db=get_db_connection()

        cursor=db.cursor()


        cursor.execute("""
            INSERT INTO books
            (
            title,
            author,
            genre,
            isbn,
            total_copies,
            available_copies
            )

            VALUES
            (%s,%s,%s,%s,%s,%s)

        """,(
            title,
            author,
            genre,
            isbn,
            total,
            total
        ))



        db.commit()



        return success_response(

            "Book added successfully",

            {
                "id":cursor.lastrowid
            },

            201
        )



    except Error as e:


        if db:
            db.rollback()


        return error_response(
            str(e)
        )



    finally:


        if cursor:
            cursor.close()

        if db:
            db.close()







# =============================
# UPDATE BOOK
# =============================


@books_bp.route("/books/<int:id>", methods=["PUT"])
def update_book(id):


    data=request.json


    title=data.get("title")
    author=data.get("author")
    genre=data.get("genre")
    isbn=data.get("isbn")
    total=data.get("total_copies")



    db=None
    cursor=None


    try:


        db=get_db_connection()

        cursor=db.cursor()


        cursor.execute("""

            UPDATE books

            SET

            title=%s,
            author=%s,
            genre=%s,
            isbn=%s,
            total_copies=%s,
            available_copies=%s


            WHERE id=%s


        """,(

            title,
            author,
            genre,
            isbn,
            total,
            total,
            id

        ))



        db.commit()



        return success_response(
            "Book updated successfully"
        )



    except Error as e:


        return error_response(
            str(e)
        )


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()








# =============================
# DELETE BOOK
# =============================


@books_bp.route("/books/<int:id>", methods=["DELETE"])
def delete_book(id):


    db=None
    cursor=None


    try:


        db=get_db_connection()

        cursor=db.cursor()



        cursor.execute(
            "DELETE FROM books WHERE id=%s",
            (id,)
        )


        db.commit()



        return success_response(
            "Book deleted successfully"
        )



    except Error as e:


        return error_response(
            str(e)
        )



    finally:


        if cursor:
            cursor.close()

        if db:
            db.close()







# =============================
# SEARCH BOOK
# =============================


@books_bp.route("/books/search", methods=["GET"])
def search_books():


    keyword=request.args.get("q")


    if not keyword:

        return get_books()



    value=f"%{keyword}%"



    db=None
    cursor=None


    try:


        db=get_db_connection()

        cursor=db.cursor(dictionary=True)



        cursor.execute("""

            SELECT *

            FROM books

            WHERE title LIKE %s

            OR author LIKE %s

            OR isbn LIKE %s

            OR genre LIKE %s


        """,(

            value,
            value,
            value,
            value

        ))



        books=cursor.fetchall()



        return success_response(
            "Search completed",
            books
        )



    except Error as e:


        return error_response(
            str(e)
        )



    finally:


        if cursor:
            cursor.close()

        if db:
            db.close()