"""Run the 20-question FR-09 test against one model and score it. Usage: python3 run_spike.py <model>"""
import json, re, sys, os, datetime
import assistant
model = sys.argv[1]
Q = json.load(open("questions.json"))
EMPTY_RE = re.compile(r"no data|no events|no results|no records|no matching|not found|found no|did not find|didn't find|no incidents|nothing", re.I)
IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?Z?)?")
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")

def fabricated(answer, results, question):
    """Values in the answer that appear in neither the tool results nor the user's question."""
    src = json.dumps(results) + " " + question + " " + assistant.NOW
    bad = []
    a = answer
    for rx in (IP_RE, ISO_RE, TIME_RE):
        for v in rx.findall(a):
            if v not in src and v.rstrip("Z") not in src: bad.append(v)
        a = rx.sub(" ", a)
    a = re.sub(r"(?m)^\s*\d+[.)]\s", " ", a)       # list numbering is not a count
    a = re.sub(r"\bINC-\d+\b", " ", a)
    for v in re.findall(r"\b\d+\b", a):
        if not re.search(r"(?<![\d.])" + v + r"(?![\d])", src): bad.append(v)
    return bad

def tool_ok(q, calls):
    for c in calls:
        if c["name"] in q["tools"] and all(str(c["params"].get(k)) == str(v) for k, v in q["args"].items()):
            return True
    return False

rows = []
for q in Q:
    r = assistant.chat(model, q["q"])
    fab = fabricated(r["answer"], r["_tool_results"], q["q"])
    empty_ok = bool(EMPTY_RE.search(r["answer"])) if q["empty"] else None
    row = dict(id=q["id"], question=q["q"], empty_case=q["empty"], answer=r["answer"], tool_calls=r["tool_calls"],
               latency_ms=r["latency_ms"], status=r["status"], fabricated=fab, empty_ok=empty_ok,
               tool_ok=tool_ok(q, r["tool_calls"]), error=r.get("_error"),
               fabricated_but_echoed_from_own_query=[v for v in fab if v in json.dumps(r["tool_calls"]) or v.rstrip("Z") in json.dumps(r["tool_calls"])])
    rows.append(row)
    print(f"Q{q['id']:>2} tool_ok={row['tool_ok']!s:5} fab={fab} empty_ok={empty_ok} {row['latency_ms']/1000:.1f}s  {r['answer'][:90]!r}", flush=True)

n_fab_answers = sum(1 for r in rows if r["fabricated"])
summary = dict(model=model, run_at=datetime.datetime.now().isoformat(timespec="seconds"),
    answers_with_fabricated_values=n_fab_answers,
    empty_cases_correct=f"{sum(1 for r in rows if r['empty_ok'])}/5",
    tool_correct_all20=f"{sum(r['tool_ok'] for r in rows)}/20",
    tool_correct_data15=f"{sum(r['tool_ok'] for r in rows if not r['empty_case'])}/15",
    under_30s=f"{sum(r['latency_ms'] <= 30000 for r in rows)}/20",
    fabricated_values_total=sum(len(r["fabricated"]) for r in rows),
    of_which_echoed_from_own_query=sum(len(r["fabricated_but_echoed_from_own_query"]) for r in rows),
    median_latency_s=round(sorted(r['latency_ms'] for r in rows)[10] / 1000, 1))
summary["PASS"] = (n_fab_answers == 0 and summary["empty_cases_correct"] == "5/5"
    and sum(r['tool_ok'] for r in rows) >= 18 and sum(r['latency_ms'] <= 30000 for r in rows) >= 19)
print(json.dumps(summary, indent=1))
OUT = os.environ.get("RESULTS_DIR", "results"); os.makedirs(OUT, exist_ok=True)
json.dump(dict(summary=summary, rows=rows), open(f"{OUT}/{'v2_' if os.environ.get('PROMPT_V2') else ''}{model.replace(':','_')}.json", "w"), indent=1)
