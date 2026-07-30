from flask import Blueprint, request, jsonify
from config import get_db_connection

members_bp = Blueprint("members", __name__)

# ---------------- GET ALL MEMBERS ---------------- #

@members_bp.route("/members", methods=["GET"])
def get_members():
    try:
        conn = get_db_connection()

        if hasattr(conn, "cursor"):  # MySQL
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM members")
            members = cursor.fetchall()
            cursor.close()
        else:  # SQLite
            cursor = conn.execute("SELECT * FROM members")
            members = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify(members), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------------- GET SINGLE MEMBER ---------------- #

@members_bp.route("/members/<int:id>", methods=["GET"])
def get_member(id):
    try:
        conn = get_db_connection()

        if hasattr(conn, "cursor"):  # MySQL
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM members WHERE id=%s",
                (id,)
            )
            member = cursor.fetchone()
            cursor.close()

        else:  # SQLite
            cursor = conn.execute(
                "SELECT * FROM members WHERE id=?",
                (id,)
            )
            member = dict(cursor.fetchone())

        conn.close()

        return jsonify(member), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------------- ADD MEMBER ---------------- #

@members_bp.route("/members", methods=["POST"])
def add_member():
    try:
        data = request.get_json()

        user_id = data.get("user_id")
        full_name = data.get("full_name")
        email = data.get("email")
        phone = data.get("phone")

        conn = get_db_connection()

        if hasattr(conn, "cursor"):  # MySQL
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO members(user_id, full_name, email, phone)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, full_name, email, phone)
            )

            conn.commit()
            cursor.close()

        else:  # SQLite
            conn.execute(
                """
                INSERT INTO members(user_id, full_name, email, phone)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, full_name, email, phone)
            )

            conn.commit()

        conn.close()

        return jsonify({"message": "Member added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- UPDATE MEMBER ---------------- #

@members_bp.route("/members/<int:id>", methods=["PUT"])
def update_member(id):
    try:
        data = request.get_json()

        full_name = data.get("full_name")
        email = data.get("email")
        phone = data.get("phone")
        is_active = data.get("is_active")

        conn = get_db_connection()

        if hasattr(conn, "cursor"):  # MySQL
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE members
                SET full_name=%s,
                    email=%s,
                    phone=%s,
                    is_active=%s
                WHERE id=%s
                """,
                (full_name, email, phone, is_active, id)
            )

            conn.commit()
            cursor.close()

        else:  # SQLite
            conn.execute(
                """
                UPDATE members
                SET full_name=?,
                    email=?,
                    phone=?,
                    is_active=?
                WHERE id=?
                """,
                (full_name, email, phone, is_active, id)
            )

            conn.commit()

        conn.close()

        return jsonify({"message": "Member updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- MEMBER BORROW HISTORY ---------------- #

@members_bp.route("/members/<int:id>/history", methods=["GET"])
def member_history(id):
    try:
        conn = get_db_connection()

        query = """
        SELECT
            b.title,
            b.author,
            br.borrow_date,
            br.due_date,
            br.return_date,
            br.status
        FROM borrows br
        JOIN books b
            ON br.book_id = b.id
        WHERE br.member_id = %s
        ORDER BY br.borrow_date DESC
        """

        if hasattr(conn, "cursor"):  # MySQL
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (id,))
            history = cursor.fetchall()
            cursor.close()

        else:  # SQLite
            query = query.replace("%s", "?")
            cursor = conn.execute(query, (id,))
            history = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify(history), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


    # ---------------- DELETE MEMBER ---------------- #

@members_bp.route("/members/<int:id>", methods=["DELETE"])
def delete_member(id):
    try:
        conn = get_db_connection()

        if hasattr(conn, "cursor"):  # MySQL

            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM members WHERE id=%s",
                (id,)
            )

            conn.commit()
            cursor.close()

        else:  # SQLite

            conn.execute(
                "DELETE FROM members WHERE id=?",
                (id,)
            )

            conn.commit()

        conn.close()

        return jsonify({
            "message": "Member deleted successfully"
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400