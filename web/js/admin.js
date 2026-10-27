window.FL = window.FL || {};

FL.admin = {
  validationCounts: function () {
    const counts = { valid: 0, invalid: 0, "reviewer-required": 0 };
    FL.store.documents.forEach(function (doc) {
      const overall = FL.validation.evaluate(doc).overall;
      counts[overall] = (counts[overall] || 0) + 1;
    });
    return counts;
  },

  renderDashboard: function () {
    const faculty = FL.store.faculty;
    const docs = FL.store.documents;
    const pending = docs.filter(function (doc) { return doc.status === "pending-review" || doc.status === "reviewer-required" || doc.status === "invalid"; }).length;
    const approved = docs.filter(function (doc) { return doc.status === "approved"; }).length;
    const attention = faculty.filter(function (person) { return FL.compliance(person.id).status !== "On track"; }).length;
    const counts = FL.admin.validationCounts();
    const kraBars = FL.rules.kras.map(function (kra) {
      const total = faculty.reduce(function (sum, person) {
        const row = FL.scoring.simulation(person.id).aggregate.kras.find(function (item) { return item.id === kra.id; });
        return sum + (row ? row.earned : 0);
      }, 0);
      const average = faculty.length ? FL.scoring.round(total / faculty.length) : 0;
      return { label: kra.code, average: average, max: kra.maxPoints };
    });
    const maxAverage = Math.max.apply(null, kraBars.map(function (bar) { return bar.max; }));
    document.getElementById("page").innerHTML = `
      <div class="page-head">
        <div>
          <p class="eyebrow">${FL.esc(FL.institution.name)}</p>
          <h1>Administrator Dashboard</h1>
          <p class="lede">Faculty readiness, document validation, KRA estimates, reviewer activity, and compliance under DBM–CHED Joint Circular No. 01, s. 2026.</p>
        </div>
      </div>
      <div class="stat-grid">
        <article class="stat"><span>Faculty</span><strong>${faculty.length}</strong><small>${attention} need attention</small></article>
        <article class="stat"><span>Documents</span><strong>${docs.length}</strong><small>${approved} approved</small></article>
        <article class="stat"><span>Awaiting validation</span><strong>${pending}</strong><small>Invalid, unclassified, or in queue</small></article>
        <article class="stat"><span>Valid documents</span><strong>${counts.valid}</strong><small>${counts.invalid} invalid · ${counts["reviewer-required"]} for reviewer</small></article>
      </div>
      <div class="split">
        <article class="card">
          <div class="card-head"><h2>KRA estimates</h2></div>
          <div class="bars">${kraBars.map(function (bar) {
            const width = Math.round((bar.average / maxAverage) * 100);
            return `<div class="bar-row"><span>${FL.esc(bar.label)}</span><div class="track"><span style="width:${width}%"></span></div><strong>${bar.average}</strong></div>`;
          }).join("")}</div>
          <p class="note">Average approved points per faculty. Each KRA maximum is 100, before any bonus points stated in the circular.</p>
        </article>
        <article class="card">
          <div class="card-head"><h2>Validation</h2></div>
          <div class="bars">
            <div class="bar-row"><span>Valid</span><div class="track"><span class="ok" style="width:${docs.length ? (counts.valid / docs.length) * 100 : 0}%"></span></div><strong>${counts.valid}</strong></div>
            <div class="bar-row"><span>Reviewer</span><div class="track"><span class="warn" style="width:${docs.length ? (counts["reviewer-required"] / docs.length) * 100 : 0}%"></span></div><strong>${counts["reviewer-required"]}</strong></div>
            <div class="bar-row"><span>Invalid</span><div class="track"><span class="bad" style="width:${docs.length ? (counts.invalid / docs.length) * 100 : 0}%"></span></div><strong>${counts.invalid}</strong></div>
          </div>
        </article>
      </div>
      <article class="card">
        <div class="card-head"><h2>Compliance monitoring</h2><a href="reports.html">Open reports</a></div>
        <div class="table-wrap"><table class="data">
          <thead><tr><th>Faculty</th><th>Rank</th><th>Submitted</th><th>Validated</th><th>Missing or held</th><th>Revision</th><th>KRA progress</th><th>Status</th></tr></thead>
          <tbody>${faculty.map(function (person) {
            const item = FL.compliance(person.id);
            const sim = FL.scoring.simulation(person.id);
            return `<tr>
              <td><a href="faculty-detail.html?id=${FL.esc(person.id)}">${FL.esc(person.name)}</a></td>
              <td>${FL.esc(person.rank)}</td>
              <td>${item.submitted}</td>
              <td>${item.validated}</td>
              <td>${item.missing}</td>
              <td>${item.revision}</td>
              <td class="progress-cell">${FL.ui.progress(sim.aggregate.kras.filter(function (kra) { return kra.earned > 0; }).length, 4, "")}</td>
              <td>${FL.ui.statusBadge(item.status)}</td>
            </tr>`;
          }).join("")}</tbody>
        </table></div>
      </article>
      <div class="split">
        <article class="card">
          <div class="card-head"><h2>Recent documents</h2><a href="documents.html">All documents</a></div>
          <div class="table-wrap"><table class="data">
            <thead><tr><th>Document</th><th>Faculty</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>${docs.slice().sort(function (a, b) { return a.dateSubmitted < b.dateSubmitted ? 1 : -1; }).slice(0, 6).map(function (doc) {
              const person = FL.store.facultyById(doc.facultyId);
              return `<tr><td><a href="document-view.html?id=${FL.esc(doc.id)}">${FL.esc(doc.id)}</a><div class="sub">${FL.esc(doc.name)}</div></td><td>${FL.esc(person ? person.name : "")}</td><td>${FL.ui.statusBadge(doc.status)}</td><td>${FL.esc(FL.formatWhen(doc.dateSubmitted))}</td></tr>`;
            }).join("")}</tbody>
          </table></div>
        </article>
        <article class="card">
          <div class="card-head"><h2>Reviewer activity</h2><a href="reviewers.html">Manage reviewers</a></div>
          <ul class="activity">${FL.store.users.filter(function (user) { return user.role === "reviewer"; }).map(function (reviewer) {
            const assigned = FL.store.faculty.filter(function (person) { return person.reviewerId === reviewer.id; }).length;
            const open = FL.store.documents.filter(function (doc) { return doc.reviewerId === reviewer.id && FL.documents.needsAction(doc); }).length;
            return `<li><strong>${FL.esc(reviewer.name)}</strong><span>${assigned} faculty · ${open} documents needing action</span></li>`;
          }).join("")}</ul>
        </article>
      </div>`;
  },

  refreshReviewerDirectory: function (draw) {
    if (FL.store.usesRealAdminApi()) {
      return FL.store.loadAdminReviewers().then(function () {
        FL.store.adminDirectoryLoaded = true;
        draw();
      }).catch(function (error) {
        FL.ui.toast(error.message || "Could not refresh the reviewer list.", "danger");
        throw error;
      });
    }
    draw();
    return Promise.resolve();
  },

  showReviewerDirectoryError: function (host, error, retryFn) {
    const retryId = "reviewer-retry-load";
    host.innerHTML = FL.ui.emptyWithRetry(
      "Could not load reviewers",
      (error && error.message) || "Start the Flask API on port 5000, then retry.",
      retryId
    );
    const btn = document.getElementById(retryId);
    if (btn) btn.addEventListener("click", retryFn);
  },

  renderReviewers: function (session) {
    const page = document.getElementById("page");
    const loadFromApi = function () {
      const host = document.getElementById("reviewer-table");
      host.innerHTML = FL.ui.loading("Loading reviewers", "Fetching accounts from PostgreSQL.");
      return FL.store.loadAdminReviewers().then(function () {
        return FL.store.loadAdminFaculty();
      }).then(function () {
        FL.store.adminDirectoryLoaded = true;
        draw();
      }).catch(function (error) {
        FL.admin.showReviewerDirectoryError(host, error, loadFromApi);
      });
    };
    const draw = function () {
      if (FL.store.usesRealAdminApi() && !FL.store.adminDirectoryLoaded) return;
      const query = (document.getElementById("reviewer-search").value || "").trim().toLowerCase();
      const live = FL.store.isLiveAccountManagement();
      const pool = live
        ? FL.store.serverReviewers.slice()
        : FL.store.users.filter(function (user) { return user.role === "reviewer"; });
      const reviewers = pool.filter(function (user) {
        if (!query) return true;
        const facultyNames = FL.store.faculty.filter(function (person) { return person.reviewerId === user.id; }).map(function (person) { return person.name || ""; }).join(" ");
        return (user.name + " " + (user.department || user.office || "") + " " + facultyNames).toLowerCase().indexOf(query) !== -1;
      });
      const host = document.getElementById("reviewer-table");
      if (!reviewers.length) {
        host.innerHTML = FL.ui.empty("No reviewers", "Add a reviewer to begin assigning faculty.");
        return;
      }
      host.innerHTML = `<table class="data"><thead><tr><th>Reviewer</th><th>Assigned faculty</th><th>Assigned documents</th><th>Review status</th><th></th></tr></thead><tbody>
        ${reviewers.map(function (reviewer) {
          let facultyCount;
          let documentCount;
          let statusCell;
          if (live) {
            facultyCount = reviewer.assignedFacultyCount != null ? reviewer.assignedFacultyCount : "—";
            documentCount = reviewer.assignedDocumentCount != null ? reviewer.assignedDocumentCount : "—";
            const status = reviewer.reviewStatus || "Not available";
            if (status === "No assignments" || status === "Not available") {
              statusCell = FL.ui.badge("info", status);
            } else if (String(status).indexOf("open") !== -1) {
              statusCell = FL.ui.badge("pending", status);
            } else {
              statusCell = FL.ui.badge("valid", status);
            }
          } else {
            const people = FL.store.faculty.filter(function (person) { return person.reviewerId === reviewer.id; });
            const documents = FL.store.documents.filter(function (doc) { return doc.reviewerId === reviewer.id; });
            const open = documents.filter(FL.documents.needsAction).length;
            facultyCount = people.length;
            documentCount = documents.length;
            statusCell = open ? FL.ui.badge("pending", open + " open") : FL.ui.badge("valid", "No open items");
          }
          return `<tr>
            <td><strong>${FL.esc(reviewer.name || reviewer.email || "Reviewer")}</strong><div class="sub">${FL.esc(reviewer.email || reviewer.department || reviewer.office || "")}</div></td>
            <td>${FL.esc(String(facultyCount))}</td>
            <td>${FL.esc(String(documentCount))}</td>
            <td>${statusCell}</td>
            <td class="action-cell">
              <button class="btn btn-small btn-ghost" type="button" data-view="${FL.esc(reviewer.id)}">View assigned work</button>
              <button class="btn btn-small btn-primary" type="button" data-assign="${FL.esc(reviewer.id)}">Assign / Reassign</button>
              <button class="btn btn-small btn-ghost" type="button" data-reissue="${FL.esc(reviewer.id)}">Resend credentials</button>
              <button class="btn btn-small btn-ghost" type="button" data-remove-reviewer="${FL.esc(reviewer.id)}">${reviewer.isActive === false ? "Reactivate" : "Remove"}</button>
            </td>
          </tr>`;
        }).join("")}
      </tbody></table>`;
      host.querySelectorAll("[data-view]").forEach(function (button) {
        button.addEventListener("click", function () { FL.admin.viewWork(button.getAttribute("data-view")); });
      });
      host.querySelectorAll("[data-assign]").forEach(function (button) {
        button.addEventListener("click", function () { FL.admin.assign(session, button.getAttribute("data-assign"), draw); });
      });
      host.querySelectorAll("[data-reissue]").forEach(function (button) {
        button.addEventListener("click", function () {
          const reviewer = FL.store.reviewerById(button.getAttribute("data-reissue"));
          if (reviewer) FL.admin.reissueCredentials(reviewer, draw);
        });
      });
      host.querySelectorAll("[data-remove-reviewer]").forEach(function (button) {
        button.addEventListener("click", function () { FL.admin.removeReviewer(session, button.getAttribute("data-remove-reviewer"), draw); });
      });
    };
    page.innerHTML = `
      <div class="page-head">
        <div>
          <p class="eyebrow">Assignments</p>
          <h1>Reviewers</h1>
          <p class="lede">Add or remove institutional reviewers, then assign or reassign faculty. Open items stay with the reviewer until a decision is recorded.</p>
        </div>
        <button class="btn btn-primary" type="button" id="reviewer-add">Add reviewer</button>
      </div>
      <div class="toolbar"><label class="search"><span class="sr-only">Search reviewers</span><input id="reviewer-search" type="search" placeholder="Search reviewers or assigned faculty"></label></div>
      <div class="card"><div class="table-wrap" id="reviewer-table">${FL.ui.loading("Loading reviewers", FL.store.usesRealAdminApi() ? "Fetching accounts from PostgreSQL." : "Preparing this view.")}</div></div>`;
    document.getElementById("reviewer-search").addEventListener("input", draw);
    document.getElementById("reviewer-add").addEventListener("click", function () {
      FL.admin.addReviewer(session, function () {
        return FL.admin.refreshReviewerDirectory(draw);
      });
    });
    if (FL.store.usesRealAdminApi()) {
      loadFromApi();
    } else {
      document.getElementById("reviewer-table").innerHTML = FL.ui.empty(
        "Sign in required",
        "Sign in as an administrator with the Flask API to load PostgreSQL reviewer accounts."
      );
    }
  },

  viewFaculty: function (facultyId) {
    if (!FL.store.isLiveAccountManagement()) {
      window.location.href = FL.faculty.detailHref(facultyId);
      return;
    }
    FL.ui.modal({
      title: "Faculty profile",
      body: FL.ui.loading("Loading faculty", "Fetching account details from PostgreSQL."),
      cancelLabel: "Close"
    });
    FL.store.fetchAdminFacultyDetail(facultyId).then(function (data) {
      const person = data.faculty || {};
      const modal = document.querySelector("#modal-root .modal-body");
      if (!modal) return;
      const docs = person.documentSummary || {};
      const kraBlock = (person.kraScores && person.kraScores.length)
        ? `<h3 class="block-label">KRA scores (PostgreSQL)</h3><ul class="plain">${person.kraScores.map(function (row) {
          return `<li>${FL.esc(row.kraKey)} — estimated ${FL.esc(String(row.estimatedPoints))}, verified ${FL.esc(String(row.verifiedPoints))}${row.statusLabel ? " (" + FL.esc(row.statusLabel) + ")" : ""}</li>`;
        }).join("")}</ul>`
        : "<p class=\"note\">No KRA score rows are stored in PostgreSQL for this faculty member yet.</p>";
      const docList = (person.documents && person.documents.length)
        ? `<ul class="plain">${person.documents.map(function (doc) {
          return `<li>${FL.esc(doc.title || doc.id)} — ${FL.esc(doc.status || "—")}</li>`;
        }).join("")}</ul>${person.documentsNote ? "<p class=\"note\">" + FL.esc(person.documentsNote) + "</p>" : ""}`
        : "<p class=\"note\">No documents are stored in PostgreSQL for this faculty member yet.</p>";
      modal.innerHTML = `
        <dl class="facts">
          <div><dt>Full name</dt><dd>${FL.esc(person.name || "—")}</dd></div>
          <div><dt>Email</dt><dd>${FL.esc(person.email || "—")}</dd></div>
          <div><dt>Current rank</dt><dd>${FL.esc((person.rank || "").trim() || "Not provided")}</dd></div>
          <div><dt>Department</dt><dd>${FL.esc((person.department || "").trim() || "Not provided")}</dd></div>
          <div><dt>Account status</dt><dd>${FL.esc(person.accountStatus || (person.isActive === false ? "Inactive" : "Active"))}</dd></div>
          <div><dt>Password setup</dt><dd>${FL.esc(person.passwordSetupStatus || (person.mustChangePassword ? "Must change temporary password" : "Password updated"))}</dd></div>
          <div><dt>Assigned reviewer</dt><dd>${FL.esc(person.reviewerName || "Unassigned")}</dd></div>
          <div><dt>Account created</dt><dd>${FL.esc(person.createdAt ? FL.formatWhen(person.createdAt) : "—")}</dd></div>
        </dl>
        <h3 class="block-label">Documents</h3>
        <p>Total ${FL.esc(String(docs.total != null ? docs.total : 0))} · Pending review ${FL.esc(String(docs.pendingReview != null ? docs.pendingReview : 0))} · Completed ${FL.esc(String(docs.completed != null ? docs.completed : 0))}</p>
        ${docList}
        ${kraBlock}`;
    }).catch(function (error) {
      const modal = document.querySelector("#modal-root .modal-body");
      if (modal) {
        modal.innerHTML = FL.ui.empty("Could not load faculty", error.message || "Try again later.");
      }
    });
  },

  viewWork: function (reviewerId) {
    const reviewer = FL.store.reviewerById(reviewerId);
    if (!reviewer) {
      FL.ui.toast("Reviewer was not found.", "danger");
      return;
    }
    if (!FL.store.isLiveAccountManagement()) {
      const people = FL.store.faculty.filter(function (person) { return person.reviewerId === reviewerId; });
      const body = people.length ? `<ul class="plain">${people.map(function (person) {
        const docs = FL.store.documents.filter(function (doc) { return doc.facultyId === person.id; });
        return `<li><a href="faculty-detail.html?id=${FL.esc(person.id)}">${FL.esc(person.name)}</a> — ${docs.length} documents</li>`;
      }).join("")}</ul>` : "<p>No faculty are assigned.</p>";
      FL.ui.modal({ title: reviewer.name || "Reviewer", body: body, cancelLabel: "Close" });
      return;
    }
    FL.ui.modal({
      title: reviewer.name || "Assigned work",
      body: FL.ui.loading("Loading assignments", "Fetching reviewer workload from PostgreSQL."),
      cancelLabel: "Close"
    });
    FL.store.fetchReviewerWork(reviewerId).then(function (data) {
      const modal = document.querySelector("#modal-root .modal-body");
      if (!modal) return;
      const faculty = data.faculty || [];
      const documents = data.documents || {};
      if (!faculty.length) {
        modal.innerHTML = "<p>No faculty members have been assigned to this reviewer yet.</p>";
        return;
      }
      const facultyList = `<h3 class="block-label">Assigned faculty</h3><ul class="plain">${faculty.map(function (person) {
        return `<li><strong>${FL.esc(person.name)}</strong> — ${FL.esc(person.department || person.rank || person.email || "")}</li>`;
      }).join("")}</ul>`;
      const pending = documents.pending || [];
      const completed = documents.completed || [];
      const docSection = documents.available
        ? `<h3 class="block-label">Documents</h3>
           <p>Pending review: ${pending.length} · Completed: ${completed.length}${documents.totalListed ? " (showing up to " + documents.totalListed + ")" : ""}</p>
           ${pending.length ? "<p><strong>Pending</strong></p><ul class=\"plain\">" + pending.map(function (doc) {
          return `<li>${FL.esc(doc.title)} — ${FL.esc(doc.facultyName || "")} (${FL.esc(doc.status)})</li>`;
        }).join("") + "</ul>" : ""}
           ${completed.length ? "<p><strong>Completed</strong></p><ul class=\"plain\">" + completed.map(function (doc) {
          return `<li>${FL.esc(doc.title)} — ${FL.esc(doc.facultyName || "")} (${FL.esc(doc.status)})</li>`;
        }).join("") + "</ul>" : ""}`
        : `<p class="note">${FL.esc(documents.note || "Document review data is not available in PostgreSQL yet.")}</p>`;
      modal.innerHTML = facultyList + docSection;
    }).catch(function (error) {
      const modal = document.querySelector("#modal-root .modal-body");
      if (modal) modal.innerHTML = FL.ui.empty("Could not load assigned work", error.message || "Try again later.");
    });
  },

  addReviewer: function (session, redraw) {
    FL.ui.modal({
      title: "Add reviewer",
      confirmLabel: "Create reviewer",
      body: `
        <label class="field"><span>Full name</span><input id="reviewer-full-name" type="text" required></label>
        <label class="field"><span>Email</span><input id="reviewer-email" type="email" required></label>
        <label class="field"><span>Office / department</span><input id="reviewer-department" type="text" value="Institutional Review"></label>
        <p class="note">FacultyLink emails a temporary password. The reviewer must change it on first sign-in.</p>`,
      onConfirm: function (modalRoot, confirmBtn) {
        const payload = {
          fullName: document.getElementById("reviewer-full-name").value.trim(),
          email: document.getElementById("reviewer-email").value.trim(),
          department: document.getElementById("reviewer-department").value.trim() || "Institutional Review"
        };
        if (!payload.fullName || !payload.email) {
          FL.ui.toast("Enter the reviewer’s name and email.", "danger");
          return false;
        }
        FL.ui.setModalConfirmBusy(
          confirmBtn,
          true,
          '<span class="spinner" aria-hidden="true"></span> Creating Reviewer...',
          "Create reviewer",
          modalRoot
        );
        return FL.store.createReviewer(payload).then(function (data) {
          const admin = FL.store.userById(session.userId);
          return FL.audit.record(
            admin,
            "Added reviewer",
            data.reviewer && data.reviewer.id,
            "Created " + payload.fullName + "."
          ).then(function () { return data; });
        }).then(function (data) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Create reviewer", modalRoot);
          let message = "Reviewer account created successfully.";
          if (data.emailSent) {
            message += " Temporary credentials were emailed to " + payload.email + ".";
            FL.ui.toast(message, "ok");
          } else {
            message += " The account was saved, but the credential email was not sent. Use Resend credentials from the reviewer row.";
            FL.ui.toast(data.emailError ? message + " (" + data.emailError + ")" : message, "danger");
          }
          return redraw().then(function () { return true; });
        }).catch(function (error) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Create reviewer", modalRoot);
          FL.ui.toast(error.message || "Reviewer was not created.", "danger");
          return false;
        });
      }
    });
  },

  reissueCredentials: function (reviewer, redraw) {
    FL.ui.modal({
      title: "Resend credentials",
      confirmLabel: "Send new temporary password",
      body: `<p>FacultyLink will generate a new temporary password and email it to ${FL.esc(reviewer.email)}.</p>
        <p>The previous temporary password and active sessions for this account will stop working immediately.</p>`,
      onConfirm: function (modalRoot, confirmBtn) {
        FL.ui.setModalConfirmBusy(confirmBtn, true, '<span class="spinner" aria-hidden="true"></span> Sending…', "Send new temporary password", modalRoot);
        return FL.store.reissueReviewerCredentials(reviewer.id).then(function (data) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Send new temporary password", modalRoot);
          if (data && data.emailSent) {
            FL.ui.toast("Temporary credentials were emailed to " + reviewer.email + ".", "ok");
          } else {
            FL.ui.toast((data && data.emailError) || "Credential email was not sent.", "danger");
          }
          return redraw();
        }).catch(function (error) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Send new temporary password", modalRoot);
          FL.ui.toast(error.message || "Credential email was not sent.", "danger");
          return false;
        });
      }
    });
  },

  removeReviewer: function (session, reviewerId, redraw) {
    const reviewer = FL.store.reviewerById(reviewerId);
    if (!reviewer) return;
    const live = FL.store.isLiveAccountManagement();
    if (live && reviewer.isActive === false) {
      FL.ui.modal({
        title: "Reactivate reviewer account",
        confirmLabel: "Reactivate account",
        body: `<p>Restore sign-in access for <strong>${FL.esc(reviewer.name)}</strong> (${FL.esc(reviewer.email)})?</p>`,
        onConfirm: function (modalRoot, confirmBtn) {
          FL.ui.setModalConfirmBusy(confirmBtn, true, '<span class="spinner" aria-hidden="true"></span> Reactivating…', "Reactivate account", modalRoot);
          return FL.store.reactivateAccount(reviewerId).then(function () {
            FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Reactivate account", modalRoot);
            FL.ui.toast(reviewer.name + " was reactivated.", "ok");
            return redraw();
          }).catch(function (error) {
            FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Reactivate account", modalRoot);
            FL.ui.toast(error.message || "Account was not reactivated.", "danger");
            return false;
          });
        }
      });
      return;
    }
    const assigned = FL.store.faculty.filter(function (person) { return person.reviewerId === reviewerId; }).length;
    FL.ui.modal({
      title: live ? "Deactivate reviewer account" : "Remove reviewer",
      danger: true,
      confirmLabel: live ? "Deactivate account" : "Remove reviewer",
      body: live
        ? `<p>Deactivate <strong>${FL.esc(reviewer.name)}</strong> (${FL.esc(reviewer.email)})?</p>
           <p>${assigned ? assigned + " faculty member(s) are still assigned. Reassign them before deactivation." : "No faculty are currently assigned."}</p>
           <p>Previous review decisions and audit history are preserved.</p>`
        : `<p>Remove <strong>${FL.esc(reviewer.name)}</strong>? ${assigned ? assigned + " faculty assignment(s) will be cleared." : "No faculty are currently assigned."}</p>`,
      onConfirm: function (modalRoot, confirmBtn) {
        FL.ui.setModalConfirmBusy(confirmBtn, true, '<span class="spinner" aria-hidden="true"></span> Processing…', live ? "Deactivate account" : "Remove reviewer", modalRoot);
        return FL.store.removeReviewer(reviewerId).then(function () {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", live ? "Deactivate account" : "Remove reviewer", modalRoot);
          FL.ui.toast(live ? reviewer.name + " was deactivated." : reviewer.name + " was removed.", "ok");
          return redraw();
        }).catch(function (error) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", live ? "Deactivate account" : "Remove reviewer", modalRoot);
          FL.ui.toast(error.message || (live ? "Account was not deactivated." : "Reviewer was not removed."), "danger");
          return false;
        });
      }
    });
  },

  assign: function (session, reviewerId, redraw) {
    const reviewer = FL.store.reviewerById(reviewerId);
    if (!reviewer) {
      FL.ui.toast("Reviewer was not found.", "danger");
      return;
    }
    const openAssignModal = function () {
      const faculty = FL.store.faculty.filter(function (person) { return person.isActive !== false; });
      if (!faculty.length) {
        FL.ui.toast("Add faculty before assigning a reviewer.", "danger");
        return;
      }
      const checklist = faculty.map(function (person) {
        const checked = String(person.reviewerId) === String(reviewerId) ? " checked" : "";
        const current = FL.store.reviewerById(person.reviewerId);
        const note = current && current.id !== reviewerId ? " (currently " + current.name + ")" : "";
        return `<label class="field check-row"><input type="checkbox" name="assign-faculty" value="${FL.esc(person.id)}"${checked}><span>${FL.esc(person.name)}${note ? " — " + FL.esc(note) : ""}</span></label>`;
      }).join("");
      const persistAssignments = function (selected, confirmReassign, modalRoot, confirmBtn) {
        if (confirmBtn) {
          FL.ui.setModalConfirmBusy(confirmBtn, true, '<span class="spinner" aria-hidden="true"></span> Saving…', "Save assignments", modalRoot);
        }
        const persist = FL.store.isLiveAccountManagement()
          ? function () { return FL.store.syncReviewerFacultyAssignments(reviewerId, selected, confirmReassign); }
          : function () {
            return Promise.all(selected.map(function (facultyId) {
              return FL.store.assignReviewer(facultyId, reviewerId);
            }));
          };
        return persist().then(function () {
          const admin = FL.store.userById(session.userId);
          return FL.audit.record(admin, "Updated reviewer assignments", reviewerId, "Updated faculty assigned to " + (reviewer.name || "reviewer") + ".");
        }).then(function () {
          if (confirmBtn) FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Save assignments", modalRoot);
          FL.ui.toast("Assignments saved.", "ok");
          return redraw();
        }).catch(function (error) {
          if (confirmBtn) FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Save assignments", modalRoot);
          if (error && error.status === 409 && !confirmReassign) {
            FL.ui.modal({
              title: "Confirm reassignment",
              body: "<p>Some selected faculty are assigned to another reviewer. Reassign them to " + FL.esc(reviewer.name || "this reviewer") + "?</p><p class=\"note\">Pending document reviews keep their original reviewer on each document.</p>",
              confirmLabel: "Reassign faculty",
              onConfirm: function () {
                return persistAssignments(selected, true, modalRoot, confirmBtn).then(function () { return true; });
              }
            });
            return false;
          }
          FL.ui.toast(error.message || "Assignments were not saved.", "danger");
          return false;
        });
      };
      FL.ui.modal({
        title: "Assign faculty to " + (reviewer.name || "reviewer"),
        body: `<p class="sub">Select faculty for ${FL.esc(reviewer.name || "this reviewer")}. This uses the same PostgreSQL assignment as Change reviewer on the Faculty page.</p><div class="check-list">${checklist}</div>`,
        confirmLabel: "Save assignments",
        onConfirm: function (modalRoot, confirmBtn) {
          const selected = Array.prototype.slice.call(document.querySelectorAll("input[name='assign-faculty']:checked")).map(function (input) {
            return input.value;
          });
          return persistAssignments(selected, false, modalRoot, confirmBtn);
        }
      });
    };
    if (FL.store.isLiveAccountManagement() && !FL.store.faculty.length) {
      FL.store.loadAdminFaculty().then(openAssignModal).catch(function (error) {
        FL.ui.toast(error.message || "Could not load faculty.", "danger");
      });
    } else {
      openAssignModal();
    }
  },

  changeFacultyReviewer: function (session, facultyId, redraw) {
    const person = FL.store.facultyById(facultyId);
    if (!person) return;
    const openModal = function () {
      const reviewers = FL.store.isLiveAccountManagement()
        ? FL.store.serverReviewers.filter(function (user) { return user.isActive !== false; })
        : FL.store.users.filter(function (user) { return user.role === "reviewer"; });
      if (!reviewers.length) {
        FL.ui.toast("Add a reviewer first, then assign faculty.", "danger");
        return;
      }
      const currentLabel = person.reviewerName || (FL.store.reviewerById(person.reviewerId) || {}).name || "Unassigned";
      const options = [`<option value="">Unassigned</option>`].concat(reviewers.map(function (reviewer) {
        const selected = String(person.reviewerId) === String(reviewer.id) ? " selected" : "";
        return `<option value="${FL.esc(reviewer.id)}"${selected}>${FL.esc(reviewer.name)}</option>`;
      })).join("");
      FL.ui.modal({
        title: "Change reviewer for " + person.name,
        body: `<p>Current reviewer: <strong>${FL.esc(currentLabel)}</strong></p>
          <label class="field"><span>Reviewer</span><select id="change-reviewer">${options}</select></label>
          <p class="note">Pending document reviews keep their original reviewer assignment on each document.</p>`,
        confirmLabel: "Save assignment",
        onConfirm: function (modalRoot, confirmBtn) {
          const reviewerId = document.getElementById("change-reviewer").value;
          const reviewer = FL.store.reviewerById(reviewerId);
          const admin = FL.store.userById(session.userId);
          FL.ui.setModalConfirmBusy(confirmBtn, true, '<span class="spinner" aria-hidden="true"></span> Saving…', "Save assignment", modalRoot);
          return FL.store.assignReviewer(facultyId, reviewerId || null).then(function (data) {
            const label = reviewer ? reviewer.name : "Unassigned";
            return FL.audit.record(admin, "Reassigned reviewer", person.id, "Set " + person.name + " to " + label + ".");
          }).then(function (data) {
            FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Save assignment", modalRoot);
            if (data && data.note) FL.ui.toast(data.note, "info");
            FL.ui.toast("Reviewer assignment saved.", "ok");
            return redraw();
          }).catch(function (error) {
            FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Save assignment", modalRoot);
            FL.ui.toast(error.message || "Assignment was not saved.", "danger");
            return false;
          });
        }
      });
    };
    if (FL.store.isLiveAccountManagement() && !FL.store.serverReviewers.length) {
      FL.store.loadAdminReviewers().then(openModal).catch(function (error) {
        FL.ui.toast(error.message || "Could not load reviewers.", "danger");
      });
    } else {
      openModal();
    }
  },

  renderKra: function (session, view) {
    FL.kraConfig.mount(document.getElementById("page"), session, view || {});
  },

  renderReports: function () {
    const page = document.getElementById("page");
    const colleges = {};
    FL.store.faculty.forEach(function (person) { colleges[person.college] = true; });
    page.innerHTML = `
      <div class="page-head"><div>
        <p class="eyebrow">Reports and analytics</p>
        <h1>Reports & Analytics</h1>
        <p class="lede">Faculty readiness, KRA scores, submissions, validation, compliance, and evaluation-support results.</p>
      </div></div>
      <div class="toolbar">
        <label class="filter"><span>College</span>
          <select id="report-college"><option value="">All colleges</option>${Object.keys(colleges).sort().map(function (college) {
            return `<option>${FL.esc(college)}</option>`;
          }).join("")}</select>
        </label>
      </div>
      <div id="report-body"></div>`;
    const draw = function () {
      const college = document.getElementById("report-college").value;
      const faculty = FL.store.faculty.filter(function (person) { return !college || person.college === college; });
      const ids = {};
      faculty.forEach(function (person) { ids[person.id] = true; });
      const docs = FL.store.documents.filter(function (doc) { return ids[doc.facultyId]; });
      const statusCounts = {};
      docs.forEach(function (doc) { statusCounts[doc.status] = (statusCounts[doc.status] || 0) + 1; });
      document.getElementById("report-body").innerHTML = `
        <div class="stat-grid">
          <article class="stat"><span>Faculty in view</span><strong>${faculty.length}</strong></article>
          <article class="stat"><span>Document submissions</span><strong>${docs.length}</strong></article>
          <article class="stat"><span>Approved</span><strong>${statusCounts.approved || 0}</strong></article>
          <article class="stat"><span>Needs attention</span><strong>${faculty.filter(function (person) { return FL.compliance(person.id).status !== "On track"; }).length}</strong></article>
        </div>
        <article class="card">
          <div class="card-head"><h2>Faculty readiness</h2></div>
          <div class="table-wrap"><table class="data">
            <thead><tr><th>Faculty</th><th>College</th><th>Rank</th><th>KRA I</th><th>KRA II</th><th>KRA III</th><th>KRA IV</th><th>Computed score</th><th>Compliance</th></tr></thead>
            <tbody>${faculty.map(function (person) {
              const sim = FL.scoring.simulation(person.id);
              const cells = sim.aggregate.kras.map(function (kra) { return `<td>${kra.credited}</td>`; }).join("");
              return `<tr><td>${FL.esc(person.name)}</td><td>${FL.esc(person.college)}</td><td>${FL.esc(person.rank)}</td>${cells}<td>${sim.aggregate.total}</td><td>${FL.ui.statusBadge(FL.compliance(person.id).status)}</td></tr>`;
            }).join("")}</tbody>
          </table></div>
          <p class="note">Scores are simulation estimates from approved documents. They are not the official sub-rank result.</p>
        </article>
        <article class="card">
          <div class="card-head"><h2>Document validation and submissions</h2></div>
          <div class="bars">${Object.keys(statusCounts).map(function (status) {
            const width = docs.length ? (statusCounts[status] / docs.length) * 100 : 0;
            return `<div class="bar-row"><span>${FL.esc(status)}</span><div class="track"><span style="width:${width}%"></span></div><strong>${statusCounts[status]}</strong></div>`;
          }).join("")}</div>
        </article>`;
    };
    document.getElementById("report-college").addEventListener("change", draw);
    draw();
  },

  renderProfile: function (session) {
    const user = FL.store.userById(session.userId);
    const page = document.getElementById("page");
    page.innerHTML = `
      <div class="page-head"><div><p class="eyebrow">Account</p><h1>My Profile</h1><p class="lede">Administrator account for FacultyLink evaluation support.</p></div></div>
      <article class="card profile-card">
        <div class="profile-banner"><span class="avatar large">${FL.esc(user.name.split(" ").map(function (part) { return part[0]; }).slice(0, 2).join(""))}</span><div><h2>${FL.esc(user.name)}</h2><p>${FL.esc(user.title)}</p>${FL.ui.badge("info", "Administrator")}</div></div>
        <form id="profile-form" class="form-grid">
          <label class="field"><span>Employee number</span><input value="${FL.esc(user.employeeNo)}" disabled></label>
          <label class="field"><span>Email</span><input value="${FL.esc(user.email)}" disabled></label>
          <label class="field"><span>Office</span><input id="profile-office" value="${FL.esc(user.office)}"></label>
          <label class="field"><span>Contact</span><input id="profile-contact" value="${FL.esc(user.contact)}"></label>
          <label class="field field-wide"><span>Assignment</span><input id="profile-spec" value="${FL.esc(user.specialization)}"></label>
          <div class="field-wide"><button class="btn btn-primary" type="submit">Save profile</button></div>
        </form>
      </article>`;
    document.getElementById("profile-form").addEventListener("submit", function (event) {
      event.preventDefault();
      user.office = document.getElementById("profile-office").value.trim();
      user.contact = document.getElementById("profile-contact").value.trim();
      user.specialization = document.getElementById("profile-spec").value.trim();
      FL.store.saveProfile(user).then(function () {
        return FL.audit.record(user, "Updated profile", user.employeeNo, "Updated administrator profile details.");
      }).then(function () {
        FL.ui.toast("Profile saved.", "ok");
      }).catch(function (error) {
        FL.ui.toast(error.message || "Profile was not saved.", "danger");
      });
    });
  },

  scheduleId: "evaluation",
  scheduleLabel: "Rank Upgrade and Reclassification",

  scheduleToday: function () {
    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return now.getFullYear() + "-" + month + "-" + day;
  },

  scheduleVisibility: function (period) {
    if (!period) return "draft";
    if (period.visibility === "all" || period.visibility === "reviewers" || period.visibility === "faculty") return "all";
    if (period.visibility === "draft") return "draft";
    return period.published ? "all" : "draft";
  },

  scheduleStatus: function (period) {
    const visibility = FL.admin.scheduleVisibility(period);
    if (visibility === "draft" || !period.startDate || !period.endDate) return "draft";
    const today = FL.admin.scheduleToday();
    if (today < period.startDate) return "upcoming";
    if (today > period.endDate) return "closed";
    return "open";
  },

  scheduleAudienceLabel: function (period) {
    return FL.admin.scheduleVisibility(period) === "all" ? "Reviewers and faculty" : "Not published";
  },

  scheduleCard: function (period, editable) {
    const item = period || {
      id: FL.admin.scheduleId,
      label: FL.admin.scheduleLabel,
      startDate: "",
      endDate: "",
      published: false,
      visibility: "draft"
    };
    const status = FL.admin.scheduleStatus(item);
    const visibility = FL.admin.scheduleVisibility(item);
    if (!editable) {
      return `<article class="card">
        <div class="card-head"><h2>${FL.esc(FL.admin.scheduleLabel)}</h2>${FL.ui.statusBadge(status)}</div>
        <dl class="facts">
          <div><dt>Evaluation type</dt><dd>${FL.esc(FL.admin.scheduleLabel)}</dd></div>
          <div><dt>Status</dt><dd>${FL.ui.statusBadge(status)}</dd></div>
          <div><dt>Start date</dt><dd>${FL.esc(FL.formatWhen(item.startDate))}</dd></div>
          <div><dt>End date</dt><dd>${FL.esc(FL.formatWhen(item.endDate))}</dd></div>
          <div><dt>Visible to</dt><dd>${FL.esc(FL.admin.scheduleAudienceLabel(item))}</dd></div>
        </dl>
      </article>`;
    }
    return `<article class="card">
      <div class="card-head"><h2>${FL.esc(FL.admin.scheduleLabel)}</h2>${FL.ui.statusBadge(status)}</div>
      <div class="form-grid">
        <label class="field"><span>Start date</span><input id="schedule-start" type="date" value="${FL.esc(item.startDate)}"></label>
        <label class="field"><span>End date</span><input id="schedule-end" type="date" value="${FL.esc(item.endDate)}"></label>
        <label class="field field-wide"><span>Visibility</span>
          <select id="schedule-visibility">
            <option value="draft"${visibility === "draft" ? " selected" : ""}>Draft — not published</option>
            <option value="all"${visibility === "all" ? " selected" : ""}>Published — reviewers and faculty can view</option>
          </select>
        </label>
      </div>
    </article>`;
  },

  renderSchedule: function (session, view) {
    const editable = !(view && view.readonly);
    const periods = FL.store.evaluationPeriods || [];
    const period = periods[0] || null;
    const page = document.getElementById("page");
    if (!editable && !period) {
      page.innerHTML = `
        <div class="page-head"><div>
          <p class="eyebrow">Evaluation period</p>
          <h1>Evaluation Schedule</h1>
          <p class="lede">Published Rank Upgrade and Reclassification dates from the administrator.</p>
        </div></div>
        ${FL.ui.empty("No published schedule", "The administrator has not published the Rank Upgrade and Reclassification schedule yet.")}`;
      return;
    }
    page.innerHTML = `
      <div class="page-head"><div>
        <p class="eyebrow">Evaluation period</p>
        <h1>Evaluation Schedule</h1>
        <p class="lede">${editable
          ? "Set one Rank Upgrade and Reclassification period, then choose who can view it. Changing these dates does not change scores already recorded on documents."
          : "This is the published Rank Upgrade and Reclassification schedule. Reviewers can read it and cannot change it."}</p>
      </div></div>
      ${editable ? `<form id="schedule-form">` : ""}
        ${FL.admin.scheduleCard(period, editable)}
        ${editable ? `<div class="form-row"><button class="btn btn-primary" type="submit">Save schedule</button></div></form>` : `<p class="note">Only an administrator can change these dates.</p>`}`;
    if (!editable) return;
    document.getElementById("schedule-form").addEventListener("submit", function (event) {
      event.preventDefault();
      const visibility = document.getElementById("schedule-visibility").value;
      const next = [{
        id: FL.admin.scheduleId,
        startDate: document.getElementById("schedule-start").value,
        endDate: document.getElementById("schedule-end").value,
        visibility: visibility,
        published: visibility !== "draft"
      }];
      if (next[0].startDate && next[0].endDate && next[0].endDate < next[0].startDate) {
        FL.ui.toast("Enter a start date on or before the end date before publishing.", "danger");
        return;
      }
      if (next[0].published && (!next[0].startDate || !next[0].endDate)) {
        FL.ui.toast("Enter a start date on or before the end date before publishing.", "danger");
        return;
      }
      FL.store.saveEvaluationPeriods(next).then(function () {
        FL.ui.toast("Evaluation schedule saved.", "ok");
        FL.admin.renderSchedule(session);
      }).catch(function (error) {
        FL.ui.toast(error.message || "The schedule was not saved.", "danger");
      });
    });
  }
};

FL.pages["admin-dashboard"] = function () { FL.admin.renderDashboard(); };
FL.pages["admin-reviewers"] = function (session) { FL.admin.renderReviewers(session); };
FL.pages["admin-kra"] = function (session) { FL.admin.renderKra(session); };
FL.pages["admin-schedule"] = function (session) { FL.admin.renderSchedule(session); };
FL.pages["admin-reports"] = function () { FL.admin.renderReports(); };
FL.pages["admin-profile"] = function (session) { FL.admin.renderProfile(session); };
FL.pages["admin-notifications"] = function (session) {
  const user = FL.store.userById(session.userId);
  const draw = function () {
    document.getElementById("page").innerHTML = FL.notifications.render(user);
    FL.notifications.bind(user, draw);
  };
  draw();
};
FL.pages["admin-audit"] = function () {
  document.getElementById("page").innerHTML = FL.audit.render();
  FL.audit.bind();
};
