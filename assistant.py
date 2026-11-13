"""Hunt assistant core: chat loop + 3 tools (D4 Part C). Used by both the test harness and the dashboard."""
import json, os, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
NOW = "2026-11-12T12:00:00Z"   # fixed clock so tests are repeatable
EVENTS = json.load(open(os.path.join(HERE, "data/events.json")))
INCIDENTS = json.load(open(os.path.join(HERE, "data/incidents.json")))
MAX_TOOL_CALLS = 3
TIMEOUT_S = 30

SYSTEM = f"""You are a home-network security hunt assistant. The current time is {NOW}.
RULES:
1. Answer ONLY from tool results. Never state an IP address, timestamp, port or count that is not in a tool result.
2. Always call a tool before answering a question about network activity or incidents.
3. If a tool returns no results or an error, reply exactly: "No data found" and say what you searched for. Do not guess.
4. Use plain language for a non-expert. Keep answers short."""

TOOLS = [
 {"type":"function","function":{"name":"search_events","description":"Search stored network events by IP, port, time range or sensor.",
  "parameters":{"type":"object","properties":{"ip":{"type":"string"},"port":{"type":"integer"},
   "start":{"type":"string","description":"ISO8601 UTC"},"end":{"type":"string","description":"ISO8601 UTC"},
   "sensor":{"type":"string","enum":["suricata","zeek"]}},"required":["start","end"]}}},
 {"type":"function","function":{"name":"get_ip_history","description":"Return all incidents involving an IP address.",
  "parameters":{"type":"object","properties":{"ip":{"type":"string"}},"required":["ip"]}}},
 {"type":"function","function":{"name":"get_incident_details","description":"Return an incident and every alert behind it.",
  "parameters":{"type":"object","properties":{"incident_id":{"type":"string"}},"required":["incident_id"]}}}]

if os.environ.get("PROMPT_V2"):   # follow-up variant: tighter empty-case rule
    SYSTEM += "\n5. When there is no data, reply with only: No data found for <the IP, port or incident ID asked about>. Do NOT mention any dates or times in that reply."

def run_tool(name, a):
    try:
        if name == "search_events":
            r = [e for e in EVENTS
                 if (not a.get("ip") or a["ip"] in (e["src_ip"], e["dst_ip"]))
                 and (not a.get("port") or int(a["port"]) in (e["src_port"], e["dst_port"]))
                 and (not a.get("sensor") or e["sensor"] == a["sensor"])
                 and (not a.get("start") or e["timestamp"] >= a["start"])
                 and (not a.get("end") or e["timestamp"] <= a["end"])]
            return {"results": r[:100], "total_count": len(r), "truncated": len(r) > 100}
        if name == "get_ip_history":
            i = [{k: x[k] for k in ("incident_id","first_seen","last_seen","alert_count","severity_label")}
                 for x in INCIDENTS if x["src_ip"] == a.get("ip")]
            return {"incidents": i, "total_count": len(i)}
        if name == "get_incident_details":
            x = next((x for x in INCIDENTS if x["incident_id"] == a.get("incident_id")), None)
            if not x: return {"error": "incident not found", "total_count": 0}
            al = [e for e in EVENTS if e["event_id"] in x["alert_ids"]]
            return {"incident": {k: v for k, v in x.items() if k != "alert_ids"}, "alerts": al, "total_count": len(al)}
        return {"error": f"unknown tool {name}"}
    except Exception as ex:
        return {"error": f"bad arguments: {ex}"}

def _chat(model, messages):
    body = json.dumps({"model": model, "messages": messages, "tools": TOOLS, "stream": False,
                       "options": {"temperature": 0}}).encode()
    req = urllib.request.Request(OLLAMA + "/api/chat", body, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))["message"]

def chat(model, message, incident_id=None, session_id="s"):
    """Returns the D4 Dashboard<->Hunt Assistant response: answer, tool_calls[], latency_ms, status."""
    t0 = time.time()
    ctx = f"\n(The user selected incident {incident_id}; use it if they say 'this'.)" if incident_id else ""
    if incident_id and os.environ.get("CONTEXT_MODE") == "explicit":   # follow-up variant: dashboard injects the facts
        inc = next((x for x in INCIDENTS if x["incident_id"] == incident_id), None)
        message = f"[Selected incident {incident_id}" + (f", source IP {inc['src_ip']}" if inc else "") + f"] {message}"
        ctx = ""
    msgs = [{"role": "system", "content": SYSTEM + ctx}, {"role": "user", "content": message}]
    calls, results = [], []
    try:
        for _ in range(MAX_TOOL_CALLS + 1):
            m = _chat(model, msgs)
            msgs.append(m)
            if not m.get("tool_calls"):
                break
            for tc in m["tool_calls"]:
                if len(calls) >= MAX_TOOL_CALLS: break
                f = tc["function"]; args = f.get("arguments") or {}
                res = run_tool(f["name"], args)
                calls.append({"name": f["name"], "params": args, "result_count": res.get("total_count", 0)})
                results.append(res)
                msgs.append({"role": "tool", "tool_name": f["name"], "content": json.dumps(res)})
            if len(calls) >= MAX_TOOL_CALLS:
                msgs.append({"role": "user", "content": "Answer now using the tool results."})
        else:
            m = {"content": ""}
        answer = (m.get("content") or "").strip()
        ms = int((time.time() - t0) * 1000)
        status = "timeout" if ms > TIMEOUT_S * 1000 else "ok"
        if calls and all(c["result_count"] == 0 for c in calls): status = "no_data" if status == "ok" else status
        return {"session_id": session_id, "answer": answer, "tool_calls": calls, "latency_ms": ms,
                "status": status, "_tool_results": results}
    except Exception as ex:
        return {"session_id": session_id, "answer": "The assistant is unavailable. Please try again.",
                "tool_calls": calls, "latency_ms": int((time.time()-t0)*1000), "status": "error",
                "_tool_results": results, "_error": str(ex)}
