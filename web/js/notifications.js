window.FL = window.FL || {};

FL.notifications = {
  visible: function (user) {
    return FL.store.notifications.filter(function (item) {
      if (item.audience === "all") return true;
      if (item.audience === "administrator") return user.role === "administrator";
      if (item.audience === "reviewer") return user.role === "reviewer" && (!item.userId || item.userId === user.id);
      return false;
    }).sort(function (a, b) { return a.at < b.at ? 1 : -1; });
  },

  unreadCount: function (user) {
    return this.visible(user).filter(function (item) { return !item.read; }).length;
  },

  mark: function (id, read) {
    const item = FL.store.notifications.find(function (row) { return row.id === id; });
    if (!item) return Promise.resolve();
    item.read = read;
    return FL.api.send("PATCH", "/api/notifications/" + encodeURIComponent(id), { read: read });
  },

  markAll: function (user) {
    const ids = this.visible(user).filter(function (item) { return !item.read; }).map(function (item) { return item.id; });
    this.visible(user).forEach(function (item) { item.read = true; });
    return FL.api.send("PATCH", "/api/notifications", { ids: ids, read: true });
  },

  render: function (user) {
    const items = this.visible(user);
    const unread = items.filter(function (item) { return !item.read; }).length;
    return `
      <div class="page-head">
        <div>
          <p class="eyebrow">FacultyLink</p>
          <h1>Notifications</h1>
          <p class="lede">Document status, reviewer feedback, missing requirements, compliance verification, and system updates.</p>
        </div>
        <div class="head-actions">
          <button class="btn btn-ghost" type="button" id="mark-all" ${unread ? "" : "disabled"}>Mark all as read</button>
        </div>
      </div>
      <div class="card">
        ${items.length ? `<div class="notice-list" id="notice-list">${items.map(FL.notifications.itemHtml).join("")}</div>` : FL.ui.empty("No notifications", "Document status, feedback, and compliance notices will appear here.")}
      </div>`;
  },

  itemHtml: function (item) {
    return `
      <article class="notice ${item.read ? "" : "is-unread"}" data-id="${FL.esc(item.id)}">
        <div>
          <div class="notice-title">
            <h2>${FL.esc(item.title)}</h2>
            ${item.read ? '<span class="badge badge-info">Read</span>' : '<span class="badge badge-pending">Unread</span>'}
          </div>
          <p>${FL.esc(item.body)}</p>
          <p class="meta">${FL.esc(FL.formatWhen(item.at))}${item.ref ? " · " + FL.esc(item.ref) : ""}</p>
        </div>
        <button class="btn btn-ghost btn-small" type="button" data-read="${FL.esc(item.id)}">${item.read ? "Mark unread" : "Mark read"}</button>
      </article>`;
  },

  bind: function (user, rerender) {
    const root = document.getElementById("page");
    const markAll = document.getElementById("mark-all");
    if (markAll) {
      markAll.addEventListener("click", function () {
        FL.notifications.markAll(user).then(rerender).catch(function (error) {
          FL.ui.toast(error.message || "Notifications were not updated.", "danger");
        });
      });
    }
    root.querySelectorAll("[data-read]").forEach(function (button) {
      button.addEventListener("click", function () {
        const item = FL.store.notifications.find(function (row) { return row.id === button.getAttribute("data-read"); });
        if (!item) return;
        const next = !item.read;
        FL.notifications.mark(item.id, next).then(rerender).catch(function (error) {
          item.read = !next;
          FL.ui.toast(error.message || "That notification was not updated.", "danger");
        });
      });
    });
  }
};
