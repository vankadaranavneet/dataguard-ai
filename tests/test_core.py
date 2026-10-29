from pathlib import Path
import pandas as pd
import pytest
from dataguard.processing import load_csv, overview
from dataguard.validation import analyze, parse_rules
from dataguard.scoring import calculate_scores
from dataguard.reporting import report_csv

ROOT = Path(__file__).resolve().parents[1]


def test_sample_and_preservation():
    raw = (ROOT / 'data/sample.csv').read_bytes()
    df = load_csv(raw)
    original = df.copy(deep=True)
    issues, counts = analyze(df, parse_rules((ROOT / 'data/sample_rules.json').read_text()))
    assert df.shape == (10, 7)
    assert counts == {'completeness': [3, 70], 'uniqueness': [1, 10], 'validity': [7, 38], 'consistency': [3, 10]}
    assert len(issues) == 14
    scores, total = calculate_scores(counts)
    assert scores['validity'] == pytest.approx(100 * 31 / 38)
    assert total == pytest.approx(84.32330827067669)
    pd.testing.assert_frame_equal(df, original)
    assert raw == (ROOT / 'data/sample.csv').read_bytes()
    assert len(pd.read_csv(__import__('io').BytesIO(report_csv(issues)))) == 14
    assert overview(df)['missing'].sum() == 3


@pytest.mark.parametrize('raw', [b'', b'\n', b'a,b\n', b'a,b\n1\n', b'a,b\n1,2,3\n', b'a,a\n1,2', b'a,\n1,2', b'a\n"unclosed', b'\xff', b'a\n\x00'])
def test_bad_csv(raw):
    with pytest.raises(ValueError):
        load_csv(raw)


def test_unsupported_and_large():
    with pytest.raises(ValueError):
        load_csv(b'a\n1', 'x.xlsx')
    with pytest.raises(ValueError):
        load_csv(b'x' * (10 * 1024 * 1024 + 1))


def test_raw_strings_and_quoted_fields():
    df = load_csv(b'id,name\n001,"A, B"\n002,NA\n')
    assert df.iloc[0].tolist() == ['001', 'A, B']
    assert df.iloc[1, 1] == 'NA'


@pytest.mark.parametrize('rules', ['[]', '{', '{"a":{"type":"unknown"}}', '{"a":{"min":1}}', '{"a":{"required":"yes"}}', '{"a":{"canonical":["US","us"]}}', '{"a":{"allowed":[]}}', '{"a":{"type":"number","min":5,"max":1}}'])
def test_invalid_rules(rules):
    with pytest.raises(ValueError):
        parse_rules(rules)


def test_missing_column_and_empty_frame():
    with pytest.raises(ValueError, match='missing'):
        analyze(load_csv(b'a\n1'), {'b': {'required': True}})
    with pytest.raises(ValueError):
        analyze(pd.DataFrame(), {})


def test_clean_and_no_rules():
    issues, counts = analyze(load_csv(b'a\n1\n2'), {})
    scores, total = calculate_scores(counts)
    assert issues.empty and total == 100
    assert scores['validity'] is None and scores['consistency'] is None
    assert report_csv(issues).decode('utf-8-sig').startswith('row,column,')


def test_all_blank_and_duplicates():
    _, counts = analyze(load_csv(b'a,b\n, \n, \n'), {'a': {'type': 'email'}})
    scores, total = calculate_scores(counts)
    assert scores == {'completeness': 0, 'uniqueness': 50, 'validity': None, 'consistency': None}
    assert total == 25


@pytest.mark.parametrize('value,kind', [('nan','number'), ('inf','number'), ('bad','number'), ('x@x','email'), ('2025-02-29','date'), ('2025-1-01','date')])
def test_invalid_formats(value, kind):
    _, counts = analyze(pd.DataFrame({'x': [value]}), {'x': {'type': kind}})
    assert counts['validity'] == [1, 1]


def test_valid_formats_and_allowed():
    df = load_csv(b'n,e,d,c\n0,a@b.com,2024-02-29,US')
    issues, _ = analyze(df, {'n': {'type':'number', 'min':0, 'max':0}, 'e':{'type':'email'}, 'd':{'type':'date'}, 'c':{'allowed':['US']}})
    assert issues.empty
    issues, _ = analyze(df, {'c': {'allowed':['UK']}})
    assert len(issues) == 1


def test_nondefault_index_and_formula_export():
    df = pd.DataFrame({'x':['=HYPERLINK("bad")']}, index=[99])
    issues, _ = analyze(df, {'x':{'type':'email'}})
    assert issues.iloc[0]['row'] == 1
    assert "'=HYPERLINK" in report_csv(issues).decode('utf-8-sig')
    assert issues.iloc[0]['value'].startswith('=')


def test_score_edge_cases():
    assert calculate_scores({'x':[0,0]}) == ({'x':None}, None)
    with pytest.raises(ValueError):
        calculate_scores({'x':[2,1]})
