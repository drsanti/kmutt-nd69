"""Deterministic, standard-library-only offline packager. Run: python build.py."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEEK = ROOT.parent
JS = ['core.js', 'signals.js', 'display.js', 'decisions.js', 'presentation.js']

def build():
    chapters = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'slides').glob('*.json'))]
    assert [len(c['slides']) for c in chapters] == [5,10,12,14,13,12,15,4]
    datasets = {}
    for name in ['idle','shake','circle','lift']:
        with (WEEK/f'labs/python/samples/{name}.csv').open(newline='',encoding='utf-8') as f:
            datasets[name] = [[float(row[k]) for k in ['t_s','ax','ay','az','gx','gy','gz']] for row in csv.DictReader(f)]
        assert len(datasets[name]) == 100
    manifest = json.loads((ROOT/'assets/source-manifest.json').read_text(encoding='utf-8'))
    for item in manifest['courseSources']:
        canonical = (WEEK/item['path']).read_bytes().replace(b'\r\n', b'\n')
        assert hashlib.sha256(canonical).hexdigest() == item['sha256'], f"Source changed: {item['path']}; review slides and update manifest."
    # JSON escapes '<' to prevent a slide string from ending an inline script.
    def js_json(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    data = f'const W09_CHAPTERS={js_json(chapters)};\nconst W09_DATA={js_json(datasets)};\nconst W09_META={js_json(manifest)};\n'
    (ROOT/'assets/content.js').write_text(data,encoding='utf-8',newline='\n')
    template = (ROOT/'template.html').read_text(encoding='utf-8')
    modular = template.replace('<!--STYLES-->','<link rel="stylesheet" href="styles/presentation.css">').replace('<!--SCRIPTS-->','\n'.join(f'<script src="{p}"></script>' for p in ['assets/content.js']+['components/'+p for p in JS]))
    offline = template.replace('<!--STYLES-->','<style>\n'+(ROOT/'styles/presentation.css').read_text(encoding='utf-8')+'\n</style>').replace('<!--SCRIPTS-->','<script>\n'+data+'\n'+ '\n'.join((ROOT/'components'/p).read_text(encoding='utf-8') for p in JS)+'\n</script>')
    (ROOT/'index.html').write_text(modular,encoding='utf-8',newline='\n')
    (ROOT/'dist/week09-presentation.html').write_text(offline,encoding='utf-8',newline='\n')
    print(f'Built 85 slides, {len(datasets)} exact CSV datasets; offline HTML {len(offline.encode()):,} bytes')

if __name__=='__main__': build()
