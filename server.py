"""Minimal dashboard + hunt-assistant chat (stand-in for OpenSearch Dashboards + POST /chat from D4 Part C).
Run: MODEL=qwen2.5:7b-instruct python3 -s server.py   then open http://localhost:8444"""
import json, os, time, uuid, datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import assistant
MODEL = os.environ.get("MODEL", "qwen2.5:7b-instruct")
LIVE = []   # alerts injected while running (simulates a new alert firing)
SEV = {"High": 0, "Medium": 1, "Low": 2}

PAGE = """<!doctype html><meta charset=utf-8><title>Home Security Dashboard - Spike</title>
<style>body{font:14px system-ui;margin:0;background:#f5f6f8;color:#1b1f24}header{background:#1f2a44;color:#fff;padding:12px 20px}
main{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:16px}section{background:#fff;border-radius:8px;padding:12px;box-shadow:0 1px 3px #0002}
h2{margin:0 0 8px;font-size:15px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:4px 6px;border-bottom:1px solid #eee;text-align:left}
.High{color:#b00020;font-weight:700}.Medium{color:#b26a00;font-weight:700}.Low{color:#2e7d32;font-weight:700}button{cursor:pointer}
#log{height:300px;overflow:auto;border:1px solid #ddd;padding:8px;margin-bottom:8px;background:#fafafa}.u{color:#1f2a44;font-weight:600}
.tc{font:12px ui-monospace,monospace;color:#555;background:#eef;padding:2px 6px;margin:2px 0;display:block}.meta{font-size:11px;color:#777}
input{width:70%;padding:6px}</style>
<header><b>Home Network Security - Technical Spike</b> &nbsp; <span class=meta style=color:#cbd>model: __MODEL__ (local, Ollama)</span></header>
<main><div>
<section><h2>Live alerts (newest first) <button onclick="fire()">Simulate new alert</button> <span id=fired class=meta></span></h2><table id=alerts></table></section>
<section style="margin-top:16px"><h2>Open incidents, sorted by severity (FR-14)</h2><table id=inc></table></section></div>
<section><h2>Hunt assistant</h2><div id=log></div>
<input id=msg placeholder="Ask a question, e.g. What did 192.168.50.23 do today?" onkeydown="if(event.key=='Enter')send()"><button onclick="send()">Send</button>
<div class=meta id=ctx>No incident selected</div></section></main>
<script>
let sel=null,session=Math.random().toString(36).slice(2);
async function load(){const a=await (await fetch('/api/alerts')).json(),i=await (await fetch('/api/incidents')).json();
document.getElementById('alerts').innerHTML='<tr><th>Time (UTC)</th><th>Source</th><th>Dest</th><th>Port</th><th>Signature</th></tr>'+a.slice(0,12).map(e=>`<tr><td>${e.timestamp.slice(11,19)}</td><td>${e.src_ip}</td><td>${e.dst_ip}</td><td>${e.dst_port}</td><td>${e.signature}</td></tr>`).join('');
document.getElementById('inc').innerHTML='<tr><th>ID</th><th>Severity</th><th>Source</th><th>Alerts</th><th></th></tr>'+i.map(x=>`<tr><td>${x.incident_id}</td><td class=${x.severity_label}>${x.severity_label}</td><td>${x.src_ip}</td><td>${x.alert_count}</td><td><button onclick="ask('${x.incident_id}')">Ask about this incident</button></td></tr>`).join('');}
async function fire(){const t0=performance.now();const r=await (await fetch('/api/inject',{method:'POST'})).json();
 for(;;){const a=await (await fetch('/api/alerts')).json();if(a.find(e=>e.event_id==r.event_id))break;await new Promise(s=>setTimeout(s,250));}
 await load();document.getElementById('fired').textContent='appeared after '+((performance.now()-t0)/1000).toFixed(2)+' s';}
function ask(id){sel=id;document.getElementById('ctx').textContent='Context preloaded: '+id;document.getElementById('msg').value='Is this dangerous?';send();}
async function send(){const m=document.getElementById('msg');const text=m.value.trim();if(!text)return;m.value='';const log=document.getElementById('log');
log.innerHTML+=`<div class=u>You: ${text}</div><div class=meta id=w>thinking...</div>`;log.scrollTop=1e9;
const r=await (await fetch('/chat',{method:'POST',body:JSON.stringify({session_id:session,incident_id:sel,message:text})})).json();
document.getElementById('w').remove();
log.innerHTML+=`<div>${r.answer.replace(/\\n/g,'<br>')}</div>`+r.tool_calls.map(c=>`<span class=tc>tool: ${c.name}(${JSON.stringify(c.params)}) -> ${c.result_count} results</span>`).join('')+`<div class=meta>status: ${r.status} &middot; ${(r.latency_ms/1000).toFixed(1)} s</div><br>`;log.scrollTop=1e9;}
load();setInterval(load,2000);
</script>"""

def alerts():
    a = [e for e in assistant.EVENTS if e["sensor"] == "suricata"] + LIVE
    return sorted(a, key=lambda e: e["timestamp"], reverse=True)

class H(BaseHTTPRequestHandler):
    def _send(self, obj, ctype="application/json"):
        b = obj.encode() if isinstance(obj, str) else json.dumps(obj).encode()
        self.send_response(200); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/": self._send(PAGE.replace("__MODEL__", MODEL), "text/html; charset=utf-8")
        elif self.path == "/api/alerts": self._send(alerts())
        elif self.path == "/api/incidents":
            self._send(sorted(assistant.INCIDENTS, key=lambda x: (SEV[x["severity_label"]], x["incident_id"])))
        else: self.send_error(404)
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); body = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/inject":
            e = dict(event_id=str(uuid.uuid4()), timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), src_ip="192.168.50.77",
                     dst_ip="192.168.50.10", src_port=51515, dst_port=443, protocol="tcp", sensor="suricata", severity=3, signature="TEST ALERT (simulated)")
            LIVE.append(e); self._send(e)
        elif self.path == "/chat":
            r = assistant.chat(MODEL, body.get("message", ""), body.get("incident_id"), body.get("session_id", "s"))
            self._send({k: v for k, v in r.items() if not k.startswith("_")})
        else: self.send_error(404)
    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"Dashboard on http://localhost:8444 (model {MODEL})"); ThreadingHTTPServer(("127.0.0.1", 8444), H).serve_forever()
