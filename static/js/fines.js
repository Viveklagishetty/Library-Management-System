// ======================================
// Fine Management JS
// ======================================


const FINE_API = "/fines";


let fineTableBody;
let fineMemberSelect;
let fineBorrowIdInput;
let fineAmountInput;
let fineAmountLoading;
let addFineBtn;



// ======================================
// Initialize
// ======================================


document.addEventListener("DOMContentLoaded",()=>{


    fineTableBody =
    document.getElementById("fineTableBody");
    fineMemberSelect = document.getElementById("fineMemberSelect");
    fineBorrowIdInput = document.getElementById("fineBorrowId");
    fineAmountInput = document.getElementById("fineAmount");
    fineAmountLoading = document.getElementById("fineAmountLoading");
    addFineBtn = document.getElementById("addFineBtn");

    if(!fineTableBody){
        return;
    }

    if (fineMemberSelect) {
        loadFineMembers();
    }

    if (addFineBtn) {
        addFineBtn.addEventListener("click", addFine);
    }

    if (fineBorrowIdInput) {
        fineBorrowIdInput.addEventListener("blur", refreshFineAmount);
        fineBorrowIdInput.addEventListener("input", () => {
            if (!fineBorrowIdInput.value.trim() && fineAmountInput) {
                fineAmountInput.value = "";
            }
        });
    }

    loadFines();


});




// ======================================
// Load Members for Fine Form
// ======================================

async function loadFineMembers() {
    try {
        const response = await fetch("/members");
        const result = await response.json();
        const members = result.data || result || [];

        if (!fineMemberSelect) return;
        fineMemberSelect.innerHTML = '<option value="">Select Member</option>';

        members.forEach(member => {
            const isActive = Number(member.is_active) === 1 || member.is_active === true;
            if (isActive) {
                fineMemberSelect.innerHTML += `<option value="${member.id}">${member.full_name || member.name}</option>`;
            }
        });
    } catch (error) {
        console.log("Load Fine Members Error:", error);
    }
}

// ======================================
// Auto-calculate fine amount from borrow dates
// ======================================

async function refreshFineAmount() {
    const borrowId = fineBorrowIdInput ? fineBorrowIdInput.value.trim() : "";

    if (!borrowId || !fineAmountInput) {
        if (fineAmountInput) fineAmountInput.value = "";
        return;
    }

    if (fineAmountLoading) {
        fineAmountLoading.style.display = "inline";
    }

    try {
        const response = await fetch(`/borrow/${borrowId}`);
        const result = await response.json();
        const borrow = result.data || null;

        if (!borrow || !borrow.due_date) {
            fineAmountInput.value = "";
            return;
        }

        const dueDate = new Date(borrow.due_date);
        const returnDate = borrow.return_date ? new Date(borrow.return_date) : new Date();
        const overdueDays = Math.max(0, Math.floor((returnDate - dueDate) / (1000 * 60 * 60 * 24)));
        const amount = overdueDays * 5;
        fineAmountInput.value = amount > 0 ? amount.toFixed(2) : "0.00";
    } catch (error) {
        console.log("Refresh Fine Amount Error:", error);
    } finally {
        if (fineAmountLoading) {
            fineAmountLoading.style.display = "none";
        }
    }
}

// ======================================
// Load Fines
// ======================================


async function loadFines(){


try{


const response =
await fetch(FINE_API);



const result =
await response.json();



console.log(
"Fine API:",
result
);



const fines =
result.data || [];



renderFines(fines);

if(window.loadDashboard){
window.loadDashboard();
}



}

catch(error){


console.log(
"Fine Load Error:",
error
);


}



}






// ======================================
// Render Fines
// ======================================


function renderFines(fines){



fineTableBody.innerHTML="";



if(fines.length===0){


fineTableBody.innerHTML=`

<tr>

<td colspan="9"
class="text-center">

No fines found

</td>

</tr>

`;

return;

}





fines.forEach(fine=>{



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


${fine.is_paid

?

`<span class="badge bg-success">
Paid
</span>`

:

`<span class="badge bg-danger">
Unpaid
</span>`

}



</td>




<td>


${
fine.is_paid

?

`<button
class="btn btn-secondary btn-sm"
disabled>

Paid

</button>`

:

`<button
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
// Add Fine
// ======================================

async function addFine() {
    const member_id = fineMemberSelect ? fineMemberSelect.value : "";
    const borrow_id = fineBorrowIdInput ? fineBorrowIdInput.value.trim() : "";
    const amount = fineAmountInput ? fineAmountInput.value.trim() : "";

    if (!member_id || !borrow_id || !amount) {
        alert("Please select a member, enter a borrow ID, and enter an amount.");
        return;
    }

    const payload = { member_id, borrow_id };
    if (amount) {
        payload.amount = amount;
    }

    try {
        const response = await fetch(FINE_API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        alert(result.message || result.error || "Fine added successfully");

        if (response.ok) {
            if (fineBorrowIdInput) fineBorrowIdInput.value = "";
            if (fineAmountInput) fineAmountInput.value = "";
            if (fineMemberSelect) fineMemberSelect.value = "";
            loadFines();
            if (window.loadDashboard) window.loadDashboard();
        }
    } catch (error) {
        console.log("Add Fine Error:", error);
    }
}

// ======================================
// Pay Fine
// ======================================


async function payFine(id){



if(!confirm("Mark this fine as paid?")){

return;

}



try{


const response =
await fetch(
`${FINE_API}/${id}/pay`,
{

method:"POST"

}

);



const result =
await response.json();



alert(
result.message || result.error
);



if(response.ok){


loadFines();

if(window.loadDashboard){
window.loadDashboard();
}


}



}

catch(error){


console.log(
"Pay Fine Error:",
error
);


}



}
