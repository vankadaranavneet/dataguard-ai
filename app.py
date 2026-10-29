"""Run with: python -m streamlit run app.py"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from dataguard.processing import load_csv, overview
from dataguard.validation import analyze, parse_rules
from dataguard.scoring import calculate_scores
from dataguard.reporting import report_csv

ROOT = Path(__file__).parent
st.set_page_config(page_title='DataGuard AI', page_icon='🛡️', layout='wide')
st.title('🛡️ DataGuard AI')
st.caption('Intelligent Data Quality & Governance Monitor · Explainable rules, no paid AI API')
st.sidebar.header('Dataset & rules')
mode = st.sidebar.radio('Data source', ['Synthetic demo', 'Upload CSV'])
upload = st.sidebar.file_uploader('UTF-8 CSV · maximum 10 MB', type=['csv']) if mode == 'Upload CSV' else None
if mode == 'Upload CSV' and upload is None:
    st.info('Upload a CSV to begin. Your original file will not be modified.')
    st.stop()
raw = (ROOT / 'data/sample.csv').read_bytes() if mode == 'Synthetic demo' else upload.getvalue()
name = 'sample.csv' if mode == 'Synthetic demo' else upload.name
try:
    df = load_csv(raw, name)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
with st.sidebar.expander('Configure validation rules', expanded=True):
    st.caption('JSON keyed by exact column name. Uploads start with no domain assumptions. See README for examples.')
    rule_text = st.text_area('Rules JSON', value=(ROOT / 'data/sample_rules.json').read_text() if mode == 'Synthetic demo' else '{}',
                             height=300, key=f'rules_{mode}')
try:
    rules = parse_rules(rule_text)
    issues, counts = analyze(df, rules)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
scores, total = calculate_scores(counts)
st.success('Read-only analysis: original CSV bytes and cell values are preserved.')
cols = st.columns(4)
for col, label, val in zip(cols, ['Quality score', 'Rows', 'Columns', 'Issue occurrences'],
                           [f'{total:.2f}/100', len(df), len(df.columns), len(issues)]):
    col.metric(label, val)
metrics = pd.DataFrame([{'dimension': k.title(), 'score': v, 'failures': counts[k][0], 'opportunities': counts[k][1]} for k, v in scores.items()])
tab1, tab2, tab3 = st.tabs(['Quality dashboard', 'Dataset overview', 'Issues & export'])
with tab1:
    st.plotly_chart(px.bar(metrics.dropna(subset=['score']), x='dimension', y='score', range_y=[0, 100],
                           color='dimension', title='Quality by assessed dimension'), use_container_width=True)
    st.dataframe(metrics, hide_index=True, use_container_width=True)
    st.caption('Blank scores mean not assessed. Overall score is the equal-weight mean of assessed dimensions. Missing cells are excluded from validity and consistency denominators.')
    if not issues.empty:
        left, right = st.columns(2)
        left.plotly_chart(px.histogram(issues, x='column', color='severity', title='Issue occurrences by column'), use_container_width=True)
        right.plotly_chart(px.histogram(issues, x='rule', color='severity', title='Issue occurrences by rule'), use_container_width=True)
    else:
        st.info('No issues detected under the active rules; this is not a guarantee of correctness.')
with tab2:
    st.write(f'Exact duplicate records beyond the first occurrence: **{counts["uniqueness"][0]}**')
    st.dataframe(overview(df), hide_index=True, use_container_width=True)
    st.caption('CSV has no type schema. Storage types are string to preserve leading zeros and formatting; expected types are set in rules.')
    st.dataframe(df.head(100), use_container_width=True)
    st.download_button('Download original CSV (unchanged)', raw, 'original.csv', 'text/csv')
with tab3:
    st.caption('Row numbers start at 1 for the first data record (excluding the header); * means the whole record. Counts are issue occurrences, not unique affected rows.')
    selected = st.multiselect('Severity filter', ['High', 'Medium'], default=['High', 'Medium'])
    st.dataframe(issues[issues.severity.isin(selected)], hide_index=True, use_container_width=True)
    st.download_button('Download all issues CSV', report_csv(issues), 'dataguard_issues.csv', 'text/csv')
    st.caption('The export always includes all issues. Suggestions require human review and are never applied automatically.')
