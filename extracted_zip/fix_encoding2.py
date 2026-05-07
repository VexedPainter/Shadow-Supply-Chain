import os
import glob
import re

def fix_mojibake(text):
    # Find all sequences of characters that are likely mojibake
    # Basically characters that resulted from utf-8 bytes being read as cp1252
    # â is \u00e2, which corresponds to the first byte of 3-byte UTF-8 sequences.
    # ð is \u00f0, which corresponds to the first byte of 4-byte UTF-8 sequences.
    
    # Let's try to find all occurrences of â or ð followed by 1 to 3 characters
    # that are typical cp1252 characters.
    
    # Actually, let's just try to encode/decode words or chunks.
    def replace_chunk(match):
        chunk = match.group(0)
        try:
            # If it's pure mojibake, this will work
            return chunk.encode('cp1252').decode('utf-8')
        except:
            return chunk

    # Regex to match sequences starting with â (\u00e2) or ð (\u00f0) followed by 1 to 3 characters from the cp1252 set that are not ASCII
    # Or we can just use the specific ones we know.
    known_bad = [
        "—", "–", "…", "’", "“", """, """, "💡", "🔄", "🔎", 
        "🛡ï¸", "🛡", "📈", "💰", "🚀", "📦", "✅", "⚠️", "⚠️", 
        "🔴", "─", "═", "→", "↓", "↑", "✕", " ï¸", "⚠️"
    ]
    
    for bad in known_bad:
        try:
            good = bad.encode('cp1252').decode('utf-8')
            text = text.replace(bad, good)
        except:
            pass
            
    # Also catch any 3-char sequence starting with â
    # that can be fixed
    def fix_any(m):
        try:
            return m.group(0).encode('cp1252').decode('utf-8')
        except:
            return m.group(0)
            
    text = re.sub(r'[=][\x80-\xff\u0153\u0161\u017e\u0152\u0160\u017d\u0192\u02c6\u02dc\u2013\u2014\u2018\u2019\u201a\u201c\u201d\u201e\u2020\u2021\u2022\u2026\u2030\u2039\u203a\u20ac]{1,3}', fix_any, text)
    
    return text

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = fix_mojibake(content)
        
        # specific hardcoded fallbacks just in case cp1252 trick fails
        fallbacks = {
            "—": "—", "–": "–", "…": "…", "’": "'", "“": '"', """: '"',
            "💡": "💡", "🔄": "🔄", "🔎": "🔍", "🛡ï¸": "🛡️", "🛡": "🛡️",
            "📈": "📈", "💰": "💰", "🚀": "🚀", "📦": "📦", "✅": "✅",
            "⚠️": "⚠️", "⚠️": "⚠️", "🔴": "🔴", "─": "─", "═": "═"
        }
        for b, g in fallbacks.items():
            new_content = new_content.replace(b, g)

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {filepath}")
    except Exception as e:
        pass

for ext in ['*.py', '*.js', '*.html', '*.css']:
    for filepath in glob.glob(f"**/{ext}", recursive=True):
        fix_file(filepath)
