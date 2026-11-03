"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = {
  esc: function (s) {
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  },
  pages: {},
  ui: { toast: function () {} },
  apiClient: {
    getAccessToken: function () { return "token"; },
    adminRequestBlob: function () { return Promise.resolve(new Blob()); }
  },
  apiConfig: { baseUrl: "http://127.0.0.1:5000" },
  store: {
    usesLiveDocuments: function () { return true; },
    documentById: function () { return null; }
  },
  scoring: {},
  validation: {}
};

eval(fs.readFileSync(path.join(__dirname, "../js/documents.js"), "utf8"));

var docs = global.FL.documents;
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

(function testInlineFileUrlEmptyUntilBlob() {
  var doc = {
    id: "d1",
    fileApiPath: "/api/reviewer/documents/d1/file",
    fileUrl: "http://127.0.0.1:5000/api/reviewer/documents/d1/file",
    fileName: "paper.pdf"
  };
  assert(docs.inlineFileUrl(doc) === "", "live API path must not expose raw URL in iframe");
})();

(function testOriginalFileHtmlDoesNotUseFragmentOnlyIframe() {
  var doc = {
    id: "d1",
    fileApiPath: "/api/reviewer/documents/d1/file",
    fileUrl: "http://127.0.0.1:5000/api/reviewer/documents/d1/file",
    fileName: "paper.pdf"
  };
  var html = docs.originalFileHtml(doc);
  assert(html.indexOf("data-doc-preview-id") >= 0, "should defer to authenticated mount");
  assert(html.indexOf('src="#toolbar') < 0, "must not embed current-page fragment iframe");
})();

(function testRenderMarkupUsesBlobUrl() {
  var doc = {
    id: "d1",
    fileName: "paper.pdf",
    mimeType: "application/pdf",
    _objectUrl: "blob:http://localhost/fake-blob-id"
  };
  var html = docs.renderOriginalFileMarkup(doc);
  assert(html.indexOf("blob:http://localhost/fake-blob-id") >= 0);
  assert(html.indexOf("#toolbar=0") >= 0);
})();

console.log("document-preview.test.js: all passed");
