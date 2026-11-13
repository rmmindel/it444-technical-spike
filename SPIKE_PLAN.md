# Spike plan (written BEFORE any test run)

**Requirement:** FR-09 (hunt assistant claims must come from tool results), with FR-10 (correct search_events call), FR-08 (answer in 30 s), FR-15 (tool calls shown).

**Question (yes/no):** Can a local open-weight model (<=8B, run through Ollama) act as the hunt assistant so that, on a fixed set of 20 questions (5 with no matching data), it:
1. puts zero IPs, timestamps, or counts in its answers that are absent from the tool results, AND
2. says "no data found" in all 5 empty cases, AND
3. answers within 30 s in at least 19 of 20 questions?

**Pass mark (all must hold, for at least one model):**
- Fabricated values: 0 across 20 answers
- Empty cases handled: 5 of 5
- Correct tool + arguments (FR-10): at least 18 of 20 on the 15 data questions' tool selection
- Latency: at least 19 of 20 under 30 s

**Setup:** Python harness + 3 seeded JSON event files (no OpenSearch), tools search_events / get_ip_history / get_incident_details, loop capped at 3 tool calls (as in D4 Part C). Models compared: llama3.1:8b, qwen2.5:7b-instruct, mistral:7b-instruct (plus a larger model if the GPU host allows).
**Time box:** one day.
**If it fails:** fallback = tighter tool schemas + prompt rules + deterministic post-check that blocks answers containing unseen values.
