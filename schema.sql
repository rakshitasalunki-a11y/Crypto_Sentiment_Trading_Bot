CREATE DATABASE IF NOT EXISTS crypto_sentiment_bot;
USE crypto_sentiment_bot;

DROP TABLE IF EXISTS trades;
DROP TABLE IF EXISTS signals;
DROP TABLE IF EXISTS operations;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE operations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    source_text TEXT NOT NULL,
    sentiment_score DECIMAL(4,2) NOT NULL,
    sentiment_label VARCHAR(20) NOT NULL,
    price DECIMAL(14,2) NOT NULL,
    moving_average DECIMAL(14,2) NOT NULL,
    rsi DECIMAL(5,2) NOT NULL,
    `signal` VARCHAR(10) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    signal_id INT NULL,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,
    entry_price DECIMAL(14,2) NOT NULL,
    stop_loss DECIMAL(6,2) NOT NULL,
    take_profit DECIMAL(6,2) NOT NULL,
    quantity DECIMAL(10,4) NOT NULL DEFAULT 1,
    pnl DECIMAL(12,2) DEFAULT 0,
    status VARCHAR(30) DEFAULT 'Simulated',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE SET NULL
);

INSERT INTO users (name, email, password, phone) VALUES
('Demo Trader', 'trader@example.com', '12345', '9876543210');

INSERT INTO operations (user_id, action, details, ip_address) VALUES
(1, 'Seed Data', 'Demo trader created for project testing', 'localhost');

INSERT INTO signals
(user_id, symbol, source_text, sentiment_score, sentiment_label, price, moving_average, rsi, `signal`, reason)
VALUES
(1, 'BTC', 'Bitcoin adoption and ETF inflows look bullish with strong support.', 0.75, 'Bullish', 67250.00, 65000.00, 52.40, 'BUY', 'Positive sentiment and price strength detected.'),
(1, 'ETH', 'Ethereum faces short term resistance but developer growth remains positive.', 0.20, 'Neutral', 3420.00, 3380.00, 61.20, 'HOLD', 'Market conditions are mixed.');

INSERT INTO trades
(user_id, signal_id, symbol, action, entry_price, stop_loss, take_profit, quantity, pnl, status)
VALUES
(1, 1, 'BTC', 'BUY', 67250.00, 2.50, 6.00, 1.0000, 35.00, 'Simulated'),
(1, 2, 'ETH', 'HOLD', 3420.00, 3.00, 5.50, 1.0000, 1.25, 'Watched');
