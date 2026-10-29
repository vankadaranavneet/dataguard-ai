# Executed verification — 29 October 2026

Environment: Linux, Python 3.12. Direct dependency versions are pinned in requirements.txt.

`python -m pytest -q`: **35 passed in 2.03 seconds**.

| Core feature | Evidence | Status |
|---|---|---|
| CSV upload processing | UTF-8 bytes, quoted fields, leading-zero preservation; upload waiting-state AppTest | Backend and waiting UI passed; native file picker not exercised |
| Overview | Sample shape 10 × 7, 3 missing cells; DataFrame overview and UI rendering | Passed |
| Validation | Sample rules detect 3 blanks, 1 duplicate, 7 invalid values, 3 inconsistent values; format/range/membership tests | Passed |
| Transparent score | Exact denominators and 84.32330827067669 overall checked against expected calculation | Passed |
| Dashboard | AppTest checks 4 metrics, 3 Plotly chart elements, and severity filter rerun | Passed; no visual/browser interaction inspection |
| Explanations | Real issue records and suggestion-generation branches present in rendered report | Report generated; wording not independently human-reviewed |
| Issue CSV | Generated CSV parsed back with 14 rows; header-only clean report; formula-prefix protection | Passed; browser download click not exercised |
| Original preservation | Deep DataFrame equality and unchanged sample bytes after analysis | Passed |
| Synthetic sample | Full pipeline and UI run against included dataset | Passed |
| Error handling | Empty/header-only/bad-width/bad-quote/invalid-encoding/binary CSV; oversized and wrong extension; bad rules, absent columns | Passed |
| Server launch | Streamlit subprocess returned HTTP 200 for `/` and `/_stcore/health` (`ok`) | Passed; server stopped after smoke check |

Remaining manual checks on your Mac:

1. Install in a fresh virtual environment and rerun tests.
2. Upload data/sample.csv through the browser file picker and paste sample_rules.json.
3. Hover and zoom Plotly charts; inspect layout at your screen size.
4. Click both downloads. Compare the original download to sample.csv and open the issue report.

No physical Mac execution, hosted deployment, load testing, screenshots, or GitHub publication was performed. The project includes no SQLite persistence (optional scope deferred).
