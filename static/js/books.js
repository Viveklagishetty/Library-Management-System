// ======================================
// Books Management
// ======================================


const BOOK_API="/books";

let editingBookId=null;



document.addEventListener("DOMContentLoaded",()=>{

const table =
document.getElementById("booksTableBody");

if(!table){
return;
}

loadBooks();

const bookModalEl =
document.getElementById("bookModal");

if(bookModalEl){
bookModalEl.addEventListener("hidden.bs.modal",()=>{
editingBookId=null;
document.getElementById("bookId").value="";
document.getElementById("title").value="";
document.getElementById("author").value="";
document.getElementById("genre").value="";
document.getElementById("isbn").value="";
document.getElementById("copies").value="";
});
}



const saveBtn =
document.getElementById("saveBookBtn");


if(saveBtn){

saveBtn.addEventListener(
"click",
saveBook
);

}



const searchBtn =
document.getElementById("searchBtn");


if(searchBtn){

searchBtn.addEventListener(
"click",
searchBooks
);

}



const refreshBtn =
document.getElementById("refreshBtn");


if(refreshBtn){

refreshBtn.addEventListener(
"click",
loadBooks
);

}



});




// Load Books


async function loadBooks(){

try{


const response =
await fetch(BOOK_API);


const result =
await response.json();



if(result.success){

renderBooks(result.data);

}



}

catch(error){

console.log(error);

}


}





function renderBooks(books){


const table =
document.getElementById("booksTableBody");


if(!table)return;


table.innerHTML="";



books.forEach(book=>{


table.innerHTML += `

<tr>

<td>${book.id}</td>

<td>${book.title}</td>

<td>${book.author}</td>

<td>${book.genre ?? ""}</td>

<td>${book.isbn ?? ""}</td>

<td>${book.total_copies}</td>

<td>${book.available_copies}</td>

<td>


<button class="btn btn-warning btn-sm"
onclick="editBook(${book.id})">

Edit

</button>


<button class="btn btn-danger btn-sm"
onclick="deleteBook(${book.id})">

Delete

</button>


</td>


</tr>


`;

});


}




// Search

async function searchBooks(){


const keyword =
document.getElementById("searchBook").value
.toLowerCase();

if(!keyword){
loadBooks();
return;
}

const response =
await fetch(`/books/search?q=${encodeURIComponent(keyword)}`);

const result =
await response.json();

if(result.success){
renderBooks(result.data || []);
}



}





// Save


async function saveBook(){


const data={


title:
document.getElementById("title").value,


author:
document.getElementById("author").value,


genre:
document.getElementById("genre").value,


isbn:
document.getElementById("isbn").value,


total_copies:
Number(
document.getElementById("copies").value
)


};

if(!data.title || !data.author || !data.total_copies){
alert("Title, Author and Total Copies are required");
return;
}


let url=BOOK_API;

let method="POST";



if(editingBookId){


url=`/books/${editingBookId}`;

method="PUT";


}



const response =
await fetch(url,{

method,

headers:{
"Content-Type":"application/json"
},

body:
JSON.stringify(data)

});



const result =
await response.json();



alert(result.message);
editingBookId=null;



if(window.loadDashboard){
window.loadDashboard();
}

const modalEl =
document.getElementById("bookModal");

if(modalEl){
bootstrap.Modal.getInstance(modalEl)?.hide();
}

loadBooks();

}




async function editBook(id){

const response =
await fetch(`/books/${id}`);


const result =
await response.json();



const book=result.data;



editingBookId=id;


document.getElementById("title").value=book.title;

document.getElementById("author").value=book.author;

document.getElementById("genre").value=book.genre;

document.getElementById("isbn").value=book.isbn;

document.getElementById("copies").value=book.total_copies;



new bootstrap.Modal(
document.getElementById("bookModal")
).show();


}





// Delete


async function deleteBook(id){


if(!confirm("Delete book?"))
return;



await fetch(`/books/${id}`,{

method:"DELETE"

});




if(window.loadDashboard){
window.loadDashboard();
}
loadBooks();
}

