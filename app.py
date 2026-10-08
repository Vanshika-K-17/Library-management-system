import os
import sqlite3
from flask import Flask, g, jsonify, request, render_template

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config["DATABASE"] = os.path.join(BASE, "library.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    with sqlite3.connect(app.config["DATABASE"]) as con:
        with open(os.path.join(BASE, "schema.sql")) as f:
            con.executescript(f.read())


def err(msg, code):
    return jsonify({"error": msg}), code


def book_dict(r):
    d = dict(r)
    d["status"] = "Available" if d["available"] else "Issued"
    return d


@app.route("/")
def index():
    return render_template("index.html")


# ---------- Books ----------
@app.route("/api/books", methods=["GET"])
def list_books():
    rows = get_db().execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    return jsonify([book_dict(r) for r in rows])


@app.route("/api/books", methods=["POST"])
def add_book():
    data = request.get_json(silent=True) or {}
    fields = {k: str(data.get(k, "")).strip() for k in ("title", "author", "isbn", "category")}
    missing = [k for k, v in fields.items() if not v]
    if missing:
        return err(f"Missing required field(s): {', '.join(missing)}", 400)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO books (title, author, isbn, category) VALUES (?,?,?,?)",
            (fields["title"], fields["author"], fields["isbn"], fields["category"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return err("A book with this ISBN already exists", 409)
    row = db.execute("SELECT * FROM books WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(book_dict(row)), 201


@app.route("/api/books/search", methods=["GET"])
def search_books():
    q = request.args.get("q", "").strip()
    if not q:
        return err("Search query 'q' is required", 400)
    like = f"%{q}%"
    rows = get_db().execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? ORDER BY id DESC",
        (like, like, like),
    ).fetchall()
    return jsonify([book_dict(r) for r in rows])


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book:
        return err("Book not found", 404)
    if not book["available"]:
        return err("Cannot delete a book that is currently issued", 409)
    db.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()
    return jsonify({"message": "Book deleted"})


@app.route("/api/books/<int:book_id>/issue", methods=["POST"])
def issue_book(book_id):
    data = request.get_json(silent=True) or {}
    member_id = data.get("member_id")
    if not member_id:
        return err("member_id is required", 400)
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book:
        return err("Book not found", 404)
    if not db.execute("SELECT 1 FROM members WHERE id=?", (member_id,)).fetchone():
        return err("Member not found", 404)
    if not book["available"]:
        return err("Book is already issued and unavailable", 409)
    db.execute("INSERT INTO issues (book_id, member_id) VALUES (?,?)", (book_id, member_id))
    db.execute("UPDATE books SET available=0 WHERE id=?", (book_id,))
    db.commit()
    return jsonify({"message": "Book issued"})


@app.route("/api/books/<int:book_id>/return", methods=["POST"])
def return_book(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book:
        return err("Book not found", 404)
    issue = db.execute(
        "SELECT id FROM issues WHERE book_id=? AND return_date IS NULL", (book_id,)
    ).fetchone()
    if book["available"] or not issue:
        return err("This book is not currently issued", 400)
    db.execute("UPDATE issues SET return_date=date('now') WHERE id=?", (issue["id"],))
    db.execute("UPDATE books SET available=1 WHERE id=?", (book_id,))
    db.commit()
    return jsonify({"message": "Book returned"})


# ---------- Members ----------
@app.route("/api/members", methods=["GET"])
def list_members():
    rows = get_db().execute("SELECT * FROM members ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/members", methods=["POST"])
def add_member():
    data = request.get_json(silent=True) or {}
    name, email = str(data.get("name", "")).strip(), str(data.get("email", "")).strip()
    if not name or not email:
        return err("name and email are required", 400)
    db = get_db()
    try:
        cur = db.execute("INSERT INTO members (name, email) VALUES (?,?)", (name, email))
        db.commit()
    except sqlite3.IntegrityError:
        return err("A member with this email already exists", 409)
    return jsonify({"id": cur.lastrowid, "name": name, "email": email}), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
