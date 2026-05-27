from datetime import datetime
import math
import os
import random
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "crypto-sentiment-bot-secret")

DB_PATH = "crypto_sentiment_bot.db"

ADMIN_EMAIL = "admin@cryptobot.com"
ADMIN_PASSWORD = "admin123"

POSITIVE_WORDS = {
    "bullish", "moon", "surge", "pump", "profit", "breakout", "gain", "rally",
    "adoption", "upgrade", "partnership", "buy", "strong", "green", "recover",
    "optimistic", "support", "high", "growth", "win", "safe", "positive",
}
NEGATIVE_WORDS = {
    "bearish", "dump", "crash", "loss", "fear", "sell", "weak", "red",
    "hack", "ban", "lawsuit", "panic", "drop", "risk", "volatile", "low",
    "negative", "scam", "liquidation", "recession", "resistance", "down",
}


# ------------------ SQLITE DB FUNCTIONS ------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, params=(), fetchone=False):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchone() if fetchone else cur.fetchall()
        if fetchone:
            return dict(rows) if rows else None
        return [dict(row) for row in rows]


def execute(sql, params=()):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid


# ------------------ CREATE TABLES IF NOT EXISTS ------------------

def init_db():
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            source_text TEXT,
            sentiment_score REAL,
            sentiment_label TEXT,
            price REAL,
            moving_average REAL,
            rsi REAL,
            signal TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            signal_id INTEGER,
            symbol TEXT,
            action TEXT,
            entry_price REAL,
            stop_loss REAL,
            take_profit REAL,
            quantity REAL,
            pnl REAL,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        conn.commit()


# ------------------ HELPERS ------------------

def current_user():
    if "user_id" not in session:
        return None
    return query("SELECT * FROM users WHERE id=?", (session["user_id"],), fetchone=True)


def log_operation(action, details):
    execute(
        "INSERT INTO operations (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)",
        (session.get("user_id"), action, details, request.remote_addr),
    )


def analyze_sentiment(text):
    words = [w.strip(".,!?;:()[]{}'\"").lower() for w in text.split()]
    positive = sum(1 for word in words if word in POSITIVE_WORDS)
    negative = sum(1 for word in words if word in NEGATIVE_WORDS)
    total = max(positive + negative, 1)
    raw = (positive - negative) / total
    score = round(max(min(raw, 1), -1), 2)

    if score >= 0.25:
        mood = "Bullish"
    elif score <= -0.25:
        mood = "Bearish"
    else:
        mood = "Neutral"

    return score, mood, positive, negative


def make_signal(sentiment_score, price, ma50, rsi):
    if sentiment_score >= 0.35 and price >= ma50 and rsi < 70:
        return "BUY", "Positive sentiment and price strength detected."
    if sentiment_score <= -0.35 or rsi > 75:
        return "SELL", "Risk is elevated due to weak sentiment or overbought RSI."
    return "HOLD", "Market conditions are mixed. Wait for stronger confirmation."


def demo_market_snapshot(symbol):
    base_prices = {"BTC": 67000, "ETH": 3400, "SOL": 155, "BNB": 610, "XRP": 0.62}
    base = base_prices.get(symbol, 120)
    price = round(base * random.uniform(0.96, 1.06), 2)
    ma50 = round(base * random.uniform(0.94, 1.04), 2)
    rsi = round(random.uniform(28, 78), 1)
    volume = round(random.uniform(2.2, 18.8), 2)
    return price, ma50, rsi, volume


# ------------------ GLOBAL TEMPLATE VARIABLES ------------------

@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "is_admin": session.get("is_admin", False),
        "year": datetime.now().year,
    }


# ------------------ ROUTES ------------------

@app.route("/")
def index():
    sample_posts = [
        "Bitcoin rally looks strong after ETF inflows and institutional adoption.",
        "Ethereum gas upgrade creates optimistic developer sentiment.",
        "Market panic after liquidation wave, but long-term support remains.",
    ]
    analyzed = []
    for post in sample_posts:
        score, mood, _, _ = analyze_sentiment(post)
        analyzed.append({"text": post, "score": score, "mood": mood})
    return render_template("index.html", analyzed=analyzed)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        phone = request.form.get("phone", "").strip()

        if not name or not email or not password:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("register"))

        try:
            user_id = execute(
                "INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)",
                (name, email, password, phone),
            )
            session["user_id"] = user_id
            log_operation("Registration", f"New user registered: {email}")
            flash("Registration successful. Welcome to CryptoSense AI.", "success")
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("Email already registered. Please login.", "warning")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session.clear()
            session["is_admin"] = True
            log_operation("Admin Login", "Admin signed into dashboard")
            return redirect(url_for("admin_dashboard"))

        user = query(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password),
            fetchone=True,
        )

        if user:
            session.clear()
            session["user_id"] = user["id"]
            log_operation("Login", f"{email} logged in")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    signals = query(
        "SELECT * FROM signals WHERE user_id=? ORDER BY created_at DESC LIMIT 6",
        (session["user_id"],),
    )
    trades = query(
        "SELECT * FROM trades WHERE user_id=? ORDER BY created_at DESC LIMIT 6",
        (session["user_id"],),
    )
    return render_template("dashboard.html", signals=signals, trades=trades)


@app.route("/analyze", methods=["POST"])
def analyze():
    if "user_id" not in session:
        return redirect(url_for("login"))

    symbol = request.form["symbol"].upper()
    text = request.form["market_text"].strip()
    stop_loss = float(request.form.get("stop_loss", 2.5))
    take_profit = float(request.form.get("take_profit", 5.0))

    score, mood, positive, negative = analyze_sentiment(text)
    price, ma50, rsi, volume = demo_market_snapshot(symbol)
    signal, reason = make_signal(score, price, ma50, rsi)

    signal_id = execute(
        """
        INSERT INTO signals
        (user_id, symbol, source_text, sentiment_score, sentiment_label, price, moving_average, rsi, signal, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (session["user_id"], symbol, text, score, mood, price, ma50, rsi, signal, reason),
    )

    pnl = round((take_profit - stop_loss) * 10 * (1 if signal == "BUY" else -0.35 if signal == "SELL" else 0.05), 2)

    execute(
        """
        INSERT INTO trades
        (user_id, signal_id, symbol, action, entry_price, stop_loss, take_profit, quantity, pnl, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (session["user_id"], signal_id, symbol, signal, price, stop_loss, take_profit, 1.0, pnl, "Simulated"),
    )

    log_operation("AI Signal Generated", f"{symbol}: {signal} ({mood}, score {score})")

    flash(f"{symbol} analysis complete: {signal} signal generated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("login"))

    users = query("SELECT * FROM users ORDER BY created_at DESC")

    operations = query("""
        SELECT operations.*, users.name AS user_name, users.email
        FROM operations
        LEFT JOIN users ON operations.user_id = users.id
        ORDER BY operations.created_at DESC
        LIMIT 100
    """)

    stats = {
        "users": query("SELECT COUNT(*) AS total FROM users", fetchone=True)["total"],
        "signals": query("SELECT COUNT(*) AS total FROM signals", fetchone=True)["total"],
        "trades": query("SELECT COUNT(*) AS total FROM trades", fetchone=True)["total"],
        "avg_sentiment": query("SELECT COALESCE(ROUND(AVG(sentiment_score), 2), 0) AS total FROM signals", fetchone=True)["total"],
    }

    return render_template("admin.html", users=users, operations=operations, stats=stats)


@app.route("/admin/user/add", methods=["POST"])
def admin_add_user():
    if not session.get("is_admin"):
        return redirect(url_for("login"))

    execute(
        "INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)",
        (
            request.form["name"].strip(),
            request.form["email"].strip().lower(),
            request.form["password"],
            request.form.get("phone", "").strip(),
        ),
    )

    log_operation("Admin Add User", request.form["email"].strip().lower())
    flash("User added successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/edit", methods=["POST"])
def admin_edit_user(user_id):
    if not session.get("is_admin"):
        return redirect(url_for("login"))

    execute(
        "UPDATE users SET name=?, email=?, password=?, phone=? WHERE id=?",
        (
            request.form["name"].strip(),
            request.form["email"].strip().lower(),
            request.form["password"],
            request.form.get("phone", "").strip(),
            user_id,
        ),
    )

    log_operation("Admin Edit User", f"Updated user ID {user_id}")
    flash("User updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def admin_delete_user(user_id):
    if not session.get("is_admin"):
        return redirect(url_for("login"))

    execute("DELETE FROM users WHERE id=?", (user_id,))
    log_operation("Admin Delete User", f"Deleted user ID {user_id}")
    flash("User deleted successfully.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/api/chart-data")
def chart_data():
    points = []
    for index in range(20):
        sentiment = round(math.sin(index / 2) * 0.45 + random.uniform(-0.18, 0.18), 2)
        price = round(100 + index * 4 + random.uniform(-8, 8), 2)
        points.append({"label": f"T{index + 1}", "sentiment": sentiment, "price": price})
    print("Chart data points:", points)
    
    return {"points": points}


# ------------------ MAIN ------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)