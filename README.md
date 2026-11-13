# IT 444 Technical Spike - Hunt assistant grounding (FR-09) and dashboard
Run on a MacBook (Apple M5, 24 GB) with Ollama 0.40 and three local models.
- SPIKE_PLAN.md - question and pass mark (first commit, before any run)
- make_data.py, data/ - seeded events/incidents (stand-in for OpenSearch)
- assistant.py - hunt-assistant chat loop + 3 tools; server.py - dashboard + POST /chat
- questions.json - the 20 questions (5 with no matching data)
- run_spike.py <model> - scores one model; results/ holds raw JSON + logs for every run
- fr13_test.py, fr16_test.py - dashboard checks; evidence/ - screenshot
Reproduce: `ollama serve`; `ollama pull llama3.1:8b`; `python3 -s run_spike.py llama3.1:8b`; `python3 -s server.py` -> http://localhost:8444
