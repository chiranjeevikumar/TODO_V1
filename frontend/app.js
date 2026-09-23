/* ============================================================
   app.js  —  Todo Reminder frontend
   Talks to FastAPI backend at http://127.0.0.1:8000
   ============================================================ */

// When opened as a local file (file://), talk directly to the local uvicorn server.
// When deployed on Vercel (https://), use the relative /api path — no hardcoding needed.
const API = window.location.protocol === "file:"
  ? "http://127.0.0.1:8000"
  : "/api";

// ── State ────────────────────────────────────────────────────
let allTodos = [];
let activeFilter = "all";

// ── DOM refs ─────────────────────────────────────────────────
const form          = document.getElementById("todo-form");
const titleInput    = document.getElementById("title");
const descInput     = document.getElementById("description");
const dateInput     = document.getElementById("due_date");
const timeInput     = document.getElementById("reminder_time");
const listEl        = document.getElementById("todos-list");
const emptyState    = document.getElementById("empty-state");
const bell          = document.getElementById("reminder-bell");
const reminderCount = document.getElementById("reminder-count");
const modal         = document.getElementById("reminder-modal");
const closeModal    = document.getElementById("close-modal");
const reminderList  = document.getElementById("reminder-list");
const toast         = document.getElementById("toast");
const statTotal     = document.getElementById("stat-total");
const statPending   = document.getElementById("stat-pending");
const statCompleted = document.getElementById("stat-completed");


// ── Helpers ──────────────────────────────────────────────────

function showToast(msg, type = "success") {
  toast.textContent = msg;
  toast.className = `toast ${type}`;
  setTimeout(() => { toast.classList.add("hidden"); }, 3000);
}

function isToday(dateStr) {
  if (!dateStr) return false;
  return dateStr === new Date().toISOString().slice(0, 10);
}

function isOverdue(dateStr) {
  if (!dateStr) return false;
  return dateStr < new Date().toISOString().slice(0, 10);
}

function formatDate(dateStr) {
  if (!dateStr) return null;
  const [y, m, d] = dateStr.split("-");
  return `${d}/${m}/${y}`;
}


// ── API calls ─────────────────────────────────────────────────

async function fetchTodos() {
  try {
    const res = await fetch(`${API}/todos`);
    allTodos = await res.json();
    renderTodos();
    updateStats();
    checkReminders();
  } catch (e) {
    showToast("❌ Cannot reach API. Is the server running?", "error");
  }
}

async function createTodo(data) {
  const res = await fetch(`${API}/todos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function deleteTodo(id) {
  const res = await fetch(`${API}/todos/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

async function toggleComplete(id) {
  const res = await fetch(`${API}/todos/${id}/complete`, { method: "PATCH" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function fetchDueReminders() {
  const res = await fetch(`${API}/reminders/due`);
  return res.json();
}


// ── Render ────────────────────────────────────────────────────

function getFilteredTodos() {
  const today = new Date().toISOString().slice(0, 10);
  switch (activeFilter) {
    case "pending":   return allTodos.filter(t => !t.completed);
    case "completed": return allTodos.filter(t =>  t.completed);
    case "due":       return allTodos.filter(t => !t.completed && t.due_date && t.due_date <= today);
    default:          return allTodos;
  }
}

function renderTodos() {
  const todos = getFilteredTodos();

  // Clear existing todo cards (keep empty-state div)
  const existing = listEl.querySelectorAll(".todo-item");
  existing.forEach(el => el.remove());

  if (todos.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");

  todos.forEach(todo => {
    const card = buildTodoCard(todo);
    listEl.appendChild(card);
  });
}

function buildTodoCard(todo) {
  const today = new Date().toISOString().slice(0, 10);
  const over   = !todo.completed && todo.due_date && todo.due_date < today;
  const dueNow = !todo.completed && todo.due_date && todo.due_date === today;

  const item = document.createElement("div");
  item.className = [
    "todo-item",
    todo.completed ? "completed" : "",
    over   ? "overdue"   : "",
    dueNow ? "due-today" : "",
  ].filter(Boolean).join(" ");
  item.dataset.id = todo.id;

  // Checkbox circle
  const check = document.createElement("button");
  check.className = "todo-check";
  check.title = todo.completed ? "Mark as pending" : "Mark as done";
  check.textContent = todo.completed ? "✓" : "";
  check.addEventListener("click", () => handleToggle(todo.id));

  // Content
  const content = document.createElement("div");
  content.className = "todo-content";

  const titleEl = document.createElement("div");
  titleEl.className = "todo-title";
  titleEl.textContent = todo.title;

  content.appendChild(titleEl);

  if (todo.description) {
    const descEl = document.createElement("div");
    descEl.className = "todo-desc";
    descEl.textContent = todo.description;
    content.appendChild(descEl);
  }

  // Badges
  const meta = document.createElement("div");
  meta.className = "todo-meta";

  if (todo.due_date) {
    const badgeClass = over ? "badge-overdue" : (dueNow ? "badge-due" : "badge-date");
    const label = over ? `⚠ Overdue: ${formatDate(todo.due_date)}` : (dueNow ? `🔥 Today: ${formatDate(todo.due_date)}` : `📅 ${formatDate(todo.due_date)}`);
    meta.insertAdjacentHTML("beforeend", `<span class="badge ${badgeClass}">${label}</span>`);
  }
  if (todo.reminder_time) {
    meta.insertAdjacentHTML("beforeend", `<span class="badge badge-time">⏰ ${todo.reminder_time}</span>`);
  }
  if (todo.completed) {
    meta.insertAdjacentHTML("beforeend", `<span class="badge badge-done">✔ Done</span>`);
  }

  content.appendChild(meta);

  // Action buttons
  const actions = document.createElement("div");
  actions.className = "todo-actions";

  const delBtn = document.createElement("button");
  delBtn.className = "btn btn-icon danger";
  delBtn.title = "Delete task";
  delBtn.textContent = "🗑";
  delBtn.addEventListener("click", () => handleDelete(todo.id));

  actions.appendChild(delBtn);

  item.append(check, content, actions);
  return item;
}

function updateStats() {
  const total     = allTodos.length;
  const completed = allTodos.filter(t => t.completed).length;
  const pending   = total - completed;
  statTotal.textContent     = total;
  statPending.textContent   = pending;
  statCompleted.textContent = completed;
}


// ── Reminders ─────────────────────────────────────────────────

async function checkReminders() {
  try {
    const due = await fetchDueReminders();
    if (due.length > 0) {
      bell.classList.remove("hidden");
      reminderCount.textContent = due.length;

      // Populate modal list
      reminderList.innerHTML = "";
      due.forEach(t => {
        const li = document.createElement("li");
        li.innerHTML = `<span>🔔</span> <strong>${t.title}</strong> — due ${formatDate(t.due_date) ?? "today"}`;
        reminderList.appendChild(li);
      });
    } else {
      bell.classList.add("hidden");
    }
  } catch (e) {
    // Silently ignore reminder errors
  }
}


// ── Event handlers ────────────────────────────────────────────

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const addBtn = document.getElementById("add-btn");
  addBtn.disabled = true;
  addBtn.textContent = "Adding…";

  const data = {
    title:         titleInput.value.trim(),
    description:   descInput.value.trim()   || null,
    due_date:      dateInput.value           || null,
    reminder_time: timeInput.value           || null,
  };

  try {
    await createTodo(data);
    form.reset();
    showToast("✅ Task added!");
    await fetchTodos();
  } catch (err) {
    showToast("❌ Failed to add task.", "error");
  } finally {
    addBtn.disabled = false;
    addBtn.innerHTML = "<span>＋</span> Add Task";
  }
});

async function handleDelete(id) {
  if (!confirm("Delete this task?")) return;
  try {
    await deleteTodo(id);
    showToast("🗑 Task deleted.");
    await fetchTodos();
  } catch {
    showToast("❌ Failed to delete.", "error");
  }
}

async function handleToggle(id) {
  try {
    await toggleComplete(id);
    await fetchTodos();
  } catch {
    showToast("❌ Failed to update.", "error");
  }
}

// Filter tabs
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    activeFilter = tab.dataset.filter;
    renderTodos();
  });
});

// Reminder bell → open modal
bell.addEventListener("click", () => modal.classList.remove("hidden"));
closeModal.addEventListener("click", () => modal.classList.add("hidden"));
modal.addEventListener("click", (e) => {
  if (e.target === modal) modal.classList.add("hidden");
});


// ── Boot ──────────────────────────────────────────────────────

fetchTodos();

// Poll for due reminders every 60 seconds
setInterval(checkReminders, 60_000);
