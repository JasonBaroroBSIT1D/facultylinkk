/**
 * HTTP client for Flask authentication. Domain routes still use FL.mock until Phase 4+.
 * Tokens: sessionStorage only (tab-scoped; refresh token not in localStorage).
 */
window.FL = window.FL || {};

FL.apiClient = {
  accessKey: "facultylink.accessToken",
  refreshKey: "facultylink.refreshToken",
  userKey: "facultylink.user",
  sessionKey: "facultylink.session",

  authRoutes: {
    "GET /api/session": { method: "GET", path: "/api/auth/session" },
    "POST /api/login": { method: "POST", path: "/api/auth/login" },
    "POST /api/logout": { method: "POST", path: "/api/auth/logout" },
    "POST /api/account/password": { method: "POST", path: "/api/auth/change-password" },
    "POST /api/forgot-password": { method: "POST", path: "/api/auth/forgot-password" },
    "POST /api/forgot-password/verify": { method: "POST", path: "/api/auth/forgot-password/verify" },
    "POST /api/forgot-password/reset": { method: "POST", path: "/api/auth/forgot-password/reset" }
  },

  handles: function (method, url) {
    const path = String(url || "").split("?")[0];
    return !!this.authRoutes[method + " " + path];
  },

  getAccessToken: function () {
    return sessionStorage.getItem(this.accessKey) || "";
  },

  getRefreshToken: function () {
    return sessionStorage.getItem(this.refreshKey) || "";
  },

  clearTokens: function () {
    sessionStorage.removeItem(this.accessKey);
    sessionStorage.removeItem(this.refreshKey);
    sessionStorage.removeItem(this.userKey);
    sessionStorage.removeItem(this.sessionKey);
  },

  storeAuthPayload: function (data) {
    if (data.accessToken) sessionStorage.setItem(this.accessKey, data.accessToken);
    if (data.refreshToken) sessionStorage.setItem(this.refreshKey, data.refreshToken);
    if (data.user) sessionStorage.setItem(this.userKey, JSON.stringify(data.user));
    if (data.session) {
      sessionStorage.setItem(this.sessionKey, JSON.stringify(data.session));
    }
  },

  hasAccessToken: function () {
    return !!this.getAccessToken();
  },

  cachedUser: function () {
    try {
      return JSON.parse(sessionStorage.getItem(this.userKey) || "null");
    } catch (error) {
      return null;
    }
  },

  mergeUserIntoStore: function (session) {
    if (!session || !FL.store) return;
    const user = this.cachedUser();
    if (!user || user.id !== session.userId) return;
    const exists = FL.store.users.some(function (u) { return u.id === user.id; });
    if (!exists) FL.store.users.push(user);
  },

  mapBody: function (legacyPath, body) {
    if (legacyPath === "/api/login") {
      return {
        email: (body && (body.identity || body.email)) || "",
        password: body && body.password,
        client: "web"
      };
    }
    return body || {};
  },

  mapResponse: function (legacyPath, data) {
    if (legacyPath === "/api/login") {
      this.storeAuthPayload(data);
      return data.session || null;
    }
    if (legacyPath === "/api/session") {
      if (data.user) sessionStorage.setItem(this.userKey, JSON.stringify(data.user));
      if (data.session) sessionStorage.setItem(this.sessionKey, JSON.stringify(data.session));
      return data;
    }
    if (legacyPath === "/api/logout") {
      this.clearTokens();
      return { ok: true };
    }
    if (legacyPath === "/api/forgot-password") {
      return {
        ok: data.ok,
        message: data.message,
        emailSent: !!data.ok,
        resendAfterSeconds: data.resendAfterSeconds,
        expiresInSeconds: data.expiresInSeconds
      };
    }
    if (legacyPath === "/api/forgot-password/verify") {
      return { resetToken: data.resetToken };
    }
    if (legacyPath === "/api/account/password" && data.accessToken) {
      this.storeAuthPayload(data);
    }
    return data;
  },

  adminRequestBlob: function (method, path) {
    const self = this;
    const access = this.getAccessToken();
    if (!access) {
      return Promise.reject(Object.assign(new Error("Sign in required."), { status: 401 }));
    }
    function doRequest(token) {
      const headers = { Accept: "*/*" };
      if (token) headers.Authorization = "Bearer " + token;
      return fetch(FL.apiConfig.baseUrl + path, {
        method: method,
        headers: headers,
        credentials: "omit"
      }).then(function (response) {
        if (!response.ok) {
          return response.text().then(function (text) {
            const err = new Error(text || "Request failed.");
            err.status = response.status;
            throw err;
          });
        }
        return response.blob();
      });
    }
    return doRequest(access).catch(function (error) {
      if (error.status !== 401 || !self.getRefreshToken()) return Promise.reject(error);
      return self.refreshAccessToken().then(function (newToken) {
        return doRequest(newToken);
      });
    });
  },

  adminRequest: function (method, path, body) {
    const self = this;
    const access = this.getAccessToken();
    if (!access) {
      return Promise.reject(Object.assign(new Error("Sign in required."), { status: 401 }));
    }
    function doRequest(token) {
      return self.request(method, path, body, token);
    }
    return doRequest(access).catch(function (error) {
      if (error.status !== 401 || !self.getRefreshToken()) return Promise.reject(error);
      return self.refreshAccessToken().then(function (newToken) {
        return doRequest(newToken);
      });
    });
  },

  request: function (method, apiPath, body, accessToken) {
    const base = FL.apiConfig.baseUrl;
    const headers = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (accessToken) headers.Authorization = "Bearer " + accessToken;

    return fetch(base + apiPath, {
      method: method,
      headers: headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: "omit"
    }).then(function (response) {
      return response.text().then(function (text) {
        let payload = null;
        if (text) {
          try {
            payload = JSON.parse(text);
          } catch (error) {
            payload = { message: text };
          }
        }
        if (!response.ok) {
          const err = new Error((payload && payload.message) || "Request failed.");
          err.status = response.status;
          throw err;
        }
        return payload;
      });
    });
  },

  refreshAccessToken: function () {
    const refresh = this.getRefreshToken();
    if (!refresh) return Promise.reject(new Error("Session expired."));
    const self = this;
    return this.request("POST", "/api/auth/refresh", undefined, refresh).then(function (data) {
      if (data.accessToken) sessionStorage.setItem(self.accessKey, data.accessToken);
      return data.accessToken;
    });
  },

  send: function (method, url, body) {
    const raw = String(url || "");
    const path = raw.split("?")[0];
    const route = this.authRoutes[method + " " + path];
    if (!route) {
      const error = new Error("Auth route not mapped: " + method + " " + path);
      error.status = 501;
      return Promise.reject(error);
    }

    const mappedBody = this.mapBody(path, body);
    const self = this;
    const access = this.getAccessToken();

    function doRequest(token) {
      let apiPath = route.path;
      if (route.method === "GET" && raw.indexOf("?") !== -1) {
        apiPath = route.path + raw.slice(raw.indexOf("?"));
      }
      return self.request(route.method, apiPath, route.method === "GET" ? undefined : mappedBody, token || access)
        .then(function (data) {
          return self.mapResponse(path, data);
        });
    }

    return doRequest(access).catch(function (error) {
      if (error.status !== 401 || path === "/api/login" || !self.getRefreshToken()) {
        return Promise.reject(error);
      }
      return self.refreshAccessToken().then(function (newToken) {
        return doRequest(newToken);
      });
    });
  }
};
