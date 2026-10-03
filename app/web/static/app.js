"use strict";

const SOURCES = { telegram_bot: "🤖 Бот", telegram_account: "💬 Telegram", manual: "✍️ Вручную" };
const STATUSES = { new: "Новый", in_progress: "В работе", won: "Успех", lost: "Отказ" };
const REFRESH_MS = 10000;

const state = { leads: [], tags: [], filters: { tag_id: "", source: "", status: "", q: "" }, openLeadId: null };
const $ = (selector) => document.querySelector(selector);

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);

const formatDate = (iso) =>
  new Date(iso).toLocaleString("ru-RU", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

const options = (map, selected) =>
  Object.entries(map).map(([value, label]) => `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`).join("");

const chip = (tag, removable = false) =>
  `<span class="chip" style="background:${esc(tag.color)}">${esc(tag.name)}${
    removable ? ` <button data-remove-tag="${tag.id}" title="Убрать тег">✕</button>` : ""
  }</span>`;

function toast(message, isError = false) {
  const el = $("#toast");
  el.textContent = message;
  el.className = `toast show${isError ? " error" : ""}`;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.className = "toast"), 2500);
}

async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(`/api${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = Array.isArray(error.detail) ? error.detail.map((d) => d.msg).join("; ") : error.detail;
    throw new Error(detail || response.statusText);
  }
  return response.status === 204 ? null : response.json();
}

async function run(action, successMessage) {
  try {
    await action();
    if (successMessage) toast(successMessage);
  } catch (error) {
    toast(error.message, true);
  }
}

async function loadTags() {
  state.tags = await api("/tags");
  renderTagNav();
}

async function loadLeads() {
  const params = new URLSearchParams(Object.entries(state.filters).filter(([, value]) => value));
  state.leads = await api(`/leads?${params}`);
  renderLeads();
}

const refresh = () => Promise.all([loadTags(), loadLeads()]);

function renderTagNav() {
  const total = `<li data-tag="" class="${state.filters.tag_id ? "" : "active"}">Все лиды</li>`;
  const items = state.tags.map(
    (tag) => `<li data-tag="${tag.id}" class="${String(tag.id) === state.filters.tag_id ? "active" : ""}">
      <span class="dot" style="background:${esc(tag.color)}"></span>${esc(tag.name)}
      <span class="count">${tag.lead_count}</span>
      <button class="del" data-delete-tag="${tag.id}" title="Удалить тег">✕</button>
    </li>`
  );
  $("#tag-nav").innerHTML = total + items.join("");
  const active = state.tags.find((tag) => String(tag.id) === state.filters.tag_id);
  $("#list-title").textContent = active ? `Тег: ${active.name}` : "Все лиды";
}

function renderLeads() {
  $("#leads-body").innerHTML = state.leads
    .map(
      (lead) => `<tr data-lead="${lead.id}">
        <td><div class="lead-name">${esc(lead.name)}</div><div class="lead-contact">${esc(lead.contact)}</div></td>
        <td><div class="request">${esc(lead.request)}</div></td>
        <td><span class="badge">${SOURCES[lead.source]}</span></td>
        <td><span class="badge status-${lead.status}">${STATUSES[lead.status]}</span></td>
        <td>${lead.tags.map((tag) => chip(tag)).join("")}</td>
        <td class="muted">${formatDate(lead.created_at)}</td>
      </tr>`
    )
    .join("");
  $("#empty").hidden = state.leads.length > 0;
}

function renderDrawer(lead) {
  $("#drawer-title").textContent = `Лид #${lead.id}`;
  const freeTags = state.tags.filter((tag) => !lead.tags.some((own) => own.id === tag.id));
  const telegram = lead.telegram_username
    ? `<a class="badge" href="https://t.me/${esc(lead.telegram_username)}" target="_blank" rel="noopener">@${esc(lead.telegram_username)}</a>`
    : "";
  const messages = lead.messages.length
    ? `<div class="drawer-section"><h3>Сообщения из Telegram</h3><ul class="messages">${lead.messages
        .map((m) => `<li>${esc(m.text)}<time>${formatDate(m.created_at)}</time></li>`)
        .join("")}</ul></div>`
    : "";

  $("#drawer-body").innerHTML = `
    <div class="meta">
      <span class="badge">${SOURCES[lead.source]}</span>${telegram}
      <span class="badge">Создан ${formatDate(lead.created_at)}</span>
    </div>
    <form id="edit-form">
      <label>Имя<input name="name" value="${esc(lead.name)}" required maxlength="255"></label>
      <label>Контакт<input name="contact" value="${esc(lead.contact)}" maxlength="255"></label>
      <label>Запрос<textarea name="request" rows="4">${esc(lead.request)}</textarea></label>
      <label>Статус<select name="status">${options(STATUSES, lead.status)}</select></label>
      <button class="btn primary">Сохранить</button>
    </form>
    <div class="drawer-section">
      <h3>Теги</h3>
      <div id="lead-tags">${lead.tags.map((tag) => chip(tag, true)).join("") || '<span class="muted">Нет тегов</span>'}</div>
      ${
        freeTags.length
          ? `<div class="row" style="margin-top:8px">
               <select id="add-tag-select">${freeTags.map((t) => `<option value="${t.id}">${esc(t.name)}</option>`).join("")}</select>
               <button class="btn small" id="add-tag-btn">Добавить</button>
             </div>`
          : ""
      }
    </div>
    ${messages}
    <div class="drawer-section"><button class="btn danger" id="delete-lead-btn">Удалить лида</button></div>`;
}

async function openLead(leadId) {
  state.openLeadId = leadId;
  await run(async () => {
    renderDrawer(await api(`/leads/${leadId}`));
    $("#drawer").classList.add("open");
    $("#backdrop").classList.add("open");
  });
}

function closeDrawer() {
  state.openLeadId = null;
  $("#drawer").classList.remove("open");
  $("#backdrop").classList.remove("open");
}

async function mutateLead(request, message) {
  await run(async () => {
    await request();
    await refresh();
    await openLead(state.openLeadId);
  }, message);
}

$("#drawer-body").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  data.contact ||= null;
  data.request ||= null;
  mutateLead(() => api(`/leads/${state.openLeadId}`, { method: "PATCH", body: data }), "Сохранено");
});

$("#drawer-body").addEventListener("click", (event) => {
  const id = state.openLeadId;
  const removeTag = event.target.closest("[data-remove-tag]");
  if (removeTag) {
    mutateLead(() => api(`/leads/${id}/tags/${removeTag.dataset.removeTag}`, { method: "DELETE" }));
  } else if (event.target.id === "add-tag-btn") {
    mutateLead(() => api(`/leads/${id}/tags/${$("#add-tag-select").value}`, { method: "POST" }), "Тег добавлен");
  } else if (event.target.id === "delete-lead-btn" && confirm("Удалить лида без возможности восстановления?")) {
    run(async () => {
      await api(`/leads/${id}`, { method: "DELETE" });
      closeDrawer();
      await refresh();
    }, "Лид удалён");
  }
});

document.querySelectorAll("[data-close-drawer]").forEach((el) => el.addEventListener("click", closeDrawer));
document.addEventListener("keydown", (event) => event.key === "Escape" && closeDrawer());

$("#leads-body").addEventListener("click", (event) => {
  const row = event.target.closest("[data-lead]");
  if (row) openLead(Number(row.dataset.lead));
});

$("#tag-nav").addEventListener("click", (event) => {
  const del = event.target.closest("[data-delete-tag]");
  if (del) {
    event.stopPropagation();
    if (!confirm("Удалить тег? С лидов он тоже будет снят.")) return;
    if (del.dataset.deleteTag === state.filters.tag_id) state.filters.tag_id = "";
    run(async () => {
      await api(`/tags/${del.dataset.deleteTag}`, { method: "DELETE" });
      await refresh();
    }, "Тег удалён");
    return;
  }
  const item = event.target.closest("[data-tag]");
  if (item) {
    state.filters.tag_id = item.dataset.tag;
    run(refresh);
  }
});

$("#tag-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.target;
  run(async () => {
    await api("/tags", { method: "POST", body: Object.fromEntries(new FormData(form)) });
    form.reset();
    await loadTags();
  }, "Тег создан");
});

$("#source-filter").insertAdjacentHTML("beforeend", options(SOURCES));
$("#status-filter").insertAdjacentHTML("beforeend", options(STATUSES));
for (const [selector, key] of [["#source-filter", "source"], ["#status-filter", "status"]]) {
  $(selector).addEventListener("change", (event) => {
    state.filters[key] = event.target.value;
    run(loadLeads);
  });
}

let searchTimer;
$("#search").addEventListener("input", (event) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.filters.q = event.target.value.trim();
    run(loadLeads);
  }, 300);
});

const dialog = $("#lead-dialog");

$("#new-lead-btn").addEventListener("click", () => {
  $("#lead-form").reset();
  $("#lead-form-tags").innerHTML =
    state.tags.map((tag) => `<label><input type="checkbox" name="tag_ids" value="${tag.id}">${chip(tag)}</label>`).join("") ||
    '<span class="muted">Тегов пока нет — создайте их слева</span>';
  dialog.showModal();
});

dialog.querySelector("[data-close-dialog]").addEventListener("click", () => dialog.close());

$("#lead-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const body = {
    name: form.get("name"),
    contact: form.get("contact") || null,
    request: form.get("request") || null,
    tag_ids: form.getAll("tag_ids").map(Number),
  };
  run(async () => {
    await api("/leads", { method: "POST", body });
    dialog.close();
    await refresh();
  }, "Лид создан");
});

run(refresh);
setInterval(() => document.visibilityState === "visible" && run(refresh), REFRESH_MS);
