import re

TARGETS = ["static/index.html", "static/app.js", "app.py"]

# Known mojibake emoji -> correct emoji (hardcoded, reliable)
EMOJI_MAP = {
    # The chars below are Latin-1 reinterpretation of UTF-8 emoji bytes
    # We match them by their Unicode codepoints as they appear in the file
    "\u00f0\u0178\u00a2":  "\U0001f3e2",  # ðŸ¢ -> 🏢 (office)
    "\u00f0\u0178\u0094":  "\U0001f514",  # ðŸ" -> 🔍 wait let me be careful
}

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # 1. Remove stray U+0090 (DCS control char - leftover from broken box-drawing fix)
    content = content.replace('\u0090', '')

    # 2. Fix Ã— -> × (multiply sign), Ã — can be close button
    content = content.replace('\u00c3\u00d7', '\u00d7')  # Ã× -> ×
    content = content.replace('\u00c3\u00a6', '\u00e6')  # Ã¦ -> æ
    # The close button × character
    content = content.replace('\u00c3\u0097', '\u00d7')  # Ã— -> ×

    # 3. Try cp1252 decode trick on any remaining sequences starting with â,ð,Ã,Â
    def try_fix(m):
        s = m.group(0)
        try:
            fixed = s.encode('cp1252').decode('utf-8')
            return fixed
        except Exception:
            return s

    content = re.sub(r'[\u00e2\u00f0\u00c3\u00c2][\u0080-\u024f]{1,4}', try_fix, content)

    # 4. Remove any remaining stray U+0090 that cp1252 trick introduced or missed
    content = content.replace('\u0090', '')

    # 5. Fix any Â· -> · (middle dot) that wasn't caught
    content = content.replace('\u00c2\u00b7', '\u00b7')

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {path}")
    else:
        print(f"No changes: {path}")

for t in TARGETS:
    fix_file(t)
