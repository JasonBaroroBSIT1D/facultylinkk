"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var root = path.join(__dirname, "..", "js");
var elements = {};

function makeEl(value) {
  return { value: value == null ? "" : String(value) };
}

global.document = {
  getElementById: function (id) {
    return elements[id] || null;
  }
};

var ctx = {
  window: {},
  FL: {
    esc: function (s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/"/g, "&quot;");
    },
    documents: { kvRow: function () { return ""; } },
    kra2Evidence: {
      patchBundle: function () {
        return Promise.resolve({ bundle: {}, validation: { approvalBlockers: [] } });
      },
      fetchBundle: function () {
        return Promise.resolve({
          bundle: { metadataConfirmed: { outputTitle: true } },
          validation: { flags: [], approvalBlockers: [] }
        });
      }
    },
    ui: { toast: function () {} }
  },
  document: global.document,
  console: console
};
ctx.window.FL = ctx.FL;

vm.runInContext(fs.readFileSync(path.join(root, "kra2-a-workspace-ui.js"), "utf8"), vm.createContext(ctx));
vm.runInContext(fs.readFileSync(path.join(root, "kra2-a-review.js"), "utf8"), vm.createContext(ctx));

var ui = ctx.FL.kra2AWorkspaceUi;
var review = ctx.FL.kra2AReview;

elements["kra2-meta-outputTitle"] = makeEl("");
elements["kra2-meta-authorsLine"] = makeEl("");
elements["kra2-meta-outputVenue"] = makeEl("");
elements["kra2-meta-publicationDate"] = makeEl("");

var state = {
  bundle: { indicatorId: "kra2-a-journal-sole" },
  doc: { indicatorId: "kra2-a-journal-sole" },
  payload: {
    ocrExtraction: {
      fields: {
        outputTitle: { value: "OCR Article Title" },
        authorsLine: { value: "Jane Faculty" },
        outputVenue: { value: "Test Journal" },
        publicationDate: { value: "2024-05-01" }
      }
    }
  }
};

var emptyResult = ui.applyOcrSuggestions(state, { onlyEmpty: true });
if (emptyResult.filled.length !== 4) {
  throw new Error("expected 4 OCR fields filled, got " + emptyResult.filled.length);
}
if (elements["kra2-meta-outputTitle"].value !== "OCR Article Title") {
  throw new Error("title not filled from OCR");
}

elements["kra2-meta-outputTitle"].value = "Manual";
var noop = ui.applyOcrSuggestions(state, { onlyEmpty: true });
if (!noop.message || noop.message.indexOf("already") < 0) {
  throw new Error("expected already-filled message, got: " + noop.message);
}

elements["kra2-meta-outputTitle"].value = "";
elements["kra2-meta-authorsLine"].value = "";
elements["kra2-meta-outputVenue"].value = "";
elements["kra2-meta-publicationDate"].value = "";
var invalid = ui.validateReviewerMetadata(state);
if (invalid.ok) throw new Error("expected validation failure on empty form");

elements["kra2-meta-outputTitle"].value = "T";
elements["kra2-meta-authorsLine"].value = "A";
elements["kra2-meta-outputVenue"].value = "J";
elements["kra2-meta-publicationDate"].value = "2024";
var valid = ui.validateReviewerMetadata(state);
if (!valid.ok) throw new Error("expected validation success");

review._activeReviewState = state;
review._reviewSession = { role: "reviewer" };
var page = {
  addEventListener: function (type, fn) {
    page._click = fn;
  }
};
global.document.getElementById = function (id) {
  if (id === "page") return page;
  return elements[id] || null;
};
review._pageDelegationBound = false;
review._ensurePageDelegation({ role: "reviewer" });
var actionBtn = {
  disabled: false,
  getAttribute: function (name) {
    return name === "data-kra2-action" ? "fill-ocr" : null;
  }
};
elements["kra2-meta-outputTitle"].value = "";
page._click({
  target: {
    closest: function (sel) {
      return sel === "[data-kra2-action]" ? actionBtn : null;
    }
  },
  preventDefault: function () {}
});
if (elements["kra2-meta-outputTitle"].value !== "OCR Article Title") {
  throw new Error("delegated fill-ocr did not apply");
}

var patchCalls = 0;
review._patchAndRefresh = function () {
  patchCalls += 1;
  state.validation = {
    flags: [],
    approvalBlockers: ["Enter reviewer remarks (at least 10 characters)."]
  };
  return Promise.resolve({});
};
review._renderPage = function () {};
review._syncApproveButton = function () {};

review
  ._handleSaveMetadata({ role: "reviewer" }, state, { disabled: false })
  .then(function () {
    if (patchCalls !== 1) throw new Error("expected one PATCH, got " + patchCalls);
    console.log("kra2-a-review-metadata.test.js OK");
    process.exit(0);
  })
  .catch(function (err) {
    console.error(err);
    process.exit(1);
  });
