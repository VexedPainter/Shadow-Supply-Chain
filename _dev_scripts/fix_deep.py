"""
Deep mojibake fix using proper cp1252 + latin-1 hybrid decoding.
The cp1252 standard maps bytes 0x80-0x9F to special Unicode chars,
but bytes like 0x81, 0x8D, 0x8F, 0x90, 0x9D are undefined in cp1252
and fall through to their Latin-1 equivalents (U+0081 etc).

When the original UTF-8 file was misread as cp1252/Latin-1, each byte
became a Unicode codepoint. This script reverses that mapping to recover
the original bytes, then decodes as UTF-8.
"""
import re

# cp1252 special mappings: code point -> byte value (reverse lookup)
CP1252_TO_BYTE = {
    '\u20ac': 0x80, '\u201a': 0x82, '\u0192': 0x83, '\u201e': 0x84,
    '\u2026': 0x85, '\u2020': 0x86, '\u2021': 0x87, '\u02c6': 0x88,
    '\u2030': 0x89, '\u0160': 0x8a, '\u2039': 0x8b, '\u0152': 0x8c,
    '\u017d': 0x8e, '\u2018': 0x91, '\u2019': 0x92, '\u201c': 0x93,
    '\u201d': 0x94, '\u2022': 0x95, '\u2013': 0x96, '\u2014': 0x97,
    '\u02dc': 0x98, '\u2122': 0x99, '\u0161': 0x9a, '\u203a': 0x9b,
    '\u0153': 0x9c, '\u017e': 0x9e, '\u0178': 0x9f,
}

def char_to_byte(c):
    """Convert a mojibake character back to its original byte value."""
    if c in CP1252_TO_BYTE:
        return CP1252_TO_BYTE[c]
    cp = ord(c)
    if cp < 256:
        return cp
    return None  # Cannot map

def fix_mojibake_seq(s):
    """Try to decode a mojibake string back to correct Unicode."""
    byte_vals = []
    for c in s:
        b = char_to_byte(c)
        if b is None:
            return s  # Can't convert, leave as is
        byte_vals.append(b)
    try:
        return bytes(byte_vals).decode('utf-8')
    except Exception:
        return s

# Pattern: sequences of chars that are mojibake.
# Lead bytes for UTF-8 multi-byte sequences:
# 0xC2-0xDF (2-byte), 0xE0-0xEF (3-byte), 0xF0-0xF4 (4-byte)
# These appear in the file as Latin-1 codepoints U+00C2, U+00E2, U+00F0, U+00EF etc.
LEAD_CHARS = (
    '\u00c2', '\u00c3',  # 2-byte UTF-8 leads
    '\u00e2', '\u00e0', '\u00e1', '\u00e3', '\u00e4', '\u00e5',
    '\u00e6', '\u00e7', '\u00e8', '\u00e9', '\u00ea', '\u00eb',
    '\u00ec', '\u00ed', '\u00ee', '\u00ef',  # 3-byte UTF-8 leads
    '\u00f0', '\u00f1', '\u00f2', '\u00f3', '\u00f4',  # 4-byte UTF-8 leads
)
LEAD_PATTERN = '[' + ''.join(re.escape(c) for c in LEAD_CHARS) + ']'
# Continuation bytes (0x80-0xBF in UTF-8) appear as U+0080-U+00BF or cp1252 special chars
CONT_CHARS = r'[\u0080-\u00bf\u0178\u0160\u0161\u0152\u0153\u017d\u017e\u0192\u02c6\u02dc\u0090\u0091\u0092\u0093\u0094\u0095\u0096\u0097\u0098\u0099\u009a\u009b\u009c\u009d\u009e\u009f\u0081\u008f\u008d\u008e\u008c\u0080\u0082\u0083\u0084\u0085\u0086\u0087\u0088\u0089\u008a\u008b]'

PATTERN = re.compile(LEAD_PATTERN + CONT_CHARS + r'{1,6}')

TARGETS = ["static/index.html", "static/app.js", "app.py"]

for path in TARGETS:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # Apply the deep fix
    content = PATTERN.sub(lambda m: fix_mojibake_seq(m.group(0)), content)

    # Remove any remaining stray C1 control chars (U+0080-U+009F) that aren't valid
    # Exception: keep U+00A0 (non-breaking space), U+00B7 (middle dot)
    content = re.sub(r'[\u0080-\u009f]', '', content)

    # Fix Ã— (close ×) - U+00C3 + U+2014 (em dash used as stand-in for 0x97)
    content = content.replace('\u00c3\u2014', '\u00d7')  # Ã— -> ×
    # Also fix plain Ã× 
    content = content.replace('\u00c3\u00d7', '\u00d7')

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {path}")
    else:
        print(f"No changes needed: {path}")

print("\nDone. Running verification scan...")
