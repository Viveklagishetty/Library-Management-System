print("Loading fines.py")

from flask import Blueprint, jsonify, request
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
# Add Fine
# ======================================


@fines_bp.route("/fines", methods=["POST"])
def create_fine():

    data = request.get_json(silent=True) or {}
    member_id = data.get("member_id")
    borrow_id = data.get("borrow_id")
    amount_value = data.get("amount")

    if not member_id or not borrow_id:
        return jsonify({
            "success": False,
            "message": "member_id and borrow_id are required",
            "data": None
        }), 400

    amount = None
    if amount_value not in (None, ""):
        try:
            amount = float(amount_value)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "amount must be a valid number",
                "data": None
            }), 400

    if amount is not None and amount <= 0:
        return jsonify({
            "success": False,
            "message": "amount must be greater than zero",
            "data": None
        }), 400

    conn = get_db_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(sql("SELECT id FROM members WHERE id = %s"), (member_id,))
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Member not found",
                "data": None
            }), 404

        cursor.execute(sql("SELECT id, member_id FROM borrows WHERE id = %s"), (borrow_id,))
        borrow = as_dict(cursor, cursor.fetchone())

        if not borrow:
            return jsonify({
                "success": False,
                "message": "Borrow record not found",
                "data": None
            }), 404

        if int(borrow["member_id"]) != int(member_id):
            return jsonify({
                "success": False,
                "message": "This borrow record does not belong to the selected member",
                "data": None
            }), 400

        cursor.execute(sql("SELECT id FROM fines WHERE borrow_id = %s"), (borrow_id,))
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "A fine already exists for this borrow record",
                "data": None
            }), 409

        if amount is None:
            from datetime import datetime
            due_date = borrow.get("due_date")
            return_date = borrow.get("return_date")
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
            if isinstance(return_date, str):
                return_date = datetime.strptime(return_date, "%Y-%m-%d").date()
            if return_date is None:
                return_date = date.today()
            if due_date is None:
                due_date = return_date
            overdue_days = max(0, (return_date - due_date).days)
            amount = overdue_days * 5

        cursor.execute(sql("""
            INSERT INTO fines (borrow_id, member_id, amount, is_paid)
            VALUES (%s, %s, %s, FALSE)
        """), (borrow_id, member_id, amount))

        fine_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Fine added successfully",
            "data": {
                "fine_id": fine_id,
                "member_id": member_id,
                "borrow_id": borrow_id,
                "amount": amount
            }
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": str(e),
            "data": None
        }), 400

    finally:
        cursor.close()
        conn.close()


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