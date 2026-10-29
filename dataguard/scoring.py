"""Each dimension is 100 * (1 - failures / opportunities)."""
def calculate_scores(counts):
    scores = {}
    for name, (failed, total) in counts.items():
        if total < 0 or not 0 <= failed <= total:
            raise ValueError('Counts must satisfy 0 <= failures <= opportunities.')
        scores[name] = 100 * (1 - failed / total) if total else None
    assessed = [score for score in scores.values() if score is not None]
    return scores, sum(assessed) / len(assessed) if assessed else None
