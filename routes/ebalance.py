from flask import Blueprint, request, jsonify
from config import get_db_connection

ebalance_bp = Blueprint("ebalance", __name__)


# ---------------- HELPERS ---------------- #

def is_mysql(conn):
    return hasattr(conn, "cursor") and conn.__class__.__module__.startswith("mysql")


def get_cursor(conn):
    if is_mysql(conn):
        return conn.cursor(dictionary=True)
    return conn.cursor()


def q(conn, sql):
    """Translate %s placeholders to ? for sqlite connections."""
    return sql if is_mysql(conn) else sql.replace("%s", "?")


def to_dict(cursor, row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def to_dicts(cursor, rows):
    return [to_dict(cursor, row) for row in rows]


def get_balance(conn, member_id):
    cursor = get_cursor(conn)
    cursor.execute(
        q(conn, """
            SELECT
                COALESCE(SUM(CASE WHEN type = 'credit' THEN amount ELSE -amount END), 0) AS balance
            FROM ebalance
            WHERE member_id = %s
        """),
        (member_id,)
    )
    row = to_dict(cursor, cursor.fetchone())
    cursor.close()
    return float(row["balance"]) if row and row["balance"] is not None else 0.0


# ---------------- GET MEMBER BALANCE + HISTORY ---------------- #

@ebalance_bp.route("/ebalance/<int:member_id>", methods=["GET"])
def get_member_balance(member_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute(
            q(conn, "SELECT id FROM members WHERE id = %s"),
            (member_id,)
        )

        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Member not found", "data": None}), 404

        balance = get_balance(conn, member_id)

        cursor.execute(
            q(conn, """
                SELECT id, type, amount, reference_type, reference_id, description, created_at
                FROM ebalance
                WHERE member_id = %s
                ORDER BY id DESC
            """),
            (member_id,)
        )
        history = to_dicts(cursor, cursor.fetchall())

        return jsonify({
            "success": True,
            "message": "Balance fetched successfully",
            "data": {
                "member_id": member_id,
                "balance": balance,
                "transactions": history
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e), "data": None}), 400

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ---------------- GET ALL TRANSACTIONS (ADMIN) ---------------- #

@ebalance_bp.route("/ebalance", methods=["GET"])
def get_all_transactions():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute("""
            SELECT
                e.id, e.type, e.amount, e.reference_type, e.reference_id,
                e.description, e.created_at,
                m.full_name AS member_name
            FROM ebalance e
            JOIN members m ON e.member_id = m.id
            ORDER BY e.id DESC
        """)
        transactions = to_dicts(cursor, cursor.fetchall())

        return jsonify({
            "success": True,
            "message": "Transactions fetched successfully",
            "data": transactions
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e), "data": []}), 400

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ---------------- TOP UP BALANCE ---------------- #

@ebalance_bp.route("/ebalance/topup", methods=["POST"])
def topup_balance():
    conn = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}
        member_id = data.get("member_id")
        amount = data.get("amount")
        description = data.get("description", "Balance top-up")

        if not member_id or amount is None:
            return jsonify({"success": False, "message": "member_id and amount are required", "data": None}), 400

        if float(amount) <= 0:
            return jsonify({"success": False, "message": "amount must be greater than zero", "data": None}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute(
            q(conn, "SELECT id FROM members WHERE id = %s"),
            (member_id,)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Member not found", "data": None}), 404

        cursor.execute(
            q(conn, """
                INSERT INTO ebalance (member_id, type, amount, reference_type, reference_id, description)
                VALUES (%s, 'credit', %s, 'topup', NULL, %s)
            """),
            (member_id, amount, description)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Balance topped up successfully",
            "data": {"member_id": member_id, "balance": get_balance(conn, member_id)}
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e), "data": None}), 400

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ---------------- PAY A FINE FROM BALANCE ---------------- #

@ebalance_bp.route("/ebalance/pay-fine/<int:fine_id>", methods=["POST"])
def pay_fine_from_balance(fine_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute(
            q(conn, "SELECT * FROM fines WHERE id = %s"),
            (fine_id,)
        )
        fine = to_dict(cursor, cursor.fetchone())

        if not fine:
            return jsonify({"success": False, "message": "Fine not found", "data": None}), 404

        if fine["is_paid"]:
            return jsonify({"success": False, "message": "Fine already paid", "data": None}), 409

        member_id = fine["member_id"]
        amount = float(fine["amount"])
        balance = get_balance(conn, member_id)

        if balance < amount:
            return jsonify({
                "success": False,
                "message": f"Insufficient balance. Available: {balance:.2f}, Required: {amount:.2f}",
                "data": None
            }), 402

        cursor.execute(
            q(conn, """
                INSERT INTO ebalance (member_id, type, amount, reference_type, reference_id, description)
                VALUES (%s, 'debit', %s, 'fine', %s, %s)
            """),
            (member_id, amount, fine_id, f"Fine #{fine_id} paid from balance")
        )

        from datetime import date
        cursor.execute(
            q(conn, "UPDATE fines SET is_paid = TRUE, paid_on = %s WHERE id = %s"),
            (date.today(), fine_id)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Fine paid successfully from balance",
            "data": {"member_id": member_id, "balance": get_balance(conn, member_id)}
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e), "data": None}), 400

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ---------------- MANUAL DEDUCTION (ADMIN) ---------------- #

@ebalance_bp.route("/ebalance/deduct", methods=["POST"])
def deduct_balance():
    conn = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}
        member_id = data.get("member_id")
        amount = data.get("amount")
        description = data.get("description", "Manual deduction")

        if not member_id or amount is None:
            return jsonify({"success": False, "message": "member_id and amount are required", "data": None}), 400

        if float(amount) <= 0:
            return jsonify({"success": False, "message": "amount must be greater than zero", "data": None}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute(
            q(conn, "SELECT id FROM members WHERE id = %s"),
            (member_id,)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Member not found", "data": None}), 404

        balance = get_balance(conn, member_id)
        if balance < float(amount):
            return jsonify({"success": False, "message": "Insufficient balance", "data": None}), 402

        cursor.execute(
            q(conn, """
                INSERT INTO ebalance (member_id, type, amount, reference_type, reference_id, description)
                VALUES (%s, 'debit', %s, 'manual', NULL, %s)
            """),
            (member_id, amount, description)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Balance deducted successfully",
            "data": {"member_id": member_id, "balance": get_balance(conn, member_id)}
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e), "data": None}), 400

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
