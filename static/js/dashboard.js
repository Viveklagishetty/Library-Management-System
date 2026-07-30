// ======================================
// Dashboard JS
// ======================================


const DASH_BOOK_API = "/books";
const DASH_MEMBER_API = "/members";
const DASH_ACTIVE_BORROW_API = "/borrows/active";
const DASH_OVERDUE_API = "/borrows/overdue";
const DASH_FINES_API = "/fines";



document.addEventListener("DOMContentLoaded",()=>{

    loadDashboard();

});



async function loadDashboard(){

    loadTotalBooks();

    loadTotalMembers();

    loadActiveBorrows();

    loadOverdueBooks();

    loadTotalFineCollected();

}





// Total Books

async function loadTotalBooks(){

try{

const response =
await fetch(DASH_BOOK_API);


const result =
await response.json();


if(result.data && document.getElementById("totalBooks")){

document.getElementById("totalBooks").innerText =
result.data.length;

}


}

catch(error){

console.log(error);

}

}





// Members

async function loadTotalMembers(){

try{


const response =
await fetch(DASH_MEMBER_API);


const result =
await response.json();


const members =
result.data || result || [];

if(document.getElementById("totalMembers")){
document.getElementById("totalMembers").innerText =
members.length;
}



}

catch(error){

console.log(error);

}


}




// Active Borrow

async function loadActiveBorrows(){

try{


const response =
await fetch(DASH_ACTIVE_BORROW_API);


const result =
await response.json();



if(document.getElementById("activeBorrows")){
document.getElementById("activeBorrows").innerText =
(result || []).length;
}



}

catch(error){

console.log(error);

}


}




// Overdue

async function loadOverdueBooks(){

try{


const response =
await fetch(DASH_OVERDUE_API);


const result =
await response.json();


if(document.getElementById("overdueBooks")){
document.getElementById("overdueBooks").innerText =
(result || []).length;
}



}

catch(error){

console.log(error);

}


}

async function loadTotalFineCollected(){
try{

const totalFineElement =
document.getElementById("totalFine");

if(!totalFineElement)return;

const response =
await fetch(DASH_FINES_API);

const result =
await response.json();

const fines =
result.data || [];

const totalPaid =
fines
.filter(f=>f.is_paid)
.reduce((sum,f)=>sum + Number(f.amount || 0),0);

totalFineElement.innerText =
`₹${totalPaid.toFixed(2)}`;

}
catch(error){
console.log(error);
}
}
