window.FL = window.FL || {};

FL.audit = {
  nextId: function () {
    return "AUD-" + Date.now();
  },

  record: function (user, action, ref, description) {
    const actor = user || (FL.apiClient && FL.apiClient.cachedUser()) || null;
    const name = actor && (actor.name || actor.email) ? (actor.name || actor.email) : "Administrator";
    const roleKey = actor && actor.role ? actor.role : "administrator";
    return FL.store.addAudit({
      id: this.nextId(),
      at: new Date().toISOString(),
      user: name,
      role: roleKey === "administrator" ? "Administrator" : "Reviewer",
      action: action,
      ref: ref,
      description: description
    });
  },

  render: function () {
    return `
      <div class="page-head">
        <div>
          <p class="eyebrow">Transparency and security</p>
          <h1>Audit Log</h1>
          <p class="lede">Actions recorded for FacultyLink document review, assignments, and account activity. Official committee records remain with the institution.</p>
        </div>
      </div>
      <div class="toolbar">
        <label class="search">
          <span class="sr-only">Search audit log</span>
          <input id="audit-search" type="search" placeholder="Search user, action, reference, or description">
        </label>
        <label class="filter">
          <span>Role</span>
          <select id="audit-role">
            <option value="">All roles</option>
            <option>Administrator</option>
            <option>Reviewer</option>
            <option>System</option>
            <option>Faculty</option>
          </select>
        </label>
      </div>
      <div class="card">
        <div class="table-wrap" id="audit-table"></div>
      </div>`;
  },

  rows: function () {
    const query = (document.getElementById("audit-search").value || "").trim().toLowerCase();
    const role = document.getElementById("audit-role").value;
    return FL.store.audit.filter(function (row) {
      if (role && row.role !== role) return false;
      if (!query) return true;
      return [row.user, row.role, row.action, row.ref, row.description].join(" ").toLowerCase().indexOf(query) !== -1;
    }).sort(function (a, b) { return a.at < b.at ? 1 : -1; });
  },

  draw: function () {
    const rows = this.rows();
    const host = document.getElementById("audit-table");
    if (!rows.length) {
      host.innerHTML = FL.ui.empty("No audit records", "No record matches this search.");
      return;
    }
    host.innerHTML = `
      <table class="data">
        <thead>
          <tr><th>Date</th><th>Time</th><th>User</th><th>Role</th><th>Action</th><th>Reference</th><th>Description</th></tr>
        </thead>
        <tbody>
          ${rows.map(function (row) {
            const parts = FL.splitWhen(row.at);
            return `<tr>
              <td>${FL.esc(parts.date)}</td>
              <td>${FL.esc(parts.time)}</td>
              <td>${FL.esc(row.user)}</td>
              <td>${FL.ui.badge(row.role === "Administrator" ? "info" : row.role === "System" ? "info" : "valid", row.role)}</td>
              <td>${FL.esc(row.action)}</td>
              <td>${FL.esc(row.ref || "—")}</td>
              <td>${FL.esc(row.description)}</td>
            </tr>`;
          }).join("")}
        </tbody>
      </table>`;
  },

  bind: function () {
    const draw = FL.audit.draw.bind(FL.audit);
    document.getElementById("audit-search").addEventListener("input", draw);
    document.getElementById("audit-role").addEventListener("change", draw);
    draw();
  }
};
