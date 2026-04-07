#!/bin/bash
apt-get update && apt-get install -y wget nano
wget -O /app/tagger_script.py https://raw.githubusercontent.com/hnaka488-maker/immich_auto_taggar/refs/heads/main/tagger_script.py
python3 -m vllm.entrypoints.openai.api_server --model /workspace/model/Qwen2.5-VL-7B-Instruct --trust-remote-code --max-model-len 4096 --gpu-memory-utilization 0.9 > /app/engine.log 2>&1 &
sleep 120
python3 /app/tagger_script.py
