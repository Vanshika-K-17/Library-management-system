import os, tempfile, unittest
import app as appmod


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".db")
        appmod.app.config["DATABASE"] = self.path
        appmod.init_db()
        self.c = appmod.app.test_client()
        self.book = self.c.post("/api/books", json={"title": "Clean Code", "author": "Robert Martin",
                                                     "isbn": "111", "category": "Programming"}).get_json()
        self.member = self.c.post("/api/members", json={"name": "Vanshika", "email": "v@x.com"}).get_json()

    def tearDown(self):
        os.close(self.fd); os.remove(self.path)

    def test_add_and_list(self):
        self.assertEqual(len(self.c.get("/api/books").get_json()), 1)

    def test_add_missing_field(self):
        self.assertEqual(self.c.post("/api/books", json={"title": "x"}).status_code, 400)

    def test_duplicate_isbn(self):
        r = self.c.post("/api/books", json={"title": "A", "author": "B", "isbn": "111", "category": "C"})
        self.assertEqual(r.status_code, 409)

    def test_search_found_and_not_found(self):
        self.assertEqual(len(self.c.get("/api/books/search?q=martin").get_json()), 1)
        self.assertEqual(self.c.get("/api/books/search?q=zzzz").get_json(), [])

    def test_issue_twice_blocked(self):
        bid, mid = self.book["id"], self.member["id"]
        self.assertEqual(self.c.post(f"/api/books/{bid}/issue", json={"member_id": mid}).status_code, 200)
        self.assertEqual(self.c.post(f"/api/books/{bid}/issue", json={"member_id": mid}).status_code, 409)

    def test_return_not_issued(self):
        self.assertEqual(self.c.post(f"/api/books/{self.book['id']}/return").status_code, 400)

    def test_issue_return_cycle(self):
        bid, mid = self.book["id"], self.member["id"]
        self.c.post(f"/api/books/{bid}/issue", json={"member_id": mid})
        self.assertEqual(self.c.post(f"/api/books/{bid}/return").status_code, 200)
        self.assertTrue(self.c.get("/api/books").get_json()[0]["available"])

    def test_delete(self):
        bid = self.book["id"]
        self.assertEqual(self.c.delete(f"/api/books/{bid}").status_code, 200)
        self.assertEqual(self.c.delete(f"/api/books/{bid}").status_code, 404)

    def test_delete_issued_blocked(self):
        bid = self.book["id"]
        self.c.post(f"/api/books/{bid}/issue", json={"member_id": self.member["id"]})
        self.assertEqual(self.c.delete(f"/api/books/{bid}").status_code, 409)

    def test_issue_unknown_member(self):
        self.assertEqual(self.c.post(f"/api/books/{self.book['id']}/issue", json={"member_id": 99}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
