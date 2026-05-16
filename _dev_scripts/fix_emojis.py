import glob

emoji_map = {
    "📊": "📊",
    "📄": "📄",
    "🚨": "🚨",
    "📉": "📉",
    "🏢": "🏢",
    "📥": "📥",
    "📄": "📄",
    "📋": "📋",
    "🔍": "🔍",
    "🛒": "🛒",
    "🔬": "🔬",
    "🧠": "🧠",
    "🤖": "🤖",
    "🗑️": "🗑️",
    "💬": "💬",
    "🟢": "🟢",
    "🟡": "🟡",
    "🚫": "🚫",
    "🏃": "🏃",
    "🚶": "🚶",
    "🎯": "🎯",
    "🔩": "🔩",
    "📍": "📍",
    "·": "·",
    "⚠️": "⚠️",
    "✅": "✅",
    "⚠️": "⚠️"
}

def fix(p):
    try:
        with open(p, 'r', encoding='utf-8') as f: c = f.read()
        orig = c
        for bad, good in emoji_map.items():
            c = c.replace(bad, good)
        if c != orig:
            with open(p, 'w', encoding='utf-8') as f: f.write(c)
            print('Fixed emojis in', p)
    except:
        pass

for e in ['*.py', '*.js', '*.html', '*.css']:
    for p in glob.glob('**/' + e, recursive=True): fix(p)
