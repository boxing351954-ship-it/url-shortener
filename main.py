import os
import sqlite3
import string
import random
from flask import Flask, request, redirect, render_template

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "links.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            original_url TEXT NOT NULL
        )
    """)
    return conn


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


@app.route("/", methods=["GET", "POST"])
def index():
    short_url = None
    if request.method == "POST":
        original_url = request.form.get("url", "").strip()
        if original_url:
            if not original_url.startswith(("http://", "https://")):
                original_url = "http://" + original_url

            conn = get_db()
            code = generate_code()
            while conn.execute("SELECT 1 FROM links WHERE code = ?", (code,)).fetchone():
                code = generate_code()
            conn.execute(
                "INSERT INTO links (code, original_url) VALUES (?, ?)",
                (code, original_url),
            )
            conn.commit()
            conn.close()
            short_url = request.host_url + code

    return render_template("index.html", short_url=short_url)


@app.route("/<code>")
def redirect_to_original(code):
    conn = get_db()
    row = conn.execute(
        "SELECT original_url FROM links WHERE code = ?", (code,)
    ).fetchone()
    conn.close()
    if row:
        return redirect(row[0])
    return "Такая короткая ссылка не найдена", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
