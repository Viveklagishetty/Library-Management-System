# Library Management System

A full-stack web application developed using **Python, Flask, MySQL, HTML, CSS, and JavaScript**.  
The system helps libraries efficiently manage books, members, borrowing, returns, overdue fines, and role-based access for **Admins, Librarians, and Members**.

---

## Features

### Authentication
- User Registration
- User Login
- User Logout
- Session Management
- Role-Based Access

### Roles
- Admin
- Librarian
- Member

### Book Management
- Add Books
- View Books
- Update Books
- Delete Books
- Search Books by Title, Author, Genre, or ISBN
- Track Available Copies

### Member Management
- Register Library Members
- View Member Details
- Update Member Information
- Deactivate Members
- View Borrow History

### Borrow & Return Management
- Borrow Books
- Return Books
- Automatic Due Date (14 Days)
- Fine Calculation (₹5 per day)
- Fine Payment

### Borrowing Restrictions
Borrowing is prevented when:
- Book copies are unavailable
- Member has unpaid fine

### Admin Dashboard
- Total Books
- Total Members
- Active Borrows
- Overdue Books
- Total Fine Collection

### Member Portal
- Login
- View Available Books
- Search Books
- View Borrowed Books
- Check Due Dates
- View Fine Status

---

## Technologies Used

### Backend
- Python
- Flask
- MySQL

### Frontend
- HTML5
- CSS3
- JavaScript

### Version Control
- Git
- GitHub

---

## Project Structure

```bash
Library-Management-System/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── routes/
│   ├── auth.py
│   ├── books.py
│   ├── members.py
│   ├── borrows.py
│   └── fines.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── pages/
│
├── templates/
│
└── database/
```

---

## Prerequisites

Before running the project, make sure you have installed:

- Python 3.10 or above
- MySQL Server
- Git
- Visual Studio Code

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Viveklagishetty/Library-Management-System.git
cd Library-Management-System
```

### 2. Create Virtual Environment

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

If `requirements.txt` is unavailable:
```bash
pip install flask flask-bcrypt flask-cors mysql-connector-python python-dotenv
```

---

## Database Setup

Open MySQL Workbench and execute the following SQL:

```sql
CREATE DATABASE library_ms;

USE library_ms;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','librarian','member') DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    genre VARCHAR(50),
    isbn VARCHAR(20) UNIQUE,
    total_copies INT DEFAULT 1,
    available_copies INT DEFAULT 1,
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    is_active BOOLEAN DEFAULT TRUE,
    joined_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE borrows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    book_id INT NOT NULL,
    borrow_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE,
    status ENUM('active','returned') DEFAULT 'active',
    FOREIGN KEY(member_id) REFERENCES members(id),
    FOREIGN KEY(book_id) REFERENCES books(id)
);

CREATE TABLE fines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_id INT UNIQUE,
    member_id INT,
    amount DECIMAL(8,2),
    is_paid BOOLEAN DEFAULT FALSE,
    paid_on DATE,
    FOREIGN KEY(borrow_id) REFERENCES borrows(id),
    FOREIGN KEY(member_id) REFERENCES members(id)
);
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=library_ms

SECRET_KEY=your_secret_key
```

---

## Running the Project

Start the Flask application:

```bash
python app.py
```

The application will run at:

```bash
http://127.0.0.1:5000
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register User |
| POST | `/login` | Login User |
| GET | `/logout` | Logout User |

### Books

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/books` | Get all books |
| GET | `/books/<id>` | Get book by ID |
| POST | `/books` | Add book |
| PUT | `/books/<id>` | Update book |
| DELETE | `/books/<id>` | Delete book |
| GET | `/books/search?q=python` | Search books |

### Members

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/members` | Get all members |
| POST | `/members` | Register member |
| PUT | `/members/<id>` | Update member |
| GET | `/members/<id>/history` | View borrow history |

### Borrow Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/borrow` | Borrow book |
| POST | `/return/<borrow_id>` | Return book |
| GET | `/borrows/active` | View active borrows |
| GET | `/borrows/overdue` | View overdue borrows |

### Fine Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/fines/<borrow_id>/pay` | Pay fine |

---

## Testing

Use **Postman** to test the APIs.

### Recommended Test Flow
1. Register User
2. Login
3. Add Book
4. View Books
5. Register Member
6. Borrow Book
7. View Active Borrows
8. Return Book
9. Verify Fine Calculation
10. Pay Fine

---

## Team Members

| Module | Team Member(s) |
|--------|----------------|
| Module 1 – Database & Authentication | Nithish Veerapalli, Venkatesh Namagiri |
| Module 2 – Book Management | Hariharan B |
| Module 3 – Member Management | Sudharsun A |
| Module 4 – Borrow, Return & Fine System | Vivek Datta, Sai Akshay Mangadudla |
| Module 5 – Admin & Librarian Dashboard | Sathish |
| Module 6 – Member Portal & QA | Barath Jaya, Bhagya Lakshmi |

---

### Responsibilities
- Created the GitHub Repository
- Managed Team Branches
- Coordinated Module Integration
- Resolved Merge Conflicts
- Fixed Integration Bugs
- Performed Final Testing
- Managed Final Project Submission

---

## Future Enhancements

- Book Reservation System
- Email Notifications
- QR Code Based Issue & Return
- Barcode Scanner Support
- CSV Export
- Pagination
- Book Cover Images
- Fine Payment Gateway Integration

---
