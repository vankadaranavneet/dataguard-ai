"""Export a separate report, with spreadsheet formula injection protection."""
def report_csv(issues):
    safe = issues.copy(deep=True)
    for col in safe.select_dtypes(include=['object', 'string']):
        safe[col] = safe[col].map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v)
    return safe.to_csv(index=False).encode('utf-8-sig')
