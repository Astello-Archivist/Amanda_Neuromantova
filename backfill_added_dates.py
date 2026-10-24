"""Restore catalog addition dates from the first publication and local import reports.

The original batch has a first-publication timestamp, not a recording or file date.
Existing dates are preserved. Future imports stamp added_at in import_new_tracks.py.
"""
import csv
import io
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
FIRST_COMMIT = '5ce3b01abb8aa7f3122ad8d57b78114f1b8277f2'
FIRST_PUBLISHED = '2026-10-12T00:37:34Z'
MOSCOW = ZoneInfo('Europe/Moscow')


def main():
    audit = ROOT/'audius-import/added-dates'
    audit.mkdir(exist_ok=True)
    snapshot = audit/'first-published-tracks.csv'
    if not snapshot.exists():
        url = f'https://raw.githubusercontent.com/Astello-Archivist/Amanda_Neuromantova/{FIRST_COMMIT}/tracks.csv'
        request = urllib.request.Request(url, headers={'User-Agent': 'Amanda-Catalog'})
        with urllib.request.urlopen(request, timeout=30) as response:
            snapshot.write_bytes(response.read())
    original = list(csv.DictReader(io.StringIO(snapshot.read_text('utf-8-sig')), delimiter=';'))
    assert len(original) == 166
    evidence = {r['id']: {'sha256': r['sha256'], 'added_at': datetime.fromisoformat(FIRST_PUBLISHED).astimezone(MOSCOW).isoformat(),
                          'source': 'first_github_publication', 'commit': FIRST_COMMIT} for r in original}
    for report_path in sorted((ROOT/'audius-import').glob('new-tracks-*/report.json')):
        report = json.loads(report_path.read_text('utf-8'))
        for entry in report.get('added', []):
            evidence.setdefault(entry['id'], {'sha256': entry['sha256'], 'added_at': entry.get('added_at') or report['checked_at'],
                                             'source': 'local_import_report', 'report': report_path.relative_to(ROOT).as_posix()})
    with (ROOT/'tracks.csv').open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream, delimiter=';')
        fields = list(reader.fieldnames)
        rows = list(reader)
    if 'added_at' not in fields:
        fields.insert(fields.index('duration_seconds') + 1, 'added_at')
    for row in rows:
        if row.get('added_at'):
            continue
        proof = evidence.get(row['id'])
        assert proof and proof['sha256'] == row['sha256'], row['id']
        row['added_at'] = proof['added_at']
    with (ROOT/'tracks.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fields, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    (audit/'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Addition dates: {len(rows)} tracks; original batch uses first publication, later tracks use import reports')


if __name__ == '__main__':
    main()
