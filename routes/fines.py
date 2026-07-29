from flask import Blueprint, jsonify
from datetime import date
from config import get_db_connection

fines_bp = Blueprint('fines', __name__)


# Mark a fine as paid so the member can borrow books again.
@fines_bp.route('/fines/<int:fine_id>/pay', methods=['POST'])
def pay_fine(fine_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM fines WHERE id = %s", (fine_id,)
        )
        fine = cursor.fetchone()

        if not fine:
            return jsonify({"error": "Fine not found"}), 404

        if fine['is_paid']:
            return jsonify({
                "error": "This fine has already been paid"
            }), 409

        cursor.execute(
            "UPDATE fines SET is_paid = TRUE, paid_on = %s WHERE id = %s",
            (date.today(), fine_id)
        )
        conn.commit()

        return jsonify({
            "message": "Fine marked as paid",
            "fine_id": fine_id,
            "amount": str(fine['amount']),
            "paid_on": str(date.today())
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()