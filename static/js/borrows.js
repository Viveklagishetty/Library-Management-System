// ======================================
// Borrow Management JS
// ======================================

const BORROW_MEMBER_API = "/members";
const BORROW_BOOK_API = "/books";
const BORROW_API = "/borrow";
const BORROW_ACTIVE_API = "/borrows/active";
const BORROW_OVERDUE_API = "/borrows/overdue";

let memberSelect;
let bookSelect;
let borrowTableBody;
let issueBookBtn;
let overdueTableBody;

document.addEventListener("DOMContentLoaded", () => {
  memberSelect = document.getElementById("memberSelect");
  bookSelect = document.getElementById("bookSelect");
  borrowTableBody = document.getElementById("borrowTableBody");
  issueBookBtn = document.getElementById("issueBookBtn");
  overdueTableBody = document.getElementById("overdueTableBody");

  if (!memberSelect || !bookSelect || !borrowTableBody || !issueBookBtn) {
    return;
  }

  loadBorrowMembers();
  loadBorrowBooks();
  loadBorrows();
  loadOverdues();

  issueBookBtn.addEventListener("click", issueBook);
});

// ======================================
// Load Members Dropdown
// ======================================
async function loadBorrowMembers() {
  try {
    const response = await fetch(BORROW_MEMBER_API);
    const result = await response.json();
    const members = result.data || result;

    if (!memberSelect) return;
    memberSelect.innerHTML = `<option value="">Select Member</option>`;

    members.forEach((member) => {
      const isActive =
        Number(member.is_active) === 1 || member.is_active === true;
      if (isActive) {
        memberSelect.innerHTML += `
                    <option value="${member.id}">
                        ${member.full_name || member.name}
                    </option>
                `;
      }
    });
  } catch (error) {
    console.log("Member Error:", error);
  }
}

// ======================================
// Load Books Dropdown
// ======================================
async function loadBorrowBooks() {
  try {
    const response = await fetch(BORROW_BOOK_API);
    const result = await response.json();
    const books = result.data || result || [];

    if (!bookSelect) return;
    bookSelect.innerHTML = `<option value="">Select Book</option>`;

    books.forEach((book) => {
      if (book.available_copies > 0) {
        bookSelect.innerHTML += `
                    <option value="${book.id}">
                        ${book.title}
                    </option>
                `;
      }
    });
  } catch (error) {
    console.log("Book Error:", error);
  }
}

// ======================================
// Issue Book
// ======================================
async function issueBook() {
  const member_id = memberSelect ? memberSelect.value : null;
  const book_id = bookSelect ? bookSelect.value : null;

  if (!member_id || !book_id) {
    alert("Please select member and book");
    return;
  }

  try {
    const response = await fetch(BORROW_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_id, book_id }),
    });

    const result = await response.json();

    if (response.ok) {
      alert(result.message || "Book issued successfully");
      loadBorrows();
      loadBorrowBooks();
      loadOverdues();
      if (window.loadBooks) window.loadBooks();
      if (window.loadDashboard) window.loadDashboard();

      if (memberSelect) memberSelect.value = "";
      if (bookSelect) bookSelect.value = "";
    } else {
      alert(result.message || result.error || "Failed to issue book");
    }
  } catch (error) {
    console.log("Issue Error:", error);
  }
}

// ======================================
// Load Borrow List
// ======================================
async function loadBorrows() {
  try {
    const response = await fetch(BORROW_ACTIVE_API);
    const result = await response.json();
    const borrows = result.data || result || [];

    if (!borrowTableBody) return;
    borrowTableBody.innerHTML = "";

    if (borrows.length === 0) {
      borrowTableBody.innerHTML = `<tr><td colspan="6" class="text-center">No active borrows</td></tr>`;
      return;
    }

    borrows.forEach((item) => {
      borrowTableBody.innerHTML += `
                <tr>
                    <td>${item.borrow_id}</td>
                    <td>${item.member_name}</td>
                    <td>${item.book_title}</td>
                    <td>${item.borrow_date}</td>
                    <td>${item.due_date}</td>
                    <td>
                        <button class="btn btn-success btn-sm" onclick="returnBook(${item.borrow_id})">
                            Return
                        </button>
                    </td>
                </tr>
            `;
    });

    if (window.loadDashboard) window.loadDashboard();
  } catch (error) {
    console.log("Borrow Load Error:", error);
  }
}

// ======================================
// Return Book
// ======================================
async function returnBook(id) {
  if (!confirm("Return this book?")) return;

  try {
    const response = await fetch(`/return/${id}`, { method: "POST" });
    const result = await response.json();

    if (response.ok) {
      alert(result.message || "Book returned successfully");
      loadBorrows();
      loadBorrowBooks();
      loadOverdues();
      if (window.loadBooks) window.loadBooks();
      if (window.loadDashboard) window.loadDashboard();
      return;
    }

    alert(result.error || result.message || "Failed to return book");
  } catch (error) {
    console.log("Return Error:", error);
  }
}

// ======================================
// Load Overdue Books
// ======================================
async function loadOverdues() {
  if (!overdueTableBody) return;

  try {
    const response = await fetch(BORROW_OVERDUE_API);
    const result = await response.json();
    const rows = result.data || result || [];

    overdueTableBody.innerHTML = "";

    if (rows.length === 0) {
      overdueTableBody.innerHTML = `<tr><td colspan="4" class="text-center">No overdue books</td></tr>`;
      return;
    }

    rows.forEach((row) => {
      overdueTableBody.innerHTML += `
                <tr>
                    <td>${row.member_name || ""}</td>
                    <td>${row.book_title || ""}</td>
                    <td>${row.due_date || ""}</td>
                    <td>${row.overdue_days ?? ""}</td>
                </tr>
            `;
    });
  } catch (error) {
    console.log("Overdue Load Error:", error);
  }
}
