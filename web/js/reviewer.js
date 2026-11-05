window.FL = window.FL || {};

FL.reviewer = {
  renderDashboard: function (session) {
    const host = document.getElementById("page");
    if (FL.store.usesLiveReviewerApi() && FL.portal) {
      host.innerHTML = FL.ui.loading("Loading dashboard", "Fetching your assigned faculty and review queue…");
      FL.portal.loadReviewerDashboard().then(function (data) {
        FL.reviewer._paintLiveDashboard(session, data);
      }).catch(function (error) {
        host.innerHTML = FL.ui.emptyWithRetry(
          "Dashboard could not load",
          error.message || "Check that Flask is running and you are signed in as a reviewer.",
          "reviewer-dashboard-retry"
        );
        const btn = document.getElementById("reviewer-dashboard-retry");
        if (btn) btn.addEventListener("click", function () { FL.reviewer.renderDashboard(session); });
      });
      return;
    }
    FL.reviewer._paintLegacyDashboard(session);
  },

  _paintLiveDashboard: function (session, data) {
    const summary = data.summary || {};
    const queue = data.reviewQueue || [];
    const activity = data.recentReviewActivity || [];
    if (data.evaluationPeriods && data.evaluationPeriods.length) {
      FL.store.evaluationPeriods = data.evaluationPeriods;
    }
    const faculty = FL.store.assignedFacultyForReviewer(session);
    document.getElementById("page").innerHTML = `
      <div class="portal-page">
      ${FL.ui.pageHeader({
        eyebrow: "FacultyLink",
        title: "Reviewer Dashboard",
        lede: "Your assigned faculty, documents waiting for review, and recent decisions."
      })}
      ${FL.ui.metricGrid([
        { label: "Assigned faculty", value: summary.assignedFaculty, iconKey: "faculty", accent: "teal", href: "assigned-faculty.html" },
        { label: "Submitted documents", value: summary.submittedDocuments, iconKey: "documents", href: "documents.html" },
        { label: "Waiting for review", value: summary.waitingForReview, iconKey: "validation", accent: "warn", href: "documents.html?filter=pending-review" },
        { label: "Needs changes", value: summary.revisionsRequested, iconKey: "revision", accent: "warn", href: "documents.html?filter=revision" }
      ])}
      <article class="card">
        <div class="card-head"><h2>Documents needing review</h2><a href="documents.html?filter=pending-review">View all</a></div>
        ${queue.length ? `<div class="table-wrap"><table class="data portal-data-table"><thead><tr><th>Faculty</th><th>Document</th><th>KRA</th><th>Status</th><th>Date</th><th class="action-cell"></th></tr></thead><tbody>
          ${queue.map(function (doc) {
            return `<tr>
              <td>${FL.esc(doc.facultyName || "")}</td>
              <td>${FL.esc(doc.name || doc.title || doc.id)}</td>
              <td>${FL.esc(FL.documents.kraLabel(doc))}</td>
              <td>${FL.ui.statusBadge(doc.status)}</td>
              <td class="fl-table-datetime-cell">${FL.ui.tableDateTimeHtml(doc.submittedAt || doc.dateSubmitted)}</td>
              <td class="action-cell"><a class="btn btn-small btn-primary" href="${FL.esc(FL.portal.reviewHref(doc))}">Review</a></td>
            </tr>`;
          }).join("")}
        </tbody></table></div>` : FL.ui.empty("No documents need review right now", "New submissions from your assigned faculty will appear here.")}
      </article>
      <article class="card">
        <div class="card-head"><h2>Evaluation schedule</h2><a href="evaluation-schedule.html">Open schedule</a></div>
        ${(FL.store.evaluationPeriods || []).length ? `<div class="table-wrap"><table class="data"><thead><tr><th>Evaluation type</th><th>Start date</th><th>End date</th><th>Status</th></tr></thead><tbody>
          ${(FL.store.evaluationPeriods || []).map(function (period) {
            return `<tr><td>${FL.esc(period.label || FL.admin.scheduleLabel)}</td><td>${FL.esc(FL.formatWhen(period.startDate))}</td><td>${FL.esc(FL.formatWhen(period.endDate))}</td><td>${FL.ui.statusBadge(FL.admin.scheduleStatus(period))}</td></tr>`;
          }).join("")}
        </tbody></table></div>` : FL.ui.empty("No evaluation schedule published yet", "The administrator has not published the Rank Upgrade and Reclassification schedule yet.")}
      </article>
      <div class="split">
        <article class="card">
          <div class="card-head"><h2>Assigned faculty</h2><a href="assigned-faculty.html">Open list</a></div>
          <ul class="activity">${faculty.length ? faculty.map(function (person) {
            return `<li><a href="faculty-detail.html?id=${FL.esc(person.id)}"><strong>${FL.esc(person.name)}</strong></a><span>${FL.esc(person.rank || person.currentRank || "")}</span></li>`;
          }).join("") : `<li><span>No faculty assigned yet.</span></li>`}
          </ul>
        </article>
        <article class="card">
          <div class="card-head"><h2>Recent review activity</h2></div>
          ${activity.length ? `<ul class="activity">${activity.map(function (row) {
            return `<li><a href="${FL.esc(FL.portal.reviewHref({ id: row.documentId }))}"><strong>${FL.esc(row.title || row.documentId)}</strong></a><span>${FL.esc(FL.portal.statusLabel(row.status))} · ${FL.esc(row.facultyName || "")}</span></li>`;
          }).join("")}</ul>` : FL.ui.empty("No recent reviews", "Decisions you record will appear here.")}
        </article>
      </div>
      </div>`;
  },

  _paintLegacyDashboard: function (session) {
    const mine = FL.documents.scoped(session);
    const faculty = FL.store.assignedFacultyForReviewer(session);
    const queue = mine.filter(FL.documents.needsAction);
    const revision = mine.filter(function (doc) { return doc.status === "revision"; });
    FL.reviewer._paintLiveDashboard(session, {
      summary: {
        assignedFaculty: faculty.length,
        submittedDocuments: mine.length,
        waitingForReview: queue.length,
        revisionsRequested: revision.length
      },
      reviewQueue: queue,
      recentReviewActivity: mine.filter(function (doc) { return doc.feedback; }).slice(0, 4).map(function (doc) {
        return {
          documentId: doc.id,
          title: doc.name,
          facultyName: (FL.store.facultyById(doc.facultyId) || {}).name,
          status: doc.status
        };
      })
    });
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
    FL.notifications.bind(user, draw, session);
  };
  if (FL.portal && FL.store.usesLiveReviewerApi()) {
    document.getElementById("page").innerHTML = FL.ui.loading("Loading notifications", "Fetching your alerts…");
    FL.portal.loadNotifications(session).then(draw).catch(function (error) {
      document.getElementById("page").innerHTML = FL.ui.empty("Notifications unavailable", error.message || "");
    });
  } else {
    draw();
  }
};
