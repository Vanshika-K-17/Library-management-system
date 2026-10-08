# Library Management System

Stack: HTML/CSS/JS (Fetch API) + Node.js tooling (Prettier/ESLint) | Flask | SQLite

## Run
    pip install -r requirements.txt
    python app.py          # open http://127.0.0.1:5000
    python test_api.py     # edge-case tests
    npm install && npm run format   # optional Node tooling

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/books | List books |
| POST | /api/books | Add book |
| GET | /api/books/search?q= | Search title/author/ISBN |
| POST | /api/books/<id>/issue | Issue (body: member_id) |
| POST | /api/books/<id>/return | Return |
| DELETE | /api/books/<id> | Delete |
| GET/POST | /api/members | List / add member |

## Schema
books(id, title, author, isbn UNIQUE, category, available) ·
members(id, name, email UNIQUE) ·
issues(id, book_id→books, member_id→members, issue_date, return_date)
