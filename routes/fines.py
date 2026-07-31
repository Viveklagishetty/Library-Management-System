print("Loading fines.py")

from flask import Blueprint, jsonify
from datetime import date
from config import DB_TYPE, get_db_connection

print("Registering GET /fines route")

fines_bp = Blueprint("fines", __name__)


def get_cursor(conn):
    if DB_TYPE == "mysql":
        return conn.cursor(dictionary=True)
    return conn.cursor()


def sql(query):
    return query if DB_TYPE == "mysql" else query.replace("%s", "?")


def as_dict(cursor, row):
    if row is None or isinstance(row, dict):
        return row
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def as_dicts(cursor, rows):
    return [as_dict(cursor, row) for row in rows]


# ======================================
# Get All Fines
# ======================================

@fines_bp.route("/fines", methods=["GET"])
def get_fines():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = get_cursor(conn)

        cursor.execute(sql("""
            SELECT
                f.id AS fine_id,
                f.amount,
                f.is_paid,
                f.paid_on,

                b.id AS borrow_id,
                b.borrow_date,
                b.due_date,
                b.return_date,

                m.id AS member_id,
                m.full_name AS member_name,

                bk.title AS book_title

            FROM fines f

            JOIN borrows b
            ON f.borrow_id = b.id

            JOIN members m
            ON b.member_id = m.id

            JOIN books bk
            ON b.book_id = bk.id

            ORDER BY f.id DESC
        """))

        fines = as_dicts(cursor, cursor.fetchall())

        # Convert DATETIME fields to DATE strings
        for fine in fines:

            if fine.get("borrow_date"):
                fine["borrow_date"] = str(fine["borrow_date"]).split(" ")[0]

            if fine.get("due_date"):
                fine["due_date"] = str(fine["due_date"]).split(" ")[0]

            if fine.get("return_date"):
                fine["return_date"] = str(fine["return_date"]).split(" ")[0]

            if fine.get("paid_on"):
                fine["paid_on"] = str(fine["paid_on"]).split(" ")[0]

        return jsonify({
            "success": True,
            "message": "Fines fetched successfully",
            "data": fines
        }), 200


    except Exception as e:


        return jsonify({

            "success":False,

            "message":str(e),

            "data":[]

        }),400


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

fines_bp.add_url_rule(
    "/fines",
    view_func=get_fines,
    methods=["GET"]
)



# ======================================
# Pay Fine
# ======================================


@fines_bp.route("/fines/<int:fine_id>/pay", methods=["POST"])
def pay_fine(fine_id):


    conn = get_db_connection()

    cursor = get_cursor(conn)


    try:


        cursor.execute(
            sql("SELECT * FROM fines WHERE id=%s"),
            (fine_id,)
        )


        fine = as_dict(cursor, cursor.fetchone())



        if not fine:

            return jsonify({

                "error":"Fine not found"

            }),404




        if fine["is_paid"]:


            return jsonify({

                "error":"Fine already paid"

            }),409




        cursor.execute(sql("""

            UPDATE fines

            SET is_paid = TRUE,
                paid_on = %s

            WHERE id=%s

        """),

        (
            date.today(),
            fine_id
        ))



        conn.commit()



        return jsonify({

            "success":True,

            "message":"Fine paid successfully"

        }),200




    except Exception as e:


        conn.rollback()


        return jsonify({

            "error":str(e)

        }),400



    finally:

        cursor.close()

        conn.close()