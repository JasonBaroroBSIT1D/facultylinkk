"use strict";

const fs = require("fs");
const path = require("path");

/** Load QA credentials from environment only (optional backend/.env for local runs). */
module.exports = async () => {
  const envPath = path.join(__dirname, "../../backend/.env");
  if (fs.existsSync(envPath) && !process.env.QA_REVIEWER_EMAIL) {
    const dotenv = require("dotenv");
    const parsed = dotenv.parse(fs.readFileSync(envPath));
    const shared = parsed.QA_ACCOUNT_PASSWORD || parsed.QA_PASSWORD;
    for (const key of [
      "QA_REVIEWER_EMAIL",
      "QA_REVIEWER_PASSWORD",
      "QA_FACULTY_EMAIL",
      "QA_FACULTY_PASSWORD",
      "QA_ADMIN_EMAIL",
      "QA_ADMIN_PASSWORD",
      "QA_ACCOUNT_PASSWORD",
    ]) {
      if (parsed[key] && !process.env[key]) {
        process.env[key] = parsed[key];
      }
    }
    if (shared) {
      if (!process.env.QA_REVIEWER_PASSWORD) process.env.QA_REVIEWER_PASSWORD = shared;
      if (!process.env.QA_FACULTY_PASSWORD) process.env.QA_FACULTY_PASSWORD = shared;
      if (!process.env.QA_ADMIN_PASSWORD) process.env.QA_ADMIN_PASSWORD = shared;
    }
  }
};
