/**
 * Frontend-only API simulation using localStorage + sessionStorage.
 * Browser-only mock API (localStorage). No network requests.
 */
window.FL = window.FL || {};

FL.mock = {
  stateKey: "facultylink.mockState",
  sessionKey: "facultylink.session",

  loadState: function () {
    try {
      const raw = localStorage.getItem(this.stateKey);
      if (raw) return JSON.parse(raw);
    } catch (error) {
      /* use seed */
    }
    const seed = FL.mockSeed ? FL.mockSeed() : { users: [], faculty: [], documents: [], notifications: [], audit: [], evaluationPeriods: [], kraSettings: {}, simulations: [] };
    this.saveState(seed);
    return seed;
  },

  saveState: function (state) {
    localStorage.setItem(this.stateKey, JSON.stringify(state));
  },

  session: function () {
    try {
      return JSON.parse(sessionStorage.getItem(this.sessionKey) || "null");
    } catch (error) {
      return null;
    }
  },

  setSession: function (session) {
    if (session) sessionStorage.setItem(this.sessionKey, JSON.stringify(session));
    else sessionStorage.removeItem(this.sessionKey);
  },

  userResponse: function (user) {
    if (!user) return null;
    return {
      id: user.id,
      email: user.email,
      role: user.role,
      name: user.name,
      office: user.office,
      contact: user.contact,
      specialization: user.specialization,
      mustChangePassword: !!user.mustChangePassword
    };
  },

  findUserByIdentity: function (state, identity) {
    const key = String(identity || "").trim().toLowerCase();
    return state.users.find(function (user) {
      return user.email.toLowerCase() === key || user.id === key;
    }) || null;
  },

  handle: function (method, url, body) {
    const state = this.loadState();
    const path = String(url || "").split("?")[0];

    if (method === "GET" && path === "/api/session") {
      const session = this.session();
      if (!session) return { user: null, session: null };
      const user = state.users.find(function (u) { return u.id === session.userId; });
      return { user: this.userResponse(user), session: session };
    }

    if (method === "POST" && path === "/api/login") {
      const user = this.findUserByIdentity(state, body && body.identity);
      if (!user || user.password !== (body && body.password)) {
        const error = new Error("The email or password is incorrect.");
        error.status = 401;
        throw error;
      }
      const session = {
        userId: user.id,
        role: user.role,
        mustChangePassword: !!user.mustChangePassword
      };
      this.setSession(session);
      return session;
    }

    if (method === "POST" && path === "/api/logout") {
      this.setSession(null);
      return { ok: true };
    }

    if (method === "POST" && path === "/api/forgot-password") {
      const email = body && body.email ? String(body.email).trim().toLowerCase() : "";
      const known = state.users.some(function (u) { return u.email.toLowerCase() === email; });
      return {
        emailSent: false,
        message: known
          ? "Password recovery is simulated in this frontend build. Use your demo credentials or contact the institution administrator."
          : "If that address is registered, instructions would be sent. In this demo, no email is sent."
      };
    }

    if (method === "POST" && path === "/api/account/password") {
      const session = this.session();
      if (!session) {
        const error = new Error("Sign in required.");
        error.status = 401;
        throw error;
      }
      const user = state.users.find(function (u) { return u.id === session.userId; });
      if (!user || user.password !== (body && body.currentPassword)) {
        const error = new Error("The current password is incorrect.");
        error.status = 400;
        throw error;
      }
      user.password = body.newPassword;
      user.mustChangePassword = false;
      session.mustChangePassword = false;
      this.setSession(session);
      this.saveState(state);
      return { ok: true };
    }

    if (method === "GET" && path === "/api/state") {
      return {
        documents: state.documents,
        faculty: state.faculty,
        users: state.users.map(function (u) { return FL.mock.userResponse(u); }),
        notifications: state.notifications,
        audit: state.audit,
        evaluationPeriods: state.evaluationPeriods,
        kraSettings: state.kraSettings,
        simulations: state.simulations || []
      };
    }

    if (method === "PATCH" && path === "/api/profile") {
      const session = this.session();
      const user = state.users.find(function (u) { return u.id === session.userId; });
      if (!user) throw Object.assign(new Error("User not found."), { status: 404 });
      user.office = body.office;
      user.contact = body.contact;
      user.specialization = body.specialization;
      this.saveState(state);
      return { user: this.userResponse(user) };
    }

    if (method === "PUT" && path.indexOf("/api/documents/") === 0) {
      const id = decodeURIComponent(path.slice("/api/documents/".length));
      const index = state.documents.findIndex(function (d) { return d.id === id; });
      if (index < 0) throw Object.assign(new Error("Document not found."), { status: 404 });
      state.documents[index] = Object.assign({}, state.documents[index], body);
      this.saveState(state);
      return state.documents[index];
    }

    if (method === "POST" && path.indexOf("/api/documents/") === 0 && path.endsWith("/correct-metadata")) {
      return { ok: true, simulated: true };
    }

    if (method === "POST" && path.match(/^\/api\/faculty\/[^/]+\/reviewer$/)) {
      const facultyId = decodeURIComponent(path.split("/")[3]);
      const person = state.faculty.find(function (f) { return f.id === facultyId; });
      if (!person) throw Object.assign(new Error("Faculty was not found."), { status: 404 });
      person.reviewerId = body.reviewerId || "";
      this.saveState(state);
      return { faculty: person };
    }

    if (method === "POST" && path === "/api/faculty") {
      const id = "fac-" + Date.now();
      const row = Object.assign({ id: id, status: "Active", reviewerId: "" }, body);
      state.faculty.push(row);
      this.saveState(state);
      return { faculty: row };
    }

    if (method === "DELETE" && path.indexOf("/api/faculty/") === 0) {
      const facultyId = decodeURIComponent(path.slice("/api/faculty/".length));
      state.faculty = state.faculty.filter(function (f) { return f.id !== facultyId; });
      state.documents = state.documents.filter(function (d) { return d.facultyId !== facultyId; });
      this.saveState(state);
      return { ok: true };
    }

    if (method === "POST" && path === "/api/reviewers") {
      const id = "user-reviewer-" + Date.now();
      const row = Object.assign({
        id: id,
        role: "reviewer",
        password: "Reviewer@2026",
        mustChangePassword: true
      }, body);
      state.users.push(row);
      this.saveState(state);
      return { reviewer: this.userResponse(row), temporaryPassword: row.password };
    }

    if (method === "DELETE" && path.indexOf("/api/reviewers/") === 0) {
      const reviewerId = decodeURIComponent(path.slice("/api/reviewers/".length));
      state.users = state.users.filter(function (u) { return u.id !== reviewerId; });
      state.faculty.forEach(function (f) {
        if (f.reviewerId === reviewerId) f.reviewerId = "";
      });
      this.saveState(state);
      return { ok: true };
    }

    if (method === "POST" && (path.indexOf("/api/faculty/") === 0 || path.indexOf("/api/reviewers/") === 0) && path.endsWith("/credentials")) {
      return { message: "Simulated: credentials would be emailed in production.", emailSent: false };
    }

    if (method === "POST" && path === "/api/notifications") {
      const item = Object.assign({ id: "note-" + Date.now(), read: false, createdAt: new Date().toISOString() }, body);
      state.notifications.unshift(item);
      this.saveState(state);
      return item;
    }

    if (method === "PATCH" && path.indexOf("/api/notifications/") === 0) {
      const id = decodeURIComponent(path.slice("/api/notifications/".length));
      const note = state.notifications.find(function (n) { return n.id === id; });
      if (note) note.read = !!body.read;
      this.saveState(state);
      return note || {};
    }

    if (method === "PATCH" && path === "/api/notifications") {
      (body.ids || []).forEach(function (id) {
        const note = state.notifications.find(function (n) { return n.id === id; });
        if (note) note.read = true;
      });
      this.saveState(state);
      return { ok: true };
    }

    if (method === "PUT" && path === "/api/kra-settings") {
      state.kraSettings = Object.assign({}, state.kraSettings, body);
      this.saveState(state);
      return { kraSettings: state.kraSettings };
    }

    if (method === "PUT" && path === "/api/evaluation-periods") {
      state.evaluationPeriods = (body && body.periods) || [];
      this.saveState(state);
      return { evaluationPeriods: state.evaluationPeriods };
    }

    if (method === "POST" && path === "/api/audit") {
      const entry = Object.assign({ id: "audit-" + Date.now(), createdAt: new Date().toISOString() }, body);
      state.audit.unshift(entry);
      this.saveState(state);
      return entry;
    }

    const error = new Error("Mock API route not implemented: " + method + " " + path);
    error.status = 501;
    throw error;
  }
};

FL.api = {
  send: function (method, url, body) {
    return Promise.resolve().then(function () {
      if (FL.apiClient && FL.apiClient.handles(method, url)) {
        return FL.apiClient.send(method, url, body);
      }
      return FL.mock.handle(method, url, body);
    }).catch(function (error) {
      if (error.status) return Promise.reject(error);
      const wrapped = new Error(error.message || "Request failed.");
      wrapped.status = 500;
      return Promise.reject(wrapped);
    });
  }
};
