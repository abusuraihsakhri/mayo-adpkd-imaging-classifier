/* Static, dependency-free Mayo ADPKD imaging classification.
 * Formula: htTKV = 150 * (1 + g)^age (Irazabal et al., JASN 2015).
 * Not a clinical decision or a patient-specific eGFR forecast.
 */
(function (root) {
  "use strict";
  function positive(value, label) {
    if (value === null || value === undefined || String(value).trim() === "") {
      throw new Error(label + " is required.");
    }
    const number = Number(value);
    if (!Number.isFinite(number) || number <= 0) throw new Error(label + " must be a finite positive number.");
    return number;
  }
  function classify(values) {
    const age = positive(values.age, "Age");
    if (age < 15 || age > 80) throw new Error("Mayo MIC applies to ages 15–80 years.");
    const morphology = String(values.morphology || "typical").trim().toLowerCase();
    if (!["typical", "atypical"].includes(morphology)) throw new Error("Select typical or atypical morphology.");
    const hasHtTKV = values.httkv_ml_per_m !== undefined && values.httkv_ml_per_m !== null && String(values.httkv_ml_per_m).trim() !== "";
    const hasTKV = values.tkv_ml !== undefined && values.tkv_ml !== null && String(values.tkv_ml).trim() !== "";
    const hasHeight = values.height_m !== undefined && values.height_m !== null && String(values.height_m).trim() !== "";
    if (hasHtTKV && (hasTKV || hasHeight)) throw new Error("Use htTKV or both TKV and height, not both.");
    if (!hasHtTKV && !(hasTKV && hasHeight)) throw new Error("Enter htTKV or both TKV and height.");
    const httkv = hasHtTKV ? positive(values.httkv_ml_per_m, "htTKV")
      : positive(values.tkv_ml, "TKV") / positive(values.height_m, "Height");
    if (!Number.isFinite(httkv) || httkv <= 0) throw new Error("Calculated htTKV must be finite and positive.");
    const result = { age_years: age, ht_tkv_ml_per_m: Math.round(httkv * 1000) / 1000,
      morphology, mayo_class: null, estimated_annual_growth_percent: null };
    if (morphology === "atypical") return result;
    const growth = 100 * Math.expm1(Math.log(httkv / 150) / age);
    result.estimated_annual_growth_percent = Math.round(growth * 10000) / 10000;
    result.mayo_class = growth < 1.5 ? "1A" : growth < 3 ? "1B" :
      growth < 4.5 ? "1C" : growth < 6 ? "1D" : "1E";
    return result;
  }
  function parseCSV(text) {
    const rows = [];
    let row = [], cell = "", quoted = false;
    const source = String(text).replace(/^\uFEFF/, "");
    for (let i = 0; i < source.length; i++) {
      const ch = source[i];
      if (quoted) {
        if (ch === '"' && source[i + 1] === '"') { cell += '"'; i++; }
        else if (ch === '"') quoted = false;
        else cell += ch;
      } else if (ch === '"' && cell === "") quoted = true;
      else if (ch === ",") { row.push(cell); cell = ""; }
      else if (ch === "\n" || ch === "\r") {
        if (ch === "\r" && source[i + 1] === "\n") i++;
        row.push(cell); rows.push(row); row = []; cell = "";
      } else cell += ch;
    }
    if (quoted) throw new Error("CSV has an unterminated quoted field.");
    if (row.length || cell !== "") { row.push(cell); rows.push(row); }
    if (!rows.length || !rows[0].length || rows[0].every(x => !x.trim()))
      throw new Error("CSV must contain a header.");
    const headers = rows.shift().map(x => x.trim());
    if (new Set(headers).size !== headers.length || headers.some(x => !x))
      throw new Error("CSV headers must be unique and nonempty.");
    if (!headers.includes("age")) throw new Error("CSV must have an age column.");
    if (rows.length > 5000) throw new Error("CSV exceeds the 5000-row limit.");
    return rows.filter(r => r.some(x => x.trim())).map((values, i) => {
      if (values.length !== headers.length) throw new Error("CSV row " + (i + 2) + " has an incorrect number of fields.");
      return Object.fromEntries(headers.map((h, k) => [h, values[k]]));
    });
  }
  function csvCell(value) {
    let str = value == null ? "" : String(value);
    if (/^[\s]*[=+@-]/.test(str)) str = "'" + str; // spreadsheet formula injection
    return '"' + str.replace(/"/g, '""') + '"';
  }
  function toCSV(rows) {
    const fields = ["case_id", "age_years", "ht_tkv_ml_per_m", "morphology",
      "mayo_class", "estimated_annual_growth_percent"];
    return [fields.join(","), ...rows.map(row => fields.map(key => csvCell(row[key])).join(","))].join("\r\n") + "\r\n";
  }
  const api = { classify, parseCSV, toCSV };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.MayoClassifier = api;
})(typeof globalThis === "object" ? globalThis : this);
