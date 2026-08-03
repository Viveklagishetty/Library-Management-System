 // ======================================
// Members Management JS
// ======================================


const MEMBERS_API = "/members";



document.addEventListener("DOMContentLoaded",()=>{

    const table =
    document.getElementById("membersTableBody");

    if(!table){
        return;
    }

    loadMembers();

});




// Load Members

async function loadMembers(){

try{


const response =
await fetch(MEMBERS_API);



const result =
await response.json();



const members =
result.data || result;



renderMembers(members);

if(window.loadBorrowMembers){
    window.loadBorrowMembers();
}

}

catch(error){

console.log("Member Error:",error);

}


}





// Display Members


function renderMembers(members){


const table =
document.getElementById("membersTableBody");


if(!table)return;



table.innerHTML="";



members.forEach(member=>{

const isActive =
Number(member.is_active) === 1 || member.is_active === true;

const statusBadge =
isActive
?
`<span class="badge bg-success">Active</span>`
:
`<span class="badge bg-danger">Inactive</span>`;

const toggleLabel =
isActive ? "Deactivate" : "Activate";

const toggleClass =
isActive ? "btn-danger" : "btn-success";


table.innerHTML += `

<tr>


<td>${member.id}</td>


<td>${member.full_name || ""}</td>


<td>${member.email}</td>


<td>${member.phone || ""}</td>


<td>

${statusBadge}

</td>


<td>

<button
class="btn btn-primary btn-sm action-btn"
onclick="showMemberHistory(${member.id}, '${String(member.full_name || "").replace(/'/g, "\\'")}')">
History
</button>

<button
class="btn ${toggleClass} btn-sm action-btn"
onclick="toggleMemberActive(${member.id})">
${toggleLabel}
</button>

</button>


</td>


`;



});



}





// Deactivate Member


async function toggleMemberActive(id){
try{
const currentResponse =
await fetch(`${MEMBERS_API}/${id}`);

const member =
await currentResponse.json();

const isActive =
Number(member.is_active) === 1 || member.is_active === true;

const nextActive =
!isActive;

const label =
nextActive ? "activate" : "deactivate";

if(!confirm(`Do you want to ${label} this member?`)){
return;
}

const response =
await fetch(`${MEMBERS_API}/${id}`,{
method:"PUT",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
full_name: member.full_name,
email: member.email,
phone: member.phone,
is_active: nextActive
})
});

const result =
await response.json();

if(!response.ok){
alert(result.error || "Failed to update member");
return;
}

alert(result.message || "Member updated");

loadMembers();

if(window.loadDashboard){
window.loadDashboard();
}
}
catch(error){
console.log(error);
}
}

async function showMemberHistory(id,name){
try{
const modalEl =
document.getElementById("memberHistoryModal");
const tableBody =
document.getElementById("memberHistoryBody");
const titleEl =
document.getElementById("memberHistoryTitle");

if(!modalEl || !tableBody){
return;
}

if(titleEl){
titleEl.innerText =
name ? `Member History - ${name}` : "Member History";
}

tableBody.innerHTML = `
<tr>
<td colspan="6" class="text-center">Loading...</td>
</tr>
`;

const response =
await fetch(`${MEMBERS_API}/${id}/history`);

const history =
await response.json();

tableBody.innerHTML = "";

if(!Array.isArray(history) || history.length === 0){
tableBody.innerHTML = `
<tr>
<td colspan="6" class="text-center">No history found</td>
</tr>
`;
}else{
history.forEach(row=>{
tableBody.innerHTML += `
<tr>
<td>${row.title || ""}</td>
<td>${row.author || ""}</td>
<td>${row.borrow_date || ""}</td>
<td>${row.due_date || ""}</td>
<td>${row.return_date || "-"}</td>
<td>${row.status || ""}</td>
</tr>
`;
});
}

new bootstrap.Modal(modalEl).show();
}
catch(error){
console.log(error);
}
}
