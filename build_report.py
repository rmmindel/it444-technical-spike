import os, subprocess
REPO = os.environ.get("REPO_URL", "REPO_URL_HERE")
html = f"""<!doctype html><meta charset=utf-8><title>Spike Report</title>
<style>@page{{size:Letter;margin:0.5in}}body{{font:9.4pt/1.25 Helvetica,Arial,sans-serif;color:#111}}
h1{{font-size:14pt;margin:0 0 2px}}h2{{font-size:10.5pt;margin:7px 0 2px;border-bottom:1px solid #999}}p{{margin:2px 0}}ul{{margin:2px 0 2px 16px;padding:0}}li{{margin:0}}
table{{border-collapse:collapse;width:100%;margin:3px 0;font-size:8.6pt}}td,th{{border:1px solid #888;padding:1.5px 4px;text-align:left}}th{{background:#e8e8e8}}.s{{font-size:8.4pt;color:#333}}</style>
<h1>IT 444 Individual Technical Spike Report</h1>
<p class=s><b>Ryan Mindel</b> | Team 09 (AI security assistant for home networks) | Risk from D4 Part G: hunt-assistant grounding | Run on 13 Nov 2026</p>

<h2>1. Question and pass mark (written and committed before any test ran)</h2>
<p><b>Requirement:</b> FR-09 (every factual claim comes from tool results), with FR-10, FR-08, FR-15, FR-16. This is D1's riskiest element, and D3 moved us from a hosted API to a local model.</p>
<p><b>Question:</b> Can a local open-weight model (7-8B, through Ollama) run the hunt assistant so that, on 20 fixed questions (5 with no matching data), it invents no IP, timestamp or count, says "no data found" in all 5 empty cases, picks the right tool, and answers within 30 s?</p>
<p><b>Pass mark (all must hold, for at least one model):</b> 0 answers containing a value not in the tool results; 5/5 empty cases; at least 18/20 correct tool and arguments; at least 19/20 answers under 30 s. A second, smaller check covered the dashboard: FR-13 (new alert visible within 15 s, 19 of 20 trials) and FR-16 (chat opened from an incident uses that incident without the user restating it).</p>

<h2>2. Setup (smallest that answers it)</h2>
<p>MacBook, Apple M5, 24 GB. Ollama with llama3.1:8b, qwen2.5:7b-instruct and mistral:7b-instruct (default 4-bit builds), temperature 0. Python harness with the three D4 tools (search_events, get_ip_history, get_incident_details) over 38 seeded events and 5 incidents in JSON (no OpenSearch), tool loop capped at 3 calls, fixed clock. A scorer extracts every IP, timestamp and number from each answer and checks it against the tool results and the user's question. A small web dashboard (live alerts, incidents sorted by severity, chat with tool calls shown, "Ask about this incident") calls the same assistant code through POST /chat. Time box: one day. The GPU home server was not used (see limits).</p>

<h2>3. Results</h2>
<table><tr><th>Model</th><th>Answers with unseen values (need 0)</th><th>Empty cases (need 5/5)</th><th>Right tool (need 18+/20)</th><th>Under 30 s (need 19+/20)</th><th>Median s</th><th>Result</th></tr>
<tr><td>llama3.1:8b</td><td>3 (4 values)</td><td>5/5</td><td>20/20</td><td>20/20</td><td>4.6</td><td><b>FAIL</b></td></tr>
<tr><td>qwen2.5:7b</td><td>1 (2 values)</td><td>5/5</td><td>19/20</td><td>20/20</td><td>7.0</td><td><b>FAIL</b></td></tr>
<tr><td>mistral:7b</td><td>9 (27 values)</td><td>2/5</td><td>6/20</td><td>19/20</td><td>10.0</td><td><b>FAIL</b></td></tr></table>
<ul>
<li><b>No model passed the pass mark as written.</b> Llama's tool calls were all correct (20/20). Its 4 flagged values sit in 3 answers (Q16, Q18, Q20); in each the model correctly said "No data found" and then repeated the search window it had sent itself in its own tool call (e.g. 2026-11-11T02:00:00Z). Qwen did the same on Q20. By the strict FR-09 wording these count as failures, but they are echoes of the query, not invented facts about the network.</li>
<li>Qwen invented an argument on Q11 (<i>incident_123456</i>, which does not exist). The tool returned an error and the answer was safe, but the model does make up identifiers.</li>
<li>Mistral printed its tool call as text instead of calling the tool, so 14 of 20 questions had no valid tool call, and it filled gaps on empty cases.</li>
<li><b>Follow-up variants</b> (kept separate from the scored run): a tighter prompt rule for empty cases cut Llama from 3 failing answers to 1 (Q20) and left Qwen at 1. Neither reached 0.</li>
<li><b>Dashboard:</b> FR-13 passed 20/20, max 0.02 s, but this is trivial because the feed is in memory on the same machine; it says nothing about the real sensor-to-OpenSearch path. <b>FR-16 failed 0/5</b> on both Llama and Qwen when the incident was only mentioned in the system prompt (Llama searched all events; Qwen asked which incident). When the dashboard put the incident ID and source IP into the user message, FR-16 passed 5/5 on both.</li></ul>

<h2>4. What it means for our design</h2>
<p><b>Decision: keep the local-model design (it satisfies the approved-software and privacy constraints), but do not rely on the model alone for FR-09.</b> Llama 3.1 8B is the primary candidate; Qwen 2.5 7B is the backup; Mistral 7B is dropped. The prompt alone does not get us to zero, so we move to the fallback we already named in D4 Part F:</p>
<ul>
<li><b>Output guard in the Hunt Assistant.</b> Reuse the Summarizer's indicator check: every IP, timestamp and count in an answer must appear in the tool results. If a tool returns zero results or an error, the code (not the model) returns "No data found for X". This would have fixed every flagged answer in this run, though that is untested. New component requirement for D2/D4 Part B.</li>
<li><b>Validate tool arguments</b> against known IDs and IPs, so a made-up incident ID returns an error instead of reaching the model.</li>
<li><b>Dashboard injects incident context</b> (ID and IP) into the chat message for FR-16. Update the Dashboard-to-Hunt Assistant contract in D4 Part C.</li>
<li><b>Reword FR-09's acceptance criterion</b> to say what counts as "tool results" (whether echoed query parameters are allowed), so the test is unambiguous. Raise it with the team and advisor.</li></ul>
<p><b>IT 445 should first:</b> (1) build the guard and rerun the same 20 questions, expecting 0 unseen values; (2) enlarge the question set well beyond 20, since 20 questions and one run at temperature 0 cannot show a rate of zero; (3) repeat on the lab GPU host with a larger model to see whether it passes without the guard; (4) retest FR-13 against real Suricata and OpenSearch. <b>Tell the team:</b> Michael (Summarizer shares the guard), Jack (query contract), and Austin (GPU sizing may need to fit a larger model).</p>

<h2>5. Limits of this result</h2>
<p>Run on a laptop, not the planned GPU host, so absolute latency is not representative and larger models were not tested. Events are 38 seeded records in JSON, not OpenSearch. I wrote the 20 questions myself, one run per model. The scorer checks for unseen values only; it does not check whether non-fabricated statements are correct or well reasoned. Models were 4-bit quantized Ollama builds. The pass mark was kept as set before the run.</p>

<h2>6. Evidence</h2>
<ul>
<li>Repository with commits (the plan and pass mark are the first commit, before any results): {REPO}</li>
<li>In the repository: <i>SPIKE_PLAN.md</i> (first commit); <i>results/</i> raw JSON and logs for every run (all answers, tool calls, latencies); <i>run_spike.py</i>, <i>assistant.py</i>, <i>server.py</i>; <i>evidence/dashboard_chat_screenshot.jpg</i> (dashboard with a "No data found" answer and tool calls shown under each answer).</li>
<li>Screen recording: RECORDING_URL_HERE</li></ul>"""
open("report.html", "w").write(html)
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu", "--no-pdf-header-footer",
                "--print-to-pdf=Mindel_Ryan_Spike.pdf", "file://" + os.path.abspath("report.html")], capture_output=True)
