"use strict";

var fs = require("fs");
var path = require("path");

var src = fs.readFileSync(path.join(__dirname, "../js/data.js"), "utf8");
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

assert(
  src.indexOf('/teaching-effectiveness" + bust') === -1,
  "admin teaching-effectiveness must not append cache buster without query string"
);
assert(
  src.indexOf("/teaching-effectiveness?_=") !== -1,
  "admin teaching-effectiveness must use ?_= cache buster"
);

console.log("data-teaching-effectiveness-url.test.js: all passed");
