CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique ID for each book (auto-incremented)
    author VARCHAR(255) NOT NULL,      -- Author of the book
    title VARCHAR(255) NOT NULL,       -- Book title
    asin VARCHAR(20),                  -- ASIN (Amazon Standard Identification Number)
    link TEXT,                         -- URL to the Amazon link
    image TEXT,                        -- URL to the book's image
    categories_flat VARCHAR(255),      -- Categories flat as a single string
    book_description TEXT,             -- Full description of the book (can be long)
    rating DECIMAL(3, 2),              -- Rating of the book (e.g., 4.7)
    isbn_13 VARCHAR(17),               -- ISBN-13 format is up to 17 chars, including "-"
    isbn_10 VARCHAR(13),               -- ISBN-10 is 10 chars long, but can be up to 13
    hardcover VARCHAR(64),             -- Information about the hardcover (e.g., pages count)
    bestsellers_rank_flat TEXT,        -- Bestseller ranking categories flattened
    specifications_flat TEXT           -- Miscellaneous specifications flattened
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_title ON books (title);
CREATE INDEX idx_author ON books (author);
CREATE INDEX idx_rating ON books (rating);
CREATE INDEX idx_categories_flat ON books (categories_flat);
