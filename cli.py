import typer
from rich.console import Console
from db import SessionLocal
from auth import librarian_login, student_login
from librarian import librarian_menu
from student import student_menu

app = typer.Typer()
console = Console()

@app.command()
def main():
    session = SessionLocal()
    while True:
        console.print("""
===================================
     Library Management System
===================================
1. Login as Librarian
2. Login as Student
3. Exit
===================================
        """)
        choice = typer.prompt("Enter your choice")

        if choice == "1":
            if librarian_login(session):
                librarian_menu(session)

        elif choice == "2":
            user_id = student_login(session)
            if user_id:
                student_menu(user_id,session)

        elif choice == "3":
            console.print("[yellow]Goodbye![/yellow]")
            break

        else:
            console.print("[red]Invalid choice, try again[/red]")

    session.close()


if __name__ == "__main__":
    app()
