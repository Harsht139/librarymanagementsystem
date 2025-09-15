# Library Management System

A comprehensive library management system built with Python, SQLAlchemy, and a rich command-line interface. This system manages books, users, borrowing, and returns with an intuitive CLI interface.

## Features

- **User Management**: Register and manage library members (students, teachers, guests)
- **Book Management**: Add, update, and track books and their copies
- **Borrowing System**: Check out and return books with due date tracking
- **Search Functionality**: Search books by title, author, or category
- **Recommendations**: Get personalized book recommendations
- **Reports**: Generate various library reports and analytics
- **CLI Interface**: User-friendly command-line interface with rich formatting

## Prerequisites

- Python 3.8+
- MySQL Server 8.0+
- pip (Python package manager)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/library-system-sql.git
   cd library-system-sql
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**:
   - Create a MySQL database named `library_db`
   - Update the database connection details in `db.py`
   - Run the schema to create tables:
     ```bash
     mysql -u your_username -p library_db < schema.sql
     ```

## Configuration

Create a `.env` file in the project root with your database credentials:

```env
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=library_db
```

## Usage

1. **Start the application**:
   ```bash
   python cli.py
   ```

2. **Login**:
   - Choose to login as a librarian or student
   - Default librarian credentials (you should change these in production):
     - Username: admin
     - Password: admin123

3. **Main Menu**:
   - Search for books
   - Borrow/return books
   - View account information
   - (For librarians) Manage books, users, and view reports

## Project Structure

- `cli.py`: Main entry point for the application
- `librarian.py`: Librarian-specific functionality
- `student.py`: Student/user functionality
- `db.py`: Database connection and session management
- `schema.sql`: Database schema definition
- `requirements.txt`: Python dependencies
- `data/`: Directory for data files (if any)

## Features in Detail

### For Students:
- Search and browse available books
- Borrow and return books
- View borrowing history
- Get personalized book recommendations
- Update account information

### For Librarians:
- Manage book inventory
- Handle book checkouts and returns
- Manage user accounts
- Generate reports and analytics
- View borrowing statistics

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with ❤️ using Python
- Uses [Rich](https://github.com/Textualize/rich) for beautiful terminal formatting
- Uses [Typer](https://typer.tiangolo.com/) for CLI interface
- Uses [SQLAlchemy](https://www.sqlalchemy.org/) for database operations