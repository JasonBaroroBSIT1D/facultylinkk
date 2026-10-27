window.FL = window.FL || {};

FL.faculty = {
  refreshAdminList: function (draw) {
    if (FL.store.usesRealAdminApi()) {
      return FL.store.loadAdminFaculty().then(function () {
        FL.store.adminDirectoryLoaded = true;
        draw();
      }).catch(function (error) {
        FL.ui.toast(error.message || "Could not refresh the faculty list.", "danger");
        throw error;
      });
    }
    draw();
    return Promise.resolve();
  },

  reviewerLabel: function (person) {
    if (person.reviewerName) return person.reviewerName;
    const reviewer = FL.store.reviewerById(person.reviewerId);
    return reviewer ? reviewer.name : "Unassigned";
  },

  accountStatusCell: function (person) {
    if (person._fromServer || FL.store.isLiveAccountManagement()) {
      if (person.isActive === false) return FL.ui.badge("invalid", "Inactive");
      const status = person.accountStatus || person.status || "Active";
      return FL.ui.badge("valid", status);
    }
    return FL.ui.statusBadge(FL.compliance(person.id).status);
  },

  displayRank: function (person) {
    const rank = (person.rank || "").trim();
    return rank || "Not provided";
  },

  displayDepartment: function (person) {
    const dept = (person.department || "").trim();
    return dept || "Not provided";
  },

  showDirectoryError: function (host, error, retryFn) {
    const retryId = "faculty-retry-load";
    host.innerHTML = FL.ui.emptyWithRetry(
      "Could not load faculty",
      (error && error.message) || "Start the Flask API on port 5000, then retry.",
      retryId
    );
    const btn = document.getElementById(retryId);
    if (btn) btn.addEventListener("click", retryFn);
  },

  detailHref: function (id) {
    return "faculty-detail.html?id=" + encodeURIComponent(id);
  },

  documentHref: function (id) {
    const page = document.body.dataset.role === "administrator" ? "document-view.html" : "document-review.html";
    return page + "?id=" + encodeURIComponent(id);
  },

  colleges: function () {
    const set = {};
    FL.store.faculty.forEach(function (person) { set[person.college] = true; });
    return Object.keys(set).sort();
  },

  ranks: function () {
    const set = {};
    FL.store.faculty.forEach(function (person) { set[person.rank] = true; });
    return Object.keys(set).sort();
  },

  listHtml: function (people, action, manage) {
    if (!people.length) {
      return FL.ui.empty("No faculty records", manage ? "Add a faculty member to begin assignments." : "No faculty match this view.");
    }
    const live = manage && FL.store.isLiveAccountManagement();
    return `
      <table class="data">
        <thead>
          <tr>
            <th>Faculty</th>
            <th>Current rank</th>
            <th>Department</th>
            <th>Reviewer</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${people.map(function (person) {
            return `<tr>
              <td><strong>${FL.esc(person.name || person.email || "Faculty")}</strong><div class="sub">${FL.esc(person.email || person.college || "")}</div></td>
              <td>${FL.esc(FL.faculty.displayRank(person))}</td>
              <td>${FL.esc(FL.faculty.displayDepartment(person))}</td>
              <td>${FL.esc(FL.faculty.reviewerLabel(person))}</td>
              <td>${FL.faculty.accountStatusCell(person)}</td>
              <td class="action-cell">
                ${live
                  ? `<button class="btn btn-small btn-ghost" type="button" data-view-faculty="${FL.esc(person.id)}">View faculty</button>`
                  : `<a class="btn btn-small btn-ghost" href="${FL.faculty.detailHref(person.id)}">${FL.esc(action || "View faculty")}</a>`}
                ${manage ? `
                  <button class="btn btn-small btn-primary" type="button" data-change-reviewer="${FL.esc(person.id)}">Change reviewer</button>
                  <button class="btn btn-small btn-ghost" type="button" data-reissue-faculty="${FL.esc(person.id)}">Resend credentials</button>
                  <button class="btn btn-small btn-ghost" type="button" data-remove-faculty="${FL.esc(person.id)}">${person.isActive === false ? "Reactivate" : "Remove"}</button>
                ` : ""}
              </td>
            </tr>`;
          }).join("")}
        </tbody>
      </table>`;
  },

  renderList: function (options) {
    const page = document.getElementById("page");
    const manage = !!options.manage;
    page.innerHTML = `
      <div class="page-head">
        <div>
          <p class="eyebrow">${FL.esc(options.eyebrow)}</p>
          <h1>${FL.esc(options.title)}</h1>
          <p class="lede">${FL.esc(options.lede)}</p>
        </div>
        ${manage ? `<button class="btn btn-primary" type="button" id="faculty-add">Add faculty</button>` : ""}
      </div>
      <div class="toolbar">
        <label class="search"><span class="sr-only">Search faculty</span>
          <input id="faculty-search" type="search" placeholder="Search faculty, department, rank, or reviewer">
        </label>
      </div>
      <div class="card"><div class="table-wrap" id="faculty-table">${FL.ui.loading("Loading faculty", manage && FL.store.usesRealAdminApi() ? "Fetching accounts from PostgreSQL." : "Preparing this view.")}</div></div>`;
    const loadFromApi = function () {
      const host = document.getElementById("faculty-table");
      host.innerHTML = FL.ui.loading("Loading faculty", "Fetching accounts from PostgreSQL.");
      return FL.store.loadAdminFaculty().then(function () {
        FL.store.adminDirectoryLoaded = true;
        draw();
      }).catch(function (error) {
        FL.faculty.showDirectoryError(host, error, loadFromApi);
      });
    };
    const draw = function () {
      if (manage && FL.store.usesRealAdminApi() && !FL.store.adminDirectoryLoaded) return;
      const query = document.getElementById("faculty-search").value.trim().toLowerCase();
      const source = manage && FL.store.usesRealAdminApi() ? FL.store.faculty : (manage ? FL.store.faculty : options.people);
      const people = source.filter(function (person) {
        if (!query) return true;
        return [person.name || "", person.email || "", person.department || "", person.college || "", person.rank || "", FL.faculty.reviewerLabel(person)]
          .join(" ")
          .toLowerCase()
          .indexOf(query) !== -1;
      });
      const host = document.getElementById("faculty-table");
      host.innerHTML = FL.faculty.listHtml(people, options.action, manage);
      if (!manage) return;
      host.querySelectorAll("[data-view-faculty]").forEach(function (button) {
        button.addEventListener("click", function () {
          FL.admin.viewFaculty(button.getAttribute("data-view-faculty"));
        });
      });
      host.querySelectorAll("[data-change-reviewer]").forEach(function (button) {
        button.addEventListener("click", function () {
          FL.admin.changeFacultyReviewer(options.session, button.getAttribute("data-change-reviewer"), function () {
            return FL.faculty.refreshAdminList(draw);
          });
        });
      });
      host.querySelectorAll("[data-reissue-faculty]").forEach(function (button) {
        button.addEventListener("click", function () {
          const person = FL.store.facultyById(button.getAttribute("data-reissue-faculty"));
          if (person) FL.faculty.reissueCredentials(person, draw);
        });
      });
      host.querySelectorAll("[data-remove-faculty]").forEach(function (button) {
        button.addEventListener("click", function () {
          FL.faculty.removeFaculty(button.getAttribute("data-remove-faculty"), draw);
        });
      });
    };
    document.getElementById("faculty-search").addEventListener("input", draw);
    if (manage) {
      document.getElementById("faculty-add").addEventListener("click", function () {
        FL.faculty.addFaculty(options.session, function () {
          return FL.faculty.refreshAdminList(draw);
        });
      });
    }
    if (manage && FL.store.usesRealAdminApi()) {
      loadFromApi();
    } else if (manage) {
      document.getElementById("faculty-table").innerHTML = FL.ui.empty(
        "Sign in required",
        "Sign in as an administrator with the Flask API to load PostgreSQL faculty accounts."
      );
    } else {
      draw();
    }
  },

  addFaculty: function (session, redraw) {
    const openModal = function () {
    const reviewers = FL.store.users.filter(function (user) { return user.role === "reviewer"; });
    const reviewerOptions = [`<option value="">Unassigned</option>`].concat(reviewers.map(function (reviewer) {
      return `<option value="${FL.esc(reviewer.id)}">${FL.esc(reviewer.name)}</option>`;
    })).join("");
    FL.ui.modal({
      title: "Add faculty",
      confirmLabel: "Create faculty",
      body: `
        <div class="form-grid">
          <label class="field"><span>Full name</span><input id="faculty-full-name" type="text" required></label>
          <label class="field"><span>Email</span><input id="faculty-email" type="email" required></label>
          <label class="field"><span>Department</span><input id="faculty-department" type="text" required></label>
          <label class="field"><span>Current rank</span><input id="faculty-rank" type="text" value="Instructor I"></label>
          <label class="field"><span>Highest academic degree (optional)</span><input id="faculty-education" type="text" placeholder="e.g. Master of Arts in Education"></label>
          <label class="field"><span>Assign reviewer</span><select id="faculty-reviewer">${reviewerOptions}</select></label>
        </div>
        <p class="note">FacultyLink emails a temporary password for the mobile app. The faculty member must change it on first sign-in.</p>`,
      onConfirm: function (modalRoot, confirmBtn) {
        const payload = {
          fullName: document.getElementById("faculty-full-name").value.trim(),
          email: document.getElementById("faculty-email").value.trim(),
          department: document.getElementById("faculty-department").value.trim(),
          rank: document.getElementById("faculty-rank").value.trim() || "Instructor I",
          education: document.getElementById("faculty-education").value.trim(),
          reviewerId: document.getElementById("faculty-reviewer").value
        };
        if (!payload.fullName || !payload.email || !payload.department) {
          FL.ui.toast("Fill in name, email, and department.", "danger");
          return false;
        }
        FL.ui.setModalConfirmBusy(
          confirmBtn,
          true,
          '<span class="spinner" aria-hidden="true"></span> Creating Faculty...',
          "Create faculty",
          modalRoot
        );
        return FL.store.createFaculty(payload).then(function (data) {
          const admin = FL.store.userById(session.userId);
          return FL.audit.record(
            admin,
            "Added faculty",
            data.faculty && data.faculty.id,
            "Created " + payload.fullName + "."
          ).then(function () { return data; });
        }).then(function (data) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Create faculty", modalRoot);
          let message = "Faculty account created successfully.";
          if (data.emailSent) {
            message += " Temporary credentials were emailed to " + payload.email + ".";
            FL.ui.toast(message, "ok");
          } else {
            message += " The account was saved, but the credential email was not sent. Use Resend credentials from the faculty row.";
            FL.ui.toast(data.emailError ? message + " (" + data.emailError + ")" : message, "danger");
          }
          return redraw().then(function () { return true; });
        }).catch(function (error) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Create faculty", modalRoot);
          FL.ui.toast(error.message || "Faculty was not created.", "danger");
          return false;
        });
      }
    });
    };
    if (FL.store.usesRealAdminApi() && !FL.store.serverReviewers.length) {
      FL.store.loadAdminReviewers().then(openModal).catch(function (error) {
        FL.ui.toast(error.message || "Could not load reviewers for assignment.", "danger");
      });
    } else {
      openModal();
    }
  },

  reissueCredentials: function (person, redraw) {
    FL.ui.modal({
      title: "Resend credentials",
      confirmLabel: "Send new temporary password",
      body: `<p>FacultyLink will generate a new temporary password and email it to ${FL.esc(person.email)}.</p>
        <p>The previous temporary password and active sessions for this account will stop working immediately.</p>`,
      onConfirm: function (modalRoot, confirmBtn) {
        FL.ui.setModalConfirmBusy(
          confirmBtn,
          true,
          '<span class="spinner" aria-hidden="true"></span> Sending…',
          "Send new temporary password",
          modalRoot
        );
        return FL.store.reissueFacultyCredentials(person.id).then(function (data) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Send new temporary password", modalRoot);
          if (data && data.emailSent) {
            FL.ui.toast("Temporary credentials were emailed to " + person.email + ".", "ok");
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

  removeFaculty: function (facultyId, redraw) {
    const person = FL.store.facultyById(facultyId);
    if (!person) return;
    const live = FL.store.isLiveAccountManagement();
    if (live && person.isActive === false) {
      FL.ui.modal({
        title: "Reactivate faculty account",
        confirmLabel: "Reactivate account",
        body: `<p>Restore sign-in access for <strong>${FL.esc(person.name)}</strong> (${FL.esc(person.email)})?</p>`,
        onConfirm: function (modalRoot, confirmBtn) {
          FL.ui.setModalConfirmBusy(confirmBtn, true, '<span class="spinner" aria-hidden="true"></span> Reactivating…', "Reactivate account", modalRoot);
          return FL.store.reactivateAccount(FL.store.facultyCredentialsId(person)).then(function () {
            FL.ui.setModalConfirmBusy(confirmBtn, false, "", "Reactivate account", modalRoot);
            FL.ui.toast(person.name + " was reactivated.", "ok");
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
    FL.ui.modal({
      title: live ? "Deactivate faculty account" : "Remove faculty",
      danger: true,
      confirmLabel: live ? "Deactivate account" : "Remove faculty",
      body: live
        ? `<p>Deactivate <strong>${FL.esc(person.name)}</strong> (${FL.esc(person.email)})?</p>
           <p>The account cannot sign in until reactivated. Documents, KRA records, reviewer feedback, and audit history are preserved.</p>`
        : `<p>Remove <strong>${FL.esc(person.name)}</strong>? Their documents, scores, and login will also be removed.</p>`,
      onConfirm: function (modalRoot, confirmBtn) {
        FL.ui.setModalConfirmBusy(
          confirmBtn,
          true,
          '<span class="spinner" aria-hidden="true"></span> Processing…',
          live ? "Deactivate account" : "Remove faculty",
          modalRoot
        );
        return FL.store.removeFaculty(facultyId).then(function () {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", live ? "Deactivate account" : "Remove faculty", modalRoot);
          FL.ui.toast(live ? person.name + " was deactivated." : person.name + " was removed.", "ok");
          return redraw();
        }).catch(function (error) {
          FL.ui.setModalConfirmBusy(confirmBtn, false, "", live ? "Deactivate account" : "Remove faculty", modalRoot);
          FL.ui.toast(error.message || (live ? "Account was not deactivated." : "Faculty was not removed."), "danger");
          return false;
        });
      }
    });
  },

  renderDetail: function (session) {
    const params = new URLSearchParams(window.location.search);
    const person = FL.store.facultyById(params.get("id"));
    const page = document.getElementById("page");
    if (!person) {
      page.innerHTML = FL.ui.empty("Faculty record not found", "The faculty record is not available.");
      return;
    }
    if (session.role === "reviewer" && person.reviewerId !== session.userId) {
      page.innerHTML = FL.ui.empty("Faculty record not assigned", "This faculty member is not assigned to your review work.");
      return;
    }
    const sim = FL.scoring.simulation(person.id);
    const compliance = FL.compliance(person.id);
    const reviewer = FL.store.userById(person.reviewerId);
    const docs = FL.store.documents.filter(function (doc) { return doc.facultyId === person.id; });
    const backHref = session.role === "administrator" ? "faculty.html" : "assigned-faculty.html";
    const backLabel = session.role === "administrator" ? "Back to faculty" : "Back to assigned faculty";
    page.innerHTML = `
      <div class="page-head">
        <div>
          <p class="eyebrow">Faculty detail</p>
          <h1>${FL.esc(person.name)}</h1>
          <p class="lede">${FL.esc(person.rank)} · ${FL.esc(person.department)}</p>
        </div>
        <div class="head-actions"><a class="btn btn-ghost" href="${backHref}">${FL.esc(backLabel)}</a></div>
      </div>
      <div class="tablist" role="tablist">
        ${["Profile", "KRA Scores", "Documents", "Validation", "Evaluation", "Rank Simulation"].map(function (tab, index) {
          return `<button class="tab ${index === 0 ? "is-active" : ""}" type="button" data-tab="${FL.esc(tab)}">${FL.esc(tab)}</button>`;
        }).join("")}
      </div>
      <section class="tab-panel is-active" data-panel="Profile">
        <div class="split">
          <article class="card">
            <div class="card-head"><h2>Faculty profile</h2></div>
            <dl class="facts">
              <div><dt>Email</dt><dd>${FL.esc(person.email)}</dd></div>
              <div><dt>Contact</dt><dd>${FL.esc(person.contact)}</dd></div>
              <div><dt>Department</dt><dd>${FL.esc(person.department)}</dd></div>
              <div><dt>Current rank</dt><dd>${FL.esc(person.rank)}</dd></div>
              <div><dt>Designation</dt><dd>${FL.esc(person.designation)}</dd></div>
              <div><dt>Employment</dt><dd>${FL.esc(person.employment)}</dd></div>
              <div><dt>Date hired</dt><dd>${FL.esc(FL.formatWhen(person.dateHired))}</dd></div>
              <div><dt>Education</dt><dd>${FL.esc(person.education)}</dd></div>
              <div><dt>Assigned reviewer</dt><dd>${FL.esc(reviewer ? reviewer.name : "Unassigned")}</dd></div>
            </dl>
          </article>
          <article class="card">
            <div class="card-head"><h2>Compliance</h2>${FL.ui.statusBadge(compliance.status)}</div>
            ${FL.ui.progress(compliance.validated, compliance.submitted || 0, "Validated documents")}
            <ul class="plain">
              <li>Submitted documents: ${compliance.submitted}</li>
              <li>Validated and approved: ${compliance.validated}</li>
              <li>Missing requirements or records needing validation: ${compliance.missing}</li>
              <li>Documents requiring revision: ${compliance.revision}</li>
            </ul>
          </article>
        </div>
      </section>
      <section class="tab-panel" data-panel="KRA Scores">
        <div class="stack">
          ${sim.aggregate.kras.map(function (kra) {
            return `<article class="card">
              <div class="card-head"><h2>${FL.esc(kra.code)} — ${FL.esc(kra.name)}</h2><strong>${kra.credited} / ${kra.maxPoints}</strong></div>
              ${FL.ui.progress(kra.credited, kra.maxPoints, "Approved points within the KRA maximum")}
              <div class="table-wrap"><table class="data">
                <thead><tr><th>Criterion</th><th>Maximum</th><th>Approved points</th></tr></thead>
                <tbody>${kra.criteria.map(function (criterion) {
                  return `<tr><td>${FL.esc(criterion.name)}</td><td>${criterion.maxPoints}${criterion.bonus ? " bonus" : ""}</td><td>${criterion.earned}</td></tr>`;
                }).join("")}</tbody>
              </table></div>
            </article>`;
          }).join("")}
        </div>
      </section>
      <section class="tab-panel" data-panel="Documents">
        <article class="card"><div class="table-wrap">${docs.length ? `<table class="data"><thead><tr><th>Document ID</th><th>Document</th><th>KRA</th><th>Status</th><th>Score</th><th></th></tr></thead><tbody>
          ${docs.map(function (doc) {
            const scored = FL.scoring.scoreDocument(doc);
            const kra = scored.kra ? scored.kra.code : "—";
            const score = scored.finalScore === null ? "—" : String(scored.finalScore);
            return `<tr><td>${FL.esc(doc.id)}</td><td>${FL.esc(doc.name)}</td><td>${FL.esc(kra)}</td><td>${FL.ui.statusBadge(doc.status)}</td><td>${FL.esc(score)}</td><td><a class="btn btn-small btn-ghost" href="${FL.faculty.documentHref(doc.id)}">Open</a></td></tr>`;
          }).join("")}
        </tbody></table>` : FL.ui.empty("No documents", "This faculty member has no submitted documents.")}</div></article>
      </section>
      <section class="tab-panel" data-panel="Validation">
        <article class="card"><div class="table-wrap">${docs.length ? `<table class="data"><thead><tr><th>Document</th><th>Required fields</th><th>Classification</th><th>Evidence</th><th>Duplicate</th><th>Overall</th></tr></thead><tbody>
          ${docs.map(function (doc) {
            const result = FL.validation.evaluate(doc);
            const fields = ["Title", "Author", "Date"].filter(function (name, index) {
              return [result.fields.title, result.fields.author, result.fields.date][index];
            });
            const klass = (doc.extractedInfo && doc.extractedInfo["Automatically identified indicator"]) || (result.classification.status === "pending" ? "OCR pending" : result.classification.detected ? result.classification.detected.label : "Cannot classify");
            return `<tr>
              <td>${FL.esc(doc.id)}</td>
              <td>${fields.length === 3 ? FL.ui.badge("valid", "Complete") : FL.ui.badge("invalid", fields.length ? fields.join(", ") + " only" : "Missing")}</td>
              <td>${FL.ui.statusBadge(result.classification.status === "pending" ? "pending" : result.classification.status)}</td>
              <td>${FL.ui.statusBadge(result.evidenceStatus)}</td>
              <td>${FL.ui.statusBadge(result.duplicateStatus)}</td>
              <td>${FL.ui.statusBadge(result.overall === "valid" ? "valid" : result.overall === "invalid" ? "invalid" : "reviewer-required")}<div class="sub">${FL.esc(klass)}</div></td>
            </tr>`;
          }).join("")}
        </tbody></table>` : FL.ui.empty("No validation records", "Validation appears after a document is submitted.")}</div></article>
      </section>
      <section class="tab-panel" data-panel="Evaluation">
        <article class="card">
          <div class="card-head"><h2>Evaluation information</h2></div>
          <p>Evaluation follows DBM–CHED Joint Circular No. 01, s. 2026 (Enhanced Implementing Guidelines of JC No. 3, s. 2022). Only accomplishments within the evaluation period (August 1, 2023 – July 31, 2026) are credited. There is no double counting of points. The SUC governing board has the final decision on reclassification.</p>
          <dl class="facts compact">
            <div><dt>Cycle</dt><dd>JC No. 01, s. 2026 (Aug 1, 2023 – Jul 31, 2026)</dd></div>
            <div><dt>Current rank</dt><dd>${FL.esc(person.rank)}</dd></div>
            <div><dt>Estimated weighted score</dt><dd>${sim.aggregate.weightedScore != null ? sim.aggregate.weightedScore : sim.aggregate.total} / 100</dd></div>
            <div><dt>Table 2.2 band</dt><dd>${FL.esc(sim.aggregate.weightBand || "—")}</dd></div>
            <div><dt>Reviewer</dt><dd>${FL.esc(reviewer ? reviewer.name : "Unassigned")}</dd></div>
            <div><dt>Compliance</dt><dd>${FL.esc(compliance.status)}</dd></div>
          </dl>
          <p class="note">FacultyLink prepares and supports evaluation. It does not replace the Institutional Evaluation Committee, the Regional Evaluation Committee, the Evaluation and Accreditation Committee, the Certification Committee, or the governing board.</p>
        </article>
      </section>
      <section class="tab-panel" data-panel="Rank Simulation">
        ${FL.faculty.simulationHtml(sim)}
      </section>`;
    page.querySelectorAll(".tab").forEach(function (button) {
      button.addEventListener("click", function () {
        page.querySelectorAll(".tab").forEach(function (tab) { tab.classList.remove("is-active"); });
        page.querySelectorAll(".tab-panel").forEach(function (panel) { panel.classList.remove("is-active"); });
        button.classList.add("is-active");
        page.querySelector('[data-panel="' + button.getAttribute("data-tab") + '"]').classList.add("is-active");
      });
    });
  },

  simulationHtml: function (sim) {
    return `
      <div class="callout">
        <strong>Simulation Result</strong>
        <p>This is an estimate based on computed KRA scores and uploaded documentary evidence. FacultyLink is a preparatory and evaluation-support system. It does not replace the official evaluation conducted by authorized committees, and it does not determine the number of sub-ranks.</p>
      </div>
      <div class="stat-grid">
        <article class="stat"><span>Current rank</span><strong>${FL.esc(sim.faculty.rank)}</strong></article>
        <article class="stat"><span>Weighted score</span><strong>${sim.aggregate.weightedScore != null ? sim.aggregate.weightedScore : sim.aggregate.total}</strong><small>Table 2.2 (${FL.esc(sim.aggregate.weightBand || "rank band")}) out of 100</small></article>
        <article class="stat"><span>Raw KRA points</span><strong>${sim.aggregate.rawTotal != null ? sim.aggregate.rawTotal : "—"}</strong><small>Sum before rank weights</small></article>
        ${sim.aggregate.kras.map(function (kra) {
          const weight = sim.aggregate.appliedWeights ? sim.aggregate.appliedWeights[kra.id] : null;
          return `<article class="stat"><span>${FL.esc(kra.code)}</span><strong>${kra.credited}</strong><small>Maximum ${kra.maxPoints}${weight != null ? " · Weight " + weight + "%" : ""}</small></article>`;
        }).join("")}
      </div>
      <article class="card">
        <div class="card-head"><h2>Assessment gaps</h2></div>
        <ul class="gaps">
          ${sim.gaps.map(function (gap) { return `<li class="gap-${FL.esc(gap.tone)}">${FL.esc(gap.text)}</li>`; }).join("")}
        </ul>
      </article>`;
  }
};

FL.pages["admin-faculty"] = function (session) {
  FL.faculty.renderList({
    eyebrow: "Faculty records",
    title: "Faculty",
    lede: "Add or remove faculty accounts, then assign or change their reviewer. Faculty readiness stays available for DBM–CHED evaluation support.",
    people: FL.store.faculty,
    manage: true,
    session: session
  });
};

FL.pages["reviewer-faculty"] = function (session) {
  FL.faculty.renderList({
    eyebrow: "Assignments",
    title: "Assigned Faculty",
    lede: "Faculty assigned to you, with rank, documents, and validation status.",
    action: "Open Faculty",
    people: FL.store.assignedFacultyForReviewer(session)
  });
};

FL.pages["admin-faculty-detail"] = function (session) { FL.faculty.renderDetail(session); };
FL.pages["reviewer-faculty-detail"] = function (session) { FL.faculty.renderDetail(session); };
