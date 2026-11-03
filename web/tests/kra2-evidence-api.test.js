"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = {
  apiClient: {
    adminRequest: function (method, pathArg, body) {
      global.__kra2LastRequest = { method: method, path: pathArg, body: body, thisArg: this };
      return Promise.resolve({ ok: true });
    }
  },
  store: {
    usesLiveDocuments: function () { return true; }
  }
};

eval(fs.readFileSync(path.join(__dirname, "../js/kra2-evidence.js"), "utf8"));

var session = { role: "reviewer" };
function assertBound(pathFragment) {
  if (!global.__kra2LastRequest) throw new Error("expected request");
  if (global.__kra2LastRequest.thisArg !== FL.apiClient) {
    throw new Error("adminRequest must be bound to apiClient");
  }
  if (global.__kra2LastRequest.path.indexOf(pathFragment) < 0) {
    throw new Error("unexpected path: " + global.__kra2LastRequest.path);
  }
}

Promise.resolve()
  .then(function () {
    return FL.kra2Evidence.fetchBundle(session, "doc-abc");
  })
  .then(function () {
    assertBound("/api/reviewer/documents/doc-abc/kra2/evidence-bundle");
    return FL.kra2Evidence.fetchFacultyAccomplishments(session, "fac-1", "kra2-a");
  })
  .then(function () {
    assertBound("/api/reviewer/me/faculty/fac-1/kra2-a/accomplishments");
    return FL.kra2Evidence.fetchFacultySummary(session, "fac-1", "kra2-a");
  })
  .then(function () {
    assertBound("/api/reviewer/me/faculty/fac-1/kra2-a/summary");
    console.log("kra2-evidence-api.test.js: all passed");
  })
  .catch(function (err) {
    console.error(err);
    process.exit(1);
  });
