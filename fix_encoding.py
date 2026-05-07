import os
import glob

replacements = {
    "—": "—",
    "–": "–",
    "…": "…",
    "'": "'",
    """: '"',
    """: '"',
    """: '"',
    "💡": "💡",
    "🔄": "🔄",
    "🔍": "🔍",
    "🛡️": "🛡️",
    "🛡️": "🛡️",
    "📈": "📈",
    "💰": "💰",
    "🚀": "🚀",
    "📦": "📦",
    "✅": "✅",
    "⚠️": "⚠️",
    "⚠️": "⚠️",
    "🔴": "🔴",
    "─": "─",
    "═": "═",
    "→": "→",
    "↓": "↓",
    "↑": "↑",
    "📦": "📦",
    "🛠️": "🛠️"
}

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for bad, good in replacements.items():
            new_content = new_content.replace(bad, good)
            
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {filepath}")
    except Exception as e:
        pass

for ext in ['*.py', '*.js', '*.html', '*.css']:
    for filepath in glob.glob(f"**/{ext}", recursive=True):
        fix_file(filepath)
