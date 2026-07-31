// ======================================
// Fine Management JS
// ======================================

const FINE_API = "/fines";

let fineTableBody;

// ======================================
// Initialize
// ======================================

document.addEventListener("DOMContentLoaded", () => {
  fineTableBody = document.getElementById("fineTableBody");

  if (!fineTableBody) {
    return;
  }

  loadFines();
});

// ======================================
// Load Fines
// ======================================

async function loadFines() {
  try {
    const response = await fetch(FINE_API);

    const result = await response.json();

    console.log("Fine API:", result);

    const fines = result.data || [];

    renderFines(fines);

    if (window.loadDashboard) {
      window.loadDashboard();
    }
  } catch (error) {
    console.log("Fine Load Error:", error);
  }
}

// ======================================
// Render Fines
// ======================================

function renderFines(fines) {
  fineTableBody.innerHTML = "";

  if (fines.length === 0) {
    fineTableBody.innerHTML = `

<tr>

<td colspan="9"
class="text-center">

No fines found

</td>

</tr>

`;

    return;
  }

  fines.forEach((fine) => {
    fineTableBody.innerHTML += `


<tr>


<td>
${fine.fine_id}
</td>



<td>
${fine.member_name}
</td>



<td>
${fine.book_title}
</td>



<td>
${fine.borrow_date}
</td>



<td>
${fine.due_date}
</td>



<td>
${fine.return_date || "-"}
</td>



<td>

₹${Number(fine.amount || 0).toFixed(2)}

</td>




<td>


${
  fine.is_paid
    ? `<span class="badge bg-success">
Paid
</span>`
    : `<span class="badge bg-danger">
Unpaid
</span>`
}



</td>




<td>


${
  fine.is_paid
    ? `<button
class="btn btn-secondary btn-sm"
disabled>

Paid

</button>`
    : `<button
class="btn btn-success btn-sm"
onclick="payFine(${fine.fine_id})">

Pay

</button>`
}



</td>



</tr>


`;
  });
}

// ======================================
// Pay Fine
// ======================================

async function payFine(id) {
  if (!confirm("Mark this fine as paid?")) {
    return;
  }

  try {
    const response = await fetch(`${FINE_API}/${id}/pay`, {
      method: "POST",
    });

    const result = await response.json();

    alert(result.message || result.error);

    if (response.ok) {
      loadFines();

      if (window.loadDashboard) {
        window.loadDashboard();
      }
    }
  } catch (error) {
    console.log("Pay Fine Error:", error);
  }
}
