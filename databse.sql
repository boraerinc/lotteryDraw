/*
Created by Bora Erinc, 5th of December 2023 
*/

-- Users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255) UNIQUE,
    password VARCHAR(255)
);

-- Shows Table
CREATE TABLE shows (
    show_id INT AUTO_INCREMENT PRIMARY KEY,
    available_tickets INT,
    name VARCHAR(255),
    time DATETIME,
    location VARCHAR(255),
    cast TEXT,
    genre VARCHAR(100)
);

-- Entries Table
CREATE TABLE entries (
    entry_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    show_id INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (show_id) REFERENCES shows(show_id)
);

-- Winners Table
CREATE TABLE winners (
    winner_id INT AUTO_INCREMENT PRIMARY KEY,
    show_id INT,
    user_id INT,
    ticket_redeemed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (show_id) REFERENCES shows(show_id)
);

-- Indices for frequent queries
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_entries_user_id ON entries(user_id);
CREATE INDEX idx_entries_show_id ON entries(show_id);
CREATE INDEX idx_winners_user_id ON winners(user_id);
CREATE INDEX idx_winners_show_id ON winners(show_id);
