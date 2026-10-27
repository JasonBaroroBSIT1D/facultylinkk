/**
 * Flask API base URL for FacultyLink web (development).
 * Override before scripts load: window.FL_API_BASE = "http://192.168.x.x:5000";
 */
window.FL = window.FL || {};

FL.apiConfig = {
  baseUrl: (typeof window.FL_API_BASE === "string" && window.FL_API_BASE.trim())
    ? window.FL_API_BASE.trim().replace(/\/$/, "")
    : "http://127.0.0.1:5000"
};
