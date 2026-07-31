from flask import Blueprint, request, jsonify
from config import DB_TYPE, get_db_connection

members_bp = Blueprint("members", __name__)


def is_mysql():
    return DB_TYPE == "mysql"


def serialize_member(m):
    if not m:
        return m
    row = dict(m) if not isinstance(m, dict) else m
    formatted = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            formatted[k] = v.isoformat()
        elif hasattr(v, "strftime"):
            formatted[k] = v.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted[k] = v
    return formatted


# ---------------- GET ALL MEMBERS ---------------- #

@members_bp.route("/members", methods=["GET"])
def get_members():
    try:
        conn = get_db_connection()

        link_sql = """
            UPDATE members m
            INNER JOIN users u ON m.email = u.email
            SET m.user_id = u.id
            WHERE m.user_id IS NULL
        """ if is_mysql() else """
            UPDATE members
            SET user_id = (SELECT id FROM users WHERE users.email = members.email LIMIT 1)
            WHERE user_id IS NULL AND email IN (SELECT email FROM users);
        """

        sync_sql = """
            INSERT INTO members (user_id, full_name, email, is_active)
            SELECT u.id, u.username, u.email, 1
            FROM users u
            WHERE LOWER(u.role) = 'member'
              AND u.id NOT IN (SELECT m.user_id FROM members m WHERE m.user_id IS NOT NULL)
              AND u.email NOT IN (SELECT m.email FROM members m WHERE m.email IS NOT NULL)
        """

        if is_mysql():  # MySQL
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(link_sql)
                cursor.execute(sync_sql)
                conn.commit()
            except Exception as sync_err:
                conn.rollback()
                print("Sync Warning:", sync_err)

            cursor.execute("SELECT * FROM members ORDER BY id DESC")
            raw_members = cursor.fetchall()
            cursor.close()
        else:  # SQLite
            try:
                conn.execute(link_sql)
                conn.execute(sync_sql)
                conn.commit()
            except Exception as sync_err:
                conn.rollback()
                print("Sync Warning:", sync_err)

            cursor = conn.execute("SELECT * FROM members ORDER BY id DESC")
            raw_members = [dict(row) for row in cursor.fetchall()]

        conn.close()

        members = [serialize_member(m) for m in raw_members]
        return jsonify(members), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- GET SINGLE MEMBER ---------------- #

@members_bp.route("/members/<int:id>", methods=["GET"])
def get_member(id):
    try:
        conn = get_db_connection()

        if is_mysql():  # MySQL
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM members WHERE id=%s", (id,))
            member = cursor.fetchone()
            cursor.close()

        else:  # SQLite
            cursor = conn.execute("SELECT * FROM members WHERE id=?", (id,))
            row = cursor.fetchone()
            member = dict(row) if row else None

        conn.close()

        if not member:
            return jsonify({"error": "Member not found"}), 404

        return jsonify(serialize_member(member)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- ADD MEMBER ---------------- #

@members_bp.route("/members", methods=["POST"])
def add_member():
    try:
        data = request.get_json() or {}

        raw_user_id = data.get("user_id")
        user_id = int(raw_user_id) if raw_user_id and str(raw_user_id).strip().isdigit() else None
        full_name = (data.get("full_name") or "").strip()
        email = (data.get("email") or "").strip()
        phone = (data.get("phone") or "").strip() or None

        if not full_name or not email:
            return jsonify({"error": "Full name and Email are required."}), 400

        conn = get_db_connection()

        if is_mysql():  # MySQL
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
        data = request.get_json() or {}

        full_name = data.get("full_name")
        email = data.get("email")
        phone = data.get("phone")
        is_active = data.get("is_active")

        conn = get_db_connection()

        if is_mysql():  # MySQL
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

        if is_mysql():  # MySQL
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (id,))
            raw_history = cursor.fetchall()
            cursor.close()

        else:  # SQLite
            query = query.replace("%s", "?")
            cursor = conn.execute(query, (id,))
            raw_history = [dict(row) for row in cursor.fetchall()]

        conn.close()

        history = [serialize_member(h) for h in raw_history]
        return jsonify(history), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- DELETE MEMBER ---------------- #

@members_bp.route("/members/<int:id>", methods=["DELETE"])
def delete_member(id):
    try:
        conn = get_db_connection()

        if is_mysql():  # MySQL
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