-- =========================================================
-- Queries for Library Management System
-- =========================================================

-- 1. Overdue books (INNER JOIN + WHERE filter)
SELECT u.full_name, b.title, br.due_date
FROM borrows br
JOIN users u ON br.user_id = u.user_id
JOIN book_copies bc ON br.copy_id = bc.copy_id
JOIN books b ON bc.book_id = b.book_id
WHERE br.return_date IS NULL AND br.due_date < CURDATE();

-- 2. Top 5 most borrowed books (GROUP BY + ORDER BY)
SELECT b.title, COUNT(*) AS borrow_count
FROM borrows br
JOIN book_copies bc ON br.copy_id = bc.copy_id
JOIN books b ON bc.book_id = b.book_id
GROUP BY b.book_id
ORDER BY borrow_count DESC
LIMIT 5;

-- 3. Users with unpaid fines (JOIN + GROUP BY)
SELECT u.full_name, SUM(f.amount) AS total_fines
FROM fines f
JOIN borrows br ON f.borrow_id = br.borrow_id
JOIN users u ON br.user_id = u.user_id
WHERE f.paid = FALSE
GROUP BY u.user_id
ORDER BY total_fines DESC;

-- 4. Books and their average review rating (AGGREGATION)
SELECT b.title, ROUND(AVG(r.rating),2) AS avg_rating, COUNT(r.review_id) AS review_count
FROM books b
LEFT JOIN reviews r ON b.book_id = r.book_id
GROUP BY b.book_id
ORDER BY avg_rating DESC;

-- 5. Most popular authors (JOIN through book_authors)
SELECT a.full_name, COUNT(*) AS times_borrowed
FROM borrows br
JOIN book_copies bc ON br.copy_id = bc.copy_id
JOIN books b ON bc.book_id = b.book_id
JOIN book_authors ba ON b.book_id = ba.book_id
JOIN authors a ON ba.author_id = a.author_id
GROUP BY a.author_id
ORDER BY times_borrowed DESC
LIMIT 5;

-- 6. Active reservations (LEFT JOIN)
SELECT u.full_name, b.title, r.reservation_date
FROM reservations r
JOIN users u ON r.user_id = u.user_id
JOIN books b ON r.book_id = b.book_id
WHERE r.status = 1
ORDER BY r.reservation_date DESC;

-- 7. Books per category (JOIN + GROUP BY)
SELECT c.name AS category, COUNT(bc.book_id) AS total_books
FROM categories c
LEFT JOIN book_categories bc ON c.category_id = bc.category_id
GROUP BY c.category_id
ORDER BY total_books DESC;

-- 8. Users with the most borrows (TOP-N)
SELECT u.full_name, COUNT(*) AS total_borrows
FROM borrows br
JOIN users u ON br.user_id = u.user_id
GROUP BY u.user_id
ORDER BY total_borrows DESC
LIMIT 5;

-- 9. Books currently available vs borrowed (CASE aggregation)
SELECT 
    SUM(CASE WHEN bc.is_available = TRUE THEN 1 ELSE 0 END) AS available,
    SUM(CASE WHEN bc.is_available = FALSE THEN 1 ELSE 0 END) AS borrowed
FROM book_copies bc;

-- 10. Fines collected per month (DATE + GROUP BY)
SELECT DATE_FORMAT(payment_date, '%Y-%m') AS month, SUM(amount) AS total_collected
FROM fines
WHERE paid = TRUE
GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
ORDER BY month;

-- 11. Subquery Example: Users who never borrowed a book
SELECT full_name
FROM users
WHERE user_id NOT IN (SELECT DISTINCT user_id FROM borrows);

-- 12. CTE Example: Find top 3 users with highest total fines
WITH user_fines AS (
    SELECT u.user_id, u.full_name, SUM(f.amount) AS total_fines
    FROM fines f
    JOIN borrows br ON f.borrow_id = br.borrow_id
    JOIN users u ON br.user_id = u.user_id
    GROUP BY u.user_id
)
SELECT * FROM user_fines
ORDER BY total_fines DESC
LIMIT 3;

-- 13. Window Function Example: Ranking books by borrow count
SELECT b.title,
       COUNT(br.borrow_id) AS borrow_count,
       RANK() OVER (ORDER BY COUNT(br.borrow_id) DESC) AS rank_position
FROM books b
LEFT JOIN book_copies bc ON b.book_id = bc.book_id
LEFT JOIN borrows br ON bc.copy_id = br.copy_id
GROUP BY b.book_id
ORDER BY borrow_count DESC;

