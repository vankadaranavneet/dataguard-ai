# DataGuard AI — Intelligent Data Quality & Governance Monitor

An explainable Python portfolio project that turns a CSV into a data-quality dashboard and a reviewable issue report. Built for a beginner learning data engineering and governance concepts, with a finance-inspired **entirely synthetic** demo.

**“AI” in the project name refers to rule-based explanations. This version uses no machine learning, LLM, paid API, or API key.** It is an educational prototype, not a regulatory compliance system or a JPMorgan Chase product.

## Run on a Mac

Install Python 3.12 if you do not already have it. Extract the project ZIP into Downloads, then open Terminal:

```bash
cd ~/Downloads/dataguard-ai
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Visit http://localhost:8501 if the browser does not open automatically. The synthetic demo loads immediately. Stop the app with Control+C. On subsequent runs:

```bash
cd ~/Downloads/dataguard-ai
source .venv/bin/activate
python -m streamlit run app.py
```

If you extracted elsewhere, change the first path. If `python3` is missing, install Python before continuing. If port 8501 is occupied, add `--server.port 8502`. Use `python -m ...` so commands use the active virtual environment. No database setup is required.

## Features

- UTF-8 CSV upload with a 10 MB input limit and strict record-width checking.
- Row/column counts, column names, storage types, blank counts, distinct values, duplicate counts, and preview.
- Missing-cell, exact-duplicate, numeric range, email, ISO date, allowed-value, and canonical-spelling checks.
- Editable JSON rules; uploaded datasets begin with `{}` so no demo-specific assumptions are applied.
- Four transparent score dimensions with denominators shown in the dashboard.
- Three interactive Plotly charts when issues exist, severity filtering, and plain-English suggestions.
- Separate downloadable issue report and byte-for-byte original CSV download.
- Automated validation, edge-case, scoring, export, and Streamlit UI tests.

## Try the demo

1. Run the app with **Synthetic demo** selected.
2. Open Dataset overview to inspect the unchanged values.
3. Inspect issue explanations under Issues & export; filter by High or Medium.
4. Download the complete issue report (the severity filter affects only the displayed table).
5. Change `age.max` in the sidebar rules, then observe recalculated results.
6. Choose Upload CSV, upload `data/sample.csv`, and paste the contents of `data/sample_rules.json` into Rules JSON to reproduce the demo.

The supplied sample has 10 rows and 7 columns. Its default rules produce:

| Dimension | Failures / opportunities | Score |
|---|---:|---:|
| Completeness | 3 / 70 cells | 95.71 |
| Uniqueness | 1 / 10 records | 90.00 |
| Validity | 7 / 38 eligible nonblank cells | 81.58 |
| Consistency | 3 / 10 eligible nonblank cells | 70.00 |
| Overall | Equal-weight mean before rounding | **84.32** |

There are **14 issue occurrences**: 3 missing cells, 1 duplicate record, 7 invalid values, and 3 noncanonical values. Occurrences are not unique affected rows: one row may contain several issues. These figures were computed and checked by tests; the app calculates them afresh, never hardcodes them.

## Scoring contract

For each dimension:

`dimension_score = 100 × (1 − failed_opportunities / total_opportunities)`

Overall score is the arithmetic mean of assessed dimension scores, without intermediate rounding. A zero denominator is **not assessed**, excluded from the overall mean, and shown as blank in the metric table. Consequently, scores under different rule sets are not directly comparable.

- **Completeness:** all cells are opportunities. Null, empty, and whitespace-only cells fail. Literal strings such as `NA`, `null`, and `NaN` are not automatically missing.
- **Uniqueness:** all rows are opportunities. Only exact repeated rows after their first occurrence fail. Whitespace and case differences remain distinct. This is not primary-key uniqueness.
- **Validity:** each nonblank cell with `type` and/or `allowed` is one opportunity. A cell that violates multiple validity constraints fails once. Missing cells are counted only in completeness.
- **Consistency:** each nonblank cell in a column with `canonical` is one opportunity. Any value not exactly in the approved vocabulary fails. Case-folding and trimming are used only to suggest a spelling, never to modify data. Unknown values also fail but receive no guessed replacement.

Every blank is flagged; `required: true` raises its severity to High. Other blanks and duplicates are Medium, validity failures High, and consistency failures Medium. Severity does not weight the score. Required fields are a review policy, not a separate scoring dimension. Rule errors or absent configured columns stop analysis rather than producing misleading partial scores.

A perfect score means only that the implemented checks passed. It cannot prove truth, accuracy against an external source, or fitness for a business decision.

## Configure rules

Rules are JSON objects keyed by exact CSV column names:

```json
{
  "email": {"required": true, "type": "email"},
  "age": {"type": "number", "min": 18, "max": 100},
  "signup_date": {"type": "date"},
  "country": {"canonical": ["India", "US", "UK"]},
  "status": {"allowed": ["active", "inactive"]}
}
```

Use only columns present in your file. `number` accepts finite numeric values, with inclusive min/max bounds. `date` requires a real calendar date in `YYYY-MM-DD` format. Email checking is deliberately basic syntax validation, not address verification. `allowed` checks exact membership; `canonical` additionally generates suggestions for case/whitespace variants. Rules combine within a column; missing values are skipped for these checks. Unknown keys, ambiguous canonical lists, wrong types, and reversed bounds are rejected.

The sample's nonnegative account balance rule is a demo assumption, **not** a universal financial rule: negative balances can be valid in real systems. Domain owners must approve business rules.

## Architecture and file guide

The interface passes original bytes to the loader, then passes the resulting DataFrame and rules to the validator. The validator returns a report and failure/opportunity counts. Scoring transforms those counts into percentages; reporting produces separate export bytes.

| File | Responsibility |
|---|---|
| `app.py` | Streamlit upload, rule editor, metrics, Plotly charts, tables, downloads, and user-facing errors |
| `dataguard/processing.py` | Strict CSV ingestion and dataset overview; preserve strings and identifiers |
| `dataguard/validation.py` | Validate rule configuration, detect issues, build explanations and score counts |
| `dataguard/scoring.py` | Pure score calculations independent of Streamlit |
| `dataguard/reporting.py` | Generate the separate CSV report and escape potential spreadsheet formulas |
| `dataguard/__init__.py` | Mark the folder as an importable Python package |
| `data/sample.csv` | Synthetic records with deliberate quality problems |
| `data/sample_rules.json` | Explicit demo schema and business assumptions |
| `tests/test_core.py` | Validation, parsing, preservation, report, and score tests |
| `tests/test_app.py` | Streamlit AppTest dashboard, filter, and error-state tests |
| `requirements.txt` | Tested direct dependencies, pinned for reproducibility |
| `.streamlit/config.toml` | Theme, upload limit, and disabled usage telemetry |
| `.gitignore` | Exclude environments, caches, secrets, uploaded data, and database files |
| `VERIFICATION.md` | Actual executed checks and remaining manual checks |
| `README.md` | Setup, scoring contract, architecture, limitations, and learning guide |

A **DataFrame** is Pandas' table abstraction. A **pure function** takes inputs and returns outputs without changing external state, making score calculations easy to test. **Separation of concerns** keeps UI changes from breaking validation logic. Pytest uses small examples to check the program's behavior, including bad inputs.

## Data safety and governance scope

Uploaded source bytes are never written to disk by application code. The app does not modify the input DataFrame, apply suggestions, delete records, or overwrite source files. It computes temporary derived objects in the running process. Downloads are explicit user actions. No analytics API or AI API receives dataset content from this application code.

When run locally, analysis runs on your computer. If hosted elsewhere, uploaded data reaches that server; deployment security and retention controls become your responsibility. Do not upload confidential/customer data to this demo. Reports include original problem values and should be treated as sensitive if used with sensitive inputs. CSV report cells that could be interpreted as spreadsheet formulas are prefixed with an apostrophe; the original download remains unchanged.

## Verification

Run `python -m pytest -q`. During development, **35 tests passed** under Python 3.12 with Pandas 2.2.3, Streamlit 1.66.1, Plotly 6.9.0, and Pytest 9.2.0. The Streamlit server started and its health endpoint responded successfully. See `VERIFICATION.md` for scope. Tests were run in Linux, not on a physical Mac. No browser screenshot is included; AppTest verified rendered elements, not visual appearance or browser click/download behavior.

## Limitations and next steps

- Small-data MVP: row-by-row validation and unbounded per-issue detail can become slow or memory-heavy even below the byte limit. Use modest datasets; this is not a streaming engine.
- Only comma-separated UTF-8 CSV. Header-only, ragged, blank-record, malformed-quote, binary, and duplicate-header files are rejected. Quoted commas/newlines work. No XLSX or delimiter detection.
- Values are stored as strings because CSV carries no schema; the displayed dtype is storage type, not inferred business type. No automatic type casting.
- No fuzzy entity matching, key uniqueness rules, cross-column logic, drift detection, lineage, persistent audit log, authentication, access controls, or regulatory certification.
- No automatic remediation and no statistical or ML anomaly detection.
- SQLite is intentionally deferred because storage was optional. A useful next step is an opt-in history table storing run timestamps, rule versions, and summary scores without raw customer data.
- Dependency pins capture the tested direct packages, not a complete transitive lockfile.

## Explain it honestly in an interview

“I built a modular CSV quality monitor using Pandas and Streamlit. It checks completeness, exact duplicates, configured validity constraints, and canonical category spelling. Each score has an explicit denominator, and unassessed dimensions are excluded. I kept source values unchanged and exported a separate issue report. I tested validation edge cases and the UI with Pytest. The intelligence is deterministic rule-based explanation, not a trained model.”

Be ready to explain why missing cells are not counted twice in validity, why duplicates count only beyond the first copy, and why business rules need domain review. Walk through `load_csv → analyze → calculate_scores → report_csv`, then deliberately break a sample value and observe the result.

## Publish to your own GitHub repository

After reviewing the code and creating an empty repository in your own GitHub account:

```bash
git init
git add .
git commit -m "Build DataGuard AI data quality monitor"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/dataguard-ai.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your account name. Publish only synthetic data. This project has not been pushed or deployed for you.
