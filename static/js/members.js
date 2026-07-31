// ======================================
// Members Management JS
// ======================================

const MEMBERS_API = "/members";

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("membersTableBody");
  if (!table) {
    return;
  }

  loadMembers();

  const saveMemberBtn = document.getElementById("saveMemberBtn");
  if (saveMemberBtn) {
    saveMemberBtn.addEventListener("click", handleSaveMember);
  }
});

// Load Members
async function loadMembers() {
  const table = document.getElementById("membersTableBody");
  try {
    const response = await fetch(MEMBERS_API);
    const result = await response.json();

    if (!response.ok || result.error) {
      if (table) {
        table.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${result.error || "Failed to load members"}</td></tr>`;
      }
      return;
    }

    const members = Array.isArray(result) ? result : result.data || [];
    renderMembers(members);

    if (window.loadBorrowMembers) {
      window.loadBorrowMembers();
    }
  } catch (error) {
    console.log("Member Error:", error);
    if (table) {
      table.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error loading members. Please try again.</td></tr>`;
    }
  }
}

// Display Members
function renderMembers(members) {
  const table = document.getElementById("membersTableBody");
  if (!table) return;

  table.innerHTML = "";

  if (!Array.isArray(members) || members.length === 0) {
    table.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No members found.</td></tr>`;
    return;
  }

  members.forEach((member) => {
    const isActive =
      Number(member.is_active) === 1 || member.is_active === true;
    const statusBadge = isActive
      ? `<span class="badge bg-success">Active</span>`
      : `<span class="badge bg-danger">Inactive</span>`;

    const toggleLabel = isActive ? "Deactivate" : "Activate";
    const toggleClass = isActive ? "btn-danger" : "btn-success";

    const safeName = escapeHtml(member.full_name || member.username || "");
    const safeEmail = escapeHtml(member.email || "");
    const safePhone = escapeHtml(member.phone || "—");

    table.innerHTML += `
            <tr>
                <td>${member.id}</td>
                <td>${safeName}</td>
                <td>${safeEmail}</td>
                <td>${safePhone}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-primary btn-sm action-btn me-1" onclick="showMemberHistory(${member.id}, '${safeName.replace(/'/g, "\\'")}')">
                        History
                    </button>
                    <button class="btn ${toggleClass} btn-sm action-btn" onclick="toggleMemberActive(${member.id})">
                        ${toggleLabel}
                    </button>
                </td>
            </tr>
        `;
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Save Member
async function handleSaveMember() {
  const userIdInput = document.getElementById("userId");
  const fullNameInput = document.getElementById("fullName");
  const emailInput = document.getElementById("email");
  const phoneInput = document.getElementById("phone");

  const full_name = fullNameInput ? fullNameInput.value.trim() : "";
  const email = emailInput ? emailInput.value.trim() : "";
  const phone = phoneInput ? phoneInput.value.trim() : "";
  const user_id = userIdInput ? userIdInput.value.trim() : "";

  if (!full_name || !email) {
    alert("Please enter Full Name and Email.");
    return;
  }

  try {
    const response = await fetch(MEMBERS_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id, full_name, email, phone }),
    });
    const result = await response.json();

    if (response.ok) {
      alert(result.message || "Member added successfully");

      // Close modal if open
      const modalEl = document.getElementById("memberModal");
      if (modalEl && window.bootstrap) {
        const modalInstance =
          bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modalInstance.hide();
      }

      // Reset form
      if (userIdInput) userIdInput.value = "";
      if (fullNameInput) fullNameInput.value = "";
      if (emailInput) emailInput.value = "";
      if (phoneInput) phoneInput.value = "";

      loadMembers();
      if (window.loadDashboard) window.loadDashboard();
    } else {
      alert(result.error || result.message || "Failed to add member");
    }
  } catch (error) {
    console.log("Add Member Error:", error);
    alert("An error occurred while adding the member.");
  }
}

// Deactivate Member
async function toggleMemberActive(id) {
  try {
    const currentResponse = await fetch(`${MEMBERS_API}/${id}`);
    const member = await currentResponse.json();

    const isActive =
      Number(member.is_active) === 1 || member.is_active === true;
    const nextActive = !isActive;
    const label = nextActive ? "activate" : "deactivate";

    if (!confirm(`Do you want to ${label} this member?`)) {
      return;
    }

    const response = await fetch(`${MEMBERS_API}/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: member.full_name,
        email: member.email,
        phone: member.phone,
        is_active: nextActive,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      alert(result.error || "Failed to update member");
      return;
    }

    alert(result.message || "Member updated");
    loadMembers();

    if (window.loadDashboard) {
      window.loadDashboard();
    }
  } catch (error) {
    console.log("Toggle Error:", error);
  }
}

async function showMemberHistory(id, name) {
  try {
    const modalEl = document.getElementById("memberHistoryModal");
    const tableBody = document.getElementById("memberHistoryBody");
    const titleEl = document.getElementById("memberHistoryTitle");

    if (!modalEl || !tableBody) {
      return;
    }

    if (titleEl) {
      titleEl.innerText = name ? `Member History - ${name}` : "Member History";
    }

    tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">Loading...</td>
            </tr>
        `;

    const response = await fetch(`${MEMBERS_API}/${id}/history`);
    const history = await response.json();

    tableBody.innerHTML = "";

    if (!Array.isArray(history) || history.length === 0) {
      tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">No history found</td>
                </tr>
            `;
    } else {
      history.forEach((row) => {
        tableBody.innerHTML += `
                    <tr>
                        <td>${escapeHtml(row.title || "")}</td>
                        <td>${escapeHtml(row.author || "")}</td>
                        <td>${escapeHtml(row.borrow_date || "")}</td>
                        <td>${escapeHtml(row.due_date || "")}</td>
                        <td>${escapeHtml(row.return_date || "-")}</td>
                        <td>${escapeHtml(row.status || "")}</td>
                    </tr>
                `;
      });
    }

    if (window.bootstrap) {
      new bootstrap.Modal(modalEl).show();
    }
  } catch (error) {
    console.log("History Error:", error);
  }
}
