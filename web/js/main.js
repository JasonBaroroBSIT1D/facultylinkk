window.FL = window.FL || {};
FL.pages = FL.pages || {};

/* Responsive helpers: label table cells with their column header so that, on small
   screens, CSS can show each row as a stacked card. Works for every table the pages render. */
FL.responsive = {
  labelTables: function (root) {
    (root || document).querySelectorAll("table.data").forEach(function (table) {
      const heads = Array.prototype.map.call(table.querySelectorAll("thead th"), function (th) {
        return th.textContent.trim();
      });
      if (!heads.length) return;
      table.querySelectorAll("tbody tr").forEach(function (row) {
        Array.prototype.forEach.call(row.children, function (cell, index) {
          if (cell.tagName === "TD" && heads[index] && cell.getAttribute("data-label") !== heads[index]) {
            cell.setAttribute("data-label", heads[index]);
          }
        });
      });
    });
  },
  watch: function (host) {
    if (!host) return;
    const run = function () { FL.responsive.labelTables(host); };
    run();
    if (!window.MutationObserver) return;
    let queued = false;
    new MutationObserver(function () {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(function () { queued = false; run(); });
    }).observe(host, { childList: true, subtree: true });
  }
};

FL.nav = {
  administrator: [
    { id: "admin-dashboard", href: "dashboard.html", label: "Dashboard" },
    { id: "admin-faculty", href: "faculty.html", label: "Faculty" },
    { id: "admin-documents", href: "documents.html", label: "Evidence Workspace" },
    { id: "admin-reviewers", href: "reviewers.html", label: "Reviewers" },
    { id: "admin-kra", href: "kra-configuration.html", label: "KRA Configuration" },
    { id: "admin-schedule", href: "evaluation-schedule.html", label: "Evaluation Schedule" },
    { id: "admin-reports", href: "reports.html", label: "Reports" },
    { id: "admin-notifications", href: "notifications.html", label: "Notifications" },
    { id: "admin-audit", href: "audit-log.html", label: "Audit Log" },
    { id: "admin-profile", href: "profile.html", label: "Profile" }
  ],
  reviewer: [
    { id: "reviewer-dashboard", href: "dashboard.html", label: "Dashboard" },
    { id: "reviewer-documents", href: "documents.html", label: "Evidence Workspace" },
    { id: "reviewer-faculty", href: "assigned-faculty.html", label: "Assigned Faculty" },
    { id: "reviewer-kra", href: "kra-reference.html", label: "Official KRA Scoring Reference" },
    { id: "reviewer-schedule", href: "evaluation-schedule.html", label: "Evaluation Schedule" },
    { id: "reviewer-notifications", href: "notifications.html", label: "Notifications" },
    { id: "reviewer-profile", href: "profile.html", label: "Profile" }
  ]
};

FL.crumbs = {
  "admin-dashboard": ["Administrator", "Dashboard"],
  "admin-faculty": ["Administrator", "Faculty"],
  "admin-faculty-detail": ["Administrator", "Faculty", "Faculty Detail"],
  "admin-documents": ["Administrator", "Evidence Workspace"],
  "admin-document-view": ["Administrator", "Documents", "Document Review"],
  "admin-reviewers": ["Administrator", "Reviewers"],
  "admin-kra": ["Administrator", "KRA Configuration"],
  "admin-schedule": ["Administrator", "Evaluation Schedule"],
  "admin-reports": ["Administrator", "Reports & Analytics"],
  "admin-notifications": ["Administrator", "Notifications"],
  "admin-audit": ["Administrator", "Audit Log"],
  "admin-profile": ["Administrator", "My Profile"],
  "reviewer-dashboard": ["Reviewer", "Dashboard"],
  "reviewer-documents": ["Reviewer", "Evidence Workspace"],
  "reviewer-review": ["Reviewer", "Evidence Workspace", "Document Review"],
  "reviewer-queue": ["Reviewer", "Evidence Workspace"],
  "reviewer-faculty": ["Reviewer", "Assigned Faculty"],
  "reviewer-faculty-detail": ["Reviewer", "Assigned Faculty", "Faculty Detail"],
  "reviewer-kra": ["Reviewer", "Official KRA Scoring Reference"],
  "reviewer-schedule": ["Reviewer", "Evaluation Schedule"],
  "reviewer-notifications": ["Reviewer", "Notifications"],
  "reviewer-profile": ["Reviewer", "My Profile"]
};

FL.layout = {
  mount: function (session, page) {
    const user = FL.store.userById(session.userId) || (FL.auth.cachedUser && FL.auth.cachedUser()) || {
      id: session.userId,
      name: "FacultyLink User",
      role: session.role
    };
    const role = session.role;
    const items = FL.nav[role];
    const unread = FL.notifications.unreadCount(user);
    const crumbs = FL.crumbs[page] || ["FacultyLink"];
    const app = document.getElementById("app");
    app.innerHTML = `
      <div class="shell">
        <aside class="sidebar" id="sidebar" aria-label="Site navigation">
          <button class="drawer-close" type="button" id="drawer-close" aria-label="Close navigation">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
          </button>
          <a class="brand" href="${FL.esc(items[0].href)}">
            <span class="brand-crest"><img src="${FL.esc(FL.assets.image("facultylink-mark.png"))}" alt="FacultyLink" width="56" height="56"></span>
            <span class="brand-copy"><strong>Faculty<span>Link</span></strong><small>${FL.esc(FL.institution.campus)}</small></span>
          </a>
          <p class="role-label">${role === "administrator" ? "Administrator" : "Reviewer"}</p>
          <nav class="side-nav" aria-label="Primary">
            ${items.map(function (item) {
              const active = item.id === page || (page.indexOf(item.id) === 0 && item.id !== "admin-dashboard" && item.id !== "reviewer-dashboard");
              const facultyActive = (page === "admin-faculty-detail" && item.id === "admin-faculty") || (page === "reviewer-faculty-detail" && item.id === "reviewer-faculty") || (page === "reviewer-review" && item.id === "reviewer-documents") || (page === "admin-document-view" && item.id === "admin-documents") || (page === "reviewer-queue" && item.id === "reviewer-documents");
              const icon = FL.navIcons ? FL.navIcons.markup(item.id) : "";
              const badge = item.id.endsWith("notifications") && unread ? `<span class="nav-count">${unread}</span>` : "";
              return `<a class="${active || facultyActive ? "is-active" : ""}" href="${FL.esc(item.href)}" title="${FL.esc(item.label)}">${icon}<span class="nav-label">${FL.esc(item.label)}</span>${badge}</a>`;
            }).join("")}
          </nav>
          <button class="sidebar-collapse" type="button" id="sidebar-collapse" aria-label="Collapse sidebar" aria-pressed="false">
            ${FL.navIcons ? FL.navIcons.icon("panel-left") : ""}<span class="nav-label">Collapse</span>
          </button>
          <button class="side-logout" type="button" id="logout-side">${FL.navIcons ? FL.navIcons.icon("log-out") : ""}<span class="nav-label">Log out</span></button>
        </aside>
        <div class="backdrop" id="backdrop" hidden></div>
        <div class="workspace">
          <header class="topbar">
            <button class="icon-btn menu-btn" type="button" id="menu-btn" aria-label="Open navigation" aria-controls="sidebar" aria-expanded="false"><span class="burger" aria-hidden="true"></span></button>
            <nav class="crumbs" aria-label="Breadcrumb">${crumbs.map(function (part, index) {
              return `<span>${FL.esc(part)}</span>${index < crumbs.length - 1 ? "<span class='sep'>/</span>" : ""}`;
            }).join("")}</nav>
            <div class="top-actions">
              <div class="notice-wrap">
                <button class="icon-btn" type="button" id="notice-btn" aria-label="Notifications">${unread ? `<span class="dot">${unread}</span>` : ""}<svg class="bell" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9a6 6 0 0 1 12 0c0 6 2.5 7.5 2.5 7.5h-17S6 15 6 9z"/><path d="M10 20a2 2 0 0 0 4 0"/></svg><span class="btn-text">Alerts</span></button>
                <div class="notice-pop" id="notice-pop" hidden></div>
              </div>
              <a class="user-chip" href="profile.html">
                <span class="avatar">${FL.esc(user.name.split(" ").map(function (p) { return p[0]; }).slice(0, 2).join(""))}</span>
                <span><strong>${FL.esc(user.name)}</strong><small>${role === "administrator" ? "Administrator" : "Reviewer"}</small></span>
              </a>
              <button class="btn btn-ghost btn-small" type="button" id="logout-top">Log out</button>
            </div>
          </header>
          <main class="page" id="page" tabindex="-1">${FL.ui.loading("Opening page")}</main>
        </div>
      </div>`;
    const sidebar = document.getElementById("sidebar");
    const collapseKey = "facultylink.sidebarCollapsed";
    const collapseBtn = document.getElementById("sidebar-collapse");
    if (localStorage.getItem(collapseKey) === "1") {
      sidebar.classList.add("is-collapsed");
      if (collapseBtn) collapseBtn.setAttribute("aria-pressed", "true");
    }
    if (collapseBtn) {
      collapseBtn.addEventListener("click", function () {
        const collapsed = sidebar.classList.toggle("is-collapsed");
        collapseBtn.setAttribute("aria-pressed", collapsed ? "true" : "false");
        localStorage.setItem(collapseKey, collapsed ? "1" : "0");
      });
    }
    const backdrop = document.getElementById("backdrop");
    const menuBtn = document.getElementById("menu-btn");
    const drawerQuery = window.matchMedia("(max-width: 1023px)");
    const setDrawer = function (open, restoreFocus) {
      sidebar.classList.toggle("is-open", open);
      backdrop.hidden = !open;
      document.body.classList.toggle("nav-open", open);
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) {
        document.getElementById("drawer-close").focus();
      } else if (restoreFocus && drawerQuery.matches) {
        menuBtn.focus();
      }
    };
    const closeMenu = function () { setDrawer(false, true); };
    menuBtn.addEventListener("click", function () { setDrawer(true); });
    document.getElementById("drawer-close").addEventListener("click", closeMenu);
    backdrop.addEventListener("click", closeMenu);
    document.querySelectorAll(".side-nav a").forEach(function (link) {
      link.addEventListener("click", function () { setDrawer(false, false); });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && sidebar.classList.contains("is-open")) closeMenu();
    });
    const onWide = function (query) { if (!query.matches) setDrawer(false, false); };
    if (drawerQuery.addEventListener) drawerQuery.addEventListener("change", function (query) { if (!query.matches) setDrawer(false, false); });
    else if (drawerQuery.addListener) drawerQuery.addListener(onWide);
    FL.responsive.watch(document.getElementById("page"));
    const logout = function () {
      FL.ui.modal({
        title: "Log out of FacultyLink",
        body: "<p>You will return to the sign-in page.</p>",
        confirmLabel: "Log out",
        onClose: function (ok) { if (ok) FL.auth.signOut(); }
      });
    };
    document.getElementById("logout-side").addEventListener("click", logout);
    document.getElementById("logout-top").addEventListener("click", logout);
    const pop = document.getElementById("notice-pop");
    document.getElementById("notice-btn").addEventListener("click", function () {
      if (!pop.hidden) { pop.hidden = true; return; }
      const latest = FL.notifications.visible(user).slice(0, 5);
      pop.innerHTML = latest.length ? latest.map(function (item) {
        return `<a href="notifications.html"><strong>${FL.esc(item.title)}</strong><span>${FL.esc(item.body)}</span></a>`;
      }).join("") + `<a class="pop-all" href="notifications.html">Open notifications</a>` : `<p class="pop-empty">No notifications</p>`;
      pop.hidden = false;
    });
    document.addEventListener("click", function (event) {
      if (!event.target.closest(".notice-wrap")) pop.hidden = true;
    });
  }
};

FL.boot = function () {
  const page = document.body.dataset.page;
  if (page === "login") {
    if (FL.pages.login) FL.pages.login();
    return;
  }
  if (page === "forgot-password") {
    if (FL.pages.forgotPassword) FL.pages.forgotPassword();
    return;
  }
  const role = document.body.dataset.role;
  FL.auth.restore().then(function (session) {
    if (!session) {
      window.location.replace(FL.auth.loginUrl());
      return null;
    }
    if (role && session.role !== role) {
      window.location.replace(FL.auth.home(session.role));
      return null;
    }
    if (session.mustChangePassword) {
      FL.auth.requirePasswordChange();
      return null;
    }
    return FL.store.load().catch(function () {
      /* Mock workspace data is optional; Flask session is authoritative */
      return null;
    }).then(function () {
      FL.auth.mergeUserIntoStore(session);
      if (FL.store.usesRealAdminApi() && (page === "admin-faculty" || page === "admin-reviewers")) {
        FL.store.clearAccountMocksForLiveAdmin();
      }
      const reviewerPages = [
        "reviewer-dashboard",
        "reviewer-faculty",
        "reviewer-faculty-detail",
        "reviewer-profile"
      ];
      const documentPages = [
        "admin-documents",
        "admin-document-view",
        "reviewer-documents",
        "reviewer-queue",
        "reviewer-review"
      ];
      const bootReviewer = session.role === "reviewer"
        && FL.store.usesLiveReviewerApi()
        && reviewerPages.indexOf(page) !== -1;
      const bootDocuments = FL.store.usesLiveDocuments()
        && documentPages.indexOf(page) !== -1;
      const finishBoot = function () {
        FL.layout.mount(session, page);
        const render = FL.pages[page];
        if (render) render(session);
        else document.getElementById("page").innerHTML = FL.ui.empty("Page unavailable", "This page is not part of the FacultyLink web application.");
      };
      const bootDocsThenRender = function () {
        const chain = [];
        if (session.role === "administrator" && bootDocuments) {
          chain.push(FL.store.loadAdminFaculty().catch(function () { return null; }));
        }
        if (session.role === "reviewer" && (bootReviewer || bootDocuments)) {
          chain.push(FL.store.loadReviewerAssignedFaculty().catch(function () {
            FL.store.reviewerDirectoryLoaded = false;
            FL.store.reviewerFaculty = [];
            return null;
          }));
        }
        if (bootDocuments) {
          chain.push(FL.store.loadLiveDocuments(session).catch(function (error) {
            FL.ui.toast(error.message || "Could not load documents from PostgreSQL.", "danger");
            return null;
          }));
        }
        if (!chain.length) {
          finishBoot();
          return;
        }
        Promise.all(chain).then(finishBoot);
      };
      if (bootReviewer && !bootDocuments) {
        return FL.store.loadReviewerAssignedFaculty().then(finishBoot).catch(function (error) {
          FL.store.reviewerDirectoryLoaded = false;
          FL.store.reviewerFaculty = [];
          finishBoot();
          FL.ui.toast(error.message || "Could not load assigned faculty from PostgreSQL.", "danger");
        });
      }
      bootDocsThenRender();
    });
  }).catch(function (error) {
    const app = document.getElementById("app");
    if (!app) return;
    if (error && error.status) {
      window.location.replace(FL.auth.loginUrl());
      return;
    }
    app.innerHTML = FL.ui.empty(
      "Unable to reach FacultyLink API",
      "Start the Flask backend on port 5000 and reload. Mock workspace data was not loaded."
    );
  });
};

document.addEventListener("DOMContentLoaded", FL.boot);
