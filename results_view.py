"""Render results/<model>.json (the scored run) as an HTML page, one per model, for screenshots."""
import json, html
for m, f in (("llama3.1:8b","llama3.1_8b"),("qwen2.5:7b-instruct","qwen2.5_7b-instruct"),("mistral:7b-instruct","mistral_7b-instruct")):
    d = json.load(open(f"results/{f}.json")); s = d["summary"]
    rows = "".join(f"<tr class={'bad' if r['fabricated'] or not r['tool_ok'] or r['empty_ok']==False else ''}><td>{r['id']}</td><td>{html.escape(r['question'])}</td>"
        f"<td>{'yes' if r['empty_case'] else ''}</td><td>{'ok' if r['tool_ok'] else 'WRONG'}</td><td>{html.escape(', '.join(r['fabricated']))}</td>"
        f"<td>{'' if r['empty_ok'] is None else ('ok' if r['empty_ok'] else 'MISSED')}</td><td>{r['latency_ms']/1000:.1f}</td><td>{html.escape(r['answer'][:70].replace(chr(10),' '))}</td></tr>" for r in d["rows"])
    page = f"""<!doctype html><meta charset=utf-8><title>{m}</title><style>body{{font:12px system-ui;margin:14px}}h2{{margin:0 0 4px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #bbb;padding:2px 5px;text-align:left}}th{{background:#eee}}.bad{{background:#fde8e8}}pre{{background:#f4f4f4;padding:6px;margin:4px 0}}</style>
<h2>Scored run: {m} (run_spike.py, {s['run_at']})</h2><pre>{html.escape(json.dumps({k:v for k,v in s.items() if k!='model'}, indent=0)).replace(chr(10),' | ')}</pre>
<table><tr><th>Q</th><th>Question</th><th>Empty case</th><th>Tool</th><th>Unseen values</th><th>Said no data</th><th>Sec</th><th>Answer (first 70 chars)</th></tr>{rows}</table>"""
    open(f"evidence/results_{f}.html","w").write(page)
