import hashlib
from sqlalchemy import text
from rich.console import Console
import typer

console = Console()

def librarian_login(session):
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)

    query = text("SELECT librarian_id, password_hash FROM librarians WHERE username = :username")
    result = session.execute(query, {"username": username}).fetchone()

    if result:
        entered_hash = hashlib.sha256(password.encode()).hexdigest()
        if entered_hash == result.password_hash:
            console.print("[green]Login successful![/green]")
            return True

    console.print("[red]Invalid username or password[/red]")
    return False


def student_login(session) -> int:
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)

    query = text("SELECT user_id, username, password_hash FROM users WHERE username = :username AND status = 'A'")
    result = session.execute(query, {"username": username}).fetchone()

    if result:
        entered_hash = hashlib.sha256(password.encode()).hexdigest()
        if entered_hash == result.password_hash:
            console.print(f"[green]Welcome {result.username}![/green]")
            return result.user_id

    console.print("[red]Invalid student credentials[/red]")
    return None
