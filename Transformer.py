#!/usr/bin/env python3
# transformer.py
#
# Convert Goodbooks-style CSVs into INSERT statements aligned to your LMS schema.
# Tables covered:
#   authors, publishers, categories, books, book_authors, book_categories, users, reviews
#
# Inputs (place these in ./real_data/):
#   - books.csv
#   - tags.csv
#   - book_tags.csv
#   - ratings.csv
#
# Outputs (written to ./data/):
#   - authors.sql
#   - publishers.sql
#   - categories.sql
#   - books.sql
#   - book_authors.sql
#   - book_categories.sql
#   - users.sql
#   - reviews.sql
#
# Notes:
# - Inserts are ordered to respect foreign keys.
# - Uses explicit IDs for authors, categories, publishers, and books so link tables can reference safely.
# - YEAR values clamped to MySQL/MariaDB YEAR range (1901..2155).
# - ISBN truncated to 20 chars; language defaults to 'English' if missing.
# - Category names cleaned and limited to top ~50 by frequency across the selected 5,000 books.
# - 50 synthetic global publishers; randomly assigned to books.
# - 500 users generated with Faker; reviews mapped from ratings.csv by hashing the original user_id.
# - Each book gets at most 10 categories and at most 3 reviews.

import os
import re
import random
from datetime import date, timedelta
import pandas as pd

try:
    from faker import Faker
except ImportError:
    raise SystemExit("Please install requirements: pip install pandas faker")

# ----------------------------- Config -----------------------------
INPUT_DIR = "real_data"
OUTPUT_DIR = "data"

BOOKS_LIMIT = 5000
NUM_USERS = 500
NUM_PUBLISHERS = 50
TOP_CATEGORIES = 50
MAX_CATEGORIES_PER_BOOK = 10
MAX_REVIEWS_PER_BOOK = 3

random.seed(42)
fake = Faker()

# ----------------------------- Helpers -----------------------------
def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def sql_escape(s: str) -> str:
    return s.replace("'", "''")

def clamp_year(y):
    try:
        yi = int(y)
    except Exception:
        return None
    if yi < 1901: yi = 1901
    if yi > 2155: yi = 2155
    return yi

def clean_isbn(isbn):
    if pd.isna(isbn):
        return None
    s = str(isbn).strip()
    s = re.sub(r"[^0-9Xx\-]", "", s)
    if not s:
        return None
    return s[:20]

def clean_language(lang):
    if pd.isna(lang) or not str(lang).strip():
        return "English"
    return str(lang)[:48]

def random_birth():
    birth = random.randint(1850, 1995)
    return clamp_year(birth)

def random_membership_date():
    days = random.randint(0, 365*10)
    return (date.today() - timedelta(days=days)).isoformat()

def random_review_date(published_year):
    start_year = published_year if published_year else 2000
    start_year = clamp_year(start_year) or 2000
    start_date = date(start_year, 1, 1)
    end_date = date.today()
    delta_days = (end_date - start_date).days
    if delta_days <= 0:
        return end_date.isoformat()
    return (start_date + timedelta(days=random.randint(0, delta_days))).isoformat()

def nice_category_name(raw):
    if pd.isna(raw):
        return None
    s = str(raw).strip()
    s = re.sub(r"[_\-]{2,}", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) < 3 or re.fullmatch(r"[-_0-9 ]+", s):
        return None
    return s[:96]

# ----------------------------- Load CSVs -----------------------------
def load_csvs():
    books = pd.read_csv(os.path.join(INPUT_DIR, "books.csv"))
    tags = pd.read_csv(os.path.join(INPUT_DIR, "tags.csv"))
    book_tags = pd.read_csv(os.path.join(INPUT_DIR, "book_tags.csv"))
    ratings = pd.read_csv(os.path.join(INPUT_DIR, "ratings.csv"))

    books = books.iloc[:BOOKS_LIMIT].copy()

    if "book_id" in books.columns:
        books["__book_id__"] = books["book_id"]
    else:
        books["__book_id__"] = books["id"]

    selected_book_ids = set(books["__book_id__"].tolist())

    if "goodreads_book_id" in book_tags.columns:
        book_tags = book_tags[book_tags["goodreads_book_id"].isin(selected_book_ids)].copy()
        book_tags.rename(columns={"goodreads_book_id": "__book_id__"}, inplace=True)
    elif "book_id" in book_tags.columns:
        book_tags = book_tags[book_tags["book_id"].isin(selected_book_ids)].copy()
        book_tags.rename(columns={"book_id": "__book_id__"}, inplace=True)
    else:
        raise ValueError("book_tags.csv must contain 'goodreads_book_id' or 'book_id'")

    ratings = ratings[ratings["book_id"].isin(selected_book_ids)].copy()
    return books, tags, book_tags, ratings

# ----------------------------- Publishers -----------------------------
PUBLISHERS_MASTER = [
    ("Penguin Random House", "New York", "USA"),
    ("HarperCollins", "New York", "USA"),
    ("Simon & Schuster", "New York", "USA"),
    ("Hachette Livre", "Paris", "France"),
    ("Macmillan Publishers", "London", "UK"),
    ("Scholastic", "New York", "USA"),
    ("Bloomsbury", "London", "UK"),
    ("Oxford University Press", "Oxford", "UK"),
    ("Cambridge University Press", "Cambridge", "UK"),
    ("Pearson", "London", "UK"),
    ("Wiley", "Hoboken", "USA"),
    ("Springer", "Berlin", "Germany"),
    ("Elsevier", "Amsterdam", "Netherlands"),
    ("Random House UK", "London", "UK"),
    ("Pan Macmillan", "London", "UK"),
    ("Vintage", "London", "UK"),
    ("Allen & Unwin", "Sydney", "Australia"),
    ("Faber & Faber", "London", "UK"),
    ("Canongate", "Edinburgh", "UK"),
    ("Ecco", "New York", "USA"),
    ("Scribner", "New York", "USA"),
    ("Ballantine Books", "New York", "USA"),
    ("Anchor Books", "New York", "USA"),
    ("Orbit", "London", "UK"),
    ("Tor Books", "New York", "USA"),
    ("Del Rey", "New York", "USA"),
    ("Bantam", "New York", "USA"),
    ("Avon", "New York", "USA"),
    ("Picador", "London", "UK"),
    ("Hodder & Stoughton", "London", "UK"),
    ("Little, Brown", "New York", "USA"),
    ("Crown", "New York", "USA"),
    ("Knopf", "New York", "USA"),
    ("Viking", "New York", "USA"),
    ("Riverhead Books", "New York", "USA"),
    ("Hamish Hamilton", "London", "UK"),
    ("Basic Books", "New York", "USA"),
    ("Da Capo Press", "Boston", "USA"),
    ("The New Press", "New York", "USA"),
    ("MIT Press", "Cambridge", "USA"),
    ("Princeton University Press", "Princeton", "USA"),
    ("Duke University Press", "Durham", "USA"),
    ("Grove Press", "New York", "USA"),
    ("SECKER & WARBURG", "London", "UK"),
    ("Penguin Classics", "London", "UK"),
    ("Harvill Secker", "London", "UK"),
    ("Fourth Estate", "London", "UK"),
    ("Headline", "London", "UK"),
    ("Transworld", "London", "UK"),
    ("SAGE Publications", "Thousand Oaks", "USA"),
]

def pick_publisher_id():
    return random.randint(1, min(NUM_PUBLISHERS, len(PUBLISHERS_MASTER)))

# ----------------------------- Main Transform -----------------------------
def main():
    ensure_dirs()
    books, tags, book_tags, ratings = load_csvs()

    # --------- Authors ---------
    author_name_to_id = {}
    authors_insert = []
    next_author_id = 1

    def add_author(name: str):
        nonlocal next_author_id
        if not name:
            return None
        name = name.strip()
        if not name:
            return None
        key = name.lower()
        if key not in author_name_to_id:
            birth= random_birth()
            author_name_to_id[key] = next_author_id
            authors_insert.append((
                next_author_id,
                name[:160],
                None,
                birth,
            ))
            next_author_id += 1
        return author_name_to_id[key]

    # --------- Books & Authors ---------
    books_rows = []
    book_authors_rows = []

    for _, row in books.iterrows():
        book_id = int(row["__book_id__"])
        title = sql_escape(str(row.get("title") or row.get("original_title") or "Untitled"))
        lang = clean_language(row.get("language_code"))
        isbn = clean_isbn(row.get("isbn") if "isbn" in row else None)
        if not isbn:
            isbn = clean_isbn(row.get("isbn13")) if "isbn13" in row else None
        pub_year_raw = row.get("original_publication_year")
        published_year = clamp_year(pub_year_raw) if not pd.isna(pub_year_raw) else None
        publisher_id = pick_publisher_id()
        edition = None

        books_rows.append((book_id, title[:255], (isbn[:20] if isbn else None),
                           publisher_id, published_year, lang, edition))

        authors_cell = row.get("authors")
        if pd.isna(authors_cell):
            continue
        for name in str(authors_cell).split(","):
            aid = add_author(name)
            if aid:
                book_authors_rows.append((book_id, aid))

    book_authors_rows = list(set(book_authors_rows))

    # --------- Categories ---------
    tags_small = tags[["tag_id", "tag_name"]].copy()
    merged = book_tags.merge(tags_small, on="tag_id", how="left")
    merged["tag_name"] = merged["tag_name"].apply(nice_category_name)
    merged = merged.dropna(subset=["tag_name"])

    tag_freq = merged.groupby(["tag_id", "tag_name"])["count"].sum().reset_index()
    tag_freq = tag_freq.sort_values("count", ascending=False).head(TOP_CATEGORIES)

    category_map = {int(r.tag_id): (i + 1) for i, r in tag_freq.reset_index(drop=True).iterrows()}
    categories_insert = []
    for tag_id, cat_id in category_map.items():
        name = tag_freq[tag_freq["tag_id"] == tag_id]["tag_name"].iloc[0]
        categories_insert.append((cat_id, name))

    book_categories_rows = []
    for book_id, group in merged.groupby("__book_id__"):
        seen = set()
        for _, r in group.iterrows():
            tag_id = int(r["tag_id"])
            if tag_id in category_map and len(seen) < MAX_CATEGORIES_PER_BOOK:
                seen.add(category_map[tag_id])
        for cat_id in seen:
            book_categories_rows.append((int(book_id), cat_id))

    # --------- Publishers ---------
    publishers_insert = []
    for i, (name, city, country) in enumerate(PUBLISHERS_MASTER[:NUM_PUBLISHERS], start=1):
        publishers_insert.append((i, name, city, country))

    # --------- Users ---------
    users_insert = []
    used_emails = set()
    used_phones = set()

    def unique_email():
        e = fake.unique.email()
        return e[:190]

    def unique_phone():
        while True:
            p = re.sub(r"\D", "", fake.phone_number())[:24]
            if p and p not in used_phones:
                used_phones.add(p)
                return p

    for _ in range(NUM_USERS):
        full_name = sql_escape(fake.name())[:120]
        email = unique_email()
        phone = unique_phone() if random.random() < 0.8 else None
        membership_type_id = random.randint(1, 3)
        membership_date = random_membership_date()
        users_insert.append((full_name, email, phone, membership_type_id, membership_date))

    # --------- Reviews ---------
    def map_user(src_user_id):
        return (int(src_user_id) % NUM_USERS) + 1

    by_book = {}
    reviews_rows = []
    for _, r in ratings.iterrows():
        book_id = int(r["book_id"])
        uid = map_user(r["user_id"])
        if book_id not in by_book:
            by_book[book_id] = set()
        if len(by_book[book_id]) >= MAX_REVIEWS_PER_BOOK:
            continue
        key = (uid, book_id)
        if key in by_book[book_id]:
            continue
        by_book[book_id].add(key)
        rating = int(r["rating"])
        pubyear = next((b[4] for b in books_rows if b[0] == book_id), None)
        rdate = random_review_date(pubyear)
        reviews_rows.append((uid, book_id, rating, rdate))

    # ---------------------- Write SQL files ----------------------
    ensure_dirs()

    with open(os.path.join(OUTPUT_DIR, "authors.sql"), "w", encoding="utf-8") as f:
        for (aid, name, nationality, birth) in authors_insert:
            nat_sql = f"'{sql_escape(nationality)}'" if nationality else "NULL"
            birth_sql = f"{birth}" if birth else "NULL"
            f.write(
                "INSERT INTO authors (author_id, full_name, nationality, birth_year) "
                f"VALUES ({aid}, '{sql_escape(name)}', {nat_sql}, {birth_sql});\n"
            )

    with open(os.path.join(OUTPUT_DIR, "publishers.sql"), "w", encoding="utf-8") as f:
        for (pid, name, city, country) in publishers_insert:
            city_sql = f"'{sql_escape(city)}'" if city else "NULL"
            country_sql = f"'{sql_escape(country)}'" if country else "NULL"
            f.write(
                "INSERT INTO publishers (publisher_id, name, city, country) "
                f"VALUES ({pid}, '{sql_escape(name)}', {city_sql}, {country_sql});\n"
            )

    with open(os.path.join(OUTPUT_DIR, "categories.sql"), "w", encoding="utf-8") as f:
        for (cid, name) in categories_insert:
            f.write(
                "INSERT INTO categories (category_id, name, parent_id) "
                f"VALUES ({cid}, '{sql_escape(name)}', NULL);\n"
            )

    with open(os.path.join(OUTPUT_DIR, "books.sql"), "w", encoding="utf-8") as f:
        for (book_id, title, isbn, pub_id, pubyear, lang, edition) in books_rows:
            isbn_sql = f"'{sql_escape(isbn)}'" if isbn else "NULL"
            pubyear_sql = f"{pubyear}" if pubyear else "NULL"
            lang_sql = f"'{sql_escape(lang)}'" if lang else "NULL"
            edition_sql = f"'{sql_escape(edition)}'" if edition else "NULL"
            f.write(
                "INSERT INTO books (book_id, title, isbn, publisher_id, published_year, language, edition) "
                f"VALUES ({book_id}, '{sql_escape(title)}', {isbn_sql}, {pub_id}, {pubyear_sql}, {lang_sql}, {edition_sql});\n"
            )

    with open(os.path.join(OUTPUT_DIR, "book_authors.sql"), "w", encoding="utf-8") as f:
        for (book_id, author_id) in sorted(book_authors_rows):
            f.write(f"INSERT INTO book_authors (book_id, author_id) VALUES ({book_id}, {author_id});\n")

    with open(os.path.join(OUTPUT_DIR, "book_categories.sql"), "w", encoding="utf-8") as f:
        for (book_id, category_id) in sorted(book_categories_rows):
            f.write(f"INSERT INTO book_categories (book_id, category_id) VALUES ({book_id}, {category_id});\n")

    with open(os.path.join(OUTPUT_DIR, "users.sql"), "w", encoding="utf-8") as f:
        for (full_name, email, phone, mtype, mdate) in users_insert:
            phone_sql = f"'{sql_escape(phone)}'" if phone else "NULL"
            f.write(
                "INSERT INTO users (full_name, email, phone, membership_type_id, membership_date) "
                f"VALUES ('{sql_escape(full_name)}', '{sql_escape(email)}', {phone_sql}, {mtype}, '{mdate}');\n"
            )

    with open(os.path.join(OUTPUT_DIR, "reviews.sql"), "w", encoding="utf-8") as f:
        for (uid, book_id, rating, rdate) in reviews_rows:
            f.write(
                "INSERT INTO reviews (user_id, book_id, rating, review_date) "
                f"VALUES ({uid}, {book_id}, {rating}, '{rdate}');\n"
            )

    print("✅ Done! SQL files written in ./data")
    print("   Order to load (after schema + membership_types):")
    print("   1) publishers.sql")
    print("   2) authors.sql")
    print("   3) categories.sql")
    print("   4) books.sql")
    print("   5) book_authors.sql")
    print("   6) book_categories.sql")
    print("   7) users.sql")
    print("   8) reviews.sql")

# -----------------------------
if __name__ == "__main__":
    main()
