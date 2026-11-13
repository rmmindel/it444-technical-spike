"""FR-13 stand-in: fire 20 simulated alerts, measure time until each is visible in the dashboard feed. Pass: >=19/20 within 15 s."""
import json, time, urllib.request
B = "http://127.0.0.1:8444"
def get(p): return json.load(urllib.request.urlopen(B + p))
res = []
for i in range(20):
    t0 = time.time(); e = json.load(urllib.request.urlopen(urllib.request.Request(B + "/api/inject", b"{}", method="POST")))
    while not any(x["event_id"] == e["event_id"] for x in get("/api/alerts")): time.sleep(0.25)
    res.append(round(time.time() - t0, 3)); time.sleep(0.5)
print("trials:", len(res), "max s:", max(res), "within 15s:", sum(r <= 15 for r in res), "/20")
json.dump(res, open("results/fr13_trials.json", "w"))
