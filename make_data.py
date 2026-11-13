"""Generate the small seeded event set (stand-in for OpenSearch) used by the spike."""
import json, uuid, random
random.seed(444)
D = "2026-11-12"
def ts(h, m, s): return f"{D}T{h:02d}:{m:02d}:{s:02d}Z"
events, incidents = [], []

def add_inc(iid, src, first, last, label, sig, dst, ports, n, sensor="suricata", sev=3):
    ids = []
    for i in range(n):
        span = (last[0]*3600+last[1]*60) - (first[0]*3600+first[1]*60)
        t = first[0]*3600 + first[1]*60 + (span * i // max(n-1, 1))
        e = dict(event_id=str(uuid.UUID(int=random.getrandbits(128))), timestamp=ts(t//3600, t%3600//60, t%60),
                 src_ip=src, dst_ip=dst, src_port=random.randint(40000, 60000), dst_port=ports[i % len(ports)],
                 protocol="tcp", sensor=sensor, severity=sev, signature=sig)
        events.append(e); ids.append(e["event_id"])
    incidents.append(dict(incident_id=iid, src_ip=src, first_seen=ts(*first, 0), last_seen=ts(*last, 0),
                          alert_ids=ids, alert_count=n, status="open", severity_label=label, signature=sig))

add_inc("INC-001", "192.168.50.23", (9,14), (9,16), "High", "ET SCAN Nmap SYN Scan", "192.168.50.10", [22, 80, 443, 445, 3306, 8080], 12)
add_inc("INC-002", "192.168.50.31", (10,2), (10,9), "High", "ET SCAN SSH Brute Force Attempt", "192.168.50.10", [22], 8)
add_inc("INC-003", "192.168.50.44", (11,30), (11,34), "Medium", "ET DNS Query to Suspicious TLD", "192.168.50.1", [53], 6, sev=2)
add_inc("INC-004", "192.168.50.23", (8,5), (8,7), "Low", "ET SCAN ICMP Ping Sweep", "192.168.50.255", [0], 5, sev=1)
add_inc("INC-005", "192.168.50.57", (11,41), (11,44), "Medium", "ET WEB_SERVER SQL Injection Attempt", "192.168.50.10", [80], 3, sev=2)
# a few Zeek conn records for .23 so sensor filtering is testable
for i in range(4):
    events.append(dict(event_id=str(uuid.UUID(int=random.getrandbits(128))), timestamp=ts(9, 14+i%3, 10+i),
        src_ip="192.168.50.23", dst_ip="192.168.50.10", src_port=random.randint(40000, 60000),
        dst_port=[22, 80, 443, 445][i], protocol="tcp", sensor="zeek", severity=0, signature=None))
events.sort(key=lambda e: e["timestamp"])
json.dump(events, open("data/events.json", "w"), indent=1)
json.dump(incidents, open("data/incidents.json", "w"), indent=1)
print(len(events), "events;", len(incidents), "incidents")
