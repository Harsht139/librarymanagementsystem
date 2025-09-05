from rich.console import Console
import typer
from sqlalchemy.orm import Session
from sqlalchemy import text

console = Console()

# ---------- SEARCH FUNCTION ----------
def search_books(session: Session):
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
                       GROUP_CONCAT(DISTINCT c.name) AS categories
                FROM books b
                LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.author_id
                LEFT JOIN book_categories bc ON b.book_id = bc.book_id
                LEFT JOIN categories c ON bc.category_id = c.category_id
                WHERE b.title LIKE :term
                GROUP BY b.book_id
            """)

        elif choice == "2":  # Author
            # Normalize input: lowercase, remove dots & spaces
            search_term = term.lower().replace(".", "").replace(" ", "")
            like_term = f"%{search_term}%"

            query = text("""
                SELECT b.book_id, b.title,
                       GROUP_CONCAT(DISTINCT a.full_name) AS authors,
                       GROUP_CONCAT(DISTINCT c.name) AS categories
                FROM books b
                LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.author_id
                LEFT JOIN book_categories bc ON b.book_id = bc.book_id
                LEFT JOIN categories c ON bc.category_id = c.category_id
                WHERE REPLACE(REPLACE(LOWER(a.full_name), '.', ''), ' ', '') LIKE :term
                GROUP BY b.book_id
            """)

        elif choice == "3":  # Category
            like_term = f"%{term}%"
            query = text("""
                SELECT b.book_id, b.title,
                       GROUP_CONCAT(DISTINCT a.full_name) AS authors,
                       GROUP_CONCAT(DISTINCT c.name) AS categories
                FROM books b
                LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.author_id
                LEFT JOIN book_categories bc ON b.book_id = bc.book_id
                LEFT JOIN categories c ON bc.category_id = c.category_id
                WHERE c.name LIKE :term
                GROUP BY b.book_id
            """)

        else:
            console.print("[red]Invalid choice![/red]")
            continue

        results = session.execute(query, {"term": like_term}).fetchall()
        display_books(results)

def my_borrowed_books(user_id: int, session: Session):
    query = text("""
        SELECT 
            br.borrow_id,
            b.book_id,
            b.title,
            GROUP_CONCAT(DISTINCT a.full_name) AS authors,
            bc.barcode,
            br.borrow_date,
            br.due_date,
            br.return_date,
            br.active
        FROM borrows br
        LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id
        LEFT JOIN books b ON bc.book_id = b.book_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        WHERE br.user_id = :user_id
        GROUP BY br.borrow_id
        ORDER BY br.borrow_date DESC
    """)

    results = session.execute(query, {"user_id": user_id}).fetchall()

    if not results:
        console.print("[yellow]You have not borrowed any books yet.[/yellow]")
        return

    from rich.table import Table
    table = Table(title="📚 My Borrowed Books", show_lines=True)
    table.add_column("Borrow ID", style="cyan", no_wrap=True)
    table.add_column("Book ID", style="green")
    table.add_column("Title", style="bold green")
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
            str(row.book_id) if row.book_id else "-",
            row.title or "-",
            row.authors or "N/A",
            row.barcode or "-",
            str(row.borrow_date),
            str(row.due_date),
            str(row.return_date) if row.return_date else "-",
            status
        )

    console.print(table)

# ---------- DISPLAY FUNCTION ----------
from rich.table import Table
from rich.console import Console

console = Console()

def display_books(results):
    if not results:
        console.print("[yellow]No books found.[/yellow]")
        return

    table = Table(title="📚 Search Results", show_lines=True)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="bold green")
    table.add_column("Authors", style="magenta")
    table.add_column("Categories", style="yellow")

    for row in results:
        table.add_row(
            str(row.book_id),
            row.title,
            row.authors or "N/A",
            row.categories or "N/A"
        )

    console.print(table)

# ---------- ISSUE BOOK FUNCTION ----------
def issue_book(user_id: int, session: Session):
    # List all books with at least one available copy
    results = session.execute(text("""
        SELECT b.book_id, b.title, GROUP_CONCAT(DISTINCT a.full_name) AS authors, 
               COUNT(bc.copy_id) AS available_copies
        FROM books b
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        LEFT JOIN book_copies bc ON b.book_id = bc.book_id AND bc.is_available = TRUE
        GROUP BY b.book_id
        HAVING available_copies > 0
        ORDER BY b.title
    """)).fetchall()

    if not results:
        console.print("[yellow]No books available to borrow.[/yellow]")
        return

    # Display books in table
    table = Table(title="📚 Available Books to Borrow")
    table.add_column("Index", style="cyan")
    table.add_column("Book ID", style="green")
    table.add_column("Title", style="bold green")
    table.add_column("Authors", style="magenta")
    table.add_column("Available Copies", style="yellow")

    for idx, row in enumerate(results, start=1):
        table.add_row(str(idx), str(row.book_id), row.title, row.authors or "N/A", str(row.available_copies))

    console.print(table)

    index = int(typer.prompt("Enter the Index of the book you want to borrow"))
    if index < 1 or index > len(results):
        console.print("[red]Invalid selection[/red]")
        return

    selected_book = results[index - 1]

    # Find an available copy
    copy = session.execute(
        text("SELECT copy_id FROM book_copies WHERE book_id = :book_id AND is_available = TRUE LIMIT 1"),
        {"book_id": selected_book.book_id}
    ).fetchone()

    # Issue the book
    session.execute(
        text("""
            INSERT INTO borrows (user_id, copy_id, librarian_id, borrow_date, due_date)
            VALUES (:user_id, :copy_id, NULL, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY))
        """),
        {"user_id": user_id, "copy_id": copy.copy_id}
    )

    session.execute(
        text("UPDATE book_copies SET is_available = FALSE WHERE copy_id = :copy_id"),
        {"copy_id": copy.copy_id}
    )
    session.commit()
    console.print(f"[green]Book '{selected_book.title}' issued successfully![/green]")


# ---------- RETURN BOOK FUNCTION ----------
def return_book(user_id: int, session: Session):
    # List all active borrowed books
    results = session.execute(text("""
        SELECT br.borrow_id, bc.copy_id, b.title, bc.barcode
        FROM borrows br
        JOIN book_copies bc ON br.copy_id = bc.copy_id
        LEFT JOIN books b ON bc.book_id = b.book_id
        WHERE br.user_id = :user_id AND br.return_date IS NULL
    """), {"user_id": user_id}).fetchall()

    if not results:
        console.print("[yellow]No active borrowed books to return.[/yellow]")
        return

    # Display borrowed books in table
    table = Table(title="📚 Active Borrowed Books")
    table.add_column("Index", style="cyan")
    table.add_column("Borrow ID", style="green")
    table.add_column("Title", style="bold green")
    table.add_column("Barcode", style="yellow")

    for idx, row in enumerate(results, start=1):
        table.add_row(str(idx), str(row.borrow_id), row.title or "-", row.barcode)

    console.print(table)

    index = int(typer.prompt("Enter the Index of the book you want to return"))
    if index < 1 or index > len(results):
        console.print("[red]Invalid selection[/red]")
        return

    selected_borrow = results[index - 1]

    # Mark returned
    session.execute(
        text("UPDATE borrows SET return_date = CURDATE() WHERE borrow_id = :borrow_id"),
        {"borrow_id": selected_borrow.borrow_id}
    )
    session.execute(
        text("UPDATE book_copies SET is_available = TRUE WHERE copy_id = :copy_id"),
        {"copy_id": selected_borrow.copy_id}
    )
    session.commit()
    console.print(f"[green]Book '{selected_borrow.title}' returned successfully![/green]")

# ---------- ACCOUNT FUNCTIONS ----------
def view_account(user_id: int, session: Session):
    query = text("""
        SELECT full_name, email, phone, membership_date, status,
               (SELECT COUNT(*) FROM borrows WHERE user_id = :user_id) AS total_borrowed,
               (SELECT COUNT(*) FROM borrows WHERE user_id = :user_id AND return_date IS NULL) AS currently_borrowed,
               (SELECT IFNULL(SUM(amount), 0) FROM fines f
                JOIN borrows b ON f.borrow_id = b.borrow_id
                WHERE b.user_id = :user_id AND f.paid = FALSE) AS fines_due
        FROM users
        WHERE user_id = :user_id
    """)
    result = session.execute(query, {"user_id": user_id}).fetchone()

    if not result:
        console.print("[red]User not found![/red]")
        return

    console.print(f"[bold green]Full Name:[/bold green] {result.full_name}")
    console.print(f"[bold green]Email:[/bold green] {result.email}")
    console.print(f"[bold green]Phone:[/bold green] {result.phone or '-'}")
    console.print(f"[bold green]Membership Type:[/bold green] Student")  # hardcoded
    console.print(f"[bold green]Membership Date:[/bold green] {result.membership_date}")
    console.print(f"[bold green]Status:[/bold green] {result.status}")
    console.print(f"[bold green]Total Books Borrowed:[/bold green] {result.total_borrowed}")
    console.print(f"[bold green]Currently Borrowed Books:[/bold green] {result.currently_borrowed}")
    console.print(f"[bold green]Fines Due:[/bold green] {result.fines_due}")


def update_full_name(user_id: int, session: Session):
    new_name = typer.prompt("Enter your new full name")
    session.execute(
        text("UPDATE users SET full_name = :full_name WHERE user_id = :user_id"),
        {"full_name": new_name, "user_id": user_id}
    )
    session.commit()
    console.print("[green]Full name updated successfully![/green]")

def update_phone(user_id: int, session: Session):
    new_phone = typer.prompt("Enter your new phone number")
    session.execute(
        text("UPDATE users SET phone = :phone WHERE user_id = :user_id"),
        {"phone": new_phone, "user_id": user_id}
    )
    session.commit()
    console.print("[green]Phone number updated successfully![/green]")

def account_menu(user_id: int, session: Session):
    while True:
        console.print("""
============== Account Menu ==============
1. View Account Details
2. Update Full Name
3. Update Phone
4. Back
==========================================
        """)
        choice = typer.prompt("Enter your choice")
        if choice == "1":
            view_account(user_id, session)
        elif choice == "2":
            update_full_name(user_id, session)
        elif choice == "3":
            update_phone(user_id, session)
        elif choice == "4":
            break
        else:
            console.print("[red]Invalid choice![/red]")

# ---------- STUDENT MENU ----------
def student_menu(user_id: int, session: Session):
    while True:
        console.print("""
============== Student Menu ==============
1. Search Books
2. My Borrowed Books
3. Issue Book
4. Return Book
5. Account
6. Logout
==========================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "1":
            search_books(session)
        elif choice == "2":
            my_borrowed_books(user_id, session)
        elif choice == "3":
            issue_book(user_id, session)
        elif choice == "4":
            return_book(user_id, session)
        elif choice == "5":
            account_menu(user_id, session)
        elif choice == "6":
            console.print("[yellow]Logging out...[/yellow]")
            break
        else:
            console.print(f"[blue]Selected option: {choice} (not implemented yet)[/blue]")