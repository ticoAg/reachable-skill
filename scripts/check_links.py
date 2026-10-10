"""Check repository-local Markdown links without network access."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
failures = []
for file in root.rglob('*.md'):
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', file.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        path = (file.parent / target.split('#', 1)[0]).resolve()
        if not path.is_relative_to(root) or not path.exists():
            failures.append(f'{file.relative_to(root)}: {target}')
if failures:
    raise SystemExit('\n'.join(failures))
print('All repository-local Markdown links resolve.')
