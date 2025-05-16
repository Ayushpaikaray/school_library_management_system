# school_library_management_system
💡 Project Title:
>School Library Management System using Python and SQL

📌 Aim:
>To develop a software application that helps school libraries efficiently manage book records, student borrowings, and return operations using Python, SQL database, and file handling.

🧩 Problem Statement:
>In many schools, managing library books and keeping track of issue/return records is done manually, which is time-consuming and error-prone. This system aims to automate and simplify the process for librarians and students.

⚙️ Features:

Book Management:-
>(i)Add new books (Title, Author, ISBN, Copies)
>(ii)Delete or update book information

Student Record Management:-
>Add/remove student details (Name, Roll No., Class)

Issue Book:-
>(i)Issue books to students
>(ii)Update available stock
>(iii)Record issue date

Return Book:-
>(i)Return books and calculate fines (if applicable)
>(ii)Update book stock
>(iii)Record return date

Search & View:-
>(i)Search books by title/author
>(ii)View all issued/returned books

File Handling:-
>Generate and save a text-based receipt for each issue and return

Database Integration:-
>All records (books, students, transactions) stored and managed using MySQL or SQLite

🛠️ Technologies Used:

Python:-
>(i)mysql.connector or sqlite3 for SQL connectivity
>(ii)os, datetime, textwrap for utilities

SQL:-
>(i)Tables: Books, Students, Transactions
>(ii)SQL commands: CREATE, INSERT, UPDATE, DELETE, JOIN, GROUP BY

File Handling:-
>Generate .txt files for issue/return receipts
