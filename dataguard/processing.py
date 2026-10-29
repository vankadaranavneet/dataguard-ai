"""Strict CSV ingestion. Keep raw strings so IDs and original formatting survive."""
import csv
import io
import pandas as pd

MAX_BYTES = 10 * 1024 * 1024


def load_csv(data: bytes, filename: str = 'dataset.csv') -> pd.DataFrame:
    if not filename.lower().endswith('.csv'):
        raise ValueError('Please upload a .csv file.')
    if len(data) > MAX_BYTES:
        raise ValueError('File exceeds the 10 MB limit.')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('Save the CSV using UTF-8 encoding.') from exc
    if '\x00' in text:
        raise ValueError('Binary content is not supported.')
    try:
        rows = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    except csv.Error as exc:
        raise ValueError(f'Malformed CSV: {exc}') from exc
    if not rows or not rows[0]:
        raise ValueError('The CSV is empty.')
    header = rows[0]
    if any(not name.strip() for name in header) or len(set(header)) != len(header):
        raise ValueError('Column names must be nonblank and unique.')
    if any(len(row) != len(header) for row in rows[1:]):
        raise ValueError('Malformed CSV: every record must have the same number of fields as the header.')
    if len(rows) == 1:
        raise ValueError('The CSV has headers but no data rows.')
    return pd.DataFrame(rows[1:], columns=header, dtype='string')


def missing_mask(df):
    return df.isna() | df.apply(lambda col: col.astype('string').str.strip().eq('').fillna(True))


def overview(df):
    return pd.DataFrame({'column': df.columns, 'storage_type': [str(t) for t in df.dtypes],
                         'missing': missing_mask(df).sum().to_numpy(),
                         'distinct_nonblank': [df.loc[~missing_mask(df)[c], c].nunique() for c in df]})
