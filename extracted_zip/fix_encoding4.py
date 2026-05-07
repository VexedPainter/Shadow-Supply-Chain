import glob, re

def fix(p):
    try:
        with open(p, 'r', encoding='utf-8') as f: c = f.read()
        orig = c
        # Replace the literal mojibake for box drawing and others
        c = c.replace('=', '=')
        c = c.replace('=', '=')
        c = c.replace('-', '-')
        c = c.replace('⏱️', '⏱️')
        c = c.replace('⏱️', '⏱️')
        
        # Aggressive blanket replace for any remaining sequence of â followed by symbols
        c = re.sub(r'â[•”€±ï¸\x80-\xff]+', '=', c)
        
        if c != orig:
            with open(p, 'w', encoding='utf-8') as f: f.write(c)
            print('Fixed', p)
    except Exception as e:
        pass

for e in ['*.py', '*.js', '*.html', '*.css']:
    for p in glob.glob('**/' + e, recursive=True): fix(p)
