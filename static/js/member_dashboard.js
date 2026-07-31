// ======================================
// Member Dashboard JS
// ======================================

document.addEventListener("DOMContentLoaded", () => {
  loadMyBooks();
  loadMyBorrows();
  loadMyFines();
  loadMyWallet();
});

// ======================================
// Browse Books
// ======================================

async function loadMyBooks() {
  try {
    const response = await fetch("/books");
    const result = await response.json();

    if (!response.ok)
      throw new Error(result.message || "Unable to load books.");

    const books = result.data || [];
    const tbody =
      document.getElementById("myBooksTableBody") ||
      document.getElementById("booksTableBody");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (books.length === 0) {
      renderTableMessage(tbody, 4, "No books available");
      return;
    }

    books.forEach((book) => {
      tbody.innerHTML += `
                <tr>
                    <td>${book.title}</td>
                    <td>${book.author}</td>
                    <td>${book.genre || "-"}</td>
                    <td>${book.available_copies ?? book.total_copies}</td>
                </tr>
            `;
    });
  } catch (error) {
    console.error("Load Books Error:", error);
    const tbody =
      document.getElementById("myBooksTableBody") ||
      document.getElementById("booksTableBody");
    if (tbody) renderTableMessage(tbody, 4, "Unable to load books.");
  }
}

// ======================================
// My Borrow History
// ======================================

async function loadMyBorrows() {
  try {
    const response = await fetch(`/members/${MEMBER_ID}/history`);
    const history = await response.json();

    const tbody = document.getElementById("myBorrowsTableBody");
    tbody.innerHTML = "";

    if (!Array.isArray(history) || history.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">No borrow history yet</td></tr>`;
    } else {
      history.forEach((item) => {
        tbody.innerHTML += `
                    <tr>
                        <td>${item.title}</td>
                        <td>${item.author}</td>
                        <td>${item.borrow_date}</td>
                        <td>${item.due_date}</td>
                        <td>${item.return_date || "-"}</td>
                        <td>
                            ${
                              item.status === "active"
                                ? `<span class="badge bg-warning">Active</span>`
                                : `<span class="badge bg-success">Returned</span>`
                            }
                        </td>
                    </tr>
                `;
      });
    }

    document.getElementById("myTotalHistory").innerText = Array.isArray(history)
      ? history.length
      : 0;
    document.getElementById("myActiveBorrows").innerText = Array.isArray(
      history,
    )
      ? history.filter((h) => h.status === "active").length
      : 0;
  } catch (error) {
    console.log("Load My Borrows Error:", error);
  }
}

// ======================================
// My Fines
// ======================================

async function loadMyFines() {
  try {
    const response = await fetch("/fines");
    const result = await response.json();
    const allFines = result.data || [];
    const myFines = allFines.filter((f) => f.member_id === MEMBER_ID);

    const tbody = document.getElementById("myFinesTableBody");
    tbody.innerHTML = "";

    if (myFines.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">No fines on your account</td></tr>`;
    } else {
      myFines.forEach((fine) => {
        tbody.innerHTML += `
                    <tr>
                        <td>${fine.book_title}</td>
                        <td>${fine.due_date}</td>
                        <td>${fine.return_date || "-"}</td>
                        <td>₹${Number(fine.amount || 0).toFixed(2)}</td>
                        <td>
                            ${
                              fine.is_paid
                                ? `<span class="badge bg-success">Paid</span>`
                                : `<span class="badge bg-danger">Unpaid</span>`
                            }
                        </td>
                        <td>
                            ${
                              fine.is_paid
                                ? `<button class="btn btn-secondary btn-sm" disabled>Paid</button>`
                                : `<button class="btn btn-success btn-sm" onclick="payFineFromWallet(${fine.fine_id})">Pay from Wallet</button>`
                            }
                        </td>
                    </tr>
                `;
      });
    }

    const unpaidTotal = myFines
      .filter((f) => !f.is_paid)
      .reduce((sum, f) => sum + Number(f.amount || 0), 0);

    document.getElementById("myUnpaidFines").innerText =
      `₹${unpaidTotal.toFixed(2)}`;
  } catch (error) {
    console.log("Load My Fines Error:", error);
  }
}

async function payFineFromWallet(fineId) {
  if (!confirm("Pay this fine from your wallet balance?")) {
    return;
  }

  try {
    const response = await fetch(`/ebalance/pay-fine/${fineId}`, {
      method: "POST",
    });
    const result = await response.json();

    alert(result.message);

    if (response.ok) {
      loadMyFines();
      loadMyWallet();
    }
  } catch (error) {
    console.log("Pay Fine Error:", error);
  }
}

// ======================================
// My Wallet
// ======================================

async function loadMyWallet() {
  try {
    const response = await fetch(`/ebalance/${MEMBER_ID}`);
    const result = await response.json();
    const data = result.data || { balance: 0, transactions: [] };

    document.getElementById("myWalletBalance").innerText =
      `₹${Number(data.balance || 0).toFixed(2)}`;
    document.getElementById("walletBalanceText").innerText =
      `₹${Number(data.balance || 0).toFixed(2)}`;

    const tbody = document.getElementById("myWalletTableBody");
    tbody.innerHTML = "";

    const transactions = data.transactions || [];

    if (transactions.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center">No transactions yet</td></tr>`;
      return;
    }

    transactions.forEach((tx) => {
      tbody.innerHTML += `
                <tr>
                    <td>${tx.created_at}</td>
                    <td>
                        ${
                          tx.type === "credit"
                            ? `<span class="badge bg-success">Credit</span>`
                            : `<span class="badge bg-danger">Debit</span>`
                        }
                    </td>
                    <td>₹${Number(tx.amount || 0).toFixed(2)}</td>
                    <td>${tx.description || "-"}</td>
                </tr>
            `;
    });
  } catch (error) {
    console.log("Load Wallet Error:", error);
  }
}

async function submitTopup() {
  const amountInput = document.getElementById("topupAmount");
  const amount = parseFloat(amountInput.value);

  if (!amount || amount <= 0) {
    alert("Please enter a valid amount.");
    return;
  }

  try {
    const response = await fetch("/ebalance/topup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        member_id: MEMBER_ID,
        amount: amount,
        description: "Wallet top-up",
      }),
    });

    const result = await response.json();
    alert(result.message);

    if (response.ok) {
      amountInput.value = "";
      const modalEl = document.getElementById("topupModal");
      bootstrap.Modal.getInstance(modalEl)?.hide();
      loadMyWallet();
    }
  } catch (error) {
    console.log("Topup Error:", error);
  }
}
