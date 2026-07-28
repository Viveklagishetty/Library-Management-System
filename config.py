import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_TYPE = os.getenv("DB_TYPE", "mysql").lower()
DB_FILE = os.getenv("DB_FILE", str(BASE_DIR / "library.db"))


def get_db_connection():

    if DB_TYPE == "mysql":
        import mysql.connector

        return mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="Srisudhan@1223",
            database="library_ms",
            autocommit=True,
        )

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():

    sqlite_schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'member',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(200) NOT NULL,
        author VARCHAR(100) NOT NULL,
        genre VARCHAR(50),
        isbn VARCHAR(20) UNIQUE,
        total_copies INTEGER NOT NULL DEFAULT 1,
        available_copies INTEGER NOT NULL DEFAULT 1,
        added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        phone VARCHAR(15),
        is_active BOOLEAN DEFAULT TRUE,
        joined_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS borrows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        borrow_date DATE NOT NULL,
        due_date DATE NOT NULL,
        return_date DATE,
        status VARCHAR(20) DEFAULT 'active',
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (book_id) REFERENCES books(id)
    );

    CREATE TABLE IF NOT EXISTS fines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        borrow_id INTEGER NOT NULL UNIQUE,
        member_id INTEGER NOT NULL,
        amount DECIMAL(8,2) NOT NULL,
        is_paid BOOLEAN DEFAULT FALSE,
        paid_on DATE,
        FOREIGN KEY (borrow_id) REFERENCES borrows(id),
        FOREIGN KEY (member_id) REFERENCES members(id)
    );
    """

    mysql_schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin','librarian','member') DEFAULT 'member',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        author VARCHAR(100) NOT NULL,
        genre VARCHAR(50),
        isbn VARCHAR(20) UNIQUE,
        total_copies INT NOT NULL DEFAULT 1,
        available_copies INT NOT NULL DEFAULT 1,
        added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS members (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT UNIQUE,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        phone VARCHAR(15),
        is_active TINYINT(1) DEFAULT 1,
        joined_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS borrows (
        id INT AUTO_INCREMENT PRIMARY KEY,
        member_id INT NOT NULL,
        book_id INT NOT NULL,
        borrow_date DATE NOT NULL,
        due_date DATE NOT NULL,
        return_date DATE,
        status ENUM('active','returned') DEFAULT 'active',
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (book_id) REFERENCES books(id)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS fines (
        id INT AUTO_INCREMENT PRIMARY KEY,
        borrow_id INT NOT NULL UNIQUE,
        member_id INT NOT NULL,
        amount DECIMAL(8,2) NOT NULL,
        is_paid TINYINT(1) DEFAULT 0,
        paid_on DATE,
        FOREIGN KEY (borrow_id) REFERENCES borrows(id),
        FOREIGN KEY (member_id) REFERENCES members(id)
    ) ENGINE=InnoDB;
    """

    connection = get_db_connection()

    if DB_TYPE == "mysql":
        cursor = connection.cursor()

        for statement in [s.strip() for s in mysql_schema.split(";") if s.strip()]:
            cursor.execute(statement)

        cursor.close()

    else:
        connection.executescript(sqlite_schema)

    connection.commit()
    connection.close()