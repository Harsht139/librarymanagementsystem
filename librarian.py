from sqlalchemy.orm import Session
from sqlalchemy import text
from rich.console import Console
from rich.table import Table
import typer

console = Console()


# ---------- Librarian Search Function ----------
def search_books_librarian(session: Session):
    while True:
        console.print("""
============== Search Books ==============
1. Search by Title
2. Search by Author
3. Search by Category
4. Back
==========================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "4":
            break

        term = typer.prompt("Enter search term")

        if choice == "1":  # Title
            like_term = f"%{term}%"
            query = text("""
                SELECT b.book_id, b.title,
                       GROUP_CONCAT(DISTINCT a.full_name) AS authors,
                       GROUP_CONCAT(DISTINCT c.name) AS categories,
                       COUNT(bc.copy_id) AS total_copies,
                       SUM(bc.is_available) AS available_copies
                FROM books b
                LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.author_id
                LEFT JOIN book_categories bcg ON b.book_id = bcg.book_id
                LEFT JOIN categories c ON bcg.category_id = c.category_id
                LEFT JOIN book_copies bc ON b.book_id = bc.book_id
                WHERE b.title LIKE :term
                GROUP BY b.book_id
            """)
        elif choice == "2":  # Author
            search_term = term.lower().replace(".", "").replace(" ", "")
            like_term = f"%{search_term}%"
            query = text("""
                SELECT b.book_id, b.title,
                       GROUP_CONCAT(DISTINCT a.full_name) AS authors,
                       GROUP_CONCAT(DISTINCT c.name) AS categories,
                       COUNT(bc.copy_id) AS total_copies,
                       SUM(bc.is_available) AS available_copies
                FROM books b
                LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.author_id
                LEFT JOIN book_categories bcg ON b.book_id = bcg.book_id
                LEFT JOIN categories c ON bcg.category_id = c.category_id
                LEFT JOIN book_copies bc ON b.book_id = bc.book_id
                WHERE REPLACE(REPLACE(LOWER(a.full_name), '.', ''), ' ', '') LIKE :term
                GROUP BY b.book_id
            """)
        elif choice == "3":  # Category
            like_term = f"%{term}%"
            query = text("""
                SELECT b.book_id, b.title,
                       GROUP_CONCAT(DISTINCT a.full_name) AS authors,
                       GROUP_CONCAT(DISTINCT c.name) AS categories,
                       COUNT(bc.copy_id) AS total_copies,
                       SUM(bc.is_available) AS available_copies
                FROM books b
                LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.author_id
                LEFT JOIN book_categories bcg ON b.book_id = bcg.book_id
                LEFT JOIN categories c ON bcg.category_id = c.category_id
                LEFT JOIN book_copies bc ON b.book_id = bc.book_id
                WHERE c.name LIKE :term
                GROUP BY b.book_id
            """)
        else:
            console.print("[red]Invalid choice![/red]")
            continue

        results = session.execute(query, {"term": like_term}).fetchall()
        display_books_librarian(results)


# ---------- Display Function ----------
def display_books_librarian(results):
    if not results:
        console.print("[yellow]No books found.[/yellow]")
        return

    table = Table(title="📚 Search Results", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="bold green")
    table.add_column("Authors", style="magenta")
    table.add_column("Categories", style="yellow")
    table.add_column("Total Copies", style="blue")
    table.add_column("Available Copies", style="green")

    for row in results:
        table.add_row(
            str(row.book_id),
            row.title,
            row.authors or "N/A",
            row.categories or "N/A",
            str(row.total_copies),
            str(row.available_copies or 0)
        )

    console.print(table)


# ---------- Add Book ----------
def add_book(session: Session):
    title = typer.prompt("Enter book title")
    authors = typer.prompt("Enter authors (comma separated)")
    categories = typer.prompt("Enter categories (comma separated)")
    copies = int(typer.prompt("Enter number of copies"))

    # Insert book
    session.execute(text("INSERT INTO books (title) VALUES (:title)"), {"title": title})
    session.commit()

    # Get book_id of newly inserted book
    book_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    # Insert authors
    for author in [a.strip() for a in authors.split(",")]:
        # Check if author exists
        existing = session.execute(text("SELECT author_id FROM authors WHERE full_name = :name"), {"name": author}).fetchone()
        if existing:
            author_id = existing.author_id
        else:
            session.execute(text("INSERT INTO authors (full_name) VALUES (:name)"), {"name": author})
            session.commit()
            author_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        session.execute(text("INSERT INTO book_authors (book_id, author_id) VALUES (:book_id, :author_id)"),
                        {"book_id": book_id, "author_id": author_id})

    # Insert categories
    for cat in [c.strip() for c in categories.split(",")]:
        existing = session.execute(text("SELECT category_id FROM categories WHERE name = :name"), {"name": cat}).fetchone()
        if existing:
            cat_id = existing.category_id
        else:
            session.execute(text("INSERT INTO categories (name) VALUES (:name)"), {"name": cat})
            session.commit()
            cat_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        session.execute(text("INSERT INTO book_categories (book_id, category_id) VALUES (:book_id, :cat_id)"),
                        {"book_id": book_id, "cat_id": cat_id})

    # Insert book copies
    for _ in range(copies):
        session.execute(text("INSERT INTO book_copies (book_id, is_available) VALUES (:book_id, TRUE)"),
                        {"book_id": book_id})

    session.commit()
    console.print(f"[green]Book '{title}' added successfully![/green]")


# ---------- Update Book ----------
def update_book(session: Session):
    console.print("[bold green]Update Book[/bold green]")
    choice = typer.prompt("Do you want to update by (1) Book ID or (2) Book Title?")

    if choice == "1":
        book_id = typer.prompt("Enter Book ID")
        book_query = text("SELECT * FROM books WHERE book_id = :book_id")
        book = session.execute(book_query, {"book_id": book_id}).fetchone()
    elif choice == "2":
        title = typer.prompt("Enter Book Title")
        book_query = text("SELECT * FROM books WHERE title LIKE :title")
        book = session.execute(book_query, {"title": f"%{title}%"}).fetchone()
    else:
        console.print("[red]Invalid choice[/red]")
        return

    if not book:
        console.print("[red]Book not found[/red]")
        return

    # Prompt new details
    new_title = typer.prompt(f"Enter new title [{book.title}]", default=book.title)
    new_description = typer.prompt(f"Enter new description [{book.description or '-'}]", default=book.description)
    
    # Update the book
    session.execute(
        text("UPDATE books SET title = :title, description = :description WHERE book_id = :book_id"),
        {"title": new_title, "description": new_description, "book_id": book.book_id}
    )
    session.commit()
    console.print(f"[green]Book '{new_title}' updated successfully![/green]")



# ---------- Delete Book ----------
def update_book(session: Session):
    # Ask for book identification
    choice = typer.prompt("Update by (1) Book ID or (2) Book Title? [1/2]")
    
    if choice == "1":
        book_id = typer.prompt("Enter Book ID")
        book = session.execute(
            text("SELECT * FROM books WHERE book_id = :book_id"),
            {"book_id": book_id}
        ).fetchone()
    else:
        title = typer.prompt("Enter Book Title")
        book = session.execute(
            text("SELECT * FROM books WHERE title LIKE :title"),
            {"title": f"%{title}%"}
        ).fetchone()
    
    if not book:
        console.print("[red]Book not found![/red]")
        return

    console.print(f"[green]Selected Book:[/green] {book.title}")

    # --- Update Authors ---
    authors = typer.prompt("Enter authors (comma separated)", default="")
    if authors:
        # Remove existing authors
        session.execute(text("DELETE FROM book_authors WHERE book_id = :book_id"), {"book_id": book.book_id})
        # Add new authors
        for a in authors.split(","):
            a = a.strip()
            # Check if author exists
            author_row = session.execute(text("SELECT author_id FROM authors WHERE full_name = :name"), {"name": a}).fetchone()
            if not author_row:
                # Insert new author
                session.execute(text("INSERT INTO authors (full_name) VALUES (:name)"), {"name": a})
                author_row = session.execute(text("SELECT author_id FROM authors WHERE full_name = :name"), {"name": a}).fetchone()
            session.execute(text("INSERT INTO book_authors (book_id, author_id) VALUES (:book_id, :author_id)"),
                            {"book_id": book.book_id, "author_id": author_row.author_id})

    # --- Update Categories ---
    categories = typer.prompt("Enter categories (comma separated)", default="")
    if categories:
        session.execute(text("DELETE FROM book_categories WHERE book_id = :book_id"), {"book_id": book.book_id})
        for c in categories.split(","):
            c = c.strip()
            cat_row = session.execute(text("SELECT category_id FROM categories WHERE name = :name"), {"name": c}).fetchone()
            if not cat_row:
                session.execute(text("INSERT INTO categories (name) VALUES (:name)"), {"name": c})
                cat_row = session.execute(text("SELECT category_id FROM categories WHERE name = :name"), {"name": c}).fetchone()
            session.execute(text("INSERT INTO book_categories (book_id, category_id) VALUES (:book_id, :category_id)"),
                            {"book_id": book.book_id, "category_id": cat_row.category_id})

    # --- Update Copies ---
    total_copies = typer.prompt("Enter total number of copies (leave blank to skip)", default="")
    if total_copies.isdigit():
        total_copies = int(total_copies)
        existing_copies = session.execute(
            text("SELECT COUNT(*) as cnt FROM book_copies WHERE book_id = :book_id"),
            {"book_id": book.book_id}
        ).fetchone().cnt
        diff = total_copies - existing_copies
        if diff > 0:
            # Add copies
            for _ in range(diff):
                session.execute(text("INSERT INTO book_copies (book_id, is_available) VALUES (:book_id, TRUE)"),
                                {"book_id": book.book_id})
        elif diff < 0:
            # Remove available copies
            to_remove = abs(diff)
            session.execute(text("""
                DELETE FROM book_copies
                WHERE book_id = :book_id AND is_available = TRUE
                LIMIT :limit
            """), {"book_id": book.book_id, "limit": to_remove})

    session.commit()
    console.print("[green]Book updated successfully![/green]")

from rich.console import Console
from rich.table import Table
from sqlalchemy import text
import typer

console = Console()


# ---------------- View all borrows ----------------
def view_all_borrows(session):
    query = text("""
        SELECT br.borrow_id, u.user_id, u.full_name AS student_name,
               b.book_id, b.title,
               GROUP_CONCAT(DISTINCT a.full_name) AS authors,
               bc.copy_id, bc.barcode,
               br.borrow_date, br.due_date, br.return_date,
               br.active
        FROM borrows br
        JOIN users u ON br.user_id = u.user_id
        JOIN book_copies bc ON br.copy_id = bc.copy_id
        JOIN books b ON bc.book_id = b.book_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        GROUP BY br.borrow_id
        ORDER BY br.borrow_date DESC
    """)
    results = session.execute(query).fetchall()

    if not results:
        console.print("[yellow]No borrow records found.[/yellow]")
        return

    table = Table(title="📚 All Borrow Records", show_lines=True)
    table.add_column("Borrow ID", style="cyan")
    table.add_column("Student", style="green")
    table.add_column("Book Title", style="bold green")
    table.add_column("Authors", style="magenta")
    table.add_column("Copy Barcode", style="yellow")
    table.add_column("Borrow Date", style="green")
    table.add_column("Due Date", style="red")
    table.add_column("Return Date", style="blue")
    table.add_column("Status", style="bright_cyan")

    for row in results:
        status = "Active" if row.active else "Returned"
        table.add_row(
            str(row.borrow_id),
            f"{row.student_name} (ID:{row.user_id})",
            row.title,
            row.authors or "N/A",
            row.barcode,
            str(row.borrow_date),
            str(row.due_date),
            str(row.return_date) if row.return_date else "-",
            status
        )
    console.print(table)


# ---------------- Issue a book to a student ----------------
def issue_book(user_id: int, session: Session):
    # List all books with available copies
    results = session.execute(text("""
        SELECT b.book_id, b.title,
               GROUP_CONCAT(DISTINCT a.full_name) AS authors,
               COUNT(bc.copy_id) AS total_copies,
               SUM(bc.is_available) AS available_copies
        FROM books b
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        LEFT JOIN book_copies bc ON b.book_id = bc.book_id
        GROUP BY b.book_id
        HAVING available_copies > 0
    """)).fetchall()

    if not results:
        console.print("[yellow]No available books to issue.[/yellow]")
        return

    # Display available books
    table = Table(title="📚 Available Books to Borrow")
    table.add_column("Index", style="cyan")
    table.add_column("Book ID", style="green")
    table.add_column("Title", style="bold green")
    table.add_column("Authors", style="magenta")
    table.add_column("Available Copies", style="yellow")

    for idx, row in enumerate(results, start=1):
        table.add_row(
            str(idx),
            str(row.book_id),
            row.title,
            row.authors or "N/A",
            str(row.available_copies)
        )

    console.print(table)

    index = int(typer.prompt("Enter the Index of the book to issue"))
    if index < 1 or index > len(results):
        console.print("[red]Invalid selection[/red]")
        return

    selected_book = results[index - 1]

    # Pick one available copy
    copy = session.execute(text("""
        SELECT copy_id FROM book_copies 
        WHERE book_id = :book_id AND is_available = TRUE
        LIMIT 1
    """), {"book_id": selected_book.book_id}).fetchone()

    if not copy:
        console.print("[red]No copies available![/red]")
        return

    # Issue the book
    session.execute(text("""
        INSERT INTO borrows (user_id, copy_id, borrow_date, due_date)
        VALUES (:user_id, :copy_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY))
    """), {"user_id": user_id, "copy_id": copy.copy_id})

    session.execute(text("""
        UPDATE book_copies SET is_available = FALSE WHERE copy_id = :copy_id
    """), {"copy_id": copy.copy_id})

    session.commit()
    console.print(f"[green]Book '{selected_book.title}' issued successfully![/green]")



# ---------------- Return a book on behalf of a student ----------------
def return_book_librarian(session):
    # List all active borrowed books
    results = session.execute(text("""
        SELECT br.borrow_id, u.full_name AS student_name,
               b.title, bc.copy_id, bc.barcode
        FROM borrows br
        JOIN book_copies bc ON br.copy_id = bc.copy_id
        JOIN books b ON bc.book_id = b.book_id
        JOIN users u ON br.user_id = u.user_id
        WHERE br.return_date IS NULL
        ORDER BY br.borrow_date
    """)).fetchall()

    if not results:
        console.print("[yellow]No active borrowed books to return.[/yellow]")
        return

    table = Table(title="📚 Active Borrowed Books")
    table.add_column("Index", style="cyan")
    table.add_column("Borrow ID", style="green")
    table.add_column("Student", style="magenta")
    table.add_column("Book Title", style="bold green")
    table.add_column("Copy Barcode", style="yellow")

    for idx, row in enumerate(results, start=1):
        table.add_row(str(idx), str(row.borrow_id), row.student_name, row.title, row.barcode)

    console.print(table)

    index = int(typer.prompt("Enter the Index of the book to return"))
    if index < 1 or index > len(results):
        console.print("[red]Invalid selection[/red]")
        return

    selected = results[index - 1]

    session.execute(text("""
        UPDATE borrows SET return_date = CURDATE() WHERE borrow_id = :borrow_id
    """), {"borrow_id": selected.borrow_id})

    session.execute(text("""
        UPDATE book_copies SET is_available = TRUE WHERE copy_id = :copy_id
    """), {"copy_id": selected.copy_id})

    session.commit()
    console.print(f"[green]Book '{selected.title}' returned successfully on behalf of {selected.student_name}![/green]")

def view_all_students(session: Session):
    query = text("""
        SELECT user_id, full_name, email, status
        FROM users
        WHERE membership_type_id = 2  -- assuming 2 = student
    """)
    results = session.execute(query).fetchall()

    table = Table(title="📋 Students List", show_lines=True)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Email", style="magenta")
    table.add_column("Status", style="yellow")

    for row in results:
        status = "Active" if row.status == "A" else "Inactive"
        table.add_row(str(row.user_id), row.full_name, row.email, status)

    console.print(table)

def change_student_status(session: Session, activate: bool):
    action = "Activate" if activate else "Deactivate"
    student_id = typer.prompt(f"Enter Student ID to {action}")

    query = text("""
        UPDATE users
        SET status = :status
        WHERE user_id = :user_id AND membership_type_id = 2
    """)
    session.execute(query, {"status": "A" if activate else "I", "user_id": student_id})
    session.commit()
    console.print(f"[green]{action}d student successfully![/green]")

# ---------------- Librarian Manage Borrows Menu ----------------
def manage_borrows(session: Session):
    while True:
        console.print("""
============== Manage Borrows / Returns ==============
1. View All Borrows
2. Issue Book
3. Return Book
4. Back
====================================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "1":
            view_all_borrows(session)
        elif choice == "2":
            # Ask librarian which student to issue book to
            user_id = typer.prompt("Enter Student User ID")
            issue_book(int(user_id), session)   # ✅ pass both user_id and session
        elif choice == "3":
            user_id = typer.prompt("Enter Student User ID")
            return_book(user_id, session)       # same for returning
        elif choice == "4":
            break
        else:
            console.print("[red]Invalid choice![/red]")

def manage_users(session: Session):
    while True:
        console.print("""
============== Manage Students ==============
1. View All Students
2. Activate Student
3. Deactivate Student
4. Back
==========================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "1":
            view_all_students(session)
        elif choice == "2":
            change_student_status(session, activate=True)
        elif choice == "3":
            change_student_status(session, activate=False)
        elif choice == "4":
            break
        else:
            console.print("[red]Invalid choice![/red]")

from rich.console import Console
from rich.table import Table
from sqlalchemy import text
import typer

console = Console()

def analytics_menu(session):
    while True:
        console.print("""
============== Analytics Menu ==============
1. Books Analytics
2. Users Analytics
3. Library Analytics
0. Back
==========================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "0":
            break

        elif choice == "1":  # Books Analytics
            books_analytics(session)

        elif choice == "2":  # Users Analytics
            users_analytics(session)

        elif choice == "3":  # Library Analytics (queries)
            library_reports(session)

        else:
            console.print("[red]Invalid choice![/red]")

# ----------------- Books Analytics -----------------
def books_analytics(session):
    while True:
        console.print("""
============== Books Analytics ==============
1. Total Book Copies
2. Total Unique Titles
3. Books Currently Issued
4. Books Available
5. Most Borrowed Books
6. Least Borrowed Books
7. Books per Category
0. Back
==========================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "0":
            break

        elif choice == "1":
            row = session.execute(text("SELECT COUNT(*) AS total FROM book_copies")).fetchone()
            console.print(f"Total Book Copies: [green]{row.total}[/green]")

        elif choice == "2":
            row = session.execute(text("SELECT COUNT(*) AS total FROM books")).fetchone()
            console.print(f"Total Unique Titles: [green]{row.total}[/green]")

        elif choice == "3":
            row = session.execute(text("SELECT COUNT(*) AS issued FROM book_copies WHERE is_available = FALSE")).fetchone()
            console.print(f"Books Currently Issued: [red]{row.issued}[/red]")

        elif choice == "4":
            row = session.execute(text("SELECT COUNT(*) AS available FROM book_copies WHERE is_available = TRUE")).fetchone()
            console.print(f"Books Available: [green]{row.available}[/green]")

        elif choice == "5":
            rows = session.execute(text("""
                SELECT b.title, COUNT(br.borrow_id) AS borrow_count
                FROM books b
                LEFT JOIN book_copies bc ON b.book_id = bc.book_id
                LEFT JOIN borrows br ON bc.copy_id = br.copy_id
                GROUP BY b.book_id
                ORDER BY borrow_count DESC
                LIMIT 5
            """)).fetchall()
            table = Table(title="Most Borrowed Books", show_lines=True)
            table.add_column("Title")
            table.add_column("Borrow Count")
            for r in rows:
                table.add_row(r.title, str(r.borrow_count))
            console.print(table)

        elif choice == "6":
            rows = session.execute(text("""
                SELECT b.title, COUNT(br.borrow_id) AS borrow_count
                FROM books b
                LEFT JOIN book_copies bc ON b.book_id = bc.book_id
                LEFT JOIN borrows br ON bc.copy_id = br.copy_id
                GROUP BY b.book_id
                ORDER BY borrow_count ASC
                LIMIT 5
            """)).fetchall()
            table = Table(title="Least Borrowed Books", show_lines=True)
            table.add_column("Title")
            table.add_column("Borrow Count")
            for r in rows:
                table.add_row(r.title, str(r.borrow_count))
            console.print(table)

        elif choice == "7":
            rows = session.execute(text("""
                SELECT c.name AS category, COUNT(bc.book_id) AS total_books
                FROM categories c
                LEFT JOIN book_categories bc ON c.category_id = bc.category_id
                GROUP BY c.category_id
                ORDER BY total_books DESC
            """)).fetchall()
            table = Table(title="Books per Category", show_lines=True)
            table.add_column("Category")
            table.add_column("Total Books")
            for r in rows:
                table.add_row(r.category, str(r.total_books))
            console.print(table)

        else:
            console.print("[red]Invalid choice![/red]")

# ----------------- Users Analytics -----------------
def users_analytics(session):
    while True:
        console.print("""
============== Users Analytics ==============
1. Total Students
2. Students with Pending Borrows
3. Students with Pending Fines
4. Most Active Students
0. Back
==========================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "0":
            break

        elif choice == "1":
            row = session.execute(text("SELECT COUNT(*) AS total FROM users WHERE membership_type_id = 2")).fetchone()
            console.print(f"Total Students: [green]{row.total}[/green]")

        elif choice == "2":
            row = session.execute(text("""
                SELECT COUNT(DISTINCT user_id) AS total
                FROM borrows
                WHERE return_date IS NULL
            """)).fetchone()
            console.print(f"Students with Pending Borrows: [yellow]{row.total}[/yellow]")

        elif choice == "3":
            row = session.execute(text("""
                SELECT COUNT(DISTINCT u.user_id) AS total
                FROM fines f
                JOIN borrows br ON f.borrow_id = br.borrow_id
                JOIN users u ON br.user_id = u.user_id
                WHERE f.paid = FALSE
            """)).fetchone()
            console.print(f"Students with Pending Fines: [red]{row.total}[/red]")

        elif choice == "4":
            rows = session.execute(text("""
                SELECT u.full_name, COUNT(*) AS total_borrows
                FROM borrows br
                JOIN users u ON br.user_id = u.user_id
                GROUP BY u.user_id
                ORDER BY total_borrows DESC
                LIMIT 5
            """)).fetchall()
            table = Table(title="Most Active Students", show_lines=True)
            table.add_column("Student")
            table.add_column("Total Borrows")
            for r in rows:
                table.add_row(r.full_name, str(r.total_borrows))
            console.print(table)

        else:
            console.print("[red]Invalid choice![/red]")

# ----------------- Library Analytics (Queries) -----------------
def library_reports(session):
    while True:
        console.print("""
============== Library Analytics ==============
1. Overdue Books
2. Top 5 Most Borrowed Books
3. Users with Unpaid Fines
4. Books & Average Review Rating
5. Most Popular Authors
6. Active Reservations
7. Books per Category
8. Users with Most Borrows
9. Books Currently Available vs Borrowed
10. Fines Collected per Month
11. Users Who Never Borrowed a Book
12. Top 3 Users with Highest Total Fines
13. Books Ranked by Borrow Count
0. Back
==========================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "0":
            break

        elif choice == "1":  # Overdue Books
            rows = session.execute(text("""
                SELECT u.full_name, b.title, br.due_date
                FROM borrows br
                JOIN users u ON br.user_id = u.user_id
                JOIN book_copies bc ON br.copy_id = bc.copy_id
                JOIN books b ON bc.book_id = b.book_id
                WHERE br.return_date IS NULL AND br.due_date < CURDATE()
            """)).fetchall()
            table = Table(title="Overdue Books", show_lines=True)
            table.add_column("Student")
            table.add_column("Book Title")
            table.add_column("Due Date")
            for r in rows:
                table.add_row(r.full_name, r.title, str(r.due_date))
            console.print(table)

        elif choice == "2":  # Top 5 Most Borrowed Books
            rows = session.execute(text("""
                SELECT b.title, COUNT(*) AS borrow_count
                FROM borrows br
                JOIN book_copies bc ON br.copy_id = bc.copy_id
                JOIN books b ON bc.book_id = b.book_id
                GROUP BY b.book_id
                ORDER BY borrow_count DESC
                LIMIT 5
            """)).fetchall()
            table = Table(title="Top 5 Most Borrowed Books", show_lines=True)
            table.add_column("Title")
            table.add_column("Borrow Count")
            for r in rows:
                table.add_row(r.title, str(r.borrow_count))
            console.print(table)

        elif choice == "3":  # Users with Unpaid Fines
            rows = session.execute(text("""
                SELECT u.full_name, SUM(f.amount) AS total_fines
                FROM fines f
                JOIN borrows br ON f.borrow_id = br.borrow_id
                JOIN users u ON br.user_id = u.user_id
                WHERE f.paid = FALSE
                GROUP BY u.user_id
                ORDER BY total_fines DESC
            """)).fetchall()
            table = Table(title="Users with Unpaid Fines", show_lines=True)
            table.add_column("Student")
            table.add_column("Total Fines")
            for r in rows:
                table.add_row(r.full_name, str(r.total_fines))
            console.print(table)

        elif choice == "4":  # Books & Average Review Rating
            rows = session.execute(text("""
                SELECT b.title, ROUND(AVG(r.rating),2) AS avg_rating, COUNT(r.review_id) AS review_count
                FROM books b
                LEFT JOIN reviews r ON b.book_id = r.book_id
                GROUP BY b.book_id
                ORDER BY avg_rating DESC
            """)).fetchall()
            table = Table(title="Books & Average Rating", show_lines=True)
            table.add_column("Title")
            table.add_column("Avg Rating")
            table.add_column("Review Count")
            for r in rows:
                table.add_row(r.title, str(r.avg_rating or 0), str(r.review_count))
            console.print(table)

        elif choice == "5":  # Most Popular Authors
            rows = session.execute(text("""
                SELECT a.full_name, COUNT(*) AS times_borrowed
                FROM borrows br
                JOIN book_copies bc ON br.copy_id = bc.copy_id
                JOIN books b ON bc.book_id = b.book_id
                JOIN book_authors ba ON b.book_id = ba.book_id
                JOIN authors a ON ba.author_id = a.author_id
                GROUP BY a.author_id
                ORDER BY times_borrowed DESC
                LIMIT 5
            """)).fetchall()
            table = Table(title="Most Popular Authors", show_lines=True)
            table.add_column("Author")
            table.add_column("Times Borrowed")
            for r in rows:
                table.add_row(r.full_name, str(r.times_borrowed))
            console.print(table)

        elif choice == "6":  # Active Reservations
            rows = session.execute(text("""
                SELECT u.full_name, b.title, r.reservation_date
                FROM reservations r
                JOIN users u ON r.user_id = u.user_id
                JOIN books b ON r.book_id = b.book_id
                WHERE r.status = 1
                ORDER BY r.reservation_date DESC
            """)).fetchall()
            table = Table(title="Active Reservations", show_lines=True)
            table.add_column("Student")
            table.add_column("Book Title")
            table.add_column("Reservation Date")
            for r in rows:
                table.add_row(r.full_name, r.title, str(r.reservation_date))
            console.print(table)

        elif choice == "7":  # Books per Category
            rows = session.execute(text("""
                SELECT c.name AS category, COUNT(bc.book_id) AS total_books
                FROM categories c
                LEFT JOIN book_categories bc ON c.category_id = bc.category_id
                GROUP BY c.category_id
                ORDER BY total_books DESC
            """)).fetchall()
            table = Table(title="Books per Category", show_lines=True)
            table.add_column("Category")
            table.add_column("Total Books")
            for r in rows:
                table.add_row(r.category, str(r.total_books))
            console.print(table)

        elif choice == "8":  # Users with Most Borrows
            rows = session.execute(text("""
                SELECT u.full_name, COUNT(*) AS total_borrows
                FROM borrows br
                JOIN users u ON br.user_id = u.user_id
                GROUP BY u.user_id
                ORDER BY total_borrows DESC
                LIMIT 5
            """)).fetchall()
            table = Table(title="Users with Most Borrows", show_lines=True)
            table.add_column("Student")
            table.add_column("Total Borrows")
            for r in rows:
                table.add_row(r.full_name, str(r.total_borrows))
            console.print(table)

        elif choice == "9":  # Books Currently Available vs Borrowed
            row = session.execute(text("""
                SELECT 
                    SUM(CASE WHEN bc.is_available = TRUE THEN 1 ELSE 0 END) AS available,
                    SUM(CASE WHEN bc.is_available = FALSE THEN 1 ELSE 0 END) AS borrowed
                FROM book_copies bc
            """)).fetchone()
            console.print(f"Books Available: [green]{row.available}[/green], Borrowed: [red]{row.borrowed}[/red]")

        elif choice == "10":  # Fines Collected per Month
            rows = session.execute(text("""
                SELECT DATE_FORMAT(payment_date, '%Y-%m') AS month, SUM(amount) AS total_collected
                FROM fines
                WHERE paid = TRUE
                GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
                ORDER BY month
            """)).fetchall()
            table = Table(title="Fines Collected Per Month", show_lines=True)
            table.add_column("Month")
            table.add_column("Total Collected")
            for r in rows:
                table.add_row(r.month, str(r.total_collected))
            console.print(table)

        elif choice == "11":  # Users who never borrowed a book
            rows = session.execute(text("""
                SELECT full_name
                FROM users
                WHERE user_id NOT IN (SELECT DISTINCT user_id FROM borrows)
            """)).fetchall()
            table = Table(title="Users Who Never Borrowed a Book", show_lines=True)
            table.add_column("Student")
            for r in rows:
                table.add_row(r.full_name)
            console.print(table)

        elif choice == "12":  # Top 3 Users with Highest Total Fines
            rows = session.execute(text("""
                WITH user_fines AS (
                    SELECT u.user_id, u.full_name, SUM(f.amount) AS total_fines
                    FROM fines f
                    JOIN borrows br ON f.borrow_id = br.borrow_id
                    JOIN users u ON br.user_id = u.user_id
                    GROUP BY u.user_id
                )
                SELECT * FROM user_fines
                ORDER BY total_fines DESC
                LIMIT 3
            """)).fetchall()
            table = Table(title="Top 3 Users with Highest Total Fines", show_lines=True)
            table.add_column("Student")
            table.add_column("Total Fines")
            for r in rows:
                table.add_row(r.full_name, str(r.total_fines))
            console.print(table)

        elif choice == "13":  # Books Ranked by Borrow Count
            rows = session.execute(text("""
                SELECT b.title,
                       COUNT(br.borrow_id) AS borrow_count,
                       RANK() OVER (ORDER BY COUNT(br.borrow_id) DESC) AS rank_position
                FROM books b
                LEFT JOIN book_copies bc ON b.book_id = bc.book_id
                LEFT JOIN borrows br ON bc.copy_id = br.copy_id
                GROUP BY b.book_id
                ORDER BY borrow_count DESC
            """)).fetchall()
            table = Table(title="Books Ranked by Borrow Count", show_lines=True)
            table.add_column("Rank")
            table.add_column("Title")
            table.add_column("Borrow Count")
            for r in rows:
                table.add_row(str(r.rank_position), r.title, str(r.borrow_count))
            console.print(table)

        else:
            console.print("[red]Invalid choice![/red]")

# ---------- Librarian Menu ----------
def librarian_menu(session: Session):
    while True:
        console.print("""
============== Librarian Menu ==============
1. Search Books
2. Add New Book
3. Update Book
4. Delete Book
5. Manage Borrows / Returns
6. Manage Users
7. Reports / Analytics
8. Logout
==========================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "1":
            search_books_librarian(session)
        elif choice == "2":
            add_book(session)
        elif choice == "3":
            update_book(session)
        elif choice == "4":
            delete_book(session)
        elif choice == "5":
            manage_borrows(session)
        elif choice == "6":
            manage_users(session)
        elif choice == "7":
            analytics_menu(session)
        elif choice == "8":
            console.print("[yellow]Logging out...[/yellow]")
            break
        else:
            console.print("[red]Option not implemented yet![/red]")
