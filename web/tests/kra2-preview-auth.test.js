"use strict";

var fs = require("fs");
var path = require("path");
var uiSrc = fs.readFileSync(path.join(__dirname, "../js/kra2-a-workspace-ui.js"), "utf8");
var reviewSrc = fs.readFileSync(path.join(__dirname, "../js/kra2-a-review.js"), "utf8");
var docsSrc = fs.readFileSync(path.join(__dirname, "../js/documents.js"), "utf8");

if (uiSrc.indexOf('data-kra2-preview-doc') < 0) {
  throw new Error("supporting preview must use data-kra2-preview-doc button");
}
if (uiSrc.indexOf("document-review.html?id=") >= 0) {
  throw new Error("KRA II evidence cards must not link to document-review for preview");
}
if (reviewSrc.indexOf("_mountKra2DocumentPreview") < 0) {
  throw new Error("kra2-a-review must mount authenticated previews for supporting docs");
}
if (reviewSrc.indexOf("mountAuthenticatedPreview") < 0) {
  throw new Error("kra2 preview must reuse mountAuthenticatedPreview");
}

if (docsSrc.indexOf("previewErrorMessage") < 0) {
  throw new Error("documents.js must define previewErrorMessage");
}
if (docsSrc.indexOf("Couldn't open this document. Please try again.") < 0) {
  throw new Error("documents.js must use friendly preview failure copy");
}
if (docsSrc.indexOf("status === 401") < 0 || docsSrc.indexOf("sessionExpired") < 0) {
  throw new Error("documents.js must distinguish 401 session expiry");
}
if (docsSrc.indexOf("[Document preview] load failed") < 0) {
  throw new Error("documents.js must log preview failures for developers");
}

console.log("kra2-preview-auth.test.js OK");
