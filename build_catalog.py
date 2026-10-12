"""Refresh browser data from the editable CSV; run after editing the table."""
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parent
with (root / 'tracks.csv').open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f, delimiter=';'))
payload = json.dumps(rows, ensure_ascii=False, indent=2)
(root / 'tracks.json').write_text(payload, encoding='utf-8')
(root / 'catalog-data.js').write_text('window.CATALOG_TRACKS = ' + payload + ';\n', encoding='utf-8')
print(f'Catalog updated: {len(rows)} tracks')
