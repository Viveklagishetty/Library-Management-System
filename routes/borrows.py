from flask import Blueprint, request, jsonify, session
from datetime import date, datetime, timedelta
from config import DB_TYPE, get_db_connection

borrows_bp = Blueprint('borrows', __name__)

FINE_PER_DAY = 5
BORROW_PERIOD_DAYS = 14

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


def parse_date(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.fromisoformat(text).date()
            except ValueError as exc:
                raise ValueError("Invalid date format. Use YYYY-MM-DD") from exc

    raise ValueError("Invalid date format")


# Issue a book to an active library member.
@borrows_bp.route('/borrow', methods=['POST'])
def issue_borrow():
    """Issue a book to an active member."""
    data = request.get_json(silent=True) or {}
    member_id = data.get('member_id')
    book_id = data.get('book_id')

    if not member_id or not book_id:
        return jsonify({"error": "member_id and book_id are required"}), 400

    try:
        borrow_date = parse_date(data.get('borrow_date')) or date.today()
        due_date = parse_date(data.get('due_date')) or (borrow_date + timedelta(days=BORROW_PERIOD_DAYS))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if due_date < borrow_date:
        return jsonify({"error": "Due date cannot be earlier than borrow date"}), 400

    conn = get_db_connection()
    cursor = get_cursor(conn)

    try:
        # Check that the member exists and is active.
        cursor.execute(
            sql_query("SELECT id, is_active FROM members WHERE id = %s"), (member_id,)
        )
        member = row_to_dict(cursor, cursor.fetchone())

        if not member:
            return jsonify({"error": "Member not found"}), 404

        if not (Number(member.get('is_active', 1)) == 1 or member.get('is_active') is True):
            return jsonify({"error": "Member is deactivated"}), 403

        # Prevent borrowing when the member has unpaid fines.
        cursor.execute(
            sql_query("SELECT COUNT(*) AS cnt FROM fines WHERE member_id = %s AND is_paid = FALSE"),
            (member_id,)
        )
        cnt_row = row_to_dict(cursor, cursor.fetchone())

        if (cnt_row.get('cnt') or 0) > 0:
            return jsonify({
                "error": "Member has unpaid fines. Clear them before borrowing."
            }), 403

        # Check that the book exists and is available.
        cursor.execute(
            sql_query("SELECT id, available_copies FROM books WHERE id = %s"), (book_id,)
        )
        book = row_to_dict(cursor, cursor.fetchone())

        if not book:
            return jsonify({"error": "Book not found"}), 404

        if book['available_copies'] <= 0:
            return jsonify({"error": "No available copies of this book"}), 409

        cursor.execute(
            sql_query("""INSERT INTO borrows (member_id, book_id, borrow_date, due_date, status)
               VALUES (%s, %s, %s, %s, 'active')"""),
            (member_id, book_id, borrow_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d"))
        )
        borrow_id = cursor.lastrowid

        # Reduce the available book count after issuing the book.
        cursor.execute(
            sql_query("UPDATE books SET available_copies = available_copies - 1 WHERE id = %s"),
            (book_id,)
        )

        conn.commit()

        return jsonify({
            "message": "Book issued successfully",
            "borrow_id": borrow_id,
            "borrow_date": borrow_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d")
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


def Number(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


# Get a single borrow record for fine calculation and editing.
@borrows_bp.route('/borrow/<int:borrow_id>', methods=['GET'])
def get_borrow(borrow_id):
    conn = get_db_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            sql_query("SELECT id, member_id, book_id, borrow_date, due_date, return_date, status FROM borrows WHERE id = %s"),
            (borrow_id,)
        )
        borrow = row_to_dict(cursor, cursor.fetchone())

        if not borrow:
            return jsonify({"success": False, "message": "Borrow record not found", "data": None}), 404

        if borrow.get("borrow_date"):
            borrow["borrow_date"] = str(borrow["borrow_date"]).split(" ")[0]

        if borrow.get("due_date"):
            borrow["due_date"] = str(borrow["due_date"]).split(" ")[0]

        if borrow.get("return_date"):
            borrow["return_date"] = str(borrow["return_date"]).split(" ")[0]

        return jsonify({"success": True, "message": "Borrow fetched successfully", "data": borrow}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e), "data": None}), 400

    finally:
        cursor.close()
        conn.close()


# Return a borrowed book and apply a fine for overdue returns.
@borrows_bp.route('/return/<int:borrow_id>', methods=['POST'])
def return_book(borrow_id):
    """Return a borrowed book and create a fine if overdue."""
    conn = get_db_connection()
    cursor = get_cursor(conn)

    try:
        # Find the borrow record and check its current status.
        cursor.execute(
            sql_query("SELECT * FROM borrows WHERE id = %s"), (borrow_id,)
        )
        borrow = row_to_dict(cursor, cursor.fetchone())

        if not borrow:
            return jsonify({"error": "Borrow record not found"}), 404

        if borrow['status'] == 'returned':
            return jsonify({
                "error": "This book has already been returned"
            }), 409

        return_date = date.today()

        # Mark the borrow as returned.
        cursor.execute(
            sql_query("UPDATE borrows SET return_date = %s, status = 'returned' WHERE id = %s"),
            (return_date, borrow_id)
        )

        # Increase the available book count after the return.
        cursor.execute(
            sql_query("UPDATE books SET available_copies = available_copies + 1 WHERE id = %s"),
            (borrow['book_id'],)
        )

        # Calculate and save a fine when the book is returned late.
        due = borrow['due_date']
        if isinstance(due, str):
            due = datetime.strptime(due, "%Y-%m-%d").date()

        overdue_days = (return_date - due).days
        fine_created = None

        if overdue_days > 0:
            fine_amount = overdue_days * FINE_PER_DAY

            cursor.execute(
                sql_query("""INSERT INTO fines (borrow_id, member_id, amount, is_paid)
                   VALUES (%s, %s, %s, FALSE)"""),
                (borrow_id, borrow['member_id'], fine_amount)
            )

            fine_created = {
                "amount": fine_amount,
                "overdue_days": overdue_days
            }

        conn.commit()

        response = {
            "message": "Book returned successfully",
            "borrow_id": borrow_id,
            "return_date": str(return_date),
            "fine": fine_created
        }

        return jsonify(response), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


# Get all currently borrowed books with member and book details.
@borrows_bp.route('/borrows/active', methods=['GET'])
def get_active_borrows():
    """Return all active borrows with member and book details."""
    conn = get_db_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            sql_query("""SELECT b.id AS borrow_id, b.borrow_date, b.due_date,
                      m.id AS member_id, m.full_name AS member_name,
                      bk.id AS book_id, bk.title AS book_title
               FROM borrows b
               JOIN members m ON b.member_id = m.id
               JOIN books bk ON b.book_id = bk.id
               WHERE b.status = 'active'
               ORDER BY b.due_date ASC""")
        )
        rows = rows_to_dicts(cursor, cursor.fetchall())

        for r in rows:

            if r["borrow_date"]:
                r["borrow_date"] = str(r["borrow_date"]).split(" ")[0]

            if r["due_date"]:
                r["due_date"] = str(r["due_date"]).split(" ")[0]
        return jsonify(rows), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


# Get all active books that have passed their due date.
@borrows_bp.route('/borrows/overdue', methods=['GET'])
def get_overdue_borrows():
    """Return active borrows that are past their due date."""
    conn = get_db_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            sql_query("""SELECT b.id AS borrow_id, b.borrow_date, b.due_date,
                      m.id AS member_id, m.full_name AS member_name,
                      bk.id AS book_id, bk.title AS book_title
               FROM borrows b
               JOIN members m ON b.member_id = m.id
               JOIN books bk ON b.book_id = bk.id
               WHERE b.status = 'active' AND b.due_date < %s
               ORDER BY b.due_date ASC"""),
            (date.today(),)
        )
        rows = rows_to_dicts(cursor, cursor.fetchall())

        today = date.today()

        for r in rows:

            due = r["due_date"]

            # Handle DATETIME objects
            if isinstance(due, datetime):
                due = due.date()

            # Handle DATE strings
            elif isinstance(due, str):
                due = datetime.strptime(
                    due.split(" ")[0],
                    "%Y-%m-%d"
                ).date()

            overdue_days = (today - due).days

            r["overdue_days"] = overdue_days
            r["projected_fine"] = overdue_days * FINE_PER_DAY

            if r["borrow_date"]:
                r["borrow_date"] = str(r["borrow_date"]).split(" ")[0]

            if r["due_date"]:
                r["due_date"] = str(r["due_date"]).split(" ")[0]
        print(rows)

        return jsonify(rows), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()