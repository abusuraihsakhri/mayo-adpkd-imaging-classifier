"use strict";
const assert = require("node:assert/strict");
const { test } = require("node:test");
const { classify, parseCSV, toCSV } = require("./classifier.js");

test("MIC classes match 1.5%, 3%, 4.5%, and 6% yearly growth bands", () => {
  for (const [rate, expected] of [[1,"1A"], [2,"1B"], [3.5,"1C"], [5,"1D"], [7,"1E"]]) {
    const result = classify({age:40, httkv_ml_per_m:150 * Math.pow(1 + rate / 100, 40)});
    assert.equal(result.mayo_class, expected);
    assert.ok(Math.abs(result.estimated_annual_growth_percent - rate) < 0.0001);
  }
});
test("TKV and height yield identical classification to htTKV", () => {
  const a = classify({age:40, httkv_ml_per_m:800});
  const b = classify({age:40, tkv_ml:1440, height_m:1.8});
  assert.deepEqual(a,b);
});
test("Atypical morphology is never assigned a typical Mayo class", () => {
  const result = classify({age:40, httkv_ml_per_m:900, morphology:"atypical"});
  assert.equal(result.mayo_class,null);
  assert.equal(result.estimated_annual_growth_percent,null);
});
test("Out of range, missing, and malformed values are rejected", () => {
  for (const x of [
    {age:14,httkv_ml_per_m:500}, {age:81,httkv_ml_per_m:500},
    {age:40,httkv_ml_per_m:""}, {age:40,httkv_ml_per_m:"NaN"},
    {age:40,tkv_ml:400}, {age:40,tkv_ml:500,height_m:0},
    {age:40,tkv_ml:500,height_m:1.7,httkv_ml_per_m:400},
    {age:40,httkv_ml_per_m:400,morphology:"unknown"},
  ]) assert.throws(()=>classify(x));
});
test("CSV parser supports quoting, escaped quotes, and CRLF", () => {
  assert.deepEqual(parseCSV('case_id,age,httkv_ml_per_m\r\n"A, ""B""",40,800\r\n'),
    [{case_id:'A, "B"',age:"40",httkv_ml_per_m:"800"}]);
  assert.throws(()=>parseCSV('case_id,age\na,40,extra'));
});
test("CSV serializes without spreadsheet formulas in case IDs", () => {
  const result = toCSV([{case_id:'=HYPERLINK("x")', age_years:40, mayo_class:"1B"}]);
  assert.match(result, /"'=HYPERLINK/);
  assert.ok(result.includes("mayo_class"));
});
