# Mayo ADPKD Imaging Classifier

An independent educational implementation of the Mayo Imaging Classification (MIC) for **typical** autosomal dominant polycystic kidney disease (ADPKD). The calculator assigns imaging classes **1A–1E** from age and height-adjusted total kidney volume (htTKV). Atypical imaging morphology is explicitly left unclassified.

## Use the browser calculator

Open `web/index.html` in a current browser, or serve the directory locally:

```bash
python -m http.server 8001 --directory web
# Visit http://localhost:8001/
```

Enter age (15–80 years), imaging morphology, and either htTKV (mL/m) **or** total kidney volume (mL) together with height (m). The app also imports and exports CSV batches entirely in the browser. Files are not uploaded, stored, or transmitted by the app. Avoid using directly identifying patient information. No account or backend is required for the browser workflow.

**Research/educational use only.** MIC is a prognostic imaging stratum, not a diagnosis, observed longitudinal growth measurement, individual eGFR decline forecast, or stand-alone treatment decision. Morphology must be determined from imaging independently. Do not apply classes 1A–1E to atypical class 2 morphology or outside the supported age range.

## Clinical formulation

For typical bilateral diffuse disease at ages 15–80:

- `htTKV = TKV (mL) / height (m)`
- `estimated annual growth (%) = 100 × ((htTKV / 150) ^ (1 / age) − 1)`
- Class 1A: growth <1.5%; 1B: 1.5–<3%; 1C: 3–<4.5%; 1D: 4.5–<6%; 1E: ≥6%.

The 150 mL/m constant is the theoretical starting htTKV at birth used in the MIC model. The growth percentage is inferred from **a single cross-sectional measurement**, not serially measured. Clinical interpretation, particularly near class thresholds, requires additional context.

References:
- [Irazabal et al., *JASN* 2015, 26:160–172](https://pmc.ncbi.nlm.nih.gov/articles/PMC4279733/)
- [KDIGO 2025 ADPKD guideline](https://kdigo.org/guidelines/autosomal-dominant-polycystic-kidney-disease-adpkd/)
- [Official Mayo research calculator](https://www.mayo.edu/research/documents/pkd-center-adpkd-classification/doc-20094754) (independent implementation here)

## Python single-case and batch usage

Requires Python 3.10 or newer:

```bash
python -m pip install -e .
mayo-adpkd single --age 40 --httkv-ml-per-m 800
mayo-adpkd single --age 40 --tkv-ml 1440 --height-m 1.8
mayo-adpkd single --age 40 --httkv-ml-per-m 800 --morphology atypical
mayo-adpkd batch -i sample.csv -o results.csv
```

CSV must include `age` and either `httkv_ml_per_m`, or **both** `tkv_ml` and `height_m`. Optional columns include `case_id` and `morphology` (defaults to `typical`). Each row is validated; invalid data aborts the export rather than generating a partial result. Input and output files must differ. Results include `mayo_class`, `ht_tkv_ml_per_m`, `estimated_annual_growth_percent` and an interpretation disclaimer.

The browser calculator requires no Python, Pyodide, server, or third-party JavaScript libraries. It uses ordinary JavaScript and local File/Blob APIs and supports modern desktop and mobile browsers.

## Optional legacy audit demonstration

`agents/`, `cli.py`, and `enrichment.py` contain a **separate nonclinical worker/audit demonstration**, preserved for existing integrations and tests. Its generic threshold alerts are **not validated ADPKD prognosis or treatment rules**. The configured `mock` reasoning provider is deterministic and does not connect to external model APIs.

To run the demonstration API locally:

```bash
python -m pip install -e ".[api]"
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export API_ACCESS_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py serve --host 127.0.0.1 --port 8000
```

Audit, chat, and log endpoints require an `Authorization: Bearer <API_ACCESS_TOKEN>` header. The HMAC ledger is process-local and lost on restart; it is **not** a persistent compliance audit store. Identifier screening uses heuristic regular expressions and is not a validated de-identification solution. Do not send real patient information to these endpoints. If running Docker Compose, set `AUDIT_SECRET_KEY` and `API_ACCESS_TOKEN` securely in your host environment; production secrets are not included in the repository.

## Tests and technology

```bash
python -m pip install -e ".[api,test]"
python -m pytest -q
node --test web/classifier.test.js   # Node.js 22+
```

The repository uses Python, Pydantic, optional FastAPI, vanilla HTML/CSS/JavaScript, and GitHub Actions. The static web application is designed for GitHub Pages (deployment requires Pages to be enabled for the repository). The repository includes a Dockerfile for the optional backend.

Licensed under [MIT](LICENSE).
