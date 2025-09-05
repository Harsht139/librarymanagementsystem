import os
import random
from faker import Faker
from datetime import datetime, timedelta

# Setup
fake = Faker()
Faker.seed(42)
random.seed(42)

# Output directory
os.makedirs("data", exist_ok=True)

def random_date(start_year=2000, end_year=2023):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return (start + timedelta(days=random.randint(0, (end-start).days))).date()

def write_sql(filename, statements):
    with open(os.path.join("data", filename), "w", encoding="utf-8") as f:
        f.write("\n".join(statements))

# =========================================================
# Membership Types
# =========================================================
membership_types = [
    "Student", "Teacher", "Guest", "Researcher", "Staff"
]
mt_sql = [
    f"INSERT INTO membership_types (membership_type_id, name) VALUES ({i+1}, '{t}');"
    for i, t in enumerate(membership_types)
]
write_sql("membership_types.sql", mt_sql)

# =========================================================
# Users
# =========================================================
user_sql = []
for i in range(1, 51):
    name = fake.name().replace("'", "''")
    email = fake.unique.email()
    phone = fake.unique.msisdn()[:10]
    mtype = random.randint(1, len(membership_types))
    mdate = random_date(2015, 2023)
    status = random.choice(["A", "I"])
    user_sql.append(
        f"INSERT INTO users (user_id, full_name, email, phone, membership_type_id, membership_date, status) "
        f"VALUES ({i}, '{name}', '{email}', '{phone}', {mtype}, '{mdate}', '{status}');"
    )
write_sql("users.sql", user_sql)

# =========================================================
# Librarians
# =========================================================
librarian_sql = []
for i in range(1, 6):
    name = fake.name().replace("'", "''")
    email = fake.unique.email()
    username = fake.unique.user_name()
    pwd = fake.sha256()
    librarian_sql.append(
        f"INSERT INTO librarians (librarian_id, full_name, email, username, password_hash) "
        f"VALUES ({i}, '{name}', '{email}', '{username}', '{pwd}');"
    )
write_sql("librarians.sql", librarian_sql)

# =========================================================
# Authors
# =========================================================
author_sql = []
for i in range(1, 31):
    name = fake.unique.name().replace("'", "''")
    nationality = fake.country()
    birth = random.randint(1900, 1980)
    death = birth + random.randint(50, 90) if random.random() < 0.3 else "NULL"
    author_sql.append(
        f"INSERT INTO authors (author_id, full_name, nationality, birth_year, death_year) "
        f"VALUES ({i}, '{name}', '{nationality}', {birth}, {death});"
    )
write_sql("authors.sql", author_sql)

# =========================================================
# Publishers
# =========================================================
publisher_sql = []
for i in range(1, 11):
    name = fake.unique.company().replace("'", "''")
    city = fake.city().replace("'", "''")
    country = fake.country()
    publisher_sql.append(
        f"INSERT INTO publishers (publisher_id, name, city, country) "
        f"VALUES ({i}, '{name}', '{city}', '{country}');"
    )
write_sql("publishers.sql", publisher_sql)

# =========================================================
# Categories
# =========================================================
category_names = ["Fiction", "Non-fiction", "Science", "Technology", "History", "Children", "Philosophy"]
category_sql = []
for i, cat in enumerate(category_names, start=1):
    category_sql.append(
        f"INSERT INTO categories (category_id, name, parent_id) VALUES ({i}, '{cat}', NULL);"
    )
write_sql("categories.sql", category_sql)

# =========================================================
# Books
# =========================================================
book_sql = []
for i in range(1, 51):
    title = fake.sentence(nb_words=4).replace("'", "''")
    isbn = fake.unique.isbn13(separator="-")
    pub = random.randint(1, 10)
    year = random.randint(1980, 2023)
    lang = random.choice(["English", "French", "German", "Spanish", "Hindi"])
    edition = f"{random.randint(1,5)} ed."
    book_sql.append(
        f"INSERT INTO books (book_id, title, isbn, publisher_id, published_year, language, edition) "
        f"VALUES ({i}, '{title}', '{isbn}', {pub}, {year}, '{lang}', '{edition}');"
    )
write_sql("books.sql", book_sql)

# =========================================================
# Book ↔ Authors
# =========================================================
book_author_sql = []
for book_id in range(1, 51):
    authors_for_book = random.sample(range(1, 31), random.randint(1, 3))
    for aid in authors_for_book:
        book_author_sql.append(
            f"INSERT INTO book_authors (book_id, author_id) VALUES ({book_id}, {aid});"
        )
write_sql("book_authors.sql", book_author_sql)

# =========================================================
# Book ↔ Categories
# =========================================================
book_cat_sql = []
for book_id in range(1, 51):
    cats_for_book = random.sample(range(1, len(category_names)+1), random.randint(1, 2))
    for cid in cats_for_book:
        book_cat_sql.append(
            f"INSERT INTO book_categories (book_id, category_id) VALUES ({book_id}, {cid});"
        )
write_sql("book_categories.sql", book_cat_sql)

# =========================================================
# Book copies
# =========================================================
copy_sql = []
copy_id = 1
for book_id in range(1, 51):
    for _ in range(random.randint(2, 5)):
        barcode = fake.unique.ean13()
        shelf = f"Shelf-{random.randint(1,20)}"
        condition = random.randint(1, 4)
        available = random.choice([0,1])
        copy_sql.append(
            f"INSERT INTO book_copies (copy_id, book_id, barcode, shelf_location, condition_code, is_available) "
            f"VALUES ({copy_id}, {book_id}, '{barcode}', '{shelf}', {condition}, {available});"
        )
        copy_id += 1
write_sql("book_copies.sql", copy_sql)

# =========================================================
# Borrows
# =========================================================
borrow_sql = []
for i in range(1, 51):
    user = random.randint(1, 50)
    copy = random.randint(1, copy_id-1)
    librarian = random.randint(1, 5)
    bdate = random_date(2020, 2023)
    ddate = bdate + timedelta(days=14)
    rdate = ddate + timedelta(days=random.randint(-2, 15)) if random.random() < 0.7 else "NULL"
    return_val = f"'{rdate}'" if rdate != "NULL" else "NULL"
    borrow_sql.append(
        f"INSERT INTO borrows (borrow_id, user_id, copy_id, librarian_id, borrow_date, due_date, return_date) "
        f"VALUES ({i}, {user}, {copy}, {librarian}, '{bdate}', '{ddate}', {return_val});"
    )
write_sql("borrows.sql", borrow_sql)

# =========================================================
# Reservations
# =========================================================
res_sql = []
for i in range(1, 21):
    user = random.randint(1, 50)
    book = random.randint(1, 50)
    rdate = fake.date_time_this_year()
    status = random.randint(1, 3)
    res_sql.append(
        f"INSERT INTO reservations (reservation_id, user_id, book_id, reservation_date, status) "
        f"VALUES ({i}, {user}, {book}, '{rdate}', {status});"
    )
write_sql("reservations.sql", res_sql)

# =========================================================
# Fines
# =========================================================
fine_sql = []
for i in range(1, 16):
    borrow = random.randint(1, 50)
    amt = round(random.uniform(10, 100), 2)
    paid = random.choice([0,1])
    pdate = fake.date_time_this_year() if paid else "NULL"
    fine_sql.append(
        f"INSERT INTO fines (fine_id, borrow_id, amount, paid, payment_date) "
        f"VALUES ({i}, {borrow}, {amt}, {paid}, {f'\"{pdate}\"' if paid else 'NULL'});"
    )
write_sql("fines.sql", fine_sql)

# =========================================================
# Reviews
# =========================================================
review_sql = []
for i in range(1, 31):
    user = random.randint(1, 50)
    book = random.randint(1, 50)
    rating = random.randint(1, 5)
    comment = fake.sentence().replace("'", "''")
    rdate = random_date(2020, 2023)
    review_sql.append(
        f"INSERT INTO reviews (review_id, user_id, book_id, rating, comment, review_date) "
        f"VALUES ({i}, {user}, {book}, {rating}, '{comment}', '{rdate}');"
    )
write_sql("reviews.sql", review_sql)

print("✅ Data generation complete! SQL files written to ./data/")
