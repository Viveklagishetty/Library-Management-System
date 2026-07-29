from flask import Blueprint, request, jsonify, session
from datetime import date, timedelta
from config import get_db_connection

borrows_bp = Blueprint('borrows', __name__)

FINE_PER_DAY = 5
BORROW_PERIOD_DAYS = 14


# Issue a book to an active library member.
@borrows_bp.route('/borrow', methods=['POST'])
def issue_borrow():
    """Issue a book to an active member."""
    data = request.get_json(silent=True) or {}
    member_id = data.get('member_id')
    book_id = data.get('book_id')

    if not member_id or not book_id:
        return jsonify({"error": "member_id and book_id are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check that the member exists and is active.
        cursor.execute(
            "SELECT id, is_active FROM members WHERE id = %s", (member_id,)
        )
        member = cursor.fetchone()

        if not member:
            return jsonify({"error": "Member not found"}), 404

        if not member['is_active']:
            return jsonify({"error": "Member is deactivated"}), 403

        # Prevent borrowing when the member has unpaid fines.
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM fines WHERE member_id = %s AND is_paid = FALSE",
            (member_id,)
        )

        if cursor.fetchone()['cnt'] > 0:
            return jsonify({
                "error": "Member has unpaid fines. Clear them before borrowing."
            }), 403

        # Check that the book exists and is available.
        cursor.execute(
            "SELECT id, available_copies FROM books WHERE id = %s", (book_id,)
        )
        book = cursor.fetchone()

        if not book:
            return jsonify({"error": "Book not found"}), 404

        if book['available_copies'] <= 0:
            return jsonify({"error": "No available copies of this book"}), 409

        # Create the borrow record with a 14-day due date.
        borrow_date = date.today()
        due_date = borrow_date + timedelta(days=BORROW_PERIOD_DAYS)

        cursor.execute(
            """INSERT INTO borrows (member_id, book_id, borrow_date, due_date, status)
               VALUES (%s, %s, %s, %s, 'active')""",
            (member_id, book_id, borrow_date, due_date)
        )
        borrow_id = cursor.lastrowid

        # Reduce the available book count after issuing the book.
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id = %s",
            (book_id,)
        )

        conn.commit()

        return jsonify({
            "message": "Book issued successfully",
            "borrow_id": borrow_id,
            "borrow_date": str(borrow_date),
            "due_date": str(due_date)
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


# Return a borrowed book and apply a fine for overdue returns.
@borrows_bp.route('/return/<int:borrow_id>', methods=['POST'])
def return_book(borrow_id):
    """Return a borrowed book and create a fine if overdue."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Find the borrow record and check its current status.
        cursor.execute(
            "SELECT * FROM borrows WHERE id = %s", (borrow_id,)
        )
        borrow = cursor.fetchone()

        if not borrow:
            return jsonify({"error": "Borrow record not found"}), 404

        if borrow['status'] == 'returned':
            return jsonify({
                "error": "This book has already been returned"
            }), 409

        return_date = date.today()

        # Mark the borrow as returned.
        cursor.execute(
            "UPDATE borrows SET return_date = %s, status = 'returned' WHERE id = %s",
            (return_date, borrow_id)
        )

        # Increase the available book count after the return.
        cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = %s",
            (borrow['book_id'],)
        )

        # Calculate and save a fine when the book is returned late.
        due_date = borrow['due_date']
        overdue_days = (return_date - due_date).days
        fine_created = None

        if overdue_days > 0:
            fine_amount = overdue_days * FINE_PER_DAY

            cursor.execute(
                """INSERT INTO fines (borrow_id, member_id, amount, is_paid)
                   VALUES (%s, %s, %s, FALSE)""",
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
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch active borrows with related member and book information.
        cursor.execute(
            """SELECT b.id AS borrow_id, b.borrow_date, b.due_date,
                      m.id AS member_id, m.full_name AS member_name,
                      bk.id AS book_id, bk.title AS book_title
               FROM borrows b
               JOIN members m ON b.member_id = m.id
               JOIN books bk ON b.book_id = bk.id
               WHERE b.status = 'active'
               ORDER BY b.due_date ASC"""
        )
        rows = cursor.fetchall()

        # Convert date values to JSON-friendly strings.
        for r in rows:
            r['borrow_date'] = str(r['borrow_date'])
            r['due_date'] = str(r['due_date'])

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
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch active borrows whose due date has already passed.
        cursor.execute(
            """SELECT b.id AS borrow_id, b.borrow_date, b.due_date,
                      m.id AS member_id, m.full_name AS member_name,
                      bk.id AS book_id, bk.title AS book_title
               FROM borrows b
               JOIN members m ON b.member_id = m.id
               JOIN books bk ON b.book_id = bk.id
               WHERE b.status = 'active' AND b.due_date < %s
               ORDER BY b.due_date ASC""",
            (date.today(),)
        )
        rows = cursor.fetchall()

        # Calculate overdue days and the current projected fine.
        today = date.today()

        for r in rows:
            overdue_days = (today - r['due_date']).days
            r['overdue_days'] = overdue_days
            r['projected_fine'] = overdue_days * FINE_PER_DAY
            r['borrow_date'] = str(r['borrow_date'])
            r['due_date'] = str(r['due_date'])

        return jsonify(rows), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()