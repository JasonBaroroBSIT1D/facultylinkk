"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

function loadUi() {
  const root = path.join(__dirname, "..", "js");
  const ctx = { window: {}, console };
  ctx.window.FL = { esc: function (s) { return String(s || ""); }, store: { documentById: function () { return null; } } };
  ctx.FL = ctx.window.FL;
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(root, "criterion-c-workspace-ui.js"), "utf8"), ctx);
  return ctx.window.FL.criterionCWorkspaceUi;
}

test("unchanged status should not persist", () => {
  const ui = loadUi();
  assert.equal(ui.slotStatusShouldPersist("verified", "verified"), false);
  assert.equal(ui.slotStatusShouldPersist("verified", "present_unverified"), true);
});

test("save indicator messages", () => {
  const ui = loadUi();
  assert.match(ui.slotSaveIndicatorMessage("saving"), /Saving/);
  assert.match(ui.slotSaveIndicatorMessage("saved", "verified"), /Verified/);
  assert.match(ui.slotSaveIndicatorMessage("error"), /retry/i);
});

test("syncConfirmedSlotStatuses tracks backend checklist", () => {
  const ui = loadUi();
  const state = {
    slotIds: ["approval_sheet", "rrpa_copc"],
    bundle: {
      checklist: {
        approval_sheet: { status: "verified", documentId: "a" },
        rrpa_copc: { status: "present_unverified", documentId: "b" }
      }
    },
    verificationSave: { pending: false, requestId: 0, confirmedBySlot: {} }
  };
  ui.syncConfirmedSlotStatuses(state);
  assert.equal(state.verificationSave.confirmedBySlot.approval_sheet, "verified");
  assert.equal(state.verificationSave.confirmedBySlot.rrpa_copc, "present_unverified");
});
