import sqlite3
import os
from datetime import datetime, timedelta
import textwrap

DB_NAME = 'school_library.db'
RECEIPTS_DIR = 'receipts'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Create Books table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Books (
        BookID INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT NOT NULL,
        Author TEXT NOT NULL,
        ISBN TEXT UNIQUE NOT NULL,
        CopiesAvailable INTEGER NOT NULL CHECK(CopiesAvailable >= 0)
    )
    ''')

    # Create Students table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Students (
        StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Class TEXT NOT NULL,
        RollNo TEXT NOT NULL
    )
    ''')

    # Create Transactions table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Transactions (
        TransID INTEGER PRIMARY KEY AUTOINCREMENT,
        StudentID INTEGER NOT NULL,
        BookID INTEGER NOT NULL,
        IssueDate TEXT NOT NULL,
        ReturnDate TEXT,
        Fine REAL DEFAULT 0,
        FOREIGN KEY(StudentID) REFERENCES Students(StudentID),
        FOREIGN KEY(BookID) REFERENCES Books(BookID)
    )
    ''')

    conn.commit()
    conn.close()

def add_book():
    print("\nAdd New Book")
    title = input("Title: ").strip()
    author = input("Author: ").strip()
    isbn = input("ISBN: ").strip()
    try:
        copies = int(input("Number of copies: "))
        if copies < 0:
            raise ValueError
    except ValueError:
        print("Invalid number of copies!")
        return

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO Books (Title, Author, ISBN, CopiesAvailable) VALUES (?, ?, ?, ?)',
                    (title, author, isbn, copies))
        conn.commit()
        print(f'Book "{title}" added successfully.')
    except sqlite3.IntegrityError:
        print("ISBN must be unique. A book with this ISBN already exists.")
    finally:
        conn.close()

def update_book():
    print("\nUpdate Book Info")
    isbn = input("Enter ISBN of the book to update: ").strip()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT BookID, Title, Author, CopiesAvailable FROM Books WHERE ISBN = ?', (isbn,))
    book = cur.fetchone()
    if not book:
        print("Book not found.")
        conn.close()
        return

    print(f"Current info: Title: {book[1]}, Author: {book[2]}, Copies Available: {book[3]}")
    new_title = input("New Title (press enter to keep current): ").strip()
    new_author = input("New Author (press enter to keep current): ").strip()
    try:
        new_copies_str = input("New Copies Available (press enter to keep current): ").strip()
        if new_copies_str:
            new_copies = int(new_copies_str)
            if new_copies < 0:
                raise ValueError
        else:
            new_copies = book[3]
    except ValueError:
        print("Invalid number of copies!")
        conn.close()
        return

    new_title = new_title if new_title else book[1]
    new_author = new_author if new_author else book[2]

    cur.execute('UPDATE Books SET Title = ?, Author = ?, CopiesAvailable = ? WHERE BookID = ?',
                (new_title, new_author, new_copies, book[0]))
    conn.commit()
    conn.close()
    print("Book information updated successfully.")

def delete_book():
    print("\nDelete Book")
    isbn = input("Enter ISBN of the book to delete: ").strip()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # Check book exists
    cur.execute('SELECT BookID, Title FROM Books WHERE ISBN = ?', (isbn,))
    book = cur.fetchone()
    if not book:
        print("Book not found.")
        conn.close()
        return

    # Check if book is issued currently (i.e. Transaction with no ReturnDate)
    cur.execute('SELECT COUNT(*) FROM Transactions WHERE BookID = ? AND ReturnDate IS NULL', (book[0],))
    count_issued = cur.fetchone()[0]
    if count_issued > 0:
        print(f"Cannot delete book '{book[1]}'. It is currently issued and not returned yet.")
        conn.close()
        return

    confirm = input(f"Are you sure you want to delete the book '{book[1]}'? (y/n): ").strip().lower()
    if confirm == 'y':
        cur.execute('DELETE FROM Books WHERE BookID = ?', (book[0],))
        conn.commit()
        print("Book deleted successfully.")
    else:
        print("Deletion cancelled.")
    conn.close()

def add_student():
    print("\nAdd New Student")
    name = input("Name: ").strip()
    sclass = input("Class: ").strip()
    rollno = input("Roll Number: ").strip()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('INSERT INTO Students (Name, Class, RollNo) VALUES (?, ?, ?)',
                (name, sclass, rollno))
    conn.commit()
    conn.close()
    print(f"Student '{name}' added successfully.")

def remove_student():
    print("\nRemove Student")
    student_id = input("Enter StudentID to remove: ").strip()
    if not student_id.isdigit():
        print("Invalid StudentID.")
        return

    student_id = int(student_id)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Check if student exists
    cur.execute('SELECT Name FROM Students WHERE StudentID = ?', (student_id,))
    student = cur.fetchone()
    if not student:
        print("Student not found.")
        conn.close()
        return

    # Check if student has issued books not returned
    cur.execute('SELECT COUNT(*) FROM Transactions WHERE StudentID = ? AND ReturnDate IS NULL', (student_id,))
    count_issued = cur.fetchone()[0]
    if count_issued > 0:
        print(f"Cannot remove student '{student[0]}'. They have books not returned yet.")
        conn.close()
        return

    confirm = input(f"Are you sure you want to remove student '{student[0]}'? (y/n): ").strip().lower()
    if confirm == 'y':
        cur.execute('DELETE FROM Students WHERE StudentID = ?', (student_id,))
        conn.commit()
        print("Student removed successfully.")
    else:
        print("Removal cancelled.")
    conn.close()

def issue_book():
    print("\nIssue Book")
    student_id = input("Enter StudentID: ").strip()
    book_isbn = input("Enter Book ISBN: ").strip()

    if not student_id.isdigit():
        print("Invalid StudentID.")
        return

    student_id = int(student_id)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Validate student
    cur.execute('SELECT Name FROM Students WHERE StudentID = ?', (student_id,))
    student = cur.fetchone()
    if not student:
        print("Student not found.")
        conn.close()
        return

    # Validate book by ISBN
    cur.execute('SELECT BookID, Title, CopiesAvailable FROM Books WHERE ISBN = ?', (book_isbn,))
    book = cur.fetchone()
    if not book:
        print("Book not found.")
        conn.close()
        return

    if book[2] < 1:
        print(f"Book '{book[1]}' is not currently available.")
        conn.close()
        return

    # Check if the student already issued this book and not returned
    cur.execute('''
    SELECT COUNT(*) FROM Transactions 
    WHERE StudentID = ? AND BookID = ? AND ReturnDate IS NULL
    ''', (student_id, book[0]))
    if cur.fetchone()[0] > 0:
        print(f"Student already issued the book '{book[1]}', and has not returned it yet.")
        conn.close()
        return

    # Issue book: Insert transaction with IssueDate = today, ReturnDate = NULL
    issue_date = datetime.now().date().isoformat()
    cur.execute('INSERT INTO Transactions (StudentID, BookID, IssueDate) VALUES (?, ?, ?)',
                (student_id, book[0], issue_date))

    # Update book stock - decrease copies
    cur.execute('UPDATE Books SET CopiesAvailable = CopiesAvailable - 1 WHERE BookID = ?', (book[0],))

    conn.commit()

    # Generate receipt
    generate_receipt_issue(student[0], student_id, book[1], book[0], issue_date)

    print(f"Book '{book[1]}' issued to student '{student[0]}' on {issue_date}.")
    conn.close()

def generate_receipt_issue(student_name, student_id, book_title, book_id, issue_date):
    if not os.path.exists(RECEIPTS_DIR):
        os.makedirs(RECEIPTS_DIR)
    filename = f'ISSUE_{student_id}_{book_id}_{issue_date}.txt'
    filepath = os.path.join(RECEIPTS_DIR, filename)
    content = textwrap.dedent(f'''
    ===============================
           School Library
    ===============================
    Issue Receipt
    -------------------------------
    Student Name: {student_name}
    Student ID: {student_id}
    Book Title: {book_title}
    Book ID: {book_id}
    Issue Date: {issue_date}


    Please return the book on time to avoid fines.
    ===============================
    ''')
    with open(filepath, 'w') as f:
        f.write(content)

def return_book():
    print("\nReturn Book")
    student_id = input("Enter StudentID: ").strip()
    book_isbn = input("Enter Book ISBN: ").strip()

    if not student_id.isdigit():
        print("Invalid StudentID.")
        return

    student_id = int(student_id)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Validate student
    cur.execute('SELECT Name FROM Students WHERE StudentID = ?', (student_id,))
    student = cur.fetchone()
    if not student:
        print("Student not found.")
        conn.close()
        return

    # Validate book by ISBN
    cur.execute('SELECT BookID, Title FROM Books WHERE ISBN = ?', (book_isbn,))
    book = cur.fetchone()
    if not book:
        print("Book not found.")
        conn.close()
        return

    # Find issued transaction without return date for this student and book
    cur.execute('''
    SELECT TransID, IssueDate FROM Transactions 
    WHERE StudentID = ? AND BookID = ? AND ReturnDate IS NULL
    ''', (student_id, book[0]))

    transaction = cur.fetchone()
    if not transaction:
        print(f"No issued record found for student '{student[0]}' and book '{book[1]}'.")
        conn.close()
        return

    trans_id = transaction[0]
    issue_date_str = transaction[1]
    issue_date = datetime.fromisoformat(issue_date_str).date()
    return_date = datetime.now().date()

    # Calculate fine (e.g. 1 currency unit per day after a 14 day loan period)
    loan_period = 14
    late_days = (return_date - issue_date).days - loan_period
    fine = 0
    if late_days > 0:
        fine = late_days * 1  # 1 unit per day fine

    # Update transaction with ReturnDate and Fine
    cur.execute('''
    UPDATE Transactions SET ReturnDate = ?, Fine = ? WHERE TransID = ?
    ''', (return_date.isoformat(), fine, trans_id))

    # Update book stock - increase copies
    cur.execute('UPDATE Books SET CopiesAvailable = CopiesAvailable + 1 WHERE BookID = ?', (book[0],))

    conn.commit()

    # Generate receipt
    generate_receipt_return(student[0], student_id, book[1], book[0], issue_date_str, return_date.isoformat(), fine)

    print(f"Book '{book[1]}' returned by student '{student[0]}'. Fine due: {fine} units.")
    conn.close()

def generate_receipt_return(student_name, student_id, book_title, book_id, issue_date, return_date, fine):
    if not os.path.exists(RECEIPTS_DIR):
        os.makedirs(RECEIPTS_DIR)
    filename = f'RETURN_{student_id}_{book_id}_{return_date}.txt'
    filepath = os.path.join(RECEIPTS_DIR, filename)
    content = textwrap.dedent(f'''
    ===============================
           School Library
    ===============================
    Return Receipt
    -------------------------------
    Student Name: {student_name}
    Student ID: {student_id}
    Book Title: {book_title}
    Book ID: {book_id}
    Issue Date: {issue_date}
    Return Date: {return_date}
    Fine Paid: {fine} units

    Thank you!
    ===============================
    ''')
    with open(filepath, 'w') as f:
        f.write(content)

def search_books():
    print("\nSearch Books")
    choice = input("Search by (1) Title or (2) Author? Enter 1 or 2: ").strip()
    if choice not in {'1', '2'}:
        print("Invalid choice.")
        return
    keyword = input("Enter search keyword: ").strip()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if choice == '1':
        cur.execute("SELECT BookID, Title, Author, ISBN, CopiesAvailable FROM Books WHERE Title LIKE ?", ('%'+keyword+'%',))
    else:
        cur.execute("SELECT BookID, Title, Author, ISBN, CopiesAvailable FROM Books WHERE Author LIKE ?", ('%'+keyword+'%',))
    rows = cur.fetchall()
    conn.close()

    if rows:
        print(f"\n{'ID':<5} {'Title':<30} {'Author':<20} {'ISBN':<15} Copies")
        print("-"*80)
        for r in rows:
            print(f"{r[0]:<5} {r[1]:<30} {r[2]:<20} {r[3]:<15} {r[4]}")
    else:
        print("No books found matching the search criteria.")

def view_issued_returned():
    print("\nView Transactions")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
    SELECT t.TransID, s.Name, b.Title, t.IssueDate, t.ReturnDate, t.Fine
    FROM Transactions t
    JOIN Students s ON t.StudentID = s.StudentID
    JOIN Books b ON t.BookID = b.BookID
    ORDER BY t.IssueDate DESC
    ''')
    rows = cur.fetchall()
    conn.close()

    if rows:
        print(f"\n{'TransID':<7} {'Student Name':<20} {'Book Title':<30} {'Issue Date':<12} {'Return Date':<12} {'Fine':<5}")
        print("-"*95)
        for r in rows:
            ret_date = r[4] if r[4] else "Not Returned"
            fine = r[5] if r[5] else 0
            print(f"{r[0]:<7} {r[1]:<20} {r[2]:<30} {r[3]:<12} {ret_date:<12} {fine:<5}")
    else:
        print("No transaction records found.")

def main_menu():
    while True:
        print(textwrap.dedent("""
        \n====== School Library Management System ======
        1. Add New Book
        2. Update Book Information
        3. Delete Book
        4. Add New Student
        5. Remove Student
        6. Issue Book
        7. Return Book
        8. Search Books
        9. View All Issued/Returned Books
        0. Exit
        ===============================================
        """))

        choice = input("Enter your choice (0-9): ").strip()
        if choice == '1':
            add_book()
        elif choice == '2':
            update_book()
        elif choice == '3':
            delete_book()
        elif choice == '4':
            add_student()
        elif choice == '5':
            remove_student()
        elif choice == '6':
            issue_book()
        elif choice == '7':
            return_book()
        elif choice == '8':
            search_books()
        elif choice == '9':
            view_issued_returned()
        elif choice == '0':
            print("Exiting system. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 0 and 9.")

if __name__ == '__main__':
    init_db()
    if not os.path.exists(RECEIPTS_DIR):
        os.makedirs(RECEIPTS_DIR)
    main_menu()

