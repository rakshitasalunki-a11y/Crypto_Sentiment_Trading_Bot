# Crypto Sentiment-Based Trading Bot

Flask + MySQL project based on the report in `Rakshita(1).PDF`.

## Features

- Index page, registration, login, user dashboard, and admin dashboard
- MySQL database import file for phpMyAdmin: `schema.sql`
- Plain password login as requested for academic/demo use
- AI-style sentiment analyzer for crypto social/news text
- BUY / SELL / HOLD signal generator using sentiment, RSI, and moving average
- Stop-loss, take-profit, trade simulation logs, and chart dashboard
- Admin can view operations, registered users, and add/edit/delete users

## Admin Credentials

- Email: `admin@cryptobot.com`
- Password: `admin123`

## Demo User

- Email: `trader@example.com`
- Password: `12345`

## Setup

1. Open phpMyAdmin.
2. Import `schema.sql`.
3. Install packages:

```bash
pip install -r requirements.txt
```

4. Run the project:

```bash
python app.py
```

5. Open:

```text
http://127.0.0.1:5000
```

In this workspace I started it on `http://127.0.0.1:5002` because port `5000` was already occupied by another local project.

## Database Settings

Default database settings are in `app.py`:

- DB name: `crypto_sentiment_bot`
- User: `root`
- Password: empty
- Host: `localhost`

You can also set `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` as environment variables.
