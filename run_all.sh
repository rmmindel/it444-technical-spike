#!/bin/bash
# Runs the full 20-question spike on all three models, one after another.
# Writes to results_live/ so the original saved results in results/ are not overwritten.
cd "$(dirname "$0")"
curl -s localhost:11434 >/dev/null || { echo "Ollama is not running. Start it with: ollama serve"; exit 1; }
export RESULTS_DIR=results_live
for m in llama3.1:8b qwen2.5:7b-instruct mistral:7b-instruct; do
  echo; echo "################ $m ################"
  python3 -s run_spike.py "$m"
done
