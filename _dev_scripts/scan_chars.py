import sys

TARGETS = ["static/index.html", "static/app.js", "app.py"]

for path in TARGETS:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    found = []
    for i, line in enumerate(lines, 1):
        for j, c in enumerate(line):
            cp = ord(c)
            if 128 <= cp <= 255:
                found.append((i, j, cp, line.strip()))
                break
    
    if found:
        sys.stdout.buffer.write(f"\n--- {path}: {len(found)} lines with latin-1 range chars ---\n".encode('utf-8'))
        for row in found[:30]:
            out = f"  Line {row[0]}: U+{row[2]:04X} -> {row[3][:100]}\n"
            sys.stdout.buffer.write(out.encode('utf-8', errors='replace'))
    else:
        sys.stdout.buffer.write(f"\n--- {path}: CLEAN ---\n".encode('utf-8'))
