"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = {
  apiClient: {
    adminRequest: function (method, pathArg, body) {
      global.__kra3LastRequest = { method: method, path: pathArg, body: body, thisArg: this };
      return Promise.resolve({ ok: true });
    }
  },
  store: {
    usesLiveDocuments: function () { return true; }
  }
};

eval(fs.readFileSync(path.join(__dirname, "../js/kra3-evidence.js"), "utf8"));

var session = { role: "reviewer" };
function assertBound(pathFragment) {
  if (!global.__kra3LastRequest) throw new Error("expected request");
  if (global.__kra3LastRequest.thisArg !== FL.apiClient) {
    throw new Error("adminRequest must be bound to apiClient");
  }
  if (global.__kra3LastRequest.path.indexOf(pathFragment) < 0) {
    throw new Error("expected path fragment " + pathFragment + " in " + global.__kra3LastRequest.path);
  }
}

Promise.resolve()
  .then(function () {
    return FL.kra3Evidence.fetchFacultySummary(session, "fac-1", "kra3-b");
  })
  .then(function () {
    assertBound("/kra3-b/summary");
    return FL.kra3Evidence.fetchFacultyAccomplishments(session, "fac-1", "kra3-a");
  })
  .then(function () {
    assertBound("/kra3-a/accomplishments");
    return FL.kra3Evidence.fetchBundle(session, "doc-x");
  })
  .then(function () {
    assertBound("/kra3/evidence-bundle");
    console.log("kra3-evidence-api.test.js: all passed");
  });
