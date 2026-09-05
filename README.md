# Mayo Adpkd Imaging Classifier

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Mayo Imaging Classification for ADPKD
Estimates future eGFR decline in autosomal dominant polycystic kidney disease from height-adjusted total kidney volume (HtTKV).

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_metrics()`**: Core domain algorithm for mayo-adpkd-imaging-classifier.
- **`process_single()`** — calculates and validates process_single parameters.
- **`process_batch()`** — calculates and validates process_batch parameters with file validation.
- **`main()`** — CLI entry point for single and batch operations.

---

## 📐 Mathematical Formulation & Logic

```text
  score = primary_val
  rounded_score = round(score, 2)
  res = calculate_metrics(**kwargs)
  calc_res = calculate_metrics(**r)
```

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/mayo-adpkd-imaging-classifier.git
cd mayo-adpkd-imaging-classifier

# Install dependencies
pip install -e .

# For API server support
pip install -e ".[api]"

# For development (includes testing)
pip install -e ".[dev]"
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python cli.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 3. Enterprise Supervisor Mode
```bash
# Set the audit security key (required)
export AUDIT_SECRET_KEY="your-secure-key-here-min-16-chars"

# Run audit evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Verify audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--v1`: Primary parameter (float, default: 10.0)
- `--v2`: Secondary parameter (float, default: 5.0)
- `--v3`: Tertiary parameter (float, default: 2.0)
- `-i, --input`: Input CSV file path (required for batch)
- `-o, --output`: Output CSV file path (default: results.csv)

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition. Requires `AUDIT_SECRET_KEY` environment variable.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

The `AUDIT_SECRET_KEY` environment variable is **required** for audit trail operations. Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t mayo-adpkd-imaging-classifier .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" mayo-adpkd-imaging-classifier
```

---

## 📁 Project Structure

```
mayo-adpkd-imaging-classifier/
├── agents/                  # Enterprise agent modules
│   ├── __init__.py         # Package initialization
│   ├── api.py              # FastAPI REST server
│   ├── base.py             # Security, PHI guard, HMAC audit
│   ├── llm_factory.py      # LLM provider factory
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Supervisor orchestrator
│   └── workers.py          # Specialized domain workers
├── tests/                  # Test suite
│   ├── test_enrichment.py  # Enrichment module tests
│   └── test_mayo_adpkd_imaging_classifier.py  # Core tests
├── web/                    # Web dashboard
│   └── index.html          # Operations console
├── mayo_adpkd.py           # Core classification algorithm
├── cli.py                  # Command-line interface
├── enrichment.py           # Enrichment feature engines
├── simulator.py            # High-throughput simulator
├── sample.csv              # Sample input data
├── benchmark_dataset.json  # Benchmark test cases
├── pyproject.toml          # Project configuration
├── Dockerfile              # Container definition
└── docker-compose.yml      # Docker Compose configuration
```
