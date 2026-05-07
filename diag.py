"""Print exact Unicode codepoints for specific bad lines to understand what's in the file."""
import sys

CHECKS = {
    "static/index.html": [519, 542],
    "static/app.js": [730, 1239, 1793, 1845, 1882],
}

for path, line_nums in CHECKS.items():
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for ln in line_nums:
        line = lines[ln - 1].rstrip('\n')
        parts = []
        for c in line[:120]:
            cp = ord(c)
            if cp > 127:
                parts.append(f'U+{cp:04X}({repr(c)})')
            else:
                parts.append(c)
        out = f"\n{path}:{ln}:\n  " + ''.join(parts) + "\n"
        sys.stdout.buffer.write(out.encode('utf-8', errors='replace'))
