from flask import Blueprint, jsonify
from datetime import date
from config import get_db_connection


fines_bp = Blueprint("fines", __name__)


# ======================================
# Get All Fines
# ======================================

@fines_bp.route("/fines", methods=["GET"])
def get_fines():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)


        cursor.execute("""
            SELECT
                f.id AS fine_id,
                f.amount,
                f.is_paid,
                f.paid_on,

                b.id AS borrow_id,
                b.borrow_date,
                b.due_date,
                b.return_date,

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

        """)


        fines = cursor.fetchall()


        return jsonify({

            "success": True,

            "message": "Fines fetched successfully",

            "data": fines

        }),200


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





# ======================================
# Pay Fine
# ======================================


@fines_bp.route("/fines/<int:fine_id>/pay", methods=["POST"])
def pay_fine(fine_id):


    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)


    try:


        cursor.execute(
            "SELECT * FROM fines WHERE id=%s",
            (fine_id,)
        )


        fine = cursor.fetchone()



        if not fine:

            return jsonify({

                "error":"Fine not found"

            }),404




        if fine["is_paid"]:


            return jsonify({

                "error":"Fine already paid"

            }),409




        cursor.execute("""

            UPDATE fines

            SET is_paid = TRUE,
                paid_on = %s

            WHERE id=%s

        """,

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