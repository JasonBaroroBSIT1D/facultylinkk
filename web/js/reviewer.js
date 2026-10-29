window.FL = window.FL || {};

FL.reviewer = {
  renderDashboard: function (session) {
    const mine = FL.documents.scoped(session);
    const faculty = FL.store.assignedFacultyForReviewer(session);
    const queue = mine.filter(FL.documents.needsAction);
    const revision = mine.filter(function (doc) { return doc.status === "revision"; });
    const feedback = mine.filter(function (doc) { return doc.feedback; }).slice(0, 4);
    document.getElementById("page").innerHTML = `
      <div class="portal-page">
      ${FL.ui.pageHeader({
        eyebrow: "FacultyLink",
        title: "Reviewer Dashboard",
        lede: "Assigned faculty, documents awaiting validation, and recorded feedback."
      })}
      ${FL.ui.metricGrid([
        { label: "Assigned faculty", value: faculty.length, iconKey: "faculty", accent: "teal" },
        { label: "Submitted documents", value: mine.length, iconKey: "documents" },
        { label: "Needs validation", value: queue.length, hint: "Open the review queue", iconKey: "validation", accent: "warn" },
        { label: "Revisions requested", value: revision.length, iconKey: "revision", accent: "warn" }
      ])}
      <article class="card">
        <div class="card-head"><h2>Documents requiring validation</h2><a href="documents.html?filter=pending-review">Pending review</a></div>
        ${queue.length ? `<div class="table-wrap"><table class="data"><thead><tr><th>Faculty</th><th>Document</th><th>KRA</th><th>Validation</th><th>Date</th><th></th></tr></thead><tbody>
          ${queue.map(function (doc) {
            const person = FL.store.facultyById(doc.facultyId);
            const result = FL.validation.evaluate(doc);
            return `<tr>
              <td>${FL.esc(person ? person.name : "")}</td>
              <td>${FL.esc(doc.name)}<div class="sub">${FL.esc(doc.id)}</div></td>
              <td>${FL.esc(FL.documents.kraLabel(doc))}</td>
              <td>${FL.ui.statusBadge(result.overall === "valid" ? "valid" : result.overall === "invalid" ? "invalid" : "reviewer-required")}</td>
              <td>${FL.esc(FL.formatWhen(doc.dateSubmitted))}</td>
              <td><a class="btn btn-small btn-primary" href="document-review.html?id=${FL.esc(doc.id)}">Open Review</a></td>
            </tr>`;
          }).join("")}
        </tbody></table></div>` : FL.ui.empty("Empty review queue", "No assigned document is waiting for validation.")}
      </article>
      <article class="card">
        <div class="card-head"><h2>Evaluation schedule</h2><a href="evaluation-schedule.html">Open schedule</a></div>
        ${(FL.store.evaluationPeriods || []).length ? `<div class="table-wrap"><table class="data"><thead><tr><th>Evaluation type</th><th>Start date</th><th>End date</th><th>Status</th></tr></thead><tbody>
          ${(FL.store.evaluationPeriods || []).map(function (period) {
            return `<tr><td>${FL.esc(period.label || FL.admin.scheduleLabel)}</td><td>${FL.esc(FL.formatWhen(period.startDate))}</td><td>${FL.esc(FL.formatWhen(period.endDate))}</td><td>${FL.ui.statusBadge(FL.admin.scheduleStatus(period))}</td></tr>`;
          }).join("")}
        </tbody></table></div>` : FL.ui.empty("No published schedule", "The administrator has not published the Rank Upgrade and Reclassification schedule yet.")}
      </article>
      <div class="split">
        <article class="card">
          <div class="card-head"><h2>Assigned faculty</h2><a href="assigned-faculty.html">Open list</a></div>
          <ul class="activity">${faculty.map(function (person) {
            const item = FL.compliance(person.id);
            return `<li><a href="faculty-detail.html?id=${FL.esc(person.id)}"><strong>${FL.esc(person.name)}</strong></a><span>${FL.esc(person.rank)} · ${FL.esc(item.status)}</span></li>`;
          }).join("")}</ul>
        </article>
        <article class="card">
          <div class="card-head"><h2>Reviewer feedback</h2></div>
          ${feedback.length ? `<ul class="activity">${feedback.map(function (doc) {
            return `<li><strong>${FL.esc(doc.id)}</strong><span>${FL.esc(doc.feedback)}</span></li>`;
          }).join("")}</ul>` : FL.ui.empty("No feedback yet", "Feedback you record on a document will appear here.")}
        </article>
      </div>
      </div>`;
  },

  renderProfile: function (session) {
    const user = FL.store.userById(session.userId);
    const assigned = FL.store.assignedFacultyForReviewer(session).length;
    document.getElementById("page").innerHTML = `
      <div class="portal-page">
      ${FL.ui.pageHeader({ eyebrow: "FacultyLink", title: "My Profile", lede: "Reviewer account for document validation and feedback." })}
      <article class="card profile-card">
        <div class="profile-banner"><span class="avatar large">${FL.esc(user.name.split(" ").map(function (part) { return part[0]; }).slice(0, 2).join(""))}</span><div><h2>${FL.esc(user.name)}</h2><p>${FL.esc(user.title)} · ${assigned} assigned faculty</p>${FL.ui.badge("info", "Reviewer")}</div></div>
        <form id="profile-form" class="form-grid">
          <label class="field"><span>Employee number</span><input value="${FL.esc(user.employeeNo)}" disabled></label>
          <label class="field"><span>Email</span><input value="${FL.esc(user.email)}" disabled></label>
          <label class="field"><span>Office</span><input id="profile-office" value="${FL.esc(user.office)}"></label>
          <label class="field"><span>Contact</span><input id="profile-contact" value="${FL.esc(user.contact)}"></label>
          <label class="field field-wide"><span>Specialization</span><input id="profile-spec" value="${FL.esc(user.specialization)}"></label>
          <div class="field-wide"><button class="btn btn-primary" type="submit">Save profile</button></div>
        </form>
      </article>
      </div>`;
    document.getElementById("profile-form").addEventListener("submit", function (event) {
      event.preventDefault();
      user.office = document.getElementById("profile-office").value.trim();
      user.contact = document.getElementById("profile-contact").value.trim();
      user.specialization = document.getElementById("profile-spec").value.trim();
      FL.store.saveProfile(user).then(function () {
        return FL.audit.record(user, "Updated profile", user.employeeNo, "Updated reviewer profile details.");
      }).then(function () {
        FL.ui.toast("Profile saved.", "ok");
      }).catch(function (error) {
        FL.ui.toast(error.message || "Profile was not saved.", "danger");
      });
    });
  }
};

FL.pages["reviewer-kra"] = function (session) { FL.admin.renderKra(session, { readonly: true }); };
FL.pages["reviewer-schedule"] = function (session) { FL.admin.renderSchedule(session, { readonly: true }); };
FL.pages["reviewer-dashboard"] = function (session) { FL.reviewer.renderDashboard(session); };
FL.pages["reviewer-profile"] = function (session) { FL.reviewer.renderProfile(session); };
FL.pages["reviewer-notifications"] = function (session) {
  const user = FL.store.userById(session.userId);
  const draw = function () {
    document.getElementById("page").innerHTML = FL.notifications.render(user);
    FL.notifications.bind(user, draw);
  };
  draw();
};
