window.FL = window.FL || {};

FL.auth = {
  sessionKey: "facultylink.session",
  rememberKey: "facultylink.remember",

  cachedUser: function () {
    return FL.apiClient ? FL.apiClient.cachedUser() : null;
  },

  mergeUserIntoStore: function (session) {
    if (FL.apiClient) FL.apiClient.mergeUserIntoStore(session);
  },

  current: function () {
    try {
      return JSON.parse(sessionStorage.getItem(this.sessionKey) || "null");
    } catch (error) {
      return null;
    }
  },

  home: function (role) {
    const here = window.location.pathname.replace(/\\/g, "/");
    const inAdmin = /\/pages\/admin\//.test(here);
    const inReviewer = /\/pages\/reviewer\//.test(here);
    const inPublic = /\/pages\/public\//.test(here);

    if (role === "administrator") {
      if (inAdmin) return "dashboard.html";
      if (inPublic || inReviewer) return "../admin/dashboard.html";
      return "pages/admin/dashboard.html";
    }
    if (role === "reviewer") {
      if (inReviewer) return "dashboard.html";
      if (inPublic || inAdmin) return "../reviewer/dashboard.html";
      return "pages/reviewer/dashboard.html";
    }
    if (inAdmin || inReviewer) return "../public/login.html";
    if (inPublic) return "login.html";
    return "pages/public/login.html";
  },

  loginUrl: function () {
    const here = window.location.pathname.replace(/\\/g, "/");
    if (/\/pages\/admin\//.test(here) || /\/pages\/reviewer\//.test(here)) {
      return "../public/login.html";
    }
    if (/\/pages\/public\//.test(here)) return "login.html";
    return "pages/public/login.html";
  },

  restore: function () {
    if (!FL.apiClient || !FL.apiClient.hasAccessToken()) {
      return Promise.resolve(null);
    }
    return FL.api.send("GET", "/api/session").then(function (data) {
      if (data.session) return data.session;
      if (data.user) {
        return {
          userId: data.user.id,
          role: data.user.role,
          mustChangePassword: !!data.user.mustChangePassword
        };
      }
      return null;
    }).catch(function (error) {
      if (error && (error.status === 401 || error.status === 403)) {
        FL.apiClient.clearTokens();
        return null;
      }
      return Promise.reject(error);
    });
  },

  signIn: function (identity, password) {
    return FL.api.send("POST", "/api/login", {
      identity: identity.trim(),
      password: password
    });
  },

  signOut: function () {
    const loginUrl = this.loginUrl();
    FL.api.send("POST", "/api/logout").catch(function () { /* clear locally even if API unreachable */ })
      .finally(function () {
        if (FL.apiClient) FL.apiClient.clearTokens();
        window.location.href = loginUrl;
      });
  },

  requirePasswordChange: function () {
    FL.ui.modal({
      title: "Change temporary password",
      confirmLabel: "Update password",
      cancelLabel: "Sign out",
      body: `
        <p>This sign-in used a temporary password. Set a new password before opening reviewer pages.</p>
        <label class="field"><span>Temporary password</span><input id="current-password" type="password" autocomplete="current-password"></label>
        <label class="field"><span>New password</span><input id="new-password" type="password" autocomplete="new-password"></label>
        <label class="field"><span>Confirm new password</span><input id="confirm-password" type="password" autocomplete="new-password"></label>
        <p class="note" id="password-change-error" hidden></p>`,
      onConfirm: function () {
        const current = document.getElementById("current-password").value;
        const next = document.getElementById("new-password").value;
        const again = document.getElementById("confirm-password").value;
        const error = document.getElementById("password-change-error");
        if (next !== again) {
          error.hidden = false;
          error.textContent = "The new passwords do not match.";
          return false;
        }
        error.hidden = true;
        FL.api.send("POST", "/api/account/password", {
          currentPassword: current,
          newPassword: next
        }).then(function (data) {
          FL.ui.closeModal();
          const session = data && data.session;
          if (session && session.role) {
            window.location.replace(FL.auth.home(session.role));
          } else {
            window.location.reload();
          }
        }).catch(function (err) {
          error.hidden = false;
          error.textContent = err.message || "The password was not changed.";
        });
        return false;
      },
      onClose: function (ok) {
        if (!ok) FL.auth.signOut();
      }
    });
  }
};

FL.pages = FL.pages || {};
FL.pages.login = function () {
  const form = document.getElementById("login-form");
  const identity = document.getElementById("identity");
  const password = document.getElementById("password");
  const identityError = document.getElementById("identity-error");
  const passwordError = document.getElementById("password-error");
  const formError = document.getElementById("form-error");
  const submit = document.getElementById("sign-in");
  const toggle = document.getElementById("toggle-password");
  const remember = document.getElementById("remember");
  const saved = localStorage.getItem(FL.auth.rememberKey);
  if (saved) {
    identity.value = saved;
    remember.checked = true;
  }
  toggle.addEventListener("click", function () {
    const show = password.type === "password";
    password.type = show ? "text" : "password";
    toggle.classList.toggle("is-visible", show);
    toggle.setAttribute("aria-pressed", show ? "true" : "false");
    toggle.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    identityError.textContent = "";
    passwordError.textContent = "";
    formError.hidden = true;
    let invalid = false;
    if (!identity.value.trim()) {
      identityError.textContent = "Email address is required.";
      invalid = true;
    }
    if (!password.value) {
      passwordError.textContent = "Password is required.";
      invalid = true;
    }
    if (invalid) return;
    submit.disabled = true;
    submit.innerHTML = '<span class="spinner" aria-hidden="true"></span> Signing in';
    FL.auth.signIn(identity.value, password.value).then(function (session) {
      if (remember.checked) localStorage.setItem(FL.auth.rememberKey, identity.value.trim());
      else localStorage.removeItem(FL.auth.rememberKey);
      formError.hidden = true;
      if (session && session.mustChangePassword) {
        FL.auth.requirePasswordChange();
        return;
      }
      submit.classList.add("is-success");
      submit.textContent = "Signed in";
      document.getElementById("login-success").hidden = false;
      window.setTimeout(function () {
        window.location.href = FL.auth.home(session.role);
      }, 400);
    }).catch(function (error) {
      submit.disabled = false;
      submit.textContent = "Sign in";
      formError.hidden = false;
      formError.textContent = error.status ? error.message : "Sign-in failed. Check your credentials and try again.";
    });
  });
  document.getElementById("contact-admin").addEventListener("click", function () {
    FL.ui.modal({
      title: "Contact institution admin",
      body: "<p>New Administrator and Reviewer accounts are issued by the institution. Contact the Office of the Vice President for Academic Affairs.</p>",
      cancelLabel: "Close"
    });
  });
  FL.auth.restore().then(function (existing) {
    if (existing && FL.apiClient && FL.apiClient.hasAccessToken()) {
      window.location.replace(FL.auth.home(existing.role));
    }
  }).catch(function () {
    /* Network error: stay on login; do not redirect in a loop */
  });
};

FL.pages.forgotPassword = function () {
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const stepEmail = document.getElementById("reset-step-email");
  const stepCode = document.getElementById("reset-step-code");
  const stepPassword = document.getElementById("reset-step-password");
  const stepSuccess = document.getElementById("reset-step-success");
  const email = document.getElementById("reset-email");
  const emailError = document.getElementById("reset-email-error");
  const code = document.getElementById("reset-code");
  const codeError = document.getElementById("reset-code-error");
  const password = document.getElementById("reset-password");
  const confirm = document.getElementById("reset-confirm");
  const passwordError = document.getElementById("reset-password-error");
  const formError = document.getElementById("reset-error");
  const sendReset = document.getElementById("send-reset");
  const verifyCode = document.getElementById("verify-reset-code");
  const savePassword = document.getElementById("save-new-password");
  const resendCode = document.getElementById("resend-reset-code");
  const backToEmail = document.getElementById("back-to-email");
  let requestedEmail = "";
  let resetToken = "";
  let resendTimer = null;
  let resendRemaining = 0;

  function showStep(name) {
    [stepEmail, stepCode, stepPassword, stepSuccess].forEach(function (el) {
      if (el) el.hidden = el.id !== "reset-step-" + name;
    });
    formError.hidden = true;
  }

  function tickResend() {
    if (!resendCode) return;
    if (resendRemaining <= 0) {
      resendCode.disabled = false;
      resendCode.textContent = "Resend code";
      if (resendTimer) window.clearInterval(resendTimer);
      resendTimer = null;
      return;
    }
    resendCode.disabled = true;
    resendCode.textContent = "Resend in " + resendRemaining + "s";
    resendRemaining -= 1;
  }

  function startResendCooldown(seconds) {
    resendRemaining = seconds || 60;
    tickResend();
    if (resendTimer) window.clearInterval(resendTimer);
    resendTimer = window.setInterval(tickResend, 1000);
  }

  function sendCode(resend) {
    const value = resend ? requestedEmail : email.value.trim();
    if (!resend) {
      emailError.textContent = "";
      if (!value) {
        emailError.textContent = "Email address is required.";
        return;
      }
      if (!emailPattern.test(value) || value.length > 254) {
        emailError.textContent = "Enter a valid email address.";
        return;
      }
    }
    sendReset.disabled = true;
    sendReset.innerHTML = '<span class="spinner" aria-hidden="true"></span> Sending';
    FL.api.send("POST", "/api/forgot-password", { email: value }).then(function (result) {
      sendReset.disabled = false;
      sendReset.textContent = "Send code";
      requestedEmail = value;
      startResendCooldown(result.resendAfterSeconds || 60);
      showStep("code");
      code.value = "";
      code.focus();
    }).catch(function (error) {
      sendReset.disabled = false;
      sendReset.textContent = "Send code";
      formError.hidden = false;
      formError.textContent = error.message || "Could not send a reset code.";
    });
  }

  stepEmail.addEventListener("submit", function (event) {
    event.preventDefault();
    sendCode(false);
  });
  if (resendCode) {
    resendCode.addEventListener("click", function () {
      sendCode(true);
    });
  }
  if (backToEmail) {
    backToEmail.addEventListener("click", function () {
      showStep("email");
    });
  }
  stepCode.addEventListener("submit", function (event) {
    event.preventDefault();
    codeError.textContent = "";
    const otp = code.value.trim();
    if (!/^\d{6}$/.test(otp)) {
      codeError.textContent = "Enter the 6-digit code from your email.";
      return;
    }
    verifyCode.disabled = true;
    FL.api.send("POST", "/api/forgot-password/verify", { email: requestedEmail, code: otp }).then(function (result) {
      verifyCode.disabled = false;
      resetToken = result.resetToken;
      showStep("password");
      password.focus();
    }).catch(function (error) {
      verifyCode.disabled = false;
      formError.hidden = false;
      formError.textContent = error.message || "The code is invalid or has expired.";
    });
  });
  stepPassword.addEventListener("submit", function (event) {
    event.preventDefault();
    passwordError.textContent = "";
    if (password.value.length < 8) {
      passwordError.textContent = "Use at least 8 characters.";
      return;
    }
    if (password.value !== confirm.value) {
      passwordError.textContent = "Passwords do not match.";
      return;
    }
    savePassword.disabled = true;
    FL.api.send("POST", "/api/forgot-password/reset", {
      email: requestedEmail,
      resetToken: resetToken,
      newPassword: password.value
    }).then(function () {
      showStep("success");
    }).catch(function (error) {
      savePassword.disabled = false;
      formError.hidden = false;
      formError.textContent = error.message || "Password was not updated.";
    });
  });
};
