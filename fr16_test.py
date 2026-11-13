"""FR-16 check: with an incident preloaded, 'Is this dangerous?' must call a tool for that incident (no restating). 5 incidents."""
import sys, json, assistant
model = sys.argv[1]; out = []
for inc in assistant.INCIDENTS:
    r = assistant.chat(model, "Is this dangerous?", inc["incident_id"])
    ok = any(inc["incident_id"] in json.dumps(c["params"]) or inc["src_ip"] in json.dumps(c["params"]) for c in r["tool_calls"])
    out.append(dict(incident=inc["incident_id"], used_context=ok, calls=r["tool_calls"], answer=r["answer"][:160], latency_ms=r["latency_ms"]))
    print(inc["incident_id"], "used preloaded context:", ok, f'{r["latency_ms"]/1000:.1f}s')
print(model, "FR-16:", sum(o["used_context"] for o in out), "/5")
json.dump(out, open(f"results/fr16{"_explicit" if __import__("os").environ.get("CONTEXT_MODE") else ""}_{model.replace(':','_')}.json", "w"), indent=1)
