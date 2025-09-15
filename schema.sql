-- =========================================================
-- Library Management System (MySQL 8.0+)
-- =========================================================
SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE DATABASE IF NOT EXISTS library_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE library_db;

-- Lookup tables
CREATE TABLE membership_types (
  membership_type_id TINYINT UNSIGNED PRIMARY KEY,
  name VARCHAR(32) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT IGNORE INTO membership_types (membership_type_id, name)
VALUES (1,'Student'),(2,'Teacher'),(3,'Guest');

-- Users
CREATE TABLE users (
  user_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(190) NOT NULL UNIQUE,
  phone VARCHAR(24) NULL UNIQUE,
  membership_type_id TINYINT UNSIGNED NOT NULL,
  membership_date DATE NOT NULL,
  status CHAR(1) NOT NULL DEFAULT 'A',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_membership_type
    FOREIGN KEY (membership_type_id) REFERENCES membership_types (membership_type_id)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT chk_users_status CHECK (status IN ('A','I'))
) ENGINE=InnoDB;

-- Librarians
CREATE TABLE librarians (
  librarian_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(190) NOT NULL UNIQUE,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash CHAR(60) NOT NULL
) ENGINE=InnoDB;

-- Authors
CREATE TABLE authors (
  author_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(160) NOT NULL,
  nationality VARCHAR(64),
  birth_year YEAR,
  death_year YEAR,
  UNIQUE KEY uq_authors_name (full_name)
) ENGINE=InnoDB;

-- Publishers
CREATE TABLE publishers (
  publisher_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(160) NOT NULL UNIQUE,
  city VARCHAR(96),
  country VARCHAR(96)
) ENGINE=InnoDB;

-- Categories
CREATE TABLE categories (
  category_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(96) NOT NULL UNIQUE,
  parent_id BIGINT UNSIGNED,
  FOREIGN KEY (parent_id) REFERENCES categories(category_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- Books
CREATE TABLE books (
  book_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  isbn VARCHAR(20) UNIQUE,
  publisher_id BIGINT UNSIGNED,
  published_year YEAR,
  language VARCHAR(48) DEFAULT 'English',
  edition VARCHAR(48),
  FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- M:N Books ↔ Authors
CREATE TABLE book_authors (
  book_id BIGINT UNSIGNED NOT NULL,
  author_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (book_id, author_id),
  FOREIGN KEY (book_id) REFERENCES books(book_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (author_id) REFERENCES authors(author_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- M:N Books ↔ Categories
CREATE TABLE book_categories (
  book_id BIGINT UNSIGNED NOT NULL,
  category_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (book_id, category_id),
  FOREIGN KEY (book_id) REFERENCES books(book_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES categories(category_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Book copies
CREATE TABLE book_copies (
  copy_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  book_id BIGINT UNSIGNED NOT NULL,
  barcode VARCHAR(64) NOT NULL UNIQUE,
  shelf_location VARCHAR(64),
  condition_code TINYINT UNSIGNED NOT NULL DEFAULT 2,
  is_available BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (book_id) REFERENCES books(book_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_condition CHECK (condition_code BETWEEN 1 AND 4)
) ENGINE=InnoDB;

-- Borrow records
CREATE TABLE borrows (
  borrow_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  copy_id BIGINT UNSIGNED NOT NULL,
  librarian_id BIGINT UNSIGNED,
  borrow_date DATE NOT NULL,
  due_date DATE NOT NULL,
  return_date DATE,
  active TINYINT(1) AS (CASE WHEN return_date IS NULL THEN 1 ELSE 0 END) STORED,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (copy_id) REFERENCES book_copies(copy_id),
  FOREIGN KEY (librarian_id) REFERENCES librarians(librarian_id)
) ENGINE=InnoDB;

-- Reservations
CREATE TABLE reservations (
  reservation_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  book_id BIGINT UNSIGNED NOT NULL,
  reservation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status TINYINT UNSIGNED NOT NULL DEFAULT 1,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (book_id) REFERENCES books(book_id)
) ENGINE=InnoDB;

-- Fines
CREATE TABLE fines (
  fine_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  borrow_id BIGINT UNSIGNED NOT NULL,
  amount DECIMAL(8,2) NOT NULL,
  paid BOOLEAN NOT NULL DEFAULT FALSE,
  payment_date DATETIME,
  FOREIGN KEY (borrow_id) REFERENCES borrows(borrow_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- Reviews
CREATE TABLE reviews (
  review_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  book_id BIGINT UNSIGNED NOT NULL,
  rating TINYINT UNSIGNED NOT NULL,
  comment TEXT,
  review_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  UNIQUE KEY uq_review_user_book (user_id, book_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (book_id) REFERENCES books(book_id),
  CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5)
) ENGINE=InnoDB;

CREATE TABLE book_damages (
    damage_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    copy_id BIGINT UNSIGNED NOT NULL,
    damage_date DATE NOT NULL,
    description TEXT,
    FOREIGN KEY (copy_id) REFERENCES book_copies(copy_id)
      ON DELETE CASCADE
);
