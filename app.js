const $ = (s) => document.querySelector(s);
const bookBody = $("#book-body");
const memberSelect = $("#member-select");
let currentQuery = "";

function toast(msg, type = "success") {
  const t = $("#toast");
  t.textContent = msg;
  t.className = `toast ${type}`;
  t.hidden = false;
  setTimeout(() => (t.hidden = true), 2800);
}

async function api(url, method = "GET", body) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function render(books) {
  bookBody.innerHTML = books
    .map(
      (b) => `<tr>
      <td>${b.id}</td><td>${esc(b.title)}</td><td>${esc(b.author)}</td>
      <td>${esc(b.isbn)}</td><td>${esc(b.category)}</td>
      <td><span class="badge ${b.available ? "ok" : "out"}">${b.status}</span></td>
      <td>
        <button data-act="issue" data-id="${b.id}">Issue</button>
        <button data-act="return" data-id="${b.id}" class="secondary">Return</button>
        <button data-act="delete" data-id="${b.id}" class="danger">Delete</button>
      </td></tr>`
    )
    .join("");
  const empty = $("#empty");
  empty.hidden = books.length > 0;
  if (!books.length)
    empty.textContent = currentQuery
      ? `No books found for "${currentQuery}".`
      : "No books yet. Add one above.";
}

async function loadBooks() {
  try {
    const url = currentQuery
      ? `/api/books/search?q=${encodeURIComponent(currentQuery)}`
      : "/api/books";
    render(await api(url));
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadMembers() {
  const members = await api("/api/members");
  memberSelect.innerHTML =
    '<option value="">-- select member --</option>' +
    members.map((m) => `<option value="${m.id}">${esc(m.name)} (${esc(m.email)})</option>`).join("");
}

$("#book-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  try {
    await api("/api/books", "POST", data);
    e.target.reset();
    toast("Book added");
    loadBooks();
  } catch (err) {
    toast(err.message, "error");
  }
});

$("#member-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  try {
    await api("/api/members", "POST", data);
    e.target.reset();
    toast("Member added");
    loadMembers();
  } catch (err) {
    toast(err.message, "error");
  }
});

bookBody.addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  const id = btn.dataset.id;
  try {
    if (btn.dataset.act === "issue") {
      if (!memberSelect.value) return toast("Select a member first", "error");
      await api(`/api/books/${id}/issue`, "POST", { member_id: Number(memberSelect.value) });
      toast("Book issued");
    } else if (btn.dataset.act === "return") {
      await api(`/api/books/${id}/return`, "POST");
      toast("Book returned");
    } else if (btn.dataset.act === "delete") {
      if (!confirm("Delete this book?")) return;
      await api(`/api/books/${id}`, "DELETE");
      toast("Book deleted");
    }
    loadBooks();
  } catch (err) {
    toast(err.message, "error");
  }
});

$("#search-btn").addEventListener("click", () => {
  currentQuery = $("#search").value.trim();
  loadBooks();
});
$("#search").addEventListener("keydown", (e) => e.key === "Enter" && $("#search-btn").click());
$("#clear-btn").addEventListener("click", () => {
  $("#search").value = "";
  currentQuery = "";
  loadBooks();
});

loadBooks();
loadMembers();
