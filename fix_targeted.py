"""
Final surgical fix based on exact codepoint diagnosis.
Known remaining broken sequences and their correct replacements:
"""

TARGETS = ["static/index.html", "static/app.js"]

# Exact Unicode sequence -> correct replacement
# Each tuple: (bad_string_in_file, correct_string)
DIRECT = [
    # ðŸ" = U+00F0 + U+0178 + U+201D  (magnifying glass 🔍, truncated F0 9F 94 [8D stripped])
    ('\u00f0\u0178\u201d', '🔍'),

    # ðŸ—' = U+00F0 + U+0178 + U+2014 + U+2018 (trash can 🗑, from F0 9F 97 91, FE0F variation stays)
    ('\u00f0\u0178\u2014\u2018', '🗑'),

    # ðŸ¢ = U+00F0 + U+0178 + U+00A2 (turtle 🐢 for "Slow", from F0 9F [90 stripped] A2)
    ('\u00f0\u0178\u00a2', '🐢'),

    # Ï€ = U+00CF + U+20AC (pi symbol π, from CF 80 where 80=€ in cp1252)
    ('\u00cf\u20ac', 'π'),

    # Any remaining Ã× close button (shouldn't be needed but just in case)
    ('\u00c3\u00d7', '×'),
    ('\u00c3\u2014', '×'),
]

for path in TARGETS:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    for bad, good in DIRECT:
        content = content.replace(bad, good)

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {path}")
    else:
        print(f"No changes: {path}")

print("\nDone.")
