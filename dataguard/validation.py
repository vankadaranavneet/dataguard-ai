"""Deterministic rules: flag observations, never alter the input."""
import json
import math
import re
from datetime import datetime
import pandas as pd
from .processing import missing_mask

ISSUE_COLUMNS = ['row', 'column', 'dimension', 'rule', 'severity', 'value', 'explanation', 'suggestion']
ALLOWED = {'required', 'type', 'min', 'max', 'allowed', 'canonical'}


def parse_rules(text):
    try:
        rules = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f'Rules must be valid JSON: {exc.msg}') from exc
    if not isinstance(rules, dict):
        raise ValueError('Rules must be a JSON object keyed by column name.')
    for col, rule in rules.items():
        if not isinstance(rule, dict) or set(rule) - ALLOWED:
            raise ValueError(f'{col}: unsupported rule keys or rule is not an object.')
        if 'required' in rule and not isinstance(rule['required'], bool):
            raise ValueError(f'{col}: required must be true or false.')
        if rule.get('type') not in (None, 'number', 'email', 'date'):
            raise ValueError(f'{col}: type must be number, email, or date.')
        for key in ('min', 'max'):
            if key in rule and (isinstance(rule[key], bool) or not isinstance(rule[key], (int, float)) or not math.isfinite(rule[key])):
                raise ValueError(f'{col}: {key} must be a finite number.')
        if ('min' in rule or 'max' in rule) and rule.get('type') != 'number':
            raise ValueError(f'{col}: numeric bounds require type number.')
        if rule.get('min', -math.inf) > rule.get('max', math.inf):
            raise ValueError(f'{col}: min cannot exceed max.')
        for key in ('allowed', 'canonical'):
            if key in rule and (not isinstance(rule[key], list) or not rule[key] or not all(isinstance(v, str) and v.strip() for v in rule[key])):
                raise ValueError(f'{col}: {key} must be a nonempty list of nonblank strings.')
        canonical = rule.get('canonical', [])
        if len({x.strip().casefold() for x in canonical}) != len(canonical):
            raise ValueError(f'{col}: canonical spellings must be unambiguous.')
    return rules


def valid_value(value, rule):
    kind = rule.get('type')
    if kind == 'number':
        try:
            number = float(value)
            if not math.isfinite(number) or not rule.get('min', -math.inf) <= number <= rule.get('max', math.inf):
                return False
        except (ValueError, OverflowError):
            return False
    elif kind == 'email' and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value) is None:
        return False
    elif kind == 'date':
        try:
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) is None:
                return False
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return False
    return 'allowed' not in rule or value in rule['allowed']


def analyze(df, rules):
    # Validate even when this function is called outside the UI.
    rules = parse_rules(json.dumps(rules))
    missing_columns = sorted(set(rules) - set(df.columns))
    if missing_columns:
        raise ValueError('Configured columns are missing: ' + ', '.join(missing_columns))
    if df.empty or not len(df.columns):
        raise ValueError('At least one row and column are required.')
    blank = missing_mask(df)
    duplicates = df.duplicated()
    issues = []
    counts = {'completeness': [int(blank.to_numpy().sum()), int(df.size)],
              'uniqueness': [int(df.duplicated().sum()), len(df)],
              'validity': [0, 0], 'consistency': [0, 0]}

    def add(row, col, dim, rule, severity, value, explanation, suggestion):
        issues.append([row, col, dim, rule, severity, '' if pd.isna(value) else str(value), explanation, suggestion])

    for pos, (_, record) in enumerate(df.iterrows(), 1):
        for col in df.columns:
            value = record[col]
            rule = rules.get(col, {})
            if blank.iloc[pos - 1][col]:
                add(pos, col, 'completeness', 'missing', 'High' if rule.get('required') else 'Medium', value,
                    'This cell is blank.', 'Confirm the source value; do not invent a replacement.')
                continue
            value = str(value)
            if any(k in rule for k in ('type', 'allowed')):
                counts['validity'][1] += 1
                if not valid_value(value, rule):
                    counts['validity'][0] += 1
                    add(pos, col, 'validity', 'validation', 'High', value,
                        f'Value violates configured constraints: {json.dumps(rule)}',
                        'Verify against the source and the configured rule before correcting.')
            if 'canonical' in rule:
                counts['consistency'][1] += 1
                mapping = {x.strip().casefold(): x for x in rule['canonical']}
                target = mapping.get(value.strip().casefold())
                if value not in rule['canonical']:
                    counts['consistency'][0] += 1
                    add(pos, col, 'consistency', 'canonical', 'Medium', value,
                        'Value is not an approved canonical spelling.',
                        f'Review proposed spelling: {target}' if target else 'Review the value or extend the approved vocabulary.')
        if duplicates.iloc[pos - 1]:
            add(pos, '*', 'uniqueness', 'duplicate', 'Medium', '',
                'This record exactly repeats an earlier record.', 'Check whether this is a legitimate repeat before removing it.')
    return pd.DataFrame(issues, columns=ISSUE_COLUMNS), counts
