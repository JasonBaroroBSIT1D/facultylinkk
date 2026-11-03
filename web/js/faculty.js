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

  criteriaRowsForKra: function (kraId, kraBlock) {
    if (kraBlock && Array.isArray(kraBlock.criteriaScores) && kraBlock.criteriaScores.length) {
      return kraBlock.criteriaScores.map(function (row) {
        const maxVal = row.maxPoints != null ? row.maxPoints : 0;
        let earned = "—";
        if (row.estimatedPoints != null) {
          earned = row.estimatedPoints;
        } else if (row.accomplishmentPreviewPoints != null) {
          earned = row.accomplishmentPreviewPoints + " (preview)";
        } else if (row.integrationState === "criterion_b_adapter_disabled") {
          earned = "Pending integration";
        }
        return {
          name: FL.rules.criterionUserLabel(row.criterionId, row.name),
          maxPoints: maxVal,
          maxLabel: row.bonus ? String(maxVal) + " bonus" : String(maxVal),
          earned: earned,
          bonus: !!row.bonus,
          previewNote: row.accomplishmentPreviewNote || null
        };
      });
    }
    const kra = FL.rules && FL.rules.findKra ? FL.rules.findKra(kraId) : null;
    if (!kra || !kra.criteria) return [];
    const critDisp = kraBlock && kraBlock.criterionADisplay ? kraBlock.criterionADisplay : null;
    const critEst = critDisp && critDisp.estimatedPoints != null
      ? critDisp.estimatedPoints
      : null;
    return kra.criteria.map(function (criterion) {
      let earned = "—";
      if (kraId === "kra1" && criterion.id === "kra1-a" && critEst != null) {
        earned = critEst;
      }
      return {
        name: FL.rules.criterionUserLabel(criterion.id, criterion.name),
        maxPoints: criterion.maxPoints || 0,
        earned: earned,
        bonus: !!criterion.bonus
      };
    });
  },

  unifiedSimulation: function (facultyId) {
    const cache = FL.store.estimatedAssessmentByFaculty || {};
    const live = cache[facultyId];
    if (live && live.kraScores) {
      const simMeta = live.simulation && typeof live.simulation === "object" ? live.simulation : {};
      const kras = (live.kraScores || []).map(function (k) {
        const pts = k.estimatedPoints != null ? k.estimatedPoints : k.currentPoints;
        const kraId = k.kraId || k.id;
        return {
          id: kraId,
          code: String(kraId || "").toUpperCase(),
          name: k.label || kraId,
          credited: pts,
          earned: pts,
          maxPoints: k.maxPoints || k.targetPoints || 100,
          criteria: FL.faculty.criteriaRowsForKra(kraId, k),
          criteriaScores: k.criteriaScores || null,
          criterionADisplay: k.criterionADisplay || null
        };
      });
      const gaps = [{ tone: "info", text: "Estimated KRA totals from the unified PostgreSQL scoring engine." }];
      (simMeta.missingRequirements || []).forEach(function (item) {
        if (!item || !item.text) return;
        gaps.push({ tone: item.severity === "danger" ? "danger" : "warning", text: item.text });
      });
      (simMeta.areasToImprove || []).forEach(function (item) {
        if (!item || !item.guidance) return;
        gaps.push({ tone: "info", text: item.guidance });
      });
      return {
        faculty: FL.store.facultyById(facultyId),
        aggregate: {
          kras: kras,
          total: live.estimatedTotalKraPoints || 0,
          rawTotal: live.estimatedTotalKraPoints || 0,
          weightedScore: live.weightedEstimatedScore,
          weightBand: simMeta.weightBand || live.weightBand,
          appliedWeights: simMeta.appliedWeights
        },
        gaps: gaps,
        live: true
      };
    }
    return FL.scoring.simulation(facultyId);
  },

  loadUnifiedAssessmentWithTimeout: function (session, facultyId, timeoutMs) {
    const ms = timeoutMs || 45000;
    const load = FL.faculty.loadUnifiedAssessment(session, facultyId);
    return Promise.race([
      load,
      new Promise(function (_resolve, reject) {
        window.setTimeout(function () {
          reject(new Error("Assessment request timed out. Check that the Flask API is running."));
        }, ms);
      })
    ]);
  },

  loadUnifiedAssessment: function (session, facultyId) {
    FL.store.estimatedAssessmentByFaculty = FL.store.estimatedAssessmentByFaculty || {};
    if (session.role === "reviewer" && FL.store.usesLiveReviewerApi()) {
      return FL.store.loadEstimatedAssessment(facultyId);
    }
    if (session.role === "administrator" && FL.store.usesRealAdminApi()) {
      return FL.store.fetchAdminFacultyDetail(facultyId).then(function (data) {
        FL.store.evidenceComplianceByFaculty = FL.store.evidenceComplianceByFaculty || {};
        if (data.estimatedAssessment) {
          FL.store.estimatedAssessmentByFaculty[facultyId] = data.estimatedAssessment;
          if (data.estimatedAssessment.evidenceCompliance) {
            FL.store.evidenceComplianceByFaculty[facultyId] = data.estimatedAssessment.evidenceCompliance;
          }
        }
        if (data.evidenceCompliance) {
          FL.store.evidenceComplianceByFaculty[facultyId] = data.evidenceCompliance;
        }
        return data.estimatedAssessment || null;
      });
    }
    return Promise.resolve(null);
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

  listHtml: function (people, action, manage, showEvidenceMetrics) {
    if (!people.length) {
      return FL.ui.empty("No faculty records", manage ? "Add a faculty member to begin assignments." : "No faculty match this view.");
    }
    const live = manage && FL.store.isLiveAccountManagement();
    const metricsCols = showEvidenceMetrics
      ? `<th>Source PDFs</th><th>Semester evaluations</th><th>PDF document review</th>`
      : "";
    return `
      <table class="data">
        <thead>
          <tr>
            <th>Faculty</th>
            <th>Current rank</th>
            <th>Department</th>
            <th>Reviewer</th>
            <th>Status</th>
            ${metricsCols}
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${people.map(function (person) {
            let metricsCells = "";
            if (showEvidenceMetrics) {
              const semTotal = person.evaluationRecordsTotal || 0;
              const semVal = person.evaluationRecordsValidated || 0;
              const semPending = person.semesterEvaluationsPending != null
                ? person.semesterEvaluationsPending
                : (person.evaluationRecordsPending || 0);
              const pdfTotal = person.sourcePdfTotal != null ? person.sourcePdfTotal : (person.documentTotal || 0);
              const pdfPending = person.sourcePdfPendingWorkflow != null
                ? person.sourcePdfPendingWorkflow
                : (person.documentPending || 0);
              const semCell = semTotal
                ? `${FL.esc(String(semVal))}/${FL.esc(String(semTotal))} validated · ${semPending ? FL.esc(String(semPending)) + " pending" : "0 pending"}`
                : "—";
              metricsCells = `
              <td>${FL.esc(String(pdfTotal))}</td>
              <td>${semCell}</td>
              <td>${pdfPending ? FL.ui.badge("pending", String(pdfPending) + " pending") : FL.ui.badge("valid", "None pending")}</td>`;
            }
            return `<tr>
              <td><strong>${FL.esc(person.name || person.email || "Faculty")}</strong><div class="sub">${FL.esc(person.email || person.college || "")}</div></td>
              <td>${FL.esc(FL.faculty.displayRank(person))}</td>
              <td>${FL.esc(FL.faculty.displayDepartment(person))}</td>
              <td>${FL.esc(FL.faculty.reviewerLabel(person))}</td>
              <td>${FL.faculty.accountStatusCell(person)}</td>
              ${metricsCells}
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
      host.innerHTML = FL.faculty.listHtml(people, options.action, manage, options.showEvidenceMetrics);
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
    const facultyId = (params.get("id") || "").trim();
    const page = document.getElementById("page");
    if (!page) return;

    const showRetry = function (title, message, retryFn) {
      page.innerHTML = FL.ui.emptyWithRetry(title, message, "faculty-detail-retry");
      const btn = document.getElementById("faculty-detail-retry");
      if (btn && typeof retryFn === "function") {
        btn.addEventListener("click", retryFn);
      }
    };

    const paintDetail = function (person, detailOpts) {
      try {
        FL.faculty._paintDetail(session, person, page, detailOpts || {});
      } catch (paintErr) {
        if (typeof console !== "undefined" && console.error) {
          console.error("Faculty detail render failed:", paintErr);
        }
        showRetry(
          "Could not display faculty detail",
          (paintErr && paintErr.message) || "An unexpected error occurred while building this page.",
          function () { FL.faculty.renderDetail(session); }
        );
      }
    };

    const beginForPerson = function (person) {
      if (session.role === "reviewer" && String(person.reviewerId) !== String(session.userId)) {
        page.innerHTML = FL.ui.empty(
          "Faculty record not assigned",
          "This faculty member is not assigned to your review work."
        );
        return;
      }
      page.innerHTML = FL.ui.loading("Loading faculty detail", "Fetching assessment and documents…");
      let assessmentError = null;
      const assessmentLoad = FL.faculty.loadUnifiedAssessmentWithTimeout(session, person.id).catch(function (err) {
        assessmentError = err;
        return null;
      });
      const documentsLoad = FL.store.usesLiveDocuments()
        ? FL.store.loadFacultyDocuments(session, person.id).catch(function (docErr) {
          if (typeof console !== "undefined" && console.warn) {
            console.warn("Faculty documents could not be loaded for detail view:", docErr);
          }
          return null;
        })
        : Promise.resolve(null);
      Promise.all([assessmentLoad, documentsLoad]).then(function () {
        paintDetail(person, { assessmentError: assessmentError });
      });
    };

    const resolvePerson = function () {
      const person = facultyId ? FL.store.facultyById(facultyId) : null;
      if (!person) {
        if (session.role === "reviewer" && FL.store.usesLiveReviewerApi()) {
          showRetry(
            "Faculty record not found",
            facultyId
              ? "This faculty member is not in your assigned list, or the link may be outdated."
              : "Open faculty detail from Assigned Faculty so the profile id is included in the URL.",
            function () {
              page.innerHTML = FL.ui.loading("Loading faculty detail", "Refreshing assigned faculty…");
              FL.store.loadReviewerAssignedFaculty().then(resolvePerson).catch(function (err) {
                showRetry(
                  "Could not load assigned faculty",
                  (err && err.message) || "Start the Flask API on port 5000, then retry.",
                  resolvePerson
                );
              });
            }
          );
          return;
        }
        page.innerHTML = FL.ui.empty("Faculty record not found", "The faculty record is not available.");
        return;
      }
      beginForPerson(person);
    };

    if (session.role === "reviewer" && FL.store.usesLiveReviewerApi() && !FL.store.reviewerDirectoryLoaded) {
      page.innerHTML = FL.ui.loading("Loading faculty detail", "Loading your assigned faculty…");
      FL.store.loadReviewerAssignedFaculty().then(resolvePerson).catch(function (err) {
        showRetry(
          "Could not load assigned faculty",
          (err && err.message) || "Start the Flask API on port 5000, then retry.",
          function () { FL.faculty.renderDetail(session); }
        );
      });
      return;
    }
    resolvePerson();
  },

  _paintDetail: function (session, person, page, detailOpts) {
    detailOpts = detailOpts || {};
    const sim = FL.faculty.unifiedSimulation(person.id);
    if (!sim.faculty) sim.faculty = person;
    const compliance = FL.compliance(person.id);
    const reviewer = FL.store.userById(person.reviewerId);
    const docs = FL.store.documents.filter(function (doc) { return doc.facultyId === person.id; });
    const assessmentBanner = detailOpts.assessmentError
      ? `<div class="alert alert-warning" role="status">Estimated assessment could not be refreshed: ${FL.esc(detailOpts.assessmentError.message || "Request failed.")} KRA totals below may use cached or mock values.</div>`
      : "";
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
      ${assessmentBanner}
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
            <div class="card-head"><h2>Compliance</h2>${FL.ui.statusBadge(compliance.status === "On track" ? "valid" : compliance.status === "Incomplete" ? "invalid" : "reviewer-required")}</div>
            <p class="sub"><strong>${FL.esc(compliance.statusLabel || compliance.status)}</strong></p>
            ${compliance.semesterTotal
              ? FL.ui.progress(compliance.validated, compliance.semesterTotal, "Semester evaluations validated")
              : FL.ui.progress(compliance.validated, compliance.submitted || 0, "Validated evidence")}
            <ul class="plain">
              <li>Semester evaluations validated: ${compliance.semesterTotal ? compliance.validated + " / " + compliance.semesterTotal : "—"}</li>
              <li>Semester evaluations pending: ${compliance.semesterTotal ? (compliance.missing != null ? compliance.missing : "—") : "—"}</li>
              <li>Source PDFs pending document review: ${compliance.documentsPendingReview != null ? compliance.documentsPendingReview : "—"}</li>
              <li>Submitted source PDFs: ${compliance.submitted}</li>
            </ul>
            ${(compliance.notes || []).length
              ? `<div class="note">${compliance.notes.map(function (n) { return "<p>" + FL.esc(n) + "</p>"; }).join("")}</div>`
              : (compliance.documentsPendingReview && compliance.semesterTotal && compliance.validated === compliance.semesterTotal
                ? `<p class="note">Semester SET/SEF records are validated. Parent PDF document-level review is tracked separately and may still show as pending in the documents list.</p>`
                : "")}
          </article>
        </div>
      </section>
      <section class="tab-panel" data-panel="KRA Scores">
        <div class="stack">
          ${sim.aggregate.kras.map(function (kra) {
            return `<article class="card">
              <div class="card-head"><h2>${FL.esc(kra.code)} — ${FL.esc(kra.name)}</h2><strong>Estimated Score ${kra.credited != null ? kra.credited : "—"} / ${kra.maxPoints}</strong></div>
              ${kra.criterionADisplay && kra.criterionADisplay.displayLabel
                ? `<p class="sub">Criterion A: ${FL.esc(kra.criterionADisplay.displayLabel)}${kra.criterionADisplay.estimatedPoints != null ? " (" + FL.esc(String(kra.criterionADisplay.estimatedPoints)) + ")" : ""}</p>`
                : ""}
              ${FL.ui.progress(kra.credited, kra.maxPoints, "Estimated score within the KRA maximum")}
              <div class="table-wrap"><table class="data">
                <thead><tr><th>Criterion</th><th>Maximum</th><th>Estimated score</th></tr></thead>
                <tbody>${(kra.criteria || []).map(function (criterion) {
                  return `<tr><td>${FL.esc(criterion.name)}</td><td>${FL.esc(criterion.maxLabel != null ? criterion.maxLabel : String(criterion.maxPoints) + (criterion.bonus ? " bonus" : ""))}</td><td>${FL.esc(String(criterion.earned))}</td></tr>`;
                }).join("") || `<tr><td colspan="3">Criterion breakdown is estimated at the KRA level from PostgreSQL. Open Evidence Workspace for document-level scores.</td></tr>`}</tbody>
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
            const wf = doc.documentWorkflowStatus || doc.status;
            const statusCell = FL.documents.displayReviewStatus(doc)
              + (wf !== (doc.reviewDisplayStatus || doc.status)
                ? `<div class="sub">PDF workflow: ${FL.ui.statusBadge(wf)}</div>` : "");
            return `<tr><td>${FL.esc(doc.id)}</td><td>${FL.esc(doc.name)}</td><td>${FL.esc(kra)}</td><td>${statusCell}</td><td>${FL.esc(score)}</td><td><a class="btn btn-small btn-ghost" href="${FL.faculty.documentHref(doc.id)}">Open</a></td></tr>`;
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
    const faculty = sim.faculty || {};
    return `
      <div class="callout">
        <strong>Simulation Result</strong>
        <p>This is an estimate based on computed KRA scores and uploaded documentary evidence. FacultyLink is a preparatory and evaluation-support system. It does not replace the official evaluation conducted by authorized committees, and it does not determine the number of sub-ranks.</p>
      </div>
      <div class="stat-grid">
        <article class="stat"><span>Current rank</span><strong>${FL.esc(faculty.rank || "—")}</strong></article>
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
  const mountList = function (people) {
    FL.faculty.renderList({
      eyebrow: "Assignments",
      title: "Assigned Faculty",
      lede: "Faculty assigned to you. Semester SET/SEF validation is separate from source PDF document review.",
      action: "Open Faculty",
      people: people,
      showEvidenceMetrics: !!FL.store.usesLiveReviewerApi()
    });
  };
  if (FL.store.usesLiveReviewerApi()) {
    const page = document.getElementById("page");
    page.innerHTML = FL.ui.loading("Loading assigned faculty", "Fetching evidence counts from PostgreSQL.");
    FL.store.loadReviewerFacultyDirectory({ page: 1, pageSize: 100, sort: "name" }).then(function (data) {
      const rows = (data && data.faculty) || [];
      const byId = {};
      FL.store.assignedFacultyForReviewer(session).forEach(function (p) { byId[p.id] = p; });
      rows.forEach(function (row) {
        byId[row.id] = Object.assign({}, byId[row.id] || {}, row);
      });
      mountList(Object.keys(byId).map(function (id) { return byId[id]; }).sort(function (a, b) {
        return (a.name || "").localeCompare(b.name || "");
      }));
    }).catch(function (err) {
      page.innerHTML = FL.ui.empty("Could not load faculty directory", err.message || "Try again.");
    });
    return;
  }
  mountList(FL.store.assignedFacultyForReviewer(session));
};

FL.pages["admin-faculty-detail"] = function (session) { FL.faculty.renderDetail(session); };
FL.pages["reviewer-faculty-detail"] = function (session) { FL.faculty.renderDetail(session); };
